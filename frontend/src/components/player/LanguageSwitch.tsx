"use client";

import { Button } from "@/components/ui/button";
import type { Language } from "@/lib/types";

interface Props {
  language: Language;
  onChange: (lang: Language) => void;
}

export function LanguageSwitch({ language, onChange }: Props) {
  return (
    <div className="inline-flex rounded-lg border border-gray-200 overflow-hidden">
      <Button
        variant={language === "en" ? "default" : "ghost"}
        size="sm"
        className="rounded-none"
        onClick={() => onChange("en")}
      >
        EN
      </Button>
      <Button
        variant={language === "es" ? "default" : "ghost"}
        size="sm"
        className="rounded-none"
        onClick={() => onChange("es")}
      >
        ES
      </Button>
    </div>
  );
}
