import Link from "next/link";
import { type Analysis, getCall, reportUrl } from "@/lib/api";

type PageProps = {
  params: Promise<{ id: string }>;
};

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="report-block">
      <h3>{title}</h3>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function ScoreCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="score">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>/100</small>
    </div>
  );
}

function ReportSummary({ analysis }: { analysis: Analysis }) {
  return (
    <div className="report-summary">
      <div>
        <span className="eyebrow">Overall Score</span>
        <div className="overall-score">{analysis.overall_score}</div>
      </div>
      <div>
        <h2>Sales Coaching Report</h2>
        <p>{analysis.short_summary}</p>
        <p>{analysis.talk_ratio_feedback}</p>
      </div>
    </div>
  );
}

export default async function CallDetailPage({ params }: PageProps) {
  const { id } = await params;
  let call;

  try {
    call = await getCall(id);
  } catch (error) {
    return (
      <section className="section">
        <div className="empty-state">
          <h1>Call not available</h1>
          <p>{error instanceof Error ? error.message : "Could not load this call."}</p>
          <Link className="button" href="/calls">
            Back to Calls
          </Link>
        </div>
      </section>
    );
  }

  const analysis = call.analysis;

  return (
    <section className="section">
      <div className="call-card-top">
        <div>
          <h1>{call.filename}</h1>
          <p>Uploaded {new Date(call.created_at).toLocaleString()}</p>
        </div>
        <span className={`status ${call.status}`}>{call.status}</span>
      </div>

      <div className="actions">
        <Link className="button secondary" href="/calls">
          Back to Calls
        </Link>
        {analysis ? (
          <a className="button" href={reportUrl(call.id)}>
            Download Text Report
          </a>
        ) : null}
      </div>

      {analysis ? (
        <>
          <ReportSummary analysis={analysis} />

          <div className="report-section">
            <div>
              <span className="eyebrow">Score Breakdown</span>
              <h2>Conversation Quality</h2>
            </div>
            <div className="score-grid">
              <ScoreCard label="Opening" value={analysis.opening_score} />
              <ScoreCard label="Discovery" value={analysis.discovery_score} />
              <ScoreCard label="Objections" value={analysis.objection_handling_score} />
              <ScoreCard label="Closing" value={analysis.closing_score} />
              <ScoreCard label="Follow Up" value={analysis.follow_up_score} />
            </div>
          </div>

          <div className="two-column">
            <ListBlock title="Top Mistakes" items={analysis.top_3_mistakes} />
            <ListBlock title="Missed Questions" items={analysis.missed_questions} />
            <ListBlock title="Suggested Improvements" items={analysis.suggested_improvements} />
            <ListBlock title="Better Example Responses" items={analysis.better_example_responses} />
          </div>
        </>
      ) : (
        <div className="empty-state">
          <h2>Analysis not ready</h2>
          <p>Run Transcribe and Analyze from the upload flow to generate this coaching report.</p>
          <Link className="button" href="/upload">
            Go to Upload
          </Link>
        </div>
      )}

      <div className="report-section">
        <div>
          <span className="eyebrow">Transcript</span>
          <h2>Call Conversation</h2>
        </div>
        {call.transcript ? <pre>{call.transcript.text}</pre> : <p>No transcript yet. Go to upload flow and run Transcribe.</p>}
      </div>
    </section>
  );
}
