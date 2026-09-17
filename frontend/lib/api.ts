export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
export const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

export interface Project {
  id: number;
  name: string;
  base_url: string;
  description: string;
  requirements_text: string;
  created_at: string;
  updated_at: string;
  sessions_count?: number;
}

export interface TestSession {
  id: number;
  project_id: number;
  mission: string;
  status: "CREATED" | "PLANNING" | "RUNNING" | "PAUSED" | "COMPLETED" | "FAILED";
  max_actions: number;
  actions_used: number;
  ai_calls_count: number;
  estimated_cost: number;
  started_at?: string;
  finished_at?: string;
  created_at: string;
  report_markdown?: string;
  scenarios_total?: number;
  scenarios_passed?: number;
  scenarios_failed?: number;
  scenarios_blocked?: number;
  findings_count?: number;
}

export interface Scenario {
  id: number;
  session_id: number;
  title: string;
  description: string;
  area: string;
  priority: "HIGH" | "MEDIUM" | "LOW";
  status: "PLANNED" | "RUNNING" | "PASSED" | "FAILED" | "BLOCKED" | "SKIPPED";
  order_index: number;
  steps_count?: number;
  created_at: string;
}

export interface TestStep {
  id: number;
  scenario_id: number;
  action: string;
  target?: string;
  value?: string;
  result: string;
  url?: string;
  screenshot_path?: string;
  duration_ms: number;
  error_message?: string;
  thought?: string;
  created_at: string;
}

export interface Evidence {
  id: number;
  finding_id: number;
  type: string;
  path: string;
  details_json?: string;
  created_at: string;
}

export interface RegressionTest {
  id: number;
  finding_id: number;
  session_id: number;
  name: string;
  file_path: string;
  test_code: string;
  created_at: string;
}

export interface Finding {
  id: number;
  session_id: number;
  scenario_id?: number;
  title: string;
  description: string;
  type: "BUG" | "MISSING_FUNCTIONALITY" | "UX_ISSUE" | "CONSOLE_ERROR" | "NETWORK_ERROR" | "UNKNOWN";
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  status: "POTENTIAL" | "VERIFYING" | "CONFIRMED" | "REJECTED";
  reproduction_attempts: number;
  reproduced: boolean;
  expected_behavior?: string;
  actual_behavior?: string;
  reproduction_steps?: string;
  created_at: string;
  evidences?: Evidence[];
  regression_test?: RegressionTest;
}

export interface ReportSummary {
  session_id: number;
  duration_seconds: number;
  actions_used: number;
  max_actions: number;
  scenarios_total: number;
  scenarios_passed: number;
  scenarios_failed: number;
  scenarios_blocked: number;
  scenarios_skipped: number;
  confirmed_bugs: number;
  potential_issues: number;
  ai_calls_count: number;
  estimated_cost: number;
}

export interface ReportAreaCoverage {
  area: string;
  scenarios_tested: number;
  scenarios_total: number;
  coverage_percent: number;
}

export interface FullReport {
  session_id: number;
  markdown: string;
  summary: ReportSummary;
  coverage: ReportAreaCoverage[];
}

// API Methods
export async function getProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE}/projects`);
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}

export async function getProject(id: number): Promise<Project> {
  const res = await fetch(`${API_BASE}/projects/${id}`);
  if (!res.ok) throw new Error("Failed to fetch project");
  return res.json();
}

export async function createProject(data: Partial<Project>): Promise<Project> {
  const res = await fetch(`${API_BASE}/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create project");
  return res.json();
}

export async function deleteProject(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/projects/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete project");
}

export async function getProjectSessions(projectId: number): Promise<TestSession[]> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/sessions`);
  if (!res.ok) throw new Error("Failed to fetch project sessions");
  return res.json();
}

export async function createSession(projectId: number, data: { mission: string; max_actions: number }): Promise<TestSession> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function getSession(sessionId: number): Promise<TestSession> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`);
  if (!res.ok) throw new Error("Failed to fetch session");
  return res.json();
}

export async function startSession(sessionId: number): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/start`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to start session");
  return res.json();
}

export async function stopSession(sessionId: number): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/stop`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to stop session");
  return res.json();
}

export async function getSessionScenarios(sessionId: number): Promise<Scenario[]> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/scenarios`);
  if (!res.ok) throw new Error("Failed to fetch scenarios");
  return res.json();
}

export async function getSessionSteps(sessionId: number, scenarioId?: number): Promise<TestStep[]> {
  const url = scenarioId ? `${API_BASE}/sessions/${sessionId}/steps?scenario_id=${scenarioId}` : `${API_BASE}/sessions/${sessionId}/steps`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch steps");
  return res.json();
}

export async function getSessionFindings(sessionId: number): Promise<Finding[]> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/findings`);
  if (!res.ok) throw new Error("Failed to fetch findings");
  return res.json();
}

export async function getSessionReport(sessionId: number): Promise<FullReport> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/report`);
  if (!res.ok) throw new Error("Failed to fetch report");
  return res.json();
}

export async function getSessionRegressionTests(sessionId: number): Promise<RegressionTest[]> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/regression-tests`);
  if (!res.ok) throw new Error("Failed to fetch regression tests");
  return res.json();
}
