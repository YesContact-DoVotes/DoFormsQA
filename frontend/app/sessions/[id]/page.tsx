"use client";

import { useEffect, useState, useRef, use } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import { 
  getSession, 
  getSessionScenarios, 
  getSessionSteps, 
  getSessionFindings, 
  getSessionReport, 
  getSessionRegressionTests, 
  stopSession, 
  TestSession, 
  Scenario, 
  TestStep, 
  Finding, 
  FullReport, 
  RegressionTest,
  WS_BASE 
} from "@/lib/api";
import { StatusBadge } from "@/components/Badge";
import { ScreenshotModal } from "@/components/ScreenshotModal";

export default function SessionLivePage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const sessionId = parseInt(resolvedParams.id, 10);

  // Core Data State
  const [session, setSession] = useState<TestSession | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [steps, setSteps] = useState<TestStep[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [report, setReport] = useState<FullReport | null>(null);
  const [regressionTests, setRegressionTests] = useState<RegressionTest[]>([]);
  const [loading, setLoading] = useState(true);

  // Active View Tabs: 'live' | 'findings' | 'report' | 'tests'
  const [activeTab, setActiveTab] = useState<"live" | "findings" | "report" | "tests">("live");
  const [selectedScenarioId, setSelectedScenarioId] = useState<number | null>(null);

  // Screenshot Lightbox Modal State
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [previewTitle, setPreviewTitle] = useState<string>("");

  // Code Copy State
  const [copiedCode, setCopiedCode] = useState(false);
  const [copiedReport, setCopiedReport] = useState(false);

  const stepsEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    loadInitialData();
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [sessionId]);

  useEffect(() => {
    if (activeTab === "live" && stepsEndRef.current) {
      stepsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [steps, activeTab]);

  async function loadInitialData() {
    try {
      setLoading(true);
      const [sessData, scData, stepsData, findData] = await Promise.all([
        getSession(sessionId),
        getSessionScenarios(sessionId),
        getSessionSteps(sessionId),
        getSessionFindings(sessionId),
      ]);
      setSession(sessData);
      setScenarios(scData);
      setSteps(stepsData);
      setFindings(findData);

      if (sessData.status === "COMPLETED" || sessData.report_markdown) {
        try {
          const [rep, reg] = await Promise.all([
            getSessionReport(sessionId),
            getSessionRegressionTests(sessionId),
          ]);
          setReport(rep);
          setRegressionTests(reg);
        } catch (e) {
          console.error(e);
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  function connectWebSocket() {
    const wsUrl = `${WS_BASE}/sessions/${sessionId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        const { event: eventType, data } = message;

        if (eventType === "session.status_change" || eventType === "session.started" || eventType === "session.completed") {
          setSession((prev) => prev ? { ...prev, status: data.status || prev.status, actions_used: data.actions_used ?? prev.actions_used } : null);
          if (eventType === "session.completed") {
            loadInitialData();
          }
        } else if (eventType === "scenario.created") {
          setScenarios((prev) => {
            if (prev.some((s) => s.id === data.id)) return prev;
            return [...prev, data];
          });
        } else if (eventType === "scenario.started") {
          setScenarios((prev) =>
            prev.map((s) => (s.id === data.id ? { ...s, status: "RUNNING" } : s))
          );
        } else if (eventType === "scenario.completed") {
          setScenarios((prev) =>
            prev.map((s) => (s.id === data.id ? { ...s, status: data.status } : s))
          );
        } else if (eventType === "action.executed") {
          setSteps((prev) => [
            ...prev,
            {
              id: data.step_id || Date.now(),
              scenario_id: data.scenario_id,
              action: data.action,
              target: data.target,
              value: data.value,
              result: data.result,
              url: data.url,
              thought: data.thought,
              screenshot_path: data.screenshot_path,
              duration_ms: data.duration_ms || 0,
              created_at: new Date().toISOString(),
            },
          ]);
          setSession((prev) =>
            prev ? { ...prev, actions_used: data.actions_used } : null
          );
        } else if (eventType === "finding.created") {
          setFindings((prev) => [data, ...prev.filter((f) => f.id !== data.id)]);
        } else if (eventType === "finding.confirmed" || eventType === "finding.rejected" || eventType === "finding.verifying") {
          setFindings((prev) =>
            prev.map((f) => (f.id === data.id ? { ...f, status: data.status, reproduced: data.reproduced } : f))
          );
        } else if (eventType === "report.generated") {
          setReport({
            session_id: sessionId,
            markdown: data.report_markdown,
            summary: {} as any,
            coverage: [],
          });
        } else if (eventType === "regression_test.created") {
          setRegressionTests((prev) => [...prev, data]);
        }
      } catch (err) {
        console.error("WS Parse error:", err);
      }
    };

    ws.onclose = () => {
      // Reconnect after 3s if session is still running
      if (session?.status === "RUNNING" || session?.status === "PLANNING") {
        setTimeout(connectWebSocket, 3000);
      }
    };
  }

  async function handleStop() {
    if (!confirm("Are you sure you want to stop this QA session?")) return;
    try {
      await stopSession(sessionId);
      await loadInitialData();
    } catch (e) {
      alert("Failed to stop session: " + (e as Error).message);
    }
  }

  const passedScenarios = scenarios.filter((s) => s.status === "PASSED").length;
  const failedScenarios = scenarios.filter((s) => s.status === "FAILED").length;

  const filteredSteps = selectedScenarioId
    ? steps.filter((st) => st.scenario_id === selectedScenarioId)
    : steps;

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      {/* Top Breadcrumb & Controls */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between mb-6">
        <div>
          <Link
            href={session ? `/projects/${session.project_id}` : "/"}
            className="inline-block text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors mb-1.5"
          >
            &larr; Back to Project
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-slate-900">
              Session #{sessionId}
            </h1>
            {session && <StatusBadge status={session.status} />}
          </div>
          <p className="text-xs text-slate-500 mt-0.5 line-clamp-1 max-w-xl">
            {session?.mission}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {(session?.status === "RUNNING" || session?.status === "PLANNING") && (
            <button
              onClick={handleStop}
              className="rounded-md border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700 hover:bg-rose-100 transition-colors cursor-pointer"
            >
              Stop Session
            </button>
          )}

          <button
            onClick={loadInitialData}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 shadow-xs cursor-pointer"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Metrics Bar */}
      {session && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-5 mb-6">
          <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-xs">
            <div className="text-slate-500 text-xs mb-1">Actions</div>
            <div className="text-base font-bold text-slate-900 font-mono">
              {session.actions_used} <span className="text-xs font-normal text-slate-400">/ {session.max_actions}</span>
            </div>
            <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full bg-blue-600 transition-all duration-300"
                style={{ width: `${Math.min((session.actions_used / session.max_actions) * 100, 100)}%` }}
              />
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-xs">
            <div className="text-slate-500 text-xs mb-1">Scenarios</div>
            <div className="text-base font-bold text-slate-900 font-mono flex items-center gap-1.5">
              <span className="text-emerald-600">{passedScenarios}</span>
              <span className="text-slate-300">/</span>
              <span className="text-rose-600">{failedScenarios}</span>
              <span className="text-slate-300">/</span>
              <span className="text-slate-600">{scenarios.length}</span>
            </div>
            <p className="mt-1 text-[11px] text-slate-400">Passed / Failed / Total</p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-xs">
            <div className="text-slate-500 text-xs mb-1">Findings</div>
            <div className="text-base font-bold text-slate-900 font-mono">
              {findings.length}
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              {findings.filter((f) => f.status === "CONFIRMED").length} confirmed
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-xs">
            <div className="text-slate-500 text-xs mb-1">AI Calls</div>
            <div className="text-base font-bold text-slate-900 font-mono">
              {session.ai_calls_count}
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              ${(session.estimated_cost || 0).toFixed(4)}
            </p>
          </div>

          <div className="col-span-2 sm:col-span-4 lg:col-span-1 rounded-xl border border-slate-200 bg-white p-3.5 shadow-xs">
            <div className="text-slate-500 text-xs mb-1">Status</div>
            <div className="text-sm font-semibold text-slate-900 truncate">
              {session.status}
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              {session.finished_at ? "Finished" : "Running"}
            </p>
          </div>
        </div>
      )}

      {/* Tabs Navigation */}
      <div className="flex border-b border-slate-200 mb-6 gap-2">
        <button
          onClick={() => setActiveTab("live")}
          className={`px-3.5 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
            activeTab === "live"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-slate-500 hover:text-slate-900"
          }`}
        >
          Live Action Log ({steps.length})
        </button>

        <button
          onClick={() => setActiveTab("findings")}
          className={`px-3.5 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
            activeTab === "findings"
              ? "border-amber-600 text-amber-700"
              : "border-transparent text-slate-500 hover:text-slate-900"
          }`}
        >
          Findings ({findings.length})
        </button>

        <button
          onClick={() => {
            setActiveTab("report");
            if (!report) getSessionReport(sessionId).then(setReport).catch(console.error);
          }}
          className={`px-3.5 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
            activeTab === "report"
              ? "border-emerald-600 text-emerald-700"
              : "border-transparent text-slate-500 hover:text-slate-900"
          }`}
        >
          Report (report.md)
        </button>

        <button
          onClick={() => {
            setActiveTab("tests");
            if (regressionTests.length === 0) getSessionRegressionTests(sessionId).then(setRegressionTests).catch(console.error);
          }}
          className={`px-3.5 py-2 text-xs font-semibold border-b-2 transition-colors cursor-pointer ${
            activeTab === "tests"
              ? "border-purple-600 text-purple-700"
              : "border-transparent text-slate-500 hover:text-slate-900"
          }`}
        >
          Regression Tests ({regressionTests.length})
        </button>
      </div>

      {/* TAB 1: Live Actions & Test Plan */}
      {activeTab === "live" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* Left Column: Scenarios Plan Tree */}
          <div className="lg:col-span-4 flex flex-col rounded-xl border border-slate-200 bg-white p-4 max-h-[700px] shadow-xs">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Test Plan ({scenarios.length})
              </h3>
              {selectedScenarioId && (
                <button
                  onClick={() => setSelectedScenarioId(null)}
                  className="text-[11px] text-blue-600 hover:underline cursor-pointer"
                >
                  All Steps
                </button>
              )}
            </div>

            <div className="space-y-2 overflow-y-auto pr-1 flex-1">
              {scenarios.map((sc) => {
                const isSelected = selectedScenarioId === sc.id;
                return (
                  <div
                    key={sc.id}
                    onClick={() => setSelectedScenarioId(isSelected ? null : sc.id)}
                    className={`p-2.5 rounded-lg border cursor-pointer transition-all ${
                      isSelected
                        ? "border-blue-500 bg-blue-50/50"
                        : "border-slate-200 bg-slate-50/70 hover:border-slate-300"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-xs font-medium text-slate-900 line-clamp-2">
                        {sc.title}
                      </span>
                      <StatusBadge status={sc.status} />
                    </div>

                    <div className="mt-1.5 flex items-center justify-between text-[10px] text-slate-500">
                      <span>{sc.area}</span>
                      <span className="font-mono">{sc.priority}</span>
                    </div>
                  </div>
                );
              })}
              {scenarios.length === 0 && (
                <div className="py-8 text-center text-xs text-slate-400">
                  Planning scenarios...
                </div>
              )}
            </div>
          </div>

          {/* Center Column: Live Action Stream */}
          <div className="lg:col-span-8 flex flex-col rounded-xl border border-slate-200 bg-white p-4 max-h-[700px] shadow-xs">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Action Log {selectedScenarioId ? "(Filtered)" : ""}
              </h3>
              <span className="text-xs font-mono text-slate-500">{filteredSteps.length} steps</span>
            </div>

            <div className="space-y-2.5 overflow-y-auto pr-1 flex-1 font-mono text-xs">
              {filteredSteps.map((step, idx) => (
                <div
                  key={step.id || idx}
                  className="rounded-lg border border-slate-200 bg-slate-50/60 p-3 hover:border-slate-300 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-blue-700 uppercase">
                        {step.action}
                      </span>
                      {step.target && (
                        <span className="text-slate-700 truncate max-w-[280px]">
                          target: <span className="text-slate-900">{step.target}</span>
                        </span>
                      )}
                      {step.value && (
                        <span className="text-slate-500 text-[11px] truncate max-w-[150px]">
                          &quot;{step.value}&quot;
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 text-[10px]">
                      {step.result === "success" ? (
                        <span className="text-emerald-700 font-semibold">OK</span>
                      ) : (
                        <span className="text-rose-700 font-semibold">ERR</span>
                      )}
                      <span className="text-slate-400">{step.duration_ms.toFixed(0)}ms</span>
                    </div>
                  </div>

                  {step.thought && (
                    <p className="text-[11px] font-sans text-slate-600 mb-1.5 bg-white rounded px-2 py-1 border border-slate-200">
                      Thought: {step.thought}
                    </p>
                  )}

                  <div className="flex items-center justify-between text-[10px] text-slate-400">
                    <span className="truncate max-w-[350px]">URL: {step.url || "N/A"}</span>

                    {step.screenshot_path && (
                      <button
                        onClick={() => {
                          setPreviewImage(step.screenshot_path!);
                          setPreviewTitle(`Step #${idx + 1}: ${step.action} ${step.target || ""}`);
                        }}
                        className="text-blue-600 hover:underline font-medium cursor-pointer"
                      >
                        Screenshot
                      </button>
                    )}
                  </div>
                </div>
              ))}

              {filteredSteps.length === 0 && (
                <div className="flex h-60 flex-col items-center justify-center text-slate-400 text-xs">
                  Waiting for actions to execute...
                </div>
              )}
              <div ref={stepsEndRef} />
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: Findings & Evidences */}
      {activeTab === "findings" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900">Findings & Verification</h3>
            <span className="text-xs text-slate-500">{findings.length} findings</span>
          </div>

          {findings.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
              <h4 className="text-sm font-semibold text-slate-800">No Bugs Detected</h4>
              <p className="mt-1 text-xs text-slate-500">
                Issues will be automatically verified and listed here.
              </p>
            </div>
          ) : (
            <div className="grid gap-3.5">
              {findings.map((finding) => (
                <div
                  key={finding.id}
                  className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-slate-100">
                    <h4 className="text-sm font-bold text-slate-900">{finding.title}</h4>
                    <div className="flex items-center gap-2">
                      <StatusBadge status={finding.severity} />
                      <StatusBadge status={finding.status} />
                    </div>
                  </div>

                  <p className="mt-2.5 text-xs text-slate-700">{finding.description}</p>

                  <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2.5 text-xs">
                    {finding.expected_behavior && (
                      <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
                        <span className="font-semibold text-slate-700 block mb-0.5">Expected:</span>
                        <p className="text-slate-600">{finding.expected_behavior}</p>
                      </div>
                    )}
                    {finding.actual_behavior && (
                      <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
                        <span className="font-semibold text-rose-700 block mb-0.5">Actual:</span>
                        <p className="text-rose-900">{finding.actual_behavior}</p>
                      </div>
                    )}
                  </div>

                  {finding.reproduction_steps && (
                    <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-xs">
                      <span className="font-semibold text-slate-700 block mb-0.5 font-mono">Reproduction Steps:</span>
                      <pre className="text-slate-700 font-mono whitespace-pre-wrap">{finding.reproduction_steps}</pre>
                    </div>
                  )}

                  {/* Evidences (Screenshots) */}
                  {finding.evidences && finding.evidences.length > 0 && (
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      <span className="text-xs text-slate-500">Evidence:</span>
                      {finding.evidences.map((ev) => (
                        <button
                          key={ev.id}
                          onClick={() => {
                            setPreviewImage(ev.path);
                            setPreviewTitle(`Evidence for: ${finding.title}`);
                          }}
                          className="rounded border border-slate-300 bg-white px-2 py-0.5 text-xs text-blue-600 hover:bg-slate-50 font-medium cursor-pointer"
                        >
                          Screenshot
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: QA Markdown Report */}
      {activeTab === "report" && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
            <h3 className="text-sm font-bold text-slate-900">QA Report (report.md)</h3>
            <button
              onClick={() => {
                if (report?.markdown) {
                  navigator.clipboard.writeText(report.markdown);
                  setCopiedReport(true);
                  setTimeout(() => setCopiedReport(false), 2000);
                }
              }}
              className="rounded-md bg-blue-600 px-3 py-1 text-xs font-semibold text-white hover:bg-blue-700 transition-colors cursor-pointer"
            >
              {copiedReport ? "Copied" : "Copy Markdown"}
            </button>
          </div>

          <div className="prose prose-slate max-w-none prose-headings:font-bold prose-headings:text-slate-900 prose-h1:text-lg prose-h2:text-base prose-table:text-xs prose-pre:bg-slate-900 prose-pre:text-slate-100 prose-pre:rounded-lg">
            {report?.markdown ? (
              <ReactMarkdown>{report.markdown}</ReactMarkdown>
            ) : (
              <div className="py-10 text-center text-slate-400 text-xs">
                Generating comprehensive report after session completion...
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: Playwright Regression Tests */}
      {activeTab === "tests" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900">Playwright Regression Tests</h3>
          </div>

          {regressionTests.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
              <h4 className="text-sm font-semibold text-slate-800">No Regression Tests Generated Yet</h4>
              <p className="mt-1 text-xs text-slate-500">
                Tests are generated automatically for confirmed findings.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {regressionTests.map((t) => (
                <div key={t.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100 mb-3">
                    <span className="font-mono text-xs font-bold text-slate-900">{t.name}</span>

                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(t.test_code);
                        setCopiedCode(true);
                        setTimeout(() => setCopiedCode(false), 2000);
                      }}
                      className="text-xs text-slate-700 hover:text-slate-900 rounded border border-slate-300 bg-white px-2 py-0.5 cursor-pointer"
                    >
                      {copiedCode ? "Copied" : "Copy Code"}
                    </button>
                  </div>

                  <pre className="rounded-lg bg-slate-900 text-slate-100 p-3.5 font-mono text-xs overflow-x-auto">
                    {t.test_code}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Lightbox Screenshot Modal */}
      <ScreenshotModal
        isOpen={Boolean(previewImage)}
        onClose={() => setPreviewImage(null)}
        imageUrl={previewImage || ""}
        title={previewTitle}
      />
    </div>
  );
}
