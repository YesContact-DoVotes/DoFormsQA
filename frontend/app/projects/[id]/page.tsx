"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { 
  ArrowLeft, 
  Play, 
  Globe, 
  FileText, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Bug, 
  Clock, 
  DollarSign, 
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Cpu
} from "lucide-react";
import { getProject, getProjectSessions, createSession, startSession, Project, TestSession } from "@/lib/api";
import { StatusBadge } from "@/components/Badge";

const DEFAULT_MISSION = `Conduct full exploratory testing of the application.
Test main user flows, negative validation, UI persistence across reload, navigation links, and error states.
Do not stop after the first successful flow.`;

export default function ProjectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const projectId = parseInt(resolvedParams.id, 10);
  const router = useRouter();

  const [project, setProject] = useState<Project | null>(null);
  const [sessions, setSessions] = useState<TestSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Start Session Form State
  const [mission, setMission] = useState(DEFAULT_MISSION);
  const [maxActions, setMaxActions] = useState(100);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    loadData();
  }, [projectId]);

  async function loadData() {
    try {
      setLoading(true);
      const [projData, sessData] = await Promise.all([
        getProject(projectId),
        getProjectSessions(projectId),
      ]);
      setProject(projData);
      setSessions(sessData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleStartSession(e: React.FormEvent) {
    e.preventDefault();
    try {
      setStarting(true);
      // 1. Create Session
      const newSession = await createSession(projectId, {
        mission,
        max_actions: maxActions,
      });

      // 2. Trigger start
      await startSession(newSession.id);

      // 3. Navigate directly to live session
      router.push(`/sessions/${newSession.id}`);
    } catch (e) {
      alert("Failed to start session: " + (e as Error).message);
      setStarting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-12 text-center text-slate-400">
        Project not found. <Link href="/" className="text-blue-400 underline">Return to projects</Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      {/* Back link */}
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-white transition-colors mb-6"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to Projects
      </Link>

      {/* Project Header */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-extrabold text-white tracking-tight">{project.name}</h1>
              <span className="rounded-md bg-blue-500/10 px-2.5 py-0.5 text-xs font-semibold text-blue-400 border border-blue-500/20">
                Active Project
              </span>
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-400">
              <a
                href={project.base_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 font-mono text-blue-400 hover:underline"
              >
                <Globe className="h-3.5 w-3.5" />
                {project.base_url}
                <ExternalLink className="h-3 w-3" />
              </a>
              {project.description && <span>• {project.description}</span>}
            </div>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-500/25 transition-all hover:from-blue-500 hover:to-indigo-500 active:scale-95"
          >
            <Play className="h-4 w-4 fill-white" />
            Start QA Session
          </button>
        </div>

        {/* Requirements Collapsible Preview */}
        {project.requirements_text && (
          <div className="mt-6 border-t border-slate-800/80 pt-4">
            <details className="group">
              <summary className="cursor-pointer text-xs font-semibold text-slate-300 hover:text-white flex items-center gap-2 select-none">
                <FileText className="h-3.5 w-3.5 text-blue-400" />
                <span>View Attached Requirements (MVP / PRD)</span>
                <span className="text-[10px] text-slate-500 font-mono">(click to toggle)</span>
              </summary>
              <div className="mt-3 rounded-lg border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-slate-300 whitespace-pre-wrap max-h-60 overflow-y-auto">
                {project.requirements_text}
              </div>
            </details>
          </div>
        )}
      </div>

      {/* Sessions Section */}
      <div className="mt-10">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-white tracking-tight">QA Test Sessions</h2>
          <span className="text-xs text-slate-400">{sessions.length} total sessions</span>
        </div>

        {sessions.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-10 text-center">
            <ShieldCheck className="mx-auto h-8 w-8 text-slate-500" />
            <h3 className="mt-3 text-sm font-semibold text-slate-200">No QA Sessions Run Yet</h3>
            <p className="mt-1 text-xs text-slate-400">
              Click &quot;Start QA Session&quot; to launch the autonomous AI testing agent against this application.
            </p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/40">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="px-5 py-3.5 font-semibold">Session</th>
                    <th className="px-5 py-3.5 font-semibold">Status</th>
                    <th className="px-5 py-3.5 font-semibold">Scenarios</th>
                    <th className="px-5 py-3.5 font-semibold">Actions Used</th>
                    <th className="px-5 py-3.5 font-semibold">Findings</th>
                    <th className="px-5 py-3.5 font-semibold">AI Cost</th>
                    <th className="px-5 py-3.5 font-semibold">Created</th>
                    <th className="px-5 py-3.5 text-right font-semibold">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {sessions.map((sess) => (
                    <tr
                      key={sess.id}
                      onClick={() => router.push(`/sessions/${sess.id}`)}
                      className="hover:bg-slate-800/50 cursor-pointer transition-colors"
                    >
                      <td className="px-5 py-4 font-mono font-bold text-white">
                        #{sess.id}
                      </td>
                      <td className="px-5 py-4">
                        <StatusBadge status={sess.status} />
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-1.5 font-medium">
                          <span className="text-emerald-400 font-bold">{sess.scenarios_passed || 0}</span>
                          <span className="text-slate-500">/</span>
                          <span>{sess.scenarios_total || 0}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className="font-mono">{sess.actions_used} / {sess.max_actions}</span>
                      </td>
                      <td className="px-5 py-4">
                        {sess.findings_count && sess.findings_count > 0 ? (
                          <span className="inline-flex items-center gap-1 font-bold text-amber-400">
                            <Bug className="h-3.5 w-3.5" />
                            {sess.findings_count}
                          </span>
                        ) : (
                          <span className="text-slate-500">0</span>
                        )}
                      </td>
                      <td className="px-5 py-4 font-mono text-slate-400">
                        ${(sess.estimated_cost || 0).toFixed(4)}
                      </td>
                      <td className="px-5 py-4 text-slate-400">
                        {new Date(sess.created_at).toLocaleString()}
                      </td>
                      <td className="px-5 py-4 text-right">
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-blue-400 hover:text-blue-300">
                          View
                          <ChevronRight className="h-4 w-4" />
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Start Session Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-xl overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl">
            <div className="border-b border-slate-800 px-6 py-4 bg-slate-950 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Play className="h-4 w-4 text-blue-400" />
                <h3 className="text-base font-bold text-white">Start New QA Session</h3>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleStartSession} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Testing Mission (AI Prompt Directive)
                </label>
                <textarea
                  rows={5}
                  required
                  value={mission}
                  onChange={(e) => setMission(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-xs font-mono text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Action Budget (Max Actions)
                  </label>
                  <input
                    type="number"
                    min={10}
                    max={500}
                    value={maxActions}
                    onChange={(e) => setMaxActions(parseInt(e.target.value, 10))}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Target Browser
                  </label>
                  <div className="rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-xs font-mono text-slate-300 flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-emerald-400" />
                    Chromium (Headed / Live)
                  </div>
                </div>
              </div>

              <div className="rounded-lg bg-blue-500/10 border border-blue-500/20 p-3 text-xs text-blue-300">
                ⚡ Once started, the agent will autonomously launch Chromium, discover application entry points, plan scenarios, and perform exploratory E2E checks with loop detection and bug verification.
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-lg px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={starting}
                  className="rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-2 text-sm font-semibold text-white shadow-md hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 flex items-center gap-2"
                >
                  {starting ? (
                    <>
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      Launching...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 fill-white" />
                      START QA SESSION
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
