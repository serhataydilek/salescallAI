"use client";

import Link from "next/link";
import { useState } from "react";
import { ALLOWED_AUDIO_EXTENSIONS, analyzeCall, transcribeCall, uploadCall, validateAudioFile } from "@/lib/api";

type ActionState = "idle" | "uploading" | "transcribing" | "analyzing";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [callId, setCallId] = useState<number | null>(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [action, setAction] = useState<ActionState>("idle");

  const isBusy = action !== "idle";

  async function runUpload() {
    const selectedFile = file;
    const validationError = validateAudioFile(selectedFile);
    if (validationError) {
      setError(validationError);
      setStatus("");
      return;
    }
    if (!selectedFile) return;

    setAction("uploading");
    setError("");
    setStatus("Uploading call...");
    try {
      const result = await uploadCall(selectedFile);
      setCallId(result.call_id);
      setStatus(`Uploaded ${result.filename}. Call ID: ${result.call_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
      setStatus("");
    } finally {
      setAction("idle");
    }
  }

  async function runTranscribe() {
    if (!callId) return;
    setAction("transcribing");
    setError("");
    setStatus("Generating mock transcript...");
    try {
      await transcribeCall(callId);
      setStatus("Mock transcript stored.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transcription failed.");
      setStatus("");
    } finally {
      setAction("idle");
    }
  }

  async function runAnalyze() {
    if (!callId) return;
    setAction("analyzing");
    setError("");
    setStatus("Running rule-based analysis...");
    try {
      await analyzeCall(callId);
      setStatus("Analysis stored. View the report when ready.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
      setStatus("");
    } finally {
      setAction("idle");
    }
  }

  return (
    <section className="section">
      <div>
        <h1>Upload a sales call</h1>
        <p>Audio is saved locally in the backend uploads folder for this MVP.</p>
      </div>

      <div className="upload-box">
        <input
          accept={ALLOWED_AUDIO_EXTENSIONS.join(",")}
          onChange={(event) => {
            const selectedFile = event.target.files?.[0] ?? null;
            setFile(selectedFile);
            setError(validateAudioFile(selectedFile) ?? "");
            setStatus("");
          }}
          type="file"
        />
        <p className="helper-text">Supported formats: mp3, wav, m4a, webm. Empty files are rejected.</p>
        <div className="actions">
          <button disabled={isBusy} onClick={runUpload} type="button">
            {action === "uploading" ? "Uploading..." : "Upload"}
          </button>
          <button className="secondary" disabled={!callId || isBusy} onClick={runTranscribe} type="button">
            {action === "transcribing" ? "Transcribing..." : "Transcribe"}
          </button>
          <button className="secondary" disabled={!callId || isBusy} onClick={runAnalyze} type="button">
            {action === "analyzing" ? "Analyzing..." : "Analyze"}
          </button>
          {callId ? (
            <Link className="button secondary" href={`/calls/${callId}`}>
              View Report
            </Link>
          ) : null}
        </div>
        <div className="demo-note">
          For demo data without an audio file, run <code>python scripts/seed_demo.py</code> from the backend folder.
        </div>
      </div>

      {status ? <div className="message">{status}</div> : null}
      {error ? <div className="message error">{error}</div> : null}
    </section>
  );
}
