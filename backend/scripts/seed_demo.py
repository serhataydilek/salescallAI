from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
load_dotenv(ROOT / ".env")

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Analysis, Call, CallStatus, Transcript  # noqa: E402
from app.schemas import AnalysisBase  # noqa: E402
from app.services.llm.mock_llm import MockLLMService  # noqa: E402


SAMPLE_TRANSCRIPT = (
    Path(__file__).resolve().parents[2] / "data" / "samples" / "good_sales_call.txt"
).read_text(encoding="utf-8")


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        call = Call(
            filename="demo-sales-call.webm",
            file_path="seeded-demo-call",
            status=CallStatus.analyzed,
        )
        db.add(call)
        db.flush()

        transcript = Transcript(call_id=call.id, text=SAMPLE_TRANSCRIPT)
        analysis_data = AnalysisBase.model_validate(
            MockLLMService().analyze_sales_call(SAMPLE_TRANSCRIPT)
        )
        analysis = Analysis(call_id=call.id, **analysis_data.model_dump())

        db.add_all([transcript, analysis])
        db.commit()
        print(f"Seeded demo call with id {call.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
