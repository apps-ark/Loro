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
  const { job, isLoading } = useJob(id);
  const { segments } = useSegments(job?.status === "completed" ? id : null);
  const isProcessing = job?.status === "pending" || job?.status === "processing";
  const { messages, isConnected } = useWebSocket(id, isProcessing);

  if (isLoading) {
    return <p className="text-center text-gray-500">Cargando...</p>;
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
          {job.error && <p className="text-sm text-gray-500 mt-2">{job.error}</p>}
        </div>
      )}
    </div>
  );
}
