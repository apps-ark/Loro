"use client";

import useSWR from "swr";
import { API_URL } from "@/lib/constants";
import type { Job, Segment } from "@/lib/types";

const fetcher = (url: string) => fetch(url).then((r) => {
  if (!r.ok) throw new Error("Fetch failed");
  return r.json();
});

export function useJob(id: string | null) {
  const { data, error, mutate } = useSWR<Job>(
    id ? `${API_URL}/api/jobs/${id}` : null,
    fetcher,
    { refreshInterval: 5000 }
  );
  return { job: data, error, isLoading: !data && !error, mutate };
}

export function useJobs() {
  const { data, error, mutate } = useSWR<Job[]>(
    `${API_URL}/api/jobs`,
    fetcher,
    { refreshInterval: 5000 }
  );
  return { jobs: data || [], error, isLoading: !data && !error, mutate };
}

export function useSegments(jobId: string | null) {
  const { data, error } = useSWR<Segment[]>(
    jobId ? `${API_URL}/api/jobs/${jobId}/segments` : null,
    fetcher
  );
  return { segments: data || [], error, isLoading: !data && !error };
}
