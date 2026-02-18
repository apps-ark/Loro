import { API_URL } from "./constants";
import type { Job, Segment } from "./types";

export async function createJob(file: File, maxSpeakers: number = 2): Promise<Job> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("max_speakers", String(maxSpeakers));

  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/jobs`, {
      method: "POST",
      body: formData,
    });
  } catch {
    throw new Error(
      `No se pudo conectar al servidor (${API_URL}). Verifica que el backend este corriendo.`
    );
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Error al subir: ${res.status} ${res.statusText}${text ? ` — ${text}` : ""}`);
  }
  return res.json();
}

export async function createJobFromYouTube(url: string, maxSpeakers: number = 2): Promise<Job> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/jobs/youtube`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, max_speakers: maxSpeakers }),
    });
  } catch {
    throw new Error(
      `No se pudo conectar al servidor (${API_URL}). Verifica que el backend este corriendo.`
    );
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Error al crear job: ${res.status} ${res.statusText}${text ? ` — ${text}` : ""}`);
  }
  return res.json();
}

export async function fetchJobs(): Promise<Job[]> {
  const res = await fetch(`${API_URL}/api/jobs`);
  if (!res.ok) throw new Error(`Failed to fetch jobs`);
  return res.json();
}

export async function fetchJob(id: string): Promise<Job> {
  const res = await fetch(`${API_URL}/api/jobs/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch job ${id}`);
  return res.json();
}

export async function retryJob(id: string): Promise<Job> {
  const res = await fetch(`${API_URL}/api/jobs/${id}/retry`, { method: "POST" });
  if (!res.ok) throw new Error(`Failed to retry job ${id}`);
  return res.json();
}

export async function deleteJob(id: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/jobs/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Failed to delete job ${id}`);
}

export async function fetchSegments(id: string): Promise<Segment[]> {
  const res = await fetch(`${API_URL}/api/jobs/${id}/segments`);
  if (!res.ok) throw new Error("Failed to fetch segments");
  return res.json();
}

export function getAudioUrl(jobId: string, track: "original" | "translated"): string {
  return `${API_URL}/api/jobs/${jobId}/audio/${track}`;
}

export function getWebSocketUrl(jobId: string): string {
  const wsBase = API_URL.replace(/^http/, "ws");
  return `${wsBase}/api/jobs/${jobId}/ws`;
}
