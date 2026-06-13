from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CallStatus(str, Enum):
    uploaded = "uploaded"
    transcribed = "transcribed"
    analyzed = "analyzed"
    failed = "failed"


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[CallStatus] = mapped_column(
        SqlEnum(CallStatus), default=CallStatus.uploaded, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    transcript: Mapped["Transcript | None"] = relationship(
        back_populates="call", cascade="all, delete-orphan", uselist=False
    )
    analysis: Mapped["Analysis | None"] = relationship(
        back_populates="call", cascade="all, delete-orphan", uselist=False
    )


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    call_id: Mapped[int] = mapped_column(ForeignKey("calls.id"), unique=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    call: Mapped[Call] = relationship(back_populates="transcript")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    call_id: Mapped[int] = mapped_column(ForeignKey("calls.id"), unique=True)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    opening_score: Mapped[int] = mapped_column(Integer, nullable=False)
    discovery_score: Mapped[int] = mapped_column(Integer, nullable=False)
    objection_handling_score: Mapped[int] = mapped_column(Integer, nullable=False)
    closing_score: Mapped[int] = mapped_column(Integer, nullable=False)
    follow_up_score: Mapped[int] = mapped_column(Integer, nullable=False)
    talk_ratio_feedback: Mapped[str] = mapped_column(Text, nullable=False)
    top_3_mistakes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    missed_questions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    suggested_improvements: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    better_example_responses: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    short_summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    call: Mapped[Call] = relationship(back_populates="analysis")
