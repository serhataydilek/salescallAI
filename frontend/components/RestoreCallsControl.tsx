"use client";

import { useState } from "react";
import { importCallsJson, type ImportCallsResponse } from "@/lib/api";

export function RestoreCallsControl() {
  const [file, setFile] = useState<File | null>(null);
  const [summary, setSummary] = useState<ImportCallsResponse | null>(null);
  const [error, setError] = useState("");
  const [isBusy, setIsBusy] = useState(false);

  async function runImport(dryRun: boolean) {
    if (!file) {
      setError("Choose a SalesMirror calls JSON export first.");
      setSummary(null);
      return;
    }

    setIsBusy(true);
    setError("");
    setSummary(null);
    try {
      const result = await importCallsJson(file, dryRun);
      setSummary(result);
      if (!dryRun && result.imported_calls > 0) {
        window.location.reload();
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : "Restore failed.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <div className="restore-control">
      <label className="field">
        <span>Restore from JSON</span>
        <input
          accept="application/json,.json"
          disabled={isBusy}
          onChange={(event) => {
            setFile(event.target.files?.[0] ?? null);
            setSummary(null);
            setError("");
          }}
          type="file"
        />
      </label>
      <div className="actions">
        <button className="secondary" disabled={isBusy || !file} onClick={() => runImport(true)} type="button">
          Preview Restore
        </button>
        <button className="secondary" disabled={isBusy || !file} onClick={() => runImport(false)} type="button">
          {isBusy ? "Restoring..." : "Restore from JSON"}
        </button>
      </div>
      <p className="helper-text">
        Restores call records, transcripts, and analyses only. Uploaded audio files are not embedded or restored.
      </p>
      {summary ? (
        <div className="message">
          <strong>{summary.message}</strong>
          <span>
            Calls: {summary.imported_calls}, transcripts: {summary.imported_transcripts}, analyses:{" "}
            {summary.imported_analyses}, skipped: {summary.skipped_items}
          </span>
        </div>
      ) : null}
      {error ? <div className="message error">{error}</div> : null}
    </div>
  );
}
