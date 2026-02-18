export type JobStatus = "pending" | "processing" | "completed" | "failed";

export interface Job {
  id: string;
  filename: string;
  status: JobStatus;
  current_step: string | null;
  created_at: string;
  error: string | null;
}

export interface Segment {
  start: number;
  end: number;
  duration: number;
  speaker: string;
  text_en: string;
  text_es: string;
  start_es: number | null;
  end_es: number | null;
  duration_es: number | null;
}

export type Language = "en" | "es";

export interface WSMessage {
  type: "step_start" | "step_progress" | "step_complete" | "pipeline_complete" | "error";
  step?: string;
  current?: number;
  total?: number;
  message?: string;
}
