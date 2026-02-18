"use client";

import { use } from "react";
import Link from "next/link";
import { useJob, useSegments } from "@/hooks/useJob";
import { useWebSocket } from "@/hooks/useWebSocket";
import { ProcessingView } from "@/components/upload/ProcessingView";
import { InterviewPlayer } from "@/components/player/InterviewPlayer";
import { Badge } from "@/components/ui/badge";

export default function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { job, error, isLoading } = useJob(id);
  const { segments } = useSegments(job?.status === "completed" ? id : null);
  const isProcessing = !job || job.status === "pending" || job.status === "processing";
  const { messages, isConnected } = useWebSocket(id, isProcessing);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col items-center gap-3 py-12">
        <svg className="h-6 w-6 animate-spin text-blue-600" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <p className="text-gray-500">Cargando...</p>
      </div>
    );
  }

  // Fetch error but no data yet — show processing view anyway
  // (the job exists server-side since we got 201, SWR will retry)
  if (error && !job) {
    return (
      <div>
        <div className="flex items-center gap-3 mb-6">
          <Link href="/jobs" className="text-gray-400 hover:text-gray-600">&larr;</Link>
          <h1 className="text-xl font-bold">Procesando...</h1>
        </div>
        <ProcessingView messages={messages} isConnected={isConnected} />
        <p className="mt-4 text-center text-xs text-amber-600">
          Conectando con el servidor...
        </p>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 mb-4">Trabajo no encontrado</p>
        <Link href="/jobs" className="text-blue-600 hover:underline">
          Ver todos los trabajos
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link href="/jobs" className="text-gray-400 hover:text-gray-600">&larr;</Link>
        <h1 className="text-xl font-bold">{job.filename}</h1>
        <Badge variant="outline">{job.status}</Badge>
      </div>

      {isProcessing && (
        <ProcessingView messages={messages} isConnected={isConnected} />
      )}

      {job.status === "completed" && (
        <InterviewPlayer jobId={id} segments={segments} />
      )}

      {job.status === "failed" && (
        <div className="text-center py-12">
          <p className="text-red-600 font-medium">Error en el procesamiento</p>
          {job.error && <p className="text-sm text-gray-500 mt-2 whitespace-pre-wrap">{job.error}</p>}
        </div>
      )}
    </div>
  );
}
