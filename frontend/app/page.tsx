"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
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
  const [baseUrl, setBaseUrl] = useState("");
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
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Projects</h1>
          <p className="mt-1 text-sm text-slate-600">
            Manage target applications and run automated exploratory QA sessions.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-xs transition-all hover:bg-blue-700 active:scale-95 cursor-pointer"
        >
          Create Project
        </button>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="mt-12 flex justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
        </div>
      ) : projects.length === 0 ? (
        <div className="mt-12 flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center">
          <h3 className="text-base font-semibold text-slate-800">No Projects Found</h3>
          <p className="mt-1 text-sm text-slate-500 max-w-md">
            Create a QA project to start autonomous exploratory and regression testing.
          </p>
          <button
            onClick={() => {
              setName("");
              setBaseUrl("");
              setDescription("");
              setRequirementsText("");
              setIsModalOpen(true);
            }}
            className="mt-5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 cursor-pointer"
          >
            Create New Project
          </button>
        </div>
      ) : (
        <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Link
              key={project.id}
              href={`/projects/${project.id}`}
              className="group relative flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-xs transition-all hover:border-slate-300 hover:shadow-md"
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-base font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                    {project.name}
                  </h3>
                  <button
                    onClick={(e) => handleDelete(e, project.id)}
                    className="opacity-0 group-hover:opacity-100 text-xs text-slate-400 hover:text-rose-600 p-1 transition-opacity cursor-pointer"
                    title="Delete Project"
                  >
                    Delete
                  </button>
                </div>

                <div className="mt-2 text-xs font-mono text-slate-500 truncate">
                  {project.base_url}
                </div>

                {project.description && (
                  <p className="mt-2 text-xs text-slate-600 line-clamp-2">
                    {project.description}
                  </p>
                )}
              </div>

              <div className="mt-5 border-t border-slate-100 pt-3 flex items-center justify-between text-xs">
                <span className="text-slate-500">
                  {project.sessions_count || 0} sessions
                </span>

                <span className="font-medium text-blue-600">
                  View &rarr;
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Create Project Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="relative w-full max-w-lg overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl">
            <div className="border-b border-slate-200 px-5 py-3.5 bg-slate-50 flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Create New Project</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreate} className="p-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Project Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. DoForms App"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Application Base URL *
                </label>
                <input
                  type="url"
                  required
                  placeholder="http://localhost:3088"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 font-mono placeholder:text-slate-400 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Description
                </label>
                <input
                  type="text"
                  placeholder="Brief description of the app"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-slate-700">
                    Requirements / PRD (Optional)
                  </label>
                  <button
                    type="button"
                    onClick={() => setRequirementsText(SAMPLE_MVP_REQUIREMENTS)}
                    className="text-xs text-blue-600 hover:text-blue-700 cursor-pointer"
                  >
                    Auto-fill Sample
                  </button>
                </div>
                <textarea
                  rows={4}
                  placeholder="Paste MVP or test requirements in Markdown format..."
                  value={requirementsText}
                  onChange={(e) => setRequirementsText(e.target.value)}
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 font-mono placeholder:text-slate-400 focus:border-blue-500 focus:outline-none"
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
                  disabled={submitting}
                  className="rounded-md bg-blue-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
                >
                  {submitting ? "Creating..." : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
