export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
export const ALLOWED_AUDIO_EXTENSIONS = [".mp3", ".wav", ".m4a", ".webm"];

export type CallStatus = "uploaded" | "transcribed" | "analyzed" | "failed";

export type Call = {
  id: number;
  filename: string;
  file_path: string;
  status: CallStatus;
  created_at: string;
  updated_at: string;
};

export type Transcript = {
  id: number;
  call_id: number;
  text: string;
  created_at: string;
};

export type Analysis = {
  id: number;
  call_id: number;
  overall_score: number;
  opening_score: number;
  discovery_score: number;
  objection_handling_score: number;
  closing_score: number;
  follow_up_score: number;
  talk_ratio_feedback: string;
  top_3_mistakes: string[];
  missed_questions: string[];
  suggested_improvements: string[];
  better_example_responses: string[];
  short_summary: string;
  created_at: string;
};

export type CallDetail = Call & {
  transcript: Transcript | null;
  analysis: Analysis | null;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      cache: "no-store",
    });
  } catch (error) {
    throw new ApiError("Cannot reach the SalesMirror API. Make sure the backend is running.", 0);
  }

  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new ApiError(message, response.status);
  }

  return response.json() as Promise<T>;
}

async function readErrorMessage(response: Response): Promise<string> {
  const fallback = `Request failed with ${response.status}.`;
  const text = await response.text();
  if (!text) return fallback;

  try {
    const parsed = JSON.parse(text) as { detail?: unknown };
    return typeof parsed.detail === "string" ? parsed.detail : fallback;
  } catch {
    return text;
  }
}

export function validateAudioFile(file: File | null): string | null {
  if (!file) return "Choose an audio file first.";
  if (file.size === 0) return "The selected file is empty.";

  const lowerName = file.name.toLowerCase();
  const isAllowed = ALLOWED_AUDIO_EXTENSIONS.some((extension) => lowerName.endsWith(extension));
  if (!isAllowed) {
    return `Only ${ALLOWED_AUDIO_EXTENSIONS.join(", ")} files are supported.`;
  }

  return null;
}

export function validateTranscriptInput(transcript: string): string | null {
  const trimmed = transcript.trim();
  if (!trimmed) return "Transcript cannot be empty.";
  if (trimmed.length < 30) return "Transcript must be at least 30 characters.";
  return null;
}

export function getCalls(): Promise<Call[]> {
  return request<Call[]>("/calls");
}

export function getCall(id: string): Promise<CallDetail> {
  return request<CallDetail>(`/calls/${id}`);
}

export function clearCalls(): Promise<{ deleted_count: number; deleted_files: number }> {
  return request<{ deleted_count: number; deleted_files: number }>("/calls", { method: "DELETE" });
}

export function deleteCall(id: number): Promise<{ deleted_call_id: number; deleted_file: boolean; message: string }> {
  return request<{ deleted_call_id: number; deleted_file: boolean; message: string }>(`/calls/${id}`, {
    method: "DELETE",
  });
}

export function uploadCall(file: File): Promise<{ call_id: number; filename: string; status: string }> {
  const body = new FormData();
  body.append("file", file);
  return request("/calls/upload", {
    method: "POST",
    body,
  });
}

export function createCallFromTranscript(input: { title?: string; transcript: string }): Promise<CallDetail> {
  return request<CallDetail>("/calls/from-transcript", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function transcribeCall(id: number): Promise<Transcript> {
  return request<Transcript>(`/calls/${id}/transcribe`, { method: "POST" });
}

export function analyzeCall(id: number): Promise<Analysis> {
  return request<Analysis>(`/calls/${id}/analyze`, { method: "POST" });
}

export function reportUrl(id: number): string {
  return `${API_BASE_URL}/calls/${id}/report.txt`;
}
