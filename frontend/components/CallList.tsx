import Link from "next/link";
import type { Call } from "@/lib/api";

export function CallList({ calls, showUploadAction = true }: { calls: Call[]; showUploadAction?: boolean }) {
  if (calls.length === 0) {
    return (
      <div className="empty-state">
        <h3>No calls yet</h3>
        <p>Upload a call or seed demo data to see the coaching report workflow.</p>
        {showUploadAction ? (
          <Link className="button" href="/upload">
            Upload First Call
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
              <div className="meta">Uploaded {new Date(call.created_at).toLocaleString()}</div>
            </div>
            <span className={`status ${call.status}`}>{call.status}</span>
          </div>
          <div className="actions">
            <Link className="button secondary" href={`/calls/${call.id}`}>
              View Report
            </Link>
          </div>
        </article>
      ))}
    </div>
  );
}
