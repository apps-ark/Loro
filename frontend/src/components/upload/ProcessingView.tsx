"use client";

import { useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { PIPELINE_STEPS, STEP_LABELS } from "@/lib/constants";
import type { WSMessage } from "@/lib/types";

interface Props {
  messages: WSMessage[];
  isConnected: boolean;
}

type StepStatus = "pending" | "running" | "completed" | "failed";

interface StepState {
  status: StepStatus;
  current: number;
  total: number;
}

// SVG icons per pipeline step (16x16 viewBox)
const STEP_ICONS: Record<string, React.ReactNode> = {
  asr: (
    // Microphone
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
      <rect x="5" y="1" width="6" height="9" rx="3" />
      <path d="M3 7a5 5 0 0010 0" />
      <line x1="8" y1="12" x2="8" y2="15" />
      <line x1="5.5" y1="15" x2="10.5" y2="15" />
    </svg>
  ),
  diarize: (
    // Two people
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
      <circle cx="5.5" cy="4" r="2.5" />
      <path d="M1 13c0-2.5 2-4.5 4.5-4.5S10 10.5 10 13" />
      <circle cx="11.5" cy="4.5" r="2" />
      <path d="M15 13c0-2 -1.5-3.5-3.5-3.5" />
    </svg>
  ),
  merge: (
    // Merge arrows
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
      <path d="M4 2v4c0 2 2 4 4 4" />
      <path d="M12 2v4c0 2-2 4-4 4" />
      <line x1="8" y1="10" x2="8" y2="14" />
      <polyline points="6 12 8 14 10 12" />
    </svg>
  ),
  translate: (
    // Globe / language
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
      <circle cx="8" cy="8" r="6.5" />
      <ellipse cx="8" cy="8" rx="3" ry="6.5" />
      <line x1="1.5" y1="8" x2="14.5" y2="8" />
    </svg>
  ),
  tts: (
    // Speaker / sound wave
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
      <polygon points="2,6 5,6 9,2 9,14 5,10 2,10" />
      <path d="M11 5.5a3.5 3.5 0 010 5" />
      <path d="M13 3.5a6 6 0 010 9" />
    </svg>
  ),
  render: (
    // Film / export
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
      <rect x="2" y="3" width="12" height="10" rx="1.5" />
      <polygon points="6.5,6 6.5,10 10.5,8" fill="currentColor" stroke="none" />
    </svg>
  ),
};

// Status indicator icons
function SpinnerIcon() {
  return (
    <svg className="h-4 w-4 animate-spin text-blue-600" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg className="h-4 w-4 text-green-600" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3.5 8 6.5 11 12.5 5" />
    </svg>
  );
}

function ErrorIcon() {
  return (
    <svg className="h-4 w-4 text-red-500" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="4" y1="4" x2="12" y2="12" />
      <line x1="12" y1="4" x2="4" y2="12" />
    </svg>
  );
}

function PendingDot() {
  return <div className="h-2 w-2 rounded-full bg-gray-300 mx-auto" />;
}

export function ProcessingView({ messages, isConnected }: Props) {
  const stepStates = useMemo(() => {
    const states: Record<string, StepState> = {};
    for (const step of PIPELINE_STEPS) {
      states[step] = { status: "pending", current: 0, total: 0 };
    }
    for (const msg of messages) {
      if (!msg.step) continue;
      switch (msg.type) {
        case "step_start":
          states[msg.step] = { status: "running", current: 0, total: 0 };
          break;
        case "step_progress":
          states[msg.step] = {
            status: "running",
            current: msg.current ?? 0,
            total: msg.total ?? 0,
          };
          break;
        case "step_complete":
          states[msg.step] = { ...states[msg.step], status: "completed" };
          break;
        case "error":
          states[msg.step] = { ...states[msg.step], status: "failed" };
          break;
      }
    }
    return states;
  }, [messages]);

  const pipelineComplete = messages.some((m) => m.type === "pipeline_complete");
  const pipelineError = messages.find((m) => m.type === "error" && !m.step);
  const activeStep = PIPELINE_STEPS.find((s) => stepStates[s].status === "running");

  return (
    <Card className="p-6 max-w-xl mx-auto">
      {/* Animated header */}
      <div className="flex items-center gap-3 mb-6">
        {pipelineComplete ? (
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
            <CheckIcon />
          </div>
        ) : pipelineError ? (
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100">
            <ErrorIcon />
          </div>
        ) : (
          <div className="relative flex h-10 w-10 items-center justify-center">
            <div className="absolute inset-0 animate-ping rounded-full bg-blue-200 opacity-30" />
            <div className="relative flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-700">
              {activeStep ? STEP_ICONS[activeStep] : <SpinnerIcon />}
            </div>
          </div>
        )}
        <div>
          <h2 className="text-lg font-semibold">
            {pipelineComplete
              ? "Traduccion completada"
              : pipelineError
                ? "Error en el procesamiento"
                : "Procesando entrevista..."}
          </h2>
          {activeStep && !pipelineComplete && (
            <p className="text-sm text-gray-500">{STEP_LABELS[activeStep]}</p>
          )}
        </div>
      </div>

      {/* Step list */}
      <div className="space-y-2">
        {PIPELINE_STEPS.map((step) => {
          const state = stepStates[step];
          const label = STEP_LABELS[step] || step;
          const progressPct = state.total > 0 ? Math.round((state.current / state.total) * 100) : 0;
          const isActive = state.status === "running";
          const isDone = state.status === "completed";

          return (
            <div
              key={step}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors ${
                isActive
                  ? "bg-blue-50 border border-blue-100"
                  : isDone
                    ? "bg-gray-50"
                    : ""
              }`}
            >
              {/* Status indicator */}
              <div className="flex h-5 w-5 shrink-0 items-center justify-center">
                {state.status === "completed" && <CheckIcon />}
                {state.status === "running" && <SpinnerIcon />}
                {state.status === "failed" && <ErrorIcon />}
                {state.status === "pending" && <PendingDot />}
              </div>

              {/* Step icon */}
              <div className={`shrink-0 ${isActive ? "text-blue-700" : isDone ? "text-gray-400" : "text-gray-300"}`}>
                {STEP_ICONS[step]}
              </div>

              {/* Label + progress */}
              <div className="flex-1 min-w-0">
                <p className={`text-sm ${isActive ? "font-medium text-blue-900" : isDone ? "text-gray-600" : "text-gray-400"}`}>
                  {label}
                </p>
                {isActive && state.total > 0 && (
                  <div className="mt-1.5 flex items-center gap-2">
                    <Progress value={progressPct} className="h-1.5 flex-1" />
                    <span className="text-xs tabular-nums text-gray-400">
                      {state.current}/{state.total}
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer messages */}
      {pipelineError && (
        <div className="mt-4 rounded-md bg-red-50 p-3">
          <p className="text-sm text-red-700">{pipelineError.message || "Error en el pipeline"}</p>
        </div>
      )}

      {!isConnected && !pipelineComplete && (
        <div className="mt-4 flex items-center gap-2 text-xs text-amber-600">
          <SpinnerIcon />
          <span>Reconectando al servidor...</span>
        </div>
      )}
    </Card>
  );
}
