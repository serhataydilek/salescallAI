import Link from "next/link";
import { DeleteCallButton } from "@/components/DeleteCallButton";
import { PrintButton } from "@/components/PrintButton";
import { type Analysis, getCall, reportUrl } from "@/lib/api";

type PageProps = {
  params: Promise<{ id: string }>;
};

function scoreLabel(score: number): string {
  if (score >= 80) return "Strong call";
  if (score >= 60) return "Decent call";
  if (score >= 40) return "Weak call";
  return "Poor call";
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="report-block">
      <h3>{title}</h3>
      {items.length > 0 ? (
        <ul className="report-list">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>No items returned for this section.</p>
      )}
    </section>
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

function SourceMeta({ label, value }: { label: string; value: string }) {
  return (
    <div className="report-meta-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function sourceLabel(filePath: string): string {
  if (filePath === "manual-transcript") {
    return "Pasted transcript";
  }

  const pathParts = filePath.split(/[/\\]/);
  const storedName = pathParts[pathParts.length - 1] ?? "";
  const firstUnderscore = storedName.indexOf("_");
  const originalName = firstUnderscore >= 0 ? storedName.slice(firstUnderscore + 1) : storedName;
  return originalName || "Uploaded audio";
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
  const createdAt = new Date(call.created_at).toLocaleString();

  return (
    <article className="section report-page">
      <header className="report-header">
        <div className="report-title-block">
          <span className="eyebrow">Sales Coaching Report</span>
          <h1>{call.filename}</h1>
          <div className="report-meta-grid">
            <SourceMeta label="Created" value={createdAt} />
            <SourceMeta label="Source" value={sourceLabel(call.file_path)} />
            <SourceMeta label="Status" value={call.status} />
          </div>
        </div>
        <div className="report-header-actions no-print">
          <span className={`status ${call.status}`}>{call.status}</span>
          <Link className="button secondary" href="/calls">
            Back to Calls
          </Link>
          {analysis ? (
            <>
              <PrintButton />
              <a className="button" href={reportUrl(call.id)}>
                Download Report
              </a>
            </>
          ) : null}
          <DeleteCallButton callId={call.id} redirectTo="/calls" />
        </div>
      </header>

      {isFailed ? (
        <div className="message error">
          This call is marked as failed. Upload the audio again or create a new report from a pasted transcript.
        </div>
      ) : null}

      {analysis ? (
        <>
          <section className="report-score-hero">
            <div className="score-hero-main">
              <span className="eyebrow">Overall Score</span>
              <div className="overall-score">{analysis.overall_score}</div>
              <strong className="score-label">{scoreLabel(analysis.overall_score)}</strong>
            </div>
            <div className="score-hero-copy">
              <h2>Analysis Summary</h2>
              <p>{analysis.short_summary}</p>
              <div className="talk-ratio-box">
                <span>Talk Ratio Feedback</span>
                <p>{analysis.talk_ratio_feedback}</p>
              </div>
            </div>
          </section>

          <section className="report-section">
            <div className="section-heading">
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
          </section>

          <section className="report-section">
            <div className="section-heading">
              <span className="eyebrow">Coaching Notes</span>
              <h2>Recommendations</h2>
            </div>
            <div className="two-column">
              <ListBlock title="Coaching Opportunities" items={analysis.top_3_mistakes} />
              <ListBlock title="Missed Questions" items={analysis.missed_questions} />
              <ListBlock title="Suggested Improvements" items={analysis.suggested_improvements} />
              <ListBlock title="Better Example Responses" items={analysis.better_example_responses} />
            </div>
          </section>
        </>
      ) : (
        <div className="empty-state">
          <h2>Analysis not ready</h2>
          <p>
            {transcriptText
              ? "A transcript is available, but this call has not been analyzed yet. Use the upload page to run analysis again or create a new report from this transcript."
              : "This call does not have a transcript yet. Run the audio analysis flow or paste a transcript to create a report."}
          </p>
          <div className="actions no-print">
            <Link className="button" href="/upload">
              Analyze a Call
            </Link>
          </div>
        </div>
      )}

      <section className="report-section">
        <div className="section-heading">
          <span className="eyebrow">Transcript</span>
          <h2>Call Transcript</h2>
        </div>
        {transcriptText ? (
          <pre className="transcript-box">{transcriptText}</pre>
        ) : (
          <div className="empty-state compact">
            <h3>No transcript yet</h3>
            <p>Transcribe uploaded audio or paste an existing transcript to generate a complete coaching report.</p>
          </div>
        )}
      </section>
    </article>
  );
}
