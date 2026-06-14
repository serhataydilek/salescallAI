"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { updateTranscript, validateTranscriptInput } from "@/lib/api";
import { ReAnalyzeButton } from "@/components/ReAnalyzeButton";

export function TranscriptEditor({
  callId,
  initialTranscript,
}: {
  callId: number;
  initialTranscript: string;
}) {
  const router = useRouter();
  const [isEditing, setIsEditing] = useState(false);
  const [transcript, setTranscript] = useState(initialTranscript);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleSave() {
    const validationError = validateTranscriptInput(transcript);
    if (validationError) {
      setError(validationError);
      setMessage("");
      return;
    }

    setIsSaving(true);
    setError("");
    setMessage("");

    try {
      const updatedCall = await updateTranscript(callId, transcript.trim());
      setTranscript(updatedCall.transcript?.text ?? transcript.trim());
      setIsEditing(false);
      setMessage("Transcript updated. Re-run analysis to refresh the report.");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save transcript.");
    } finally {
      setIsSaving(false);
    }
  }

  function handleCancel() {
    setTranscript(initialTranscript);
    setIsEditing(false);
    setError("");
  }

  if (!initialTranscript && !isEditing) {
    return (
      <div className="empty-state compact">
        <h3>No transcript yet</h3>
        <p>Transcribe uploaded audio or paste an existing transcript to generate a complete coaching report.</p>
      </div>
    );
  }

  return (
    <div className="transcript-editor">
      {message ? (
        <div className="message transcript-update-message">
          <span>{message}</span>
          <ReAnalyzeButton callId={callId} />
        </div>
      ) : null}
      {error ? <div className="message error">{error}</div> : null}

      {isEditing ? (
        <div className="transcript-edit-form">
          <textarea
            disabled={isSaving}
            onChange={(event) => {
              setTranscript(event.target.value);
              setError("");
            }}
            rows={16}
            value={transcript}
          />
          <div className="workspace-footer">
            <p className="helper-text">Minimum 30 characters. Saving marks the report as needing refresh.</p>
            <div className="actions">
              <button disabled={isSaving} onClick={handleSave} type="button">
                {isSaving ? "Saving..." : "Save Transcript"}
              </button>
              <button className="secondary" disabled={isSaving} onClick={handleCancel} type="button">
                Cancel
              </button>
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="actions no-print">
            <button className="secondary" onClick={() => setIsEditing(true)} type="button">
              Edit Transcript
            </button>
          </div>
          <pre className="transcript-box">{transcript}</pre>
        </>
      )}
    </div>
  );
}
