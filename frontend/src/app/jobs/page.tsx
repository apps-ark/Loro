"use client";

import Link from "next/link";
import { useJobs } from "@/hooks/useJob";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

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
  const { jobs, isLoading } = useJobs();

  if (isLoading) {
    return <p className="text-center text-gray-500">Cargando trabajos...</p>;
  }

  if (jobs.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 mb-4">No hay trabajos todavía</p>
        <Link href="/" className="text-blue-600 hover:underline">
          Subir una entrevista
        </Link>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Trabajos</h1>
      <div className="space-y-3">
        {jobs.map((job) => (
          <Link key={job.id} href={`/jobs/${job.id}`}>
            <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex items-center justify-between">
                <div>
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
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
