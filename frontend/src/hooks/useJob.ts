"use client";

import useSWR from "swr";
import { API_URL } from "@/lib/constants";
import type { Job, Segment } from "@/lib/types";

const fetcher = async (url: string) => {
  const r = await fetch(url);
  if (!r.ok) {
    const err = new Error(`HTTP ${r.status}`);
    throw err;
  }
  return r.json();
};

export function useJob(id: string | null) {
  const { data, error, mutate } = useSWR<Job>(
    id ? `${API_URL}/api/jobs/${id}` : null,
    fetcher,
    {
      refreshInterval: 3000,
      errorRetryCount: 10,
      errorRetryInterval: 2000,
      shouldRetryOnError: true,
    }
  );
  return { job: data, error, isLoading: !data && !error, mutate };
}

export function useJobs() {
  const { data, error, mutate } = useSWR<Job[]>(
    `${API_URL}/api/jobs`,
    fetcher,
    {
      refreshInterval: 5000,
      errorRetryCount: 5,
      shouldRetryOnError: true,
    }
  );
  return { jobs: data || [], error, isLoading: !data && !error, mutate };
}

export function useSegments(jobId: string | null) {
  const { data, error } = useSWR<Segment[]>(
    jobId ? `${API_URL}/api/jobs/${jobId}/segments` : null,
    fetcher,
    {
      errorRetryCount: 3,
      shouldRetryOnError: true,
    }
  );
  return { segments: data || [], error, isLoading: !data && !error };
}
