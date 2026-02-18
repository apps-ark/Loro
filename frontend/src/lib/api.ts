import { API_URL } from "./constants";
import type { Job, Segment } from "./types";

export async function createJob(file: File, maxSpeakers: number = 2): Promise<Job> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("max_speakers", String(maxSpeakers));

  const res = await fetch(`${API_URL}/api/jobs`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`);
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
