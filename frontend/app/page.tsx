"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Plus, 
  Globe, 
  FileText, 
  Play, 
  Trash2, 
  Layers, 
  ShieldAlert, 
  CheckCircle2, 
  ArrowRight,
  ExternalLink,
  Sparkles
} from "lucide-react";
import { getProjects, createProject, deleteProject, Project } from "@/lib/api";

const SAMPLE_MVP_REQUIREMENTS = `# DoForms MVP Requirements Specification

## 1. Overview
DoForms is a modern web application for creating, managing, and publishing dynamic interactive web forms and collecting user responses.

## 2. Key Modules & Functional Requirements
- **Authentication & Header Navigation**: Navigation links: Dashboard, Form Builder, Templates, Settings. User login modal.
- **Form Builder**: Form Title (required), Form Description. Add Question, Delete Question, Duplicate Question. Save Form (persistence), Publish Form.
- **Response Submission**: Public form view, email validation on submit, submission confirmation.
- **Validation**: Cannot save empty forms without a title. Form data must persist across reload.`;

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form State
  const [name, setName] = useState("");
  const [baseUrl, setBaseUrl] = useState("http://localhost:3000");
  const [description, setDescription] = useState("");
  const [requirementsText, setRequirementsText] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
    try {
      setLoading(true);
      const data = await getProjects();
      setProjects(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!name || !baseUrl) return;

    try {
      setSubmitting(true);
      await createProject({
        name,
        base_url: baseUrl,
        description,
        requirements_text: requirementsText,
      });
      setIsModalOpen(false);
      setName("");
      setDescription("");
      setRequirementsText("");
      await loadProjects();
    } catch (e) {
      alert("Failed to create project: " + (e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(e: React.MouseEvent, id: number) {
    e.stopPropagation();
    e.preventDefault();
    if (!confirm("Are you sure you want to delete this project and all its QA sessions?")) return;
    try {
      await deleteProject(id);
      await loadProjects();
    } catch (e) {
      alert("Failed to delete project: " + (e as Error).message);
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      {/* Header Banner */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b border-slate-800 pb-8">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-extrabold tracking-tight text-white">QA Projects</h1>
            <span className="rounded-full bg-blue-500/10 px-2.5 py-0.5 text-xs font-semibold text-blue-400 border border-blue-500/20">
              Autonomous
            </span>
          </div>
          <p className="mt-1.5 text-sm text-slate-400 max-w-2xl">
            Manage web application targets and run autonomous exploratory and E2E testing sessions powered by AI and Playwright.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 transition-all hover:bg-blue-500 active:scale-95"
        >
          <Plus className="h-4 w-4" />
          Create New Project
        </button>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="mt-12 flex justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        </div>
      ) : projects.length === 0 ? (
        <div className="mt-12 flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-800 text-slate-400">
            <Layers className="h-6 w-6" />
          </div>
          <h3 className="mt-4 text-base font-semibold text-slate-200">No Projects Found</h3>
          <p className="mt-1 text-sm text-slate-400 max-w-md">
            Get started by creating your first QA project. Specify your web application URL and optionally add requirements.
          </p>
          <button
            onClick={() => {
              setName("DoForms Web App");
              setBaseUrl("http://localhost:3000");
              setDescription("Dynamic form builder and response collection system");
              setRequirementsText(SAMPLE_MVP_REQUIREMENTS);
              setIsModalOpen(true);
            }}
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500"
          >
            <Sparkles className="h-4 w-4" />
            Create Sample DoForms Project
          </button>
        </div>
      ) : (
        <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Link
              key={project.id}
              href={`/projects/${project.id}`}
              className="group relative flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-sm transition-all hover:border-blue-500/40 hover:bg-slate-900/90 hover:shadow-xl hover:shadow-blue-500/5"
            >
              <div>
                <div className="flex items-start justify-between gap-4">
                  <h3 className="text-lg font-bold text-white group-hover:text-blue-400 transition-colors">
                    {project.name}
                  </h3>
                  <button
                    onClick={(e) => handleDelete(e, project.id)}
                    className="opacity-0 group-hover:opacity-100 p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-all"
                    title="Delete Project"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                <div className="mt-3 flex items-center gap-2 text-xs font-mono text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2.5 py-1 rounded-md w-fit">
                  <Globe className="h-3.5 w-3.5" />
                  <span className="truncate max-w-[200px]">{project.base_url}</span>
                </div>

                {project.description && (
                  <p className="mt-3 text-xs text-slate-400 line-clamp-2">
                    {project.description}
                  </p>
                )}
              </div>

              <div className="mt-6 border-t border-slate-800/80 pt-4 flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  <Play className="h-3.5 w-3.5 text-slate-500" />
                  <span>{project.sessions_count || 0} Sessions</span>
                </div>

                <span className="inline-flex items-center gap-1 text-xs font-semibold text-blue-400 group-hover:translate-x-0.5 transition-transform">
                  View Sessions
                  <ArrowRight className="h-3.5 w-3.5" />
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Create Project Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-xl overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl">
            <div className="border-b border-slate-800 px-6 py-4 bg-slate-950 flex items-center justify-between">
              <h3 className="text-base font-bold text-white">Create New QA Project</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Project Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. DoForms App"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Application Base URL *
                </label>
                <input
                  type="url"
                  required
                  placeholder="http://localhost:3000"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Description
                </label>
                <input
                  type="text"
                  placeholder="Brief description of the app"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold text-slate-300">
                    Requirements / PRD (Optional)
                  </label>
                  <button
                    type="button"
                    onClick={() => setRequirementsText(SAMPLE_MVP_REQUIREMENTS)}
                    className="text-xs text-blue-400 hover:text-blue-300 font-medium"
                  >
                    Auto-fill Sample MVP.md
                  </button>
                </div>
                <textarea
                  rows={4}
                  placeholder="Paste MVP, PRD, or user stories in Markdown format..."
                  value={requirementsText}
                  onChange={(e) => setRequirementsText(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-white font-mono placeholder:text-slate-500 focus:border-blue-500 focus:outline-none"
                />
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
                  disabled={submitting}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-md hover:bg-blue-500 disabled:opacity-50"
                >
                  {submitting ? "Creating..." : "Create Project"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
