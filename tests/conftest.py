import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

_tmp_dir = tempfile.mkdtemp(prefix="fin-dash-test-")
os.environ["DATABASE_PATH"] = os.path.join(_tmp_dir, "test.db")

from database.database import engine  # noqa: E402
from database.models import Base  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
