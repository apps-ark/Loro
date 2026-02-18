import { SpeakerBadge } from "./SpeakerBadge";
import type { Language, Segment } from "@/lib/types";

interface Props {
  segment: Segment;
  language: Language;
  isActive: boolean;
  onClick: () => void;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function SubtitleLine({ segment, language, isActive, onClick }: Props) {
  const text = language === "en" ? segment.text_en : segment.text_es;

  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
        isActive
          ? "bg-blue-50 border border-blue-200"
          : "hover:bg-gray-50"
      }`}
    >
      <div className="flex items-center gap-2 mb-1">
        <SpeakerBadge speaker={segment.speaker} />
        <span className="text-xs text-gray-400">{formatTime(segment.start)}</span>
      </div>
      <p className={`text-sm ${isActive ? "text-gray-900 font-medium" : "text-gray-600"}`}>
        {text}
      </p>
    </button>
  );
}
