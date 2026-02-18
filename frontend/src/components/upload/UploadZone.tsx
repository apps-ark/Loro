"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createJob, createJobFromYouTube } from "@/lib/api";

const YT_RE = /^(https?:\/\/)?(www\.)?(youtube\.com\/(watch\?v=|shorts\/)|youtu\.be\/)[\w-]{11}/;

export function UploadZone() {
  const router = useRouter();
  const [mode, setMode] = useState<"file" | "youtube">("file");
  const [file, setFile] = useState<File | null>(null);
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [maxSpeakers, setMaxSpeakers] = useState(2);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isYouTubeValid = YT_RE.test(youtubeUrl);
  const canSubmit = mode === "file" ? !!file : isYouTubeValid;

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

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setUploading(true);
    setError(null);
    try {
      const job =
        mode === "youtube"
          ? await createJobFromYouTube(youtubeUrl, maxSpeakers)
          : await createJob(file!, maxSpeakers);
      router.push(`/jobs/${job.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al procesar la solicitud");
    } finally {
      setUploading(false);
    }
  };

  const switchMode = (newMode: "file" | "youtube") => {
    setMode(newMode);
    setError(null);
  };

  return (
    <Card className="p-8 max-w-xl mx-auto">
      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        <button
          type="button"
          onClick={() => switchMode("file")}
          className={`flex-1 pb-3 text-sm font-medium transition-colors ${
            mode === "file"
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Subir archivo
        </button>
        <button
          type="button"
          onClick={() => switchMode("youtube")}
          className={`flex-1 pb-3 text-sm font-medium transition-colors ${
            mode === "youtube"
              ? "border-b-2 border-blue-600 text-blue-600"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          URL de YouTube
        </button>
      </div>

      {/* File upload mode */}
      {mode === "file" && (
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
      )}

      {/* YouTube URL mode */}
      {mode === "youtube" && (
        <div className="space-y-3">
          <Input
            type="url"
            placeholder="https://www.youtube.com/watch?v=..."
            value={youtubeUrl}
            onChange={(e) => {
              setYoutubeUrl(e.target.value);
              setError(null);
            }}
          />
          {youtubeUrl && !isYouTubeValid && (
            <p className="text-xs text-amber-600">
              Ingresa una URL de YouTube valida (youtube.com/watch?v=... o youtu.be/...)
            </p>
          )}
        </div>
      )}

      {/* Controls — shown when there's valid input */}
      {canSubmit && (
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
          <Button onClick={handleSubmit} disabled={uploading} className="w-full">
            {uploading ? (
              <span className="flex items-center gap-2">
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {mode === "youtube" ? "Enviando..." : "Subiendo..."}
              </span>
            ) : (
              "Traducir entrevista"
            )}
          </Button>
        </div>
      )}

      {error && (
        <p className="mt-4 text-sm text-red-600">{error}</p>
      )}
    </Card>
  );
}
