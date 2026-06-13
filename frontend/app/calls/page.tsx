import Link from "next/link";
import { CallList } from "@/components/CallList";
import { type Call, getCalls } from "@/lib/api";

export default async function CallsPage() {
  let calls: Call[] = [];
  let loadError = "";

  try {
    calls = await getCalls();
  } catch {
    loadError = "Backend is not reachable. Start the FastAPI server to load calls.";
  }

  return (
    <section className="section">
      <div className="call-card-top">
        <div>
          <h1>Calls</h1>
          <p>All uploaded calls in local storage.</p>
        </div>
        <Link className="button" href="/upload">
          Upload
        </Link>
      </div>
      {loadError ? <div className="message error">{loadError}</div> : <CallList calls={calls} />}
    </section>
  );
}
