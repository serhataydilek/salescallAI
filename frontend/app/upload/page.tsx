"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  ALLOWED_AUDIO_EXTENSIONS,
  analyzeCall,
  createCallFromTranscript,
  transcribeCall,
  uploadCall,
  validateAudioFile,
  validateTranscriptInput,
} from "@/lib/api";

type ActionState = "idle" | "audio" | "transcript";
type WorkflowStatus = "idle" | "uploaded" | "transcribing" | "transcribed" | "analyzing" | "analyzed" | "failed";

const audioLoadingSteps = [
  "Uploading audio",
  "Transcribing call",
  "Analyzing sales performance",
  "Building coaching report",
];

const transcriptLoadingSteps = [
  "Creating call record",
  "Reading transcript",
  "Analyzing sales performance",
  "Building coaching report",
];

const statusLabels: Record<WorkflowStatus, string> = {
  idle: "Ready",
  uploaded: "Uploaded",
  transcribing: "Transcribing",
  transcribed: "Transcribed",
  analyzing: "Analyzing",
  analyzed: "Analyzed",
  failed: "Failed",
};

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [manualTranscript, setManualTranscript] = useState("");
  const [status, setStatus] = useState<WorkflowStatus>("idle");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [action, setAction] = useState<ActionState>("idle");
  const [loadingStepIndex, setLoadingStepIndex] = useState(0);

  const isBusy = action !== "idle";
  const activeSteps = action === "audio" ? audioLoadingSteps : transcriptLoadingSteps;

  useEffect(() => {
    if (!isBusy) {
      setLoadingStepIndex(0);
      return;
    }

    const intervalId = window.setInterval(() => {
      setLoadingStepIndex((current) => Math.min(current + 1, activeSteps.length - 1));
    }, 1800);

    return () => window.clearInterval(intervalId);
  }, [activeSteps.length, isBusy]);

  async function runAudioAnalysis() {
    const selectedFile = file;
    const validationError = validateAudioFile(selectedFile);
    if (validationError) {
      setError(validationError);
      setMessage("");
      setStatus("failed");
      return;
    }
    if (!selectedFile) return;

    setAction("audio");
    setError("");
    setMessage("");
    setStatus("uploaded");

    try {
      setLoadingStepIndex(0);
      const uploaded = await uploadCall(selectedFile);

      setStatus("transcribing");
      setLoadingStepIndex(1);
      await transcribeCall(uploaded.call_id);

      setStatus("analyzing");
      setLoadingStepIndex(2);
      await analyzeCall(uploaded.call_id);

      setStatus("analyzed");
      setLoadingStepIndex(3);
      router.push(`/calls/${uploaded.call_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not analyze audio call.");
      setStatus("failed");
      setAction("idle");
    }
  }

  async function runTranscriptAnalysis() {
    const validationError = validateTranscriptInput(manualTranscript);
    if (validationError) {
      setError(validationError);
      setMessage("");
      setStatus("failed");
      return;
    }

    setAction("transcript");
    setError("");
    setMessage("");
    setStatus("uploaded");

    try {
      setLoadingStepIndex(0);
      const createdCall = await createCallFromTranscript({
        title: title.trim() || undefined,
        transcript: manualTranscript.trim(),
      });

      setStatus("analyzing");
      setLoadingStepIndex(2);
      await analyzeCall(createdCall.id);

      setStatus("analyzed");
      setLoadingStepIndex(3);
      router.push(`/calls/${createdCall.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not analyze transcript.");
      setStatus("failed");
      setAction("idle");
    }
  }

  if (isBusy) {
    return (
      <section className="analysis-loading">
        <div className="loading-card">
          <div className="loader-ring" />
          <span className="eyebrow">SalesMirror</span>
          <h1>Generating Sales Coaching Report</h1>
          <p>{activeSteps[loadingStepIndex]}</p>
          <div className="loading-steps">
            {activeSteps.map((step, index) => (
              <span className={index <= loadingStepIndex ? "active" : ""} key={step}>
                {step}
              </span>
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="section">
      <div className="hero compact-hero">
        <h1>Analyze Sales Call Audio</h1>
        <p>Upload a sales call recording and SalesMirror will transcribe it, analyze it, and generate a coaching report.</p>
      </div>

      <div className="primary-workspace">
        <div className="upload-box">
          <div>
            <span className="eyebrow">Primary Flow</span>
            <h2>Upload Audio Call</h2>
            <p>Use a short sales call file for the local MVP. Real local transcription can take a while on CPU.</p>
          </div>

          <input
            accept={ALLOWED_AUDIO_EXTENSIONS.join(",")}
            disabled={isBusy}
            onChange={(event) => {
              const selectedFile = event.target.files?.[0] ?? null;
              setFile(selectedFile);
              setError(validateAudioFile(selectedFile) ?? "");
              setMessage("");
              setStatus("idle");
            }}
            type="file"
          />
          <p className="helper-text">Supported formats: mp3, wav, m4a, webm. Empty files are rejected.</p>

          <div className="workflow-status">
            <span className={`status ${status === "idle" ? "uploaded" : status}`}>{statusLabels[status]}</span>
            <p>
              {status === "idle"
                ? "Choose an audio file, then run the full analysis flow."
                : status === "failed"
                  ? "The last step failed. Check the error and try again."
                  : "SalesMirror is preparing the report."}
            </p>
          </div>

          <div className="actions">
            <button disabled={isBusy} onClick={runAudioAnalysis} type="button">
              Analyze Audio Call
            </button>
            <Link className="button secondary" href="/calls">
              View Calls
            </Link>
          </div>
        </div>
      </div>

      {error ? <div className="message error">{error}</div> : null}
      {message ? <div className="message">{message}</div> : null}

      <details className="secondary-tool">
        <summary>Already have a transcript?</summary>
        <div className="secondary-tool-body">
          <p>
            Paste an existing transcript when you want to test analysis quality without running local audio transcription.
            If your source is video, you can convert it first with{" "}
            <a href="https://github.com/serhataydilek/videototext" rel="noreferrer" target="_blank">
              VideoToText
            </a>
            .
          </p>

          <label className="field">
            <span>Call title</span>
            <input
              disabled={isBusy}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Optional title"
              type="text"
              value={title}
            />
          </label>
          <label className="field">
            <span>Transcript</span>
            <textarea
              disabled={isBusy}
              onChange={(event) => {
                setManualTranscript(event.target.value);
                setError("");
                setMessage("");
              }}
              placeholder={"Salesperson: Hi, thanks for joining today.\nCustomer: Happy to talk."}
              rows={12}
              value={manualTranscript}
            />
          </label>
          <div className="workspace-footer">
            <p className="helper-text">Use speaker labels like Salesperson and Customer. Minimum 30 characters.</p>
            <button disabled={isBusy} onClick={runTranscriptAnalysis} type="button">
              Analyze Transcript
            </button>
          </div>
        </div>
      </details>
    </section>
  );
}
