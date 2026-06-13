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

type ActionState = "idle" | "uploading" | "transcribing" | "analyzing" | "analyzingTranscript";
type WorkflowStatus = "idle" | "uploaded" | "transcribed" | "analyzed" | "failed";

const loadingSteps = [
  "Creating call record",
  "Reading transcript",
  "Analyzing sales performance",
  "Building coaching report",
];

const statusLabels: Record<WorkflowStatus, string> = {
  idle: "Ready",
  uploaded: "Uploaded",
  transcribed: "Transcribed",
  analyzed: "Analyzed",
  failed: "Failed",
};

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [manualTranscript, setManualTranscript] = useState("");
  const [audioCallId, setAudioCallId] = useState<number | null>(null);
  const [audioStatus, setAudioStatus] = useState<WorkflowStatus>("idle");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [action, setAction] = useState<ActionState>("idle");
  const [loadingStepIndex, setLoadingStepIndex] = useState(0);

  const isBusy = action !== "idle";
  const isTranscriptRunning = action === "analyzingTranscript";
  const canTranscribeAudio = Boolean(audioCallId) && !isBusy && audioStatus !== "analyzed";
  const canAnalyzeAudio = Boolean(audioCallId) && !isBusy && (audioStatus === "transcribed" || audioStatus === "analyzed");

  useEffect(() => {
    if (!isTranscriptRunning) {
      setLoadingStepIndex(0);
      return;
    }

    const intervalId = window.setInterval(() => {
      setLoadingStepIndex((current) => Math.min(current + 1, loadingSteps.length - 1));
    }, 1400);

    return () => window.clearInterval(intervalId);
  }, [isTranscriptRunning]);

  function resetAudioState() {
    setAudioCallId(null);
    setAudioStatus("idle");
    setStatus("");
    setError("");
  }

  async function runTranscriptAnalysis() {
    const validationError = validateTranscriptInput(manualTranscript);
    if (validationError) {
      setError(validationError);
      setStatus("");
      return;
    }

    setAction("analyzingTranscript");
    setError("");
    setStatus("");

    try {
      setLoadingStepIndex(0);
      const createdCall = await createCallFromTranscript({
        title: title.trim() || undefined,
        transcript: manualTranscript.trim(),
      });

      setLoadingStepIndex(2);
      await analyzeCall(createdCall.id);

      setLoadingStepIndex(3);
      router.push(`/calls/${createdCall.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not analyze transcript.");
      setAction("idle");
    }
  }

  async function runAudioUpload() {
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
    setAudioStatus("idle");
    setStatus("Uploading call...");
    try {
      const result = await uploadCall(selectedFile);
      setAudioCallId(result.call_id);
      setAudioStatus("uploaded");
      setStatus(`Uploaded ${result.filename}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
      setAudioStatus("failed");
      setStatus("");
    } finally {
      setAction("idle");
    }
  }

  async function runAudioTranscribe() {
    if (!audioCallId) return;
    setAction("transcribing");
    setError("");
    setStatus("Transcribing audio locally. This can take a while for real audio...");
    try {
      await transcribeCall(audioCallId);
      setAudioStatus("transcribed");
      setStatus("Transcribed. You can now analyze the call.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transcription failed.");
      setAudioStatus("failed");
      setStatus("");
    } finally {
      setAction("idle");
    }
  }

  async function runAudioAnalyze() {
    if (!audioCallId) return;
    setAction("analyzing");
    setError("");
    setStatus("Analyzing transcript with the configured local provider...");
    try {
      await analyzeCall(audioCallId);
      setAudioStatus("analyzed");
      setStatus("Analyzed. The coaching report is ready.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
      setAudioStatus("failed");
      setStatus("");
    } finally {
      setAction("idle");
    }
  }

  if (isTranscriptRunning) {
    return (
      <section className="analysis-loading">
        <div className="loading-card">
          <div className="loader-ring" />
          <span className="eyebrow">SalesMirror</span>
          <h1>Generating Sales Coaching Report</h1>
          <p>{loadingSteps[loadingStepIndex]}</p>
          <div className="loading-steps">
            {loadingSteps.map((step, index) => (
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
        <h1>Analyze Sales Call Transcript</h1>
        <p>Paste a sales call transcript and SalesMirror will generate a coaching report.</p>
      </div>

      <div className="primary-workspace">
        <label className="field">
          <span>Call title</span>
          <input
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Discovery call with Acme"
            type="text"
            value={title}
          />
        </label>
        <label className="field">
          <span>Transcript</span>
          <textarea
            onChange={(event) => {
              setManualTranscript(event.target.value);
              setError("");
              setStatus("");
            }}
            placeholder={"Salesperson: Hi, thanks for joining today.\nCustomer: Happy to talk."}
            rows={16}
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

      {error ? <div className="message error">{error}</div> : null}
      {status ? <div className="message">{status}</div> : null}

      <details className="secondary-tool">
        <summary>Need to convert audio/video first?</summary>
        <div className="secondary-tool-body">
          <p>
            SalesMirror works best with transcripts. If you have audio or video, convert it to text first using the{" "}
            <a href="https://github.com/serhataydilek/videototext" rel="noreferrer" target="_blank">
              VideoToText tool
            </a>
            .
          </p>

          <div className="upload-box subtle">
            <div>
              <h2>Optional Dev Audio Flow</h2>
              <p>Keep using the local audio pipeline when you want to test faster-whisper inside SalesMirror.</p>
            </div>
            <input
              accept={ALLOWED_AUDIO_EXTENSIONS.join(",")}
              onChange={(event) => {
                const selectedFile = event.target.files?.[0] ?? null;
                setFile(selectedFile);
                resetAudioState();
                setError(validateAudioFile(selectedFile) ?? "");
              }}
              type="file"
            />
            <p className="helper-text">Supported formats: mp3, wav, m4a, webm. Empty files are rejected.</p>
            <div className="workflow-status">
              <span className={`status ${audioStatus === "idle" ? "uploaded" : audioStatus}`}>
                {action === "uploading"
                  ? "Uploading"
                  : action === "transcribing"
                    ? "Transcribing"
                    : action === "analyzing"
                      ? "Analyzing"
                      : statusLabels[audioStatus]}
              </span>
              <p>
                {audioStatus === "idle"
                  ? "Upload audio only when testing the local transcription path."
                  : audioStatus === "uploaded"
                    ? "Audio is saved. Run transcription next."
                    : audioStatus === "transcribed"
                      ? "Transcript is saved. Run analysis next."
                      : audioStatus === "analyzed"
                        ? "Report is ready to view."
                        : "The last step failed. Check the error and try again."}
              </p>
            </div>
            <div className="actions">
              <button disabled={isBusy} onClick={runAudioUpload} type="button">
                {action === "uploading" ? "Uploading..." : "Upload Audio"}
              </button>
              <button className="secondary" disabled={!canTranscribeAudio} onClick={runAudioTranscribe} type="button">
                {action === "transcribing" ? "Transcribing..." : "Transcribe"}
              </button>
              <button className="secondary" disabled={!canAnalyzeAudio} onClick={runAudioAnalyze} type="button">
                {action === "analyzing" ? "Analyzing..." : "Analyze"}
              </button>
              {audioCallId ? (
                <Link className="button secondary" href={`/calls/${audioCallId}`}>
                  View Report
                </Link>
              ) : null}
            </div>
          </div>
        </div>
      </details>
    </section>
  );
}
