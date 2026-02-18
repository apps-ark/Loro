"use client";

import Link from "next/link";
import { useJobs } from "@/hooks/useJob";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { deleteJob } from "@/lib/api";

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  processing: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "Pendiente",
  processing: "Procesando",
  completed: "Completado",
  failed: "Error",
};

export default function JobsPage() {
  const { jobs, isLoading, mutate } = useJobs();

  if (isLoading) {
    return <p className="text-center text-gray-500">Cargando trabajos...</p>;
  }

  if (jobs.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 mb-4">No hay trabajos todavia</p>
        <Link href="/" className="text-blue-600 hover:underline">
          Subir una entrevista
        </Link>
      </div>
    );
  }

  const handleDelete = async (e: React.MouseEvent, jobId: string) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await deleteJob(jobId);
      mutate();
    } catch {
      // silently fail, SWR will refresh
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Trabajos</h1>
      <div className="space-y-4">
        {jobs.map((job) => (
          <Link key={job.id} href={`/jobs/${job.id}`}>
            <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex items-center justify-between">
                <div className="min-w-0 flex-1">
                  <p className="font-medium">{job.filename}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(job.created_at).toLocaleString("es-ES")}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  {job.current_step && job.status === "processing" && (
                    <span className="text-xs text-gray-500">{job.current_step}</span>
                  )}
                  <Badge className={STATUS_STYLES[job.status] || ""}>
                    {STATUS_LABELS[job.status] || job.status}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 text-gray-400 hover:text-red-600"
                    onClick={(e) => handleDelete(e, job.id)}
                  >
                    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className="h-4 w-4">
                      <line x1="4" y1="4" x2="12" y2="12" />
                      <line x1="12" y1="4" x2="4" y2="12" />
                    </svg>
                  </Button>
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
