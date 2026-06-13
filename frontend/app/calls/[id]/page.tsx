import Link from "next/link";
import { type Analysis, getCall, reportUrl } from "@/lib/api";

type PageProps = {
  params: Promise<{ id: string }>;
};

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="report-block">
      <div className="block-heading">
        <span aria-hidden="true">•</span>
        <h3>{title}</h3>
      </div>
      {items.length > 0 ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>No items returned for this section.</p>
      )}
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
        <h2>Analysis Summary</h2>
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
  const transcriptText = call.transcript?.text.trim() ?? "";
  const isFailed = call.status === "failed";

  return (
    <section className="section">
      <div className="report-header">
        <div>
          <span className="eyebrow">Sales Coaching Report</span>
          <h1>{call.filename}</h1>
          <p>Uploaded {new Date(call.created_at).toLocaleString()}</p>
        </div>
        <div className="report-header-actions">
          <span className={`status ${call.status}`}>{call.status}</span>
          <Link className="button secondary" href="/calls">
            Back to Calls
          </Link>
          {analysis ? (
            <a className="button" href={reportUrl(call.id)}>
              Download Text Report
            </a>
          ) : null}
        </div>
      </div>

      {isFailed ? (
        <div className="message error">
          This call is marked as failed. Try uploading the audio again or rerun the last step from the upload flow.
        </div>
      ) : null}

      {analysis ? (
        <>
          <ReportSummary analysis={analysis} />

          <div className="report-section">
            <div>
              <span className="eyebrow">Score Breakdown</span>
              <h2>Category Scores</h2>
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
            <ListBlock title="Coaching Opportunities" items={analysis.top_3_mistakes} />
            <ListBlock title="Missed Questions" items={analysis.missed_questions} />
            <ListBlock title="Suggested Improvements" items={analysis.suggested_improvements} />
            <ListBlock title="Better Example Responses" items={analysis.better_example_responses} />
          </div>
        </>
      ) : (
        <div className="empty-state">
          <h2>Analysis not ready</h2>
          <p>
            {transcriptText
              ? "Transcript is available. Run Analyze from the upload flow to generate this coaching report."
              : "Run Transcribe and Analyze from the upload flow to generate this coaching report."}
          </p>
          <Link className="button" href="/upload">
            Go to Upload
          </Link>
        </div>
      )}

      <div className="report-section">
        <div>
          <span className="eyebrow">Transcript</span>
          <h2>Call Transcript</h2>
        </div>
        {transcriptText ? (
          <pre className="transcript-box">{transcriptText}</pre>
        ) : (
          <div className="empty-state compact">
            <h3>No transcript yet</h3>
            <p>Run Transcribe from the upload flow. Real local transcription can take a while on CPU.</p>
          </div>
        )}
      </div>
    </section>
  );
}
