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

  return (
    <Card className="p-6 max-w-xl mx-auto">
      <h2 className="text-lg font-semibold mb-4">Procesando entrevista...</h2>

      <div className="space-y-3">
        {PIPELINE_STEPS.map((step) => {
          const state = stepStates[step];
          const label = STEP_LABELS[step] || step;
          const progressPct = state.total > 0 ? Math.round((state.current / state.total) * 100) : 0;

          return (
            <div key={step} className="flex items-center gap-3">
              <div className="w-5 text-center">
                {state.status === "completed" && <span className="text-green-600">&#10003;</span>}
                {state.status === "running" && <span className="animate-spin inline-block">&#9696;</span>}
                {state.status === "failed" && <span className="text-red-600">&#10007;</span>}
                {state.status === "pending" && <span className="text-gray-300">&#9675;</span>}
              </div>
              <div className="flex-1 min-w-0">
                <p className={`text-sm ${state.status === "running" ? "font-medium" : "text-gray-500"}`}>
                  {label}
                </p>
                {state.status === "running" && state.total > 0 && (
                  <div className="mt-1 flex items-center gap-2">
                    <Progress value={progressPct} className="h-1.5 flex-1" />
                    <span className="text-xs text-gray-400">{state.current}/{state.total}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {pipelineComplete && (
        <p className="mt-4 text-sm text-green-700 font-medium">Pipeline completado</p>
      )}
      {pipelineError && (
        <p className="mt-4 text-sm text-red-600">{pipelineError.message || "Error en el pipeline"}</p>
      )}

      {!isConnected && !pipelineComplete && (
        <p className="mt-4 text-xs text-amber-600">Reconectando...</p>
      )}
    </Card>
  );
}
