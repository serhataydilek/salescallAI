import Link from "next/link";
import { type AnalyticsSummary, getAnalyticsSummary } from "@/lib/api";

function formatScore(score: number | null): string {
  return score === null ? "No data" : `${score.toFixed(1)}/100`;
}

function StatCard({ label, value, helper }: { label: string; value: string | number; helper?: string }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {helper ? <small>{helper}</small> : null}
    </div>
  );
}

function DistributionBar({ label, value, total }: { label: string; value: number; total: number }) {
  const width = total > 0 ? Math.round((value / total) * 100) : 0;

  return (
    <div className="distribution-row">
      <div className="distribution-label">
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      <div className="distribution-track">
        <div className="distribution-fill" style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

function trendDeltaLabel(summary: AnalyticsSummary): { label: string; helper: string } {
  const delta = summary.improvement_delta;
  if (delta.direction === "insufficient_data" || delta.delta === null) {
    return {
      label: "Need more analyzed calls",
      helper: "Analyze at least two calls to see trend.",
    };
  }
  if (delta.direction === "improved") {
    return {
      label: `Improved +${delta.delta}`,
      helper: `${delta.first_score}/100 to ${delta.latest_score}/100`,
    };
  }
  if (delta.direction === "declined") {
    return {
      label: `Declined ${delta.delta}`,
      helper: `${delta.first_score}/100 to ${delta.latest_score}/100`,
    };
  }
  return {
    label: "No change",
    helper: `${delta.first_score}/100 to ${delta.latest_score}/100`,
  };
}

function ScoreTrend({ summary }: { summary: AnalyticsSummary }) {
  if (summary.score_trend.length < 2) {
    return (
      <div className="empty-state compact">
        <h3>Not enough trend data</h3>
        <p>Analyze at least two calls to see trend.</p>
      </div>
    );
  }

  return (
    <div className="trend-list">
      {summary.score_trend.map((point) => (
        <Link className="trend-row" href={`/calls/${point.id}`} key={point.id}>
          <div className="trend-row-top">
            <strong>{point.title}</strong>
            <span>{point.overall_score}/100</span>
          </div>
          <div className="trend-track">
            <div className="trend-fill" style={{ width: `${point.overall_score}%` }} />
          </div>
          <span className="trend-date">{new Date(point.created_at).toLocaleDateString()}</span>
        </Link>
      ))}
    </div>
  );
}

function LatestCalls({ summary }: { summary: AnalyticsSummary }) {
  if (summary.recent_calls.length === 0) {
    return (
      <div className="empty-state compact">
        <h3>No calls yet</h3>
        <p>Analyze your first sales call to start building coaching insights.</p>
      </div>
    );
  }

  return (
    <div className="recent-list">
      {summary.recent_calls.map((call) => (
        <Link className="recent-row" href={`/calls/${call.id}`} key={call.id}>
          <div>
            <strong>{call.title}</strong>
            <span>
              {call.source === "audio" ? "Audio upload" : "Pasted transcript"} -{" "}
              {new Date(call.created_at).toLocaleString()}
            </span>
          </div>
          <div className="recent-row-meta">
            <span className={`status ${call.status}`}>{call.status}</span>
            <strong>{call.overall_score === null ? "No score" : `${call.overall_score}/100`}</strong>
          </div>
        </Link>
      ))}
    </div>
  );
}

export default async function DashboardPage() {
  let summary: AnalyticsSummary | null = null;
  let loadError = "";

  try {
    summary = await getAnalyticsSummary();
  } catch {
    loadError = "Backend is not reachable. Start the FastAPI server to load dashboard insights.";
  }
  const deltaLabel = summary ? trendDeltaLabel(summary) : null;

  return (
    <>
      <section className="hero">
        <h1>SalesMirror coaching dashboard</h1>
        <p>Track local sales call coaching quality across analyzed calls without sending data to external analytics tools.</p>
        <div className="actions">
          <Link className="button" href="/upload">
            Analyze New Call
          </Link>
          <Link className="button secondary" href="/calls">
            View All Calls
          </Link>
        </div>
      </section>

      {loadError ? <div className="message error">{loadError}</div> : null}

      {summary ? (
        <>
          {summary.total_calls === 0 ? (
            <section className="empty-state">
              <h2>No calls analyzed yet</h2>
              <p>Upload audio or paste a transcript to generate your first coaching report.</p>
              <Link className="button" href="/upload">
                Analyze First Call
              </Link>
            </section>
          ) : null}

          <section className="dashboard-grid">
            <StatCard label="Total Calls" value={summary.total_calls} helper="All local call records" />
            <StatCard label="Analyzed Calls" value={summary.analyzed_calls} helper="Reports with scorecards" />
            <StatCard
              label="Average Overall Score"
              value={formatScore(summary.average_overall_score)}
              helper="Analyzed calls only"
            />
            <StatCard label="Weakest Category" value={summary.weakest_category ?? "No data"} />
            <StatCard label="Strongest Category" value={summary.strongest_category ?? "No data"} />
            <StatCard label="Score Trend" value={deltaLabel?.label ?? "No data"} helper={deltaLabel?.helper} />
          </section>

          {summary.analyzed_calls === 0 && summary.total_calls > 0 ? (
            <div className="message">
              Calls exist, but none have been analyzed yet. Run analysis to see averages and score distribution.
            </div>
          ) : null}

          <section className="section dashboard-two-column">
            <div className="panel analytics-panel">
              <div className="section-heading">
                <span className="eyebrow">Trend</span>
                <h2>Latest Analyzed Scores</h2>
              </div>
              <ScoreTrend summary={summary} />
            </div>

            <div className="panel analytics-panel">
              <div className="section-heading">
                <span className="eyebrow">Score Distribution</span>
                <h2>Coaching Quality</h2>
              </div>
              <DistributionBar label="Strong" value={summary.score_distribution.strong} total={summary.analyzed_calls} />
              <DistributionBar label="Decent" value={summary.score_distribution.decent} total={summary.analyzed_calls} />
              <DistributionBar label="Weak" value={summary.score_distribution.weak} total={summary.analyzed_calls} />
              <DistributionBar label="Poor" value={summary.score_distribution.poor} total={summary.analyzed_calls} />
            </div>

            <div className="panel analytics-panel">
              <div className="section-heading">
                <span className="eyebrow">Sources</span>
                <h2>Call Mix</h2>
              </div>
              <div className="source-grid">
                <StatCard label="Pasted Transcripts" value={summary.transcript_calls} />
                <StatCard label="Audio Uploads" value={summary.audio_calls} />
                <StatCard label="Transcribed" value={summary.transcribed_calls} />
                <StatCard label="Failed" value={summary.failed_calls} />
              </div>
            </div>
          </section>

          <section className="section">
            <div className="call-card-top">
              <div>
                <span className="eyebrow">Latest Activity</span>
                <h2>Latest 5 Calls</h2>
              </div>
              <Link className="button secondary" href="/calls">
                View All Calls
              </Link>
            </div>
            <LatestCalls summary={summary} />
          </section>
        </>
      ) : null}
    </>
  );
}
