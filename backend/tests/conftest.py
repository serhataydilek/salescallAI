import os
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


os.environ["USE_MOCK_TRANSCRIPTION"] = "true"
os.environ["USE_MOCK_LLM"] = "true"
TEST_DB_PATH = Path(tempfile.gettempdir()) / f"salesmirror-test-{uuid4().hex}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"

from app.database import Base, engine
from app.main import app
from app.config import reset_upload_dir


@pytest.fixture(autouse=True)
def reset_database():
    reset_upload_dir()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    reset_upload_dir()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    TEST_DB_PATH.unlink(missing_ok=True)
