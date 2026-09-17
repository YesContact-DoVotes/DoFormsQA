"use client";

import { useEffect, useState, useRef, use } from "react";
import Link from "next/link";
import { 
  ArrowLeft, 
  Play, 
  Square, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Clock, 
  Bug, 
  Terminal, 
  Cpu, 
  DollarSign, 
  Image as ImageIcon, 
  FileCode, 
  FileText, 
  Layers, 
  ShieldAlert, 
  Copy, 
  Check, 
  ExternalLink,
  ChevronRight,
  Maximize2
} from "lucide-react";
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
  const blockedScenarios = scenarios.filter((s) => s.status === "BLOCKED").length;

  const filteredSteps = selectedScenarioId
    ? steps.filter((st) => st.scenario_id === selectedScenarioId)
    : steps;

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      {/* Top Breadcrumb & Controls */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between mb-6">
        <div className="flex items-center gap-3">
          <Link
            href={session ? `/projects/${session.project_id}` : "/"}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
            title="Back to Project"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-extrabold text-white">
                QA Session #{sessionId}
              </h1>
              {session && <StatusBadge status={session.status} />}
            </div>
            <p className="text-xs text-slate-400 mt-0.5 line-clamp-1 max-w-xl">
              {session?.mission}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {(session?.status === "RUNNING" || session?.status === "PLANNING") && (
            <button
              onClick={handleStop}
              className="inline-flex items-center gap-1.5 rounded-lg bg-rose-500/10 border border-rose-500/30 px-3.5 py-1.5 text-xs font-semibold text-rose-400 hover:bg-rose-500/20 transition-colors"
            >
              <Square className="h-3.5 w-3.5 fill-rose-400" />
              Stop Session
            </button>
          )}

          <button
            onClick={loadInitialData}
            className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-800"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Metrics Bar */}
      {session && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-5 mb-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 backdrop-blur-sm">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Action Budget</span>
              <Terminal className="h-3.5 w-3.5 text-blue-400" />
            </div>
            <div className="text-lg font-bold text-white font-mono">
              {session.actions_used} <span className="text-xs text-slate-500">/ {session.max_actions}</span>
            </div>
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
              <div
                className="h-full bg-blue-500 transition-all duration-300"
                style={{ width: `${Math.min((session.actions_used / session.max_actions) * 100, 100)}%` }}
              />
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 backdrop-blur-sm">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Scenarios</span>
              <Layers className="h-3.5 w-3.5 text-indigo-400" />
            </div>
            <div className="text-lg font-bold text-white font-mono flex items-center gap-1.5">
              <span className="text-emerald-400">{passedScenarios}</span>
              <span className="text-slate-600">/</span>
              <span className="text-rose-400">{failedScenarios}</span>
              <span className="text-slate-600">/</span>
              <span className="text-slate-400">{scenarios.length}</span>
            </div>
            <p className="mt-1 text-[11px] text-slate-400">Passed / Failed / Planned</p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 backdrop-blur-sm">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Findings</span>
              <Bug className="h-3.5 w-3.5 text-amber-400" />
            </div>
            <div className="text-lg font-bold text-amber-400 font-mono">
              {findings.length}
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              {findings.filter((f) => f.status === "CONFIRMED").length} Confirmed Bugs
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 backdrop-blur-sm">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>AI Engine Calls</span>
              <Cpu className="h-3.5 w-3.5 text-purple-400" />
            </div>
            <div className="text-lg font-bold text-white font-mono">
              {session.ai_calls_count}
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              Est. Cost: ${(session.estimated_cost || 0).toFixed(4)}
            </p>
          </div>

          <div className="col-span-2 sm:col-span-4 lg:col-span-1 rounded-xl border border-slate-800 bg-slate-900/60 p-3.5 backdrop-blur-sm">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
              <span>Status</span>
              <Clock className="h-3.5 w-3.5 text-slate-400" />
            </div>
            <div className="text-sm font-semibold text-white truncate">
              {session.status}
            </div>
            <p className="mt-1 text-[11px] text-slate-400">
              {session.finished_at ? "Finished" : "In Progress"}
            </p>
          </div>
        </div>
      )}

      {/* Tabs Navigation */}
      <div className="flex border-b border-slate-800 mb-6 gap-2">
        <button
          onClick={() => setActiveTab("live")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
            activeTab === "live"
              ? "border-blue-500 text-blue-400 bg-blue-500/5"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Terminal className="h-4 w-4" />
          Live Action Feed & Plan ({steps.length})
        </button>

        <button
          onClick={() => setActiveTab("findings")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
            activeTab === "findings"
              ? "border-amber-500 text-amber-400 bg-amber-500/5"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Bug className="h-4 w-4" />
          Findings & Evidence ({findings.length})
        </button>

        <button
          onClick={() => {
            setActiveTab("report");
            if (!report) getSessionReport(sessionId).then(setReport).catch(console.error);
          }}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
            activeTab === "report"
              ? "border-emerald-500 text-emerald-400 bg-emerald-500/5"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileText className="h-4 w-4" />
          QA Report (report.md)
        </button>

        <button
          onClick={() => {
            setActiveTab("tests");
            if (regressionTests.length === 0) getSessionRegressionTests(sessionId).then(setRegressionTests).catch(console.error);
          }}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
            activeTab === "tests"
              ? "border-purple-500 text-purple-400 bg-purple-500/5"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileCode className="h-4 w-4" />
          Regression Tests ({regressionTests.length})
        </button>
      </div>

      {/* TAB 1: Live Actions & Test Plan */}
      {activeTab === "live" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Scenarios Plan Tree */}
          <div className="lg:col-span-4 flex flex-col rounded-2xl border border-slate-800 bg-slate-900/60 p-4 max-h-[700px]">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Test Plan ({scenarios.length})
              </h3>
              {selectedScenarioId && (
                <button
                  onClick={() => setSelectedScenarioId(null)}
                  className="text-[11px] text-blue-400 hover:underline"
                >
                  Show All Steps
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
                    className={`p-3 rounded-xl border cursor-pointer transition-all ${
                      isSelected
                        ? "border-blue-500 bg-blue-500/10 shadow-md"
                        : "border-slate-800 bg-slate-950/60 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-xs font-semibold text-white line-clamp-2">
                        {sc.title}
                      </span>
                      <StatusBadge status={sc.status} />
                    </div>

                    <div className="mt-2 flex items-center justify-between text-[10px] text-slate-400">
                      <span className="rounded bg-slate-800 px-1.5 py-0.5 text-slate-300 font-medium">
                        {sc.area}
                      </span>
                      <span className="font-mono text-slate-500">Priority: {sc.priority}</span>
                    </div>
                  </div>
                );
              })}
              {scenarios.length === 0 && (
                <div className="py-8 text-center text-xs text-slate-500">
                  Planning scenarios...
                </div>
              )}
            </div>
          </div>

          {/* Center Column: Live Action Stream */}
          <div className="lg:col-span-8 flex flex-col rounded-2xl border border-slate-800 bg-slate-900/60 p-4 max-h-[700px]">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Terminal className="h-4 w-4 text-blue-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  Live Action Log {selectedScenarioId ? "(Filtered by Scenario)" : ""}
                </h3>
              </div>
              <span className="text-xs font-mono text-slate-400">{filteredSteps.length} recorded steps</span>
            </div>

            <div className="space-y-3 overflow-y-auto pr-2 flex-1 font-mono text-xs">
              {filteredSteps.map((step, idx) => (
                <div
                  key={step.id || idx}
                  className="rounded-xl border border-slate-800/80 bg-slate-950/80 p-3.5 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-blue-500/20 text-blue-300 font-bold px-2 py-0.5 text-[11px] border border-blue-500/30 uppercase">
                        {step.action}
                      </span>
                      {step.target && (
                        <span className="text-slate-300 font-medium truncate max-w-[280px]">
                          target: <span className="text-white font-semibold">{step.target}</span>
                        </span>
                      )}
                      {step.value && (
                        <span className="text-slate-400 text-[11px] truncate max-w-[150px]">
                          val: &quot;{step.value}&quot;
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 text-[10px]">
                      {step.result === "success" ? (
                        <span className="text-emerald-400 flex items-center gap-1 font-semibold">
                          <CheckCircle2 className="h-3 w-3" /> OK
                        </span>
                      ) : (
                        <span className="text-rose-400 flex items-center gap-1 font-semibold">
                          <XCircle className="h-3 w-3" /> Error
                        </span>
                      )}
                      <span className="text-slate-500">{step.duration_ms.toFixed(0)}ms</span>
                    </div>
                  </div>

                  {step.thought && (
                    <p className="text-[11px] font-sans text-slate-400 mb-2 italic bg-slate-900/60 rounded px-2 py-1 border border-slate-800">
                      💡 Thought: {step.thought}
                    </p>
                  )}

                  <div className="flex items-center justify-between text-[10px] text-slate-500">
                    <span className="truncate max-w-[350px]">URL: {step.url || "N/A"}</span>

                    {step.screenshot_path && (
                      <button
                        onClick={() => {
                          setPreviewImage(step.screenshot_path!);
                          setPreviewTitle(`Step #${idx + 1}: ${step.action} ${step.target || ""}`);
                        }}
                        className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 hover:underline"
                      >
                        <ImageIcon className="h-3 w-3" />
                        View Screenshot
                      </button>
                    )}
                  </div>
                </div>
              ))}

              {filteredSteps.length === 0 && (
                <div className="flex h-60 flex-col items-center justify-center text-slate-500 text-xs">
                  <Terminal className="h-8 w-8 text-slate-700 mb-2 animate-pulse" />
                  Waiting for initial actions to execute...
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
            <h3 className="text-sm font-bold text-white">Discovered Findings & Verification</h3>
            <span className="text-xs text-slate-400">{findings.length} findings recorded</span>
          </div>

          {findings.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center">
              <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-400" />
              <h4 className="mt-3 text-sm font-semibold text-slate-200">No Bugs Detected So Far</h4>
              <p className="mt-1 text-xs text-slate-400">
                Any UI anomalies, console exceptions, or validation issues will automatically be registered and verified here.
              </p>
            </div>
          ) : (
            <div className="grid gap-4">
              {findings.map((finding) => (
                <div
                  key={finding.id}
                  className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm hover:border-slate-700 transition-colors"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
                    <div className="flex items-center gap-2.5">
                      <Bug className={`h-5 w-5 ${finding.severity === "HIGH" || finding.severity === "CRITICAL" ? "text-rose-400" : "text-amber-400"}`} />
                      <h4 className="text-base font-bold text-white">{finding.title}</h4>
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusBadge status={finding.severity} />
                      <StatusBadge status={finding.status} />
                    </div>
                  </div>

                  <p className="mt-3 text-xs text-slate-300">{finding.description}</p>

                  <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    {finding.expected_behavior && (
                      <div className="rounded-xl border border-slate-800 bg-slate-950 p-3">
                        <span className="font-semibold text-emerald-400 block mb-1">Expected Behavior:</span>
                        <p className="text-slate-400">{finding.expected_behavior}</p>
                      </div>
                    )}
                    {finding.actual_behavior && (
                      <div className="rounded-xl border border-slate-800 bg-slate-950 p-3">
                        <span className="font-semibold text-rose-400 block mb-1">Actual Behavior:</span>
                        <p className="text-slate-400">{finding.actual_behavior}</p>
                      </div>
                    )}
                  </div>

                  {finding.reproduction_steps && (
                    <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950 p-3 text-xs">
                      <span className="font-semibold text-slate-300 block mb-1 font-mono">Reproduction Steps:</span>
                      <pre className="text-slate-400 font-mono whitespace-pre-wrap">{finding.reproduction_steps}</pre>
                    </div>
                  )}

                  {/* Evidences (Screenshots) */}
                  {finding.evidences && finding.evidences.length > 0 && (
                    <div className="mt-4 flex flex-wrap items-center gap-3">
                      <span className="text-xs font-semibold text-slate-400">Attached Evidence:</span>
                      {finding.evidences.map((ev) => (
                        <button
                          key={ev.id}
                          onClick={() => {
                            setPreviewImage(ev.path);
                            setPreviewTitle(`Evidence for: ${finding.title}`);
                          }}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-2.5 py-1 text-xs text-blue-400 hover:bg-slate-800"
                        >
                          <ImageIcon className="h-3.5 w-3.5" />
                          <span>View Screenshot</span>
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
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-6">
            <div>
              <h3 className="text-base font-bold text-white">Full Autonomous QA Report (report.md)</h3>
              <p className="text-xs text-slate-400 mt-0.5">Comprehensive exploratory testing summary & coverage analysis</p>
            </div>
            <button
              onClick={() => {
                if (report?.markdown) {
                  navigator.clipboard.writeText(report.markdown);
                  setCopiedReport(true);
                  setTimeout(() => setCopiedReport(false), 2000);
                }
              }}
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-blue-500 transition-colors"
            >
              {copiedReport ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              {copiedReport ? "Copied!" : "Copy Markdown"}
            </button>
          </div>

          <div className="prose prose-invert max-w-none prose-headings:font-bold prose-h1:text-xl prose-h2:text-lg prose-table:text-xs prose-pre:bg-slate-950 prose-pre:border prose-pre:border-slate-800">
            {report?.markdown ? (
              <ReactMarkdown>{report.markdown}</ReactMarkdown>
            ) : (
              <div className="py-12 text-center text-slate-500 text-xs">
                Generating comprehensive report after session completion...
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: Playwright Regression Tests */}
      {activeTab === "tests" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Generated Playwright Regression Tests</h3>
              <p className="text-xs text-slate-400 mt-0.5">Standalone automated tests generated for confirmed bugs</p>
            </div>
          </div>

          {regressionTests.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center">
              <FileCode className="mx-auto h-8 w-8 text-slate-500" />
              <h4 className="mt-3 text-sm font-semibold text-slate-200">No Regression Tests Generated Yet</h4>
              <p className="mt-1 text-xs text-slate-400">
                Regression tests are automatically generated for all confirmed bugs upon session completion.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {regressionTests.map((t) => (
                <div key={t.id} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 overflow-hidden">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                    <div className="flex items-center gap-2">
                      <FileCode className="h-4 w-4 text-purple-400" />
                      <span className="font-mono text-xs font-bold text-white">{t.name}</span>
                    </div>

                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(t.test_code);
                        setCopiedCode(true);
                        setTimeout(() => setCopiedCode(false), 2000);
                      }}
                      className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-white rounded bg-slate-800 px-2.5 py-1"
                    >
                      {copiedCode ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                      {copiedCode ? "Copied" : "Copy Test Code"}
                    </button>
                  </div>

                  <pre className="rounded-xl border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-purple-200 overflow-x-auto">
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
