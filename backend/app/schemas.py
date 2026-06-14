from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class TranscriptOut(BaseModel):
    id: int
    call_id: int
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisBase(BaseModel):
    overall_score: int
    opening_score: int
    discovery_score: int
    objection_handling_score: int
    closing_score: int
    follow_up_score: int
    talk_ratio_feedback: str
    top_3_mistakes: list[str]
    missed_questions: list[str]
    suggested_improvements: list[str]
    better_example_responses: list[str]
    short_summary: str


class AnalysisOut(AnalysisBase):
    id: int
    call_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CallOut(BaseModel):
    id: int
    filename: str
    file_path: str
    status: Literal["uploaded", "transcribed", "analyzed", "failed"]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CallDetailOut(CallOut):
    transcript: TranscriptOut | None = None
    analysis: AnalysisOut | None = None


class UploadResponse(BaseModel):
    call_id: int
    filename: str
    status: str


class CreateTranscriptCallRequest(BaseModel):
    title: str | None = None
    transcript: str


class UpdateTranscriptRequest(BaseModel):
    transcript: str


class ClearCallsResponse(BaseModel):
    deleted_count: int
    deleted_files: int


class DeleteCallResponse(BaseModel):
    deleted_call_id: int
    deleted_file: bool
    message: str


class ImportCallsResponse(BaseModel):
    imported_calls: int
    imported_transcripts: int
    imported_analyses: int
    skipped_items: int
    message: str


class ScoreDistributionOut(BaseModel):
    strong: int
    decent: int
    weak: int
    poor: int


class RecentCallSummaryOut(BaseModel):
    id: int
    title: str
    status: Literal["uploaded", "transcribed", "analyzed", "failed"]
    source: Literal["audio", "transcript"]
    overall_score: int | None
    created_at: datetime


class ScoreTrendPointOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    overall_score: int
    opening_score: int
    discovery_score: int
    objection_handling_score: int
    closing_score: int
    follow_up_score: int


class ImprovementDeltaOut(BaseModel):
    first_score: int | None
    latest_score: int | None
    delta: int | None
    direction: Literal["improved", "declined", "unchanged", "insufficient_data"]


class AnalyticsSummaryOut(BaseModel):
    total_calls: int
    analyzed_calls: int
    transcribed_calls: int
    uploaded_calls: int
    failed_calls: int
    transcript_calls: int
    audio_calls: int
    average_overall_score: float | None
    average_opening_score: float | None
    average_discovery_score: float | None
    average_objection_handling_score: float | None
    average_closing_score: float | None
    average_follow_up_score: float | None
    weakest_category: str | None
    strongest_category: str | None
    score_distribution: ScoreDistributionOut
    recent_calls: list[RecentCallSummaryOut]
    score_trend: list[ScoreTrendPointOut]
    improvement_delta: ImprovementDeltaOut
