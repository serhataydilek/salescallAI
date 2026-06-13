import Link from "next/link";
import { CallList } from "@/components/CallList";
import { type Call, getCalls } from "@/lib/api";

export default async function DashboardPage() {
  let calls: Call[] = [];
  let loadError = "";

  try {
    calls = (await getCalls()).slice(0, 5);
  } catch {
    loadError = "Backend is not reachable. Start the FastAPI server to load recent calls.";
  }

  return (
    <>
      <section className="hero">
        <h1>Review sales calls and generate coaching reports locally.</h1>
        <p>
          Upload an audio file, run mock transcription, and get a rule-based sales coaching
          scorecard for the MVP workflow.
        </p>
        <div className="actions">
          <Link className="button" href="/upload">
            Upload a Call
          </Link>
          <Link className="button secondary" href="/calls">
            View Calls
          </Link>
        </div>
      </section>

      <section className="section">
        <h2>Recent Calls</h2>
        {loadError ? <div className="message error">{loadError}</div> : <CallList calls={calls} />}
      </section>
    </>
  );
}
