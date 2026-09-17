"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
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
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-12 text-center text-slate-500">
        Project not found. <Link href="/" className="text-blue-600 underline">Return to projects</Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      {/* Back link */}
      <Link
        href="/"
        className="inline-block text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors mb-4"
      >
        &larr; Back to Projects
      </Link>

      {/* Project Header */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{project.name}</h1>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-slate-500">
              <a
                href={project.base_url}
                target="_blank"
                rel="noreferrer"
                className="font-mono text-blue-600 hover:underline"
              >
                {project.base_url}
              </a>
              {project.description && <span>• {project.description}</span>}
            </div>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-xs transition-all hover:bg-blue-700 active:scale-95 cursor-pointer"
          >
            Start QA Session
          </button>
        </div>

        {/* Requirements Collapsible Preview */}
        {project.requirements_text && (
          <div className="mt-5 border-t border-slate-100 pt-4">
            <details className="group">
              <summary className="cursor-pointer text-xs font-medium text-slate-600 hover:text-slate-900 select-none">
                View Attached Requirements (MVP / PRD)
              </summary>
              <div className="mt-2.5 rounded-lg border border-slate-200 bg-slate-50 p-4 font-mono text-xs text-slate-700 whitespace-pre-wrap max-h-60 overflow-y-auto">
                {project.requirements_text}
              </div>
            </details>
          </div>
        )}
      </div>

      {/* Sessions Section */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-bold text-slate-900 tracking-tight">QA Sessions</h2>
          <span className="text-xs text-slate-500">{sessions.length} total</span>
        </div>

        {sessions.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center">
            <h3 className="text-sm font-semibold text-slate-800">No QA Sessions Run Yet</h3>
            <p className="mt-1 text-xs text-slate-500">
              Click &quot;Start QA Session&quot; to begin exploratory testing.
            </p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 uppercase tracking-wider border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Session</th>
                    <th className="px-4 py-3 font-semibold">Status</th>
                    <th className="px-4 py-3 font-semibold">Passed / Total</th>
                    <th className="px-4 py-3 font-semibold">Actions</th>
                    <th className="px-4 py-3 font-semibold">Bugs</th>
                    <th className="px-4 py-3 font-semibold">AI Cost</th>
                    <th className="px-4 py-3 font-semibold">Created</th>
                    <th className="px-4 py-3 text-right font-semibold"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {sessions.map((sess) => (
                    <tr
                      key={sess.id}
                      onClick={() => router.push(`/sessions/${sess.id}`)}
                      className="hover:bg-slate-50 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3.5 font-mono font-semibold text-slate-900">
                        #{sess.id}
                      </td>
                      <td className="px-4 py-3.5">
                        <StatusBadge status={sess.status} />
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="font-medium text-slate-900">{sess.scenarios_passed || 0}</span>
                        <span className="text-slate-400"> / </span>
                        <span>{sess.scenarios_total || 0}</span>
                      </td>
                      <td className="px-4 py-3.5 font-mono">
                        {sess.actions_used} / {sess.max_actions}
                      </td>
                      <td className="px-4 py-3.5">
                        {sess.findings_count && sess.findings_count > 0 ? (
                          <span className="font-semibold text-rose-600">
                            {sess.findings_count}
                          </span>
                        ) : (
                          <span className="text-slate-400">0</span>
                        )}
                      </td>
                      <td className="px-4 py-3.5 font-mono text-slate-500">
                        ${(sess.estimated_cost || 0).toFixed(4)}
                      </td>
                      <td className="px-4 py-3.5 text-slate-500">
                        {new Date(sess.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3.5 text-right font-medium text-blue-600">
                        Open &rarr;
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="relative w-full max-w-lg overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl">
            <div className="border-b border-slate-200 px-5 py-3.5 bg-slate-50 flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Start QA Session</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleStartSession} className="p-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Testing Mission (Directive)
                </label>
                <textarea
                  rows={4}
                  required
                  value={mission}
                  onChange={(e) => setMission(e.target.value)}
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-xs font-mono text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Action Budget (Max Actions)
                </label>
                <input
                  type="number"
                  min={10}
                  max={500}
                  value={maxActions}
                  onChange={(e) => setMaxActions(parseInt(e.target.value, 10))}
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2.5 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-md px-3.5 py-1.5 text-sm text-slate-700 hover:bg-slate-100 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={starting}
                  className="rounded-md bg-blue-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
                >
                  {starting ? "Launching..." : "Start Session"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
