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


class ClearCallsResponse(BaseModel):
    deleted_count: int
    deleted_files: int


class DeleteCallResponse(BaseModel):
    deleted_call_id: int
    deleted_file: bool
    message: str
