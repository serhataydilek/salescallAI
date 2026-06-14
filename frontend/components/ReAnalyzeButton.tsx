"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { analyzeCall } from "@/lib/api";

export function ReAnalyzeButton({ callId }: { callId: number }) {
  const router = useRouter();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState("");

  async function handleReAnalyze() {
    setIsAnalyzing(true);
    setError("");

    try {
      await analyzeCall(callId);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not re-run analysis.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  return (
    <div className="reanalyze-control">
      <button disabled={isAnalyzing} onClick={handleReAnalyze} type="button">
        {isAnalyzing ? "Analyzing updated transcript..." : "Re-run Analysis"}
      </button>
      {error ? <div className="message error">{error}</div> : null}
    </div>
  );
}
