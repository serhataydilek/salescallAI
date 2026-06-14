import Link from "next/link";
import { CallList } from "@/components/CallList";
import { ClearCallsButton } from "@/components/ClearCallsButton";
import { RestoreCallsControl } from "@/components/RestoreCallsControl";
import { callsCsvExportUrl, callsJsonExportUrl, type Call, type CallFilters, getCalls } from "@/lib/api";

type CallsPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

const statusOptions = ["uploaded", "transcribed", "analyzed", "failed"] as const;
const sourceOptions = ["audio", "transcript"] as const;
const sortOptions = [
  { label: "Newest", value: "newest" },
  { label: "Oldest", value: "oldest" },
  { label: "Score: High to Low", value: "score_desc" },
  { label: "Score: Low to High", value: "score_asc" },
] as const;

function singleValue(value: string | string[] | undefined): string {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}

function parseFilters(params: Record<string, string | string[] | undefined>): CallFilters {
  const q = singleValue(params.q).trim();
  const status = singleValue(params.status);
  const source = singleValue(params.source);
  const minScore = singleValue(params.min_score);
  const maxScore = singleValue(params.max_score);
  const sort = singleValue(params.sort);

  return {
    q,
    status: statusOptions.includes(status as (typeof statusOptions)[number])
      ? (status as CallFilters["status"])
      : undefined,
    source: sourceOptions.includes(source as (typeof sourceOptions)[number])
      ? (source as CallFilters["source"])
      : undefined,
    min_score: minScore,
    max_score: maxScore,
    sort: sortOptions.some((option) => option.value === sort) ? (sort as CallFilters["sort"]) : undefined,
  };
}

function activeFilterLabels(filters: CallFilters): string[] {
  const labels: string[] = [];
  if (filters.q) labels.push(`Search: ${filters.q}`);
  if (filters.status) labels.push(`Status: ${filters.status}`);
  if (filters.source) labels.push(`Source: ${filters.source}`);
  if (filters.min_score || filters.max_score) {
    labels.push(`Score: ${filters.min_score || "0"}-${filters.max_score || "100"}`);
  }
  if (filters.sort && filters.sort !== "newest") {
    labels.push(sortOptions.find((option) => option.value === filters.sort)?.label ?? filters.sort);
  }
  return labels;
}

export default async function CallsPage({ searchParams }: CallsPageProps) {
  const filters = parseFilters(await searchParams);
  const activeFilters = activeFilterLabels(filters);
  let calls: Call[] = [];
  let loadError = "";

  try {
    calls = await getCalls(filters);
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

      <div className="export-actions">
        <a className="button secondary" href={callsJsonExportUrl()}>
          Download Calls JSON
        </a>
        <a className="button secondary" href={callsCsvExportUrl()}>
          Download Calls CSV
        </a>
      </div>

      <details className="secondary-tool">
        <summary>Backup and restore</summary>
        <div className="secondary-tool-body">
          <p>
            Download Calls JSON for a local backup, or restore a previous SalesMirror JSON export. Restore creates new
            local call IDs and skips duplicates when the same title, date, and transcript already exist.
          </p>
          <RestoreCallsControl />
        </div>
      </details>

      <form action="/calls" className="filter-panel calls-filter-panel">
        <label className="field calls-search-field">
          <span>Search calls</span>
          <input
            defaultValue={filters.q ?? ""}
            name="q"
            placeholder="Title or transcript text"
            type="search"
          />
        </label>
        <div className="filter-grid">
          <label className="field">
            <span>Status</span>
            <select defaultValue={filters.status ?? ""} name="status">
              <option value="">All statuses</option>
              {statusOptions.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Source</span>
            <select defaultValue={filters.source ?? ""} name="source">
              <option value="">All sources</option>
              <option value="audio">Audio upload</option>
              <option value="transcript">Pasted transcript</option>
            </select>
          </label>
          <fieldset className="score-range-control">
            <legend>Score range</legend>
            <div>
              <label>
                <span>Min</span>
                <input defaultValue={filters.min_score ?? ""} max="100" min="0" name="min_score" type="number" />
              </label>
              <label>
                <span>Max</span>
                <input defaultValue={filters.max_score ?? ""} max="100" min="0" name="max_score" type="number" />
              </label>
            </div>
          </fieldset>
          <label className="field">
            <span>Sort by</span>
            <select defaultValue={filters.sort ?? "newest"} name="sort">
              {sortOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <div className="filter-actions">
            <button type="submit">Apply</button>
            <Link className="button secondary" href="/calls">
              Reset
            </Link>
          </div>
        </div>
        {activeFilters.length > 0 ? (
          <div className="active-filters">
            <span>Active filters</span>
            {activeFilters.map((filter) => (
              <strong key={filter}>{filter}</strong>
            ))}
          </div>
        ) : null}
      </form>

      {loadError ? (
        <div className="message error">{loadError}</div>
      ) : (
        <CallList
          calls={calls}
          emptyMessage={
            activeFilters.length > 0
              ? "No calls match the current filters. Reset filters or adjust the search."
              : undefined
          }
          showUploadAction={activeFilters.length === 0}
        />
      )}

      {!loadError ? (
        <div className="danger-zone">
          <div>
            <h2>Danger Zone</h2>
            <p>Local development utility. Use single-call delete for normal cleanup.</p>
          </div>
          <ClearCallsButton disabled={calls.length === 0} />
        </div>
      ) : null}
    </section>
  );
}
