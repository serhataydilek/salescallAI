import Link from "next/link";
import { DeleteCallButton } from "@/components/DeleteCallButton";
import type { Call } from "@/lib/api";

const categoryScores = [
  ["Opening", "opening_score"],
  ["Discovery", "discovery_score"],
  ["Objections", "objection_handling_score"],
  ["Closing", "closing_score"],
  ["Follow Up", "follow_up_score"],
] as const;

function scoreLabel(score: number): string {
  if (score >= 80) return "Strong call";
  if (score >= 60) return "Decent call";
  if (score >= 40) return "Weak call";
  return "Poor call";
}

function scoreClass(score: number): string {
  if (score >= 80) return "score-strong";
  if (score >= 60) return "score-decent";
  if (score >= 40) return "score-weak";
  return "score-poor";
}

export function CallList({
  calls,
  emptyMessage = "Analyze a call or seed demo data to see the coaching report workflow.",
  showUploadAction = true,
}: {
  calls: Call[];
  emptyMessage?: string;
  showUploadAction?: boolean;
}) {
  if (calls.length === 0) {
    return (
      <div className="empty-state">
        <h3>No calls yet</h3>
        <p>{emptyMessage}</p>
        {showUploadAction ? (
          <Link className="button" href="/upload">
            Analyze First Call
          </Link>
        ) : null}
      </div>
    );
  }

  return (
    <div className="card-grid">
      {calls.map((call) => (
        <article className="call-card" key={call.id}>
          <div className="call-card-top">
            <div>
              <h3>{call.filename}</h3>
              <div className="meta">Created {new Date(call.created_at).toLocaleString()}</div>
            </div>
            <div className="call-card-badges">
              <span className={`status ${call.status}`}>{call.status}</span>
              {call.overall_score !== null ? (
                <div className={`call-score ${scoreClass(call.overall_score)}`} aria-label="Overall score">
                  <strong>{call.overall_score}</strong>
                  <span>{scoreLabel(call.overall_score)}</span>
                </div>
              ) : (
                <div className="call-score no-score">
                  <strong>-</strong>
                  <span>No score yet</span>
                </div>
              )}
            </div>
          </div>
          {call.overall_score !== null ? (
            <div className="call-score-preview" aria-label="Category score preview">
              {categoryScores.map(([label, key]) => (
                <span key={key}>
                  {label} <strong>{call[key] ?? "-"}</strong>
                </span>
              ))}
            </div>
          ) : null}
          <div className="actions">
            <Link className="button secondary" href={`/calls/${call.id}`}>
              View Report
            </Link>
            <DeleteCallButton callId={call.id} />
          </div>
        </article>
      ))}
    </div>
  );
}
