"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createJob } from "@/lib/api";

export function UploadZone() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [maxSpeakers, setMaxSpeakers] = useState(2);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && (droppedFile.type.startsWith("audio/") || droppedFile.name.match(/\.(mp3|wav|m4a|ogg|flac)$/i))) {
      setFile(droppedFile);
      setError(null);
    } else {
      setError("Por favor, sube un archivo de audio (.mp3, .wav, etc.)");
    }
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      setError(null);
    }
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const job = await createJob(file, maxSpeakers);
      router.push(`/jobs/${job.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al subir el archivo");
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card className="p-8 max-w-xl mx-auto">
      <div
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
          dragOver ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        {file ? (
          <div>
            <p className="text-lg font-medium">{file.name}</p>
            <p className="text-sm text-gray-500 mt-1">
              {(file.size / (1024 * 1024)).toFixed(1)} MB
            </p>
            <Button variant="ghost" size="sm" className="mt-2" onClick={() => setFile(null)}>
              Cambiar archivo
            </Button>
          </div>
        ) : (
          <div>
            <p className="text-lg text-gray-600 mb-2">
              Arrastra un archivo de audio aquí
            </p>
            <p className="text-sm text-gray-400 mb-4">o</p>
            <label>
              <Button variant="outline" asChild>
                <span>Seleccionar archivo</span>
              </Button>
              <input
                type="file"
                className="hidden"
                accept="audio/*,.mp3,.wav,.m4a,.ogg,.flac"
                onChange={handleFileInput}
              />
            </label>
          </div>
        )}
      </div>

      {file && (
        <div className="mt-6 space-y-4">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
              Max. hablantes:
            </label>
            <Input
              type="number"
              min={1}
              max={10}
              value={maxSpeakers}
              onChange={(e) => setMaxSpeakers(Number(e.target.value))}
              className="w-20"
            />
          </div>
          <Button onClick={handleUpload} disabled={uploading} className="w-full">
            {uploading ? "Subiendo..." : "Traducir entrevista"}
          </Button>
        </div>
      )}

      {error && (
        <p className="mt-4 text-sm text-red-600">{error}</p>
      )}
    </Card>
  );
}
