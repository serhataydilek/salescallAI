"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { clearCalls } from "@/lib/api";

export function ClearCallsButton({ disabled = false }: { disabled?: boolean }) {
  const router = useRouter();
  const [isClearing, setIsClearing] = useState(false);
  const [error, setError] = useState("");

  async function handleClear() {
    const confirmed = window.confirm(
      "Clear all local calls? This removes call records, transcripts, analyses, and uploaded audio files."
    );
    if (!confirmed) return;

    setIsClearing(true);
    setError("");
    try {
      await clearCalls();
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not clear calls.");
    } finally {
      setIsClearing(false);
    }
  }

  return (
    <div className="clear-calls-control">
      <button className="secondary danger strong" disabled={disabled || isClearing} onClick={handleClear} type="button">
        {isClearing ? "Clearing..." : "Clear Calls"}
      </button>
      {error ? <div className="message error">{error}</div> : null}
    </div>
  );
}
