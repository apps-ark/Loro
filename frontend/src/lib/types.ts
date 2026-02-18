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
}

export type Language = "en" | "es";

export interface WSMessage {
  type: "step_start" | "step_progress" | "step_complete" | "pipeline_complete" | "error";
  step?: string;
  current?: number;
  total?: number;
  message?: string;
}
