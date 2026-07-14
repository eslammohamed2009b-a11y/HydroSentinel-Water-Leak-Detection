import { apiFetch } from "@/lib/api";

export type ScenarioSummary = {
  slug: string;
  label: string;
  filename: string;
  description: string;
  occupancy_mode?: string;
  expected_has_leak?: boolean;
};

export type AnalysisRequest = {
  scenario_selected: string;
  event_mode: boolean;
};

export type AnalysisResponse = {
  analysis_id: string | null;
  has_leak: boolean;
  leak_lpm: number;
  total_liters: number;
  leak_type: string | null;
  confidence: number;
  event_mode: boolean;
  event_rows: number;
  source_mode: string;
  scenario_selected: string | null;
  validation_summary: Record<string, unknown>;
  reasoning_string: string;
  financial_loss: Record<string, unknown>;
  environmental_impact: Record<string, unknown>;
  insights: Record<string, unknown>;
  anomalies: Array<Record<string, unknown>>;
  telemetry_points: Array<Record<string, unknown>>;
};

export type AnalysisHistoryItem = {
  analysis_id: string;
  scenario_selected: string;
  event_mode: boolean;
  has_leak: boolean;
  confidence: number;
  leak_lpm: number;
  total_liters: number;
  created_at: string;
};

export type FeedbackResponse = {
  analysis_id: string;
  feedback: string;
  confidence: number;
  predicted_leak: boolean;
};

export function fetchScenarios() {
  return apiFetch<ScenarioSummary[]>("/scenarios");
}

export function runAnalysis(payload: AnalysisRequest) {
  return apiFetch<AnalysisResponse>("/analyses", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchAnalysisHistory() {
  return apiFetch<AnalysisHistoryItem[]>("/analyses");
}

export function fetchAnalysisById(analysisId: string) {
  return apiFetch<AnalysisResponse>(`/analyses/${analysisId}`);
}

export function submitFeedback(analysisId: string, verdict: string) {
  return apiFetch<FeedbackResponse>(`/analyses/${analysisId}/feedback`, {
    method: "POST",
    body: JSON.stringify({ verdict }),
  });
}