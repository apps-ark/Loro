export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const SPEAKER_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  SPEAKER_00: { bg: "bg-blue-100", text: "text-blue-800", border: "border-blue-300" },
  SPEAKER_01: { bg: "bg-emerald-100", text: "text-emerald-800", border: "border-emerald-300" },
  SPEAKER_02: { bg: "bg-purple-100", text: "text-purple-800", border: "border-purple-300" },
  SPEAKER_03: { bg: "bg-amber-100", text: "text-amber-800", border: "border-amber-300" },
};

export const STEP_LABELS: Record<string, string> = {
  asr: "Transcripción (ASR)",
  diarize: "Diarización de hablantes",
  merge: "Fusión de segmentos",
  translate: "Traducción EN→ES",
  tts: "Síntesis de voz (TTS)",
  render: "Renderizado de audio",
};

export const PIPELINE_STEPS = ["asr", "diarize", "merge", "translate", "tts", "render"];

export function getSpeakerColor(speaker: string) {
  return SPEAKER_COLORS[speaker] || { bg: "bg-gray-100", text: "text-gray-800", border: "border-gray-300" };
}
