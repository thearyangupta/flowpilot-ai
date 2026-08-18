from types import SimpleNamespace
from uuid import uuid4

from app.worker import gmail_tasks


def test_missing_history_cursor_is_initialized(
    monkeypatch,
):
    user_id = uuid4()

    connection = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        gmail_history_id=None,
    )

    saved = {}

    monkeypatch.setattr(
        gmail_tasks,
        "get_gmail_history_cursor",
        lambda **kwargs: "12345",
    )

    def fake_save(
        *,
        db,
        connection,
        history_id,
    ):
        saved["history_id"] = history_id
        connection.gmail_history_id = (
            history_id
        )

    monkeypatch.setattr(
        gmail_tasks,
        "save_gmail_history_cursor",
        fake_save,
    )

    class FakeDB:
        def commit(self):
            pass

    gmail_tasks._initialize_history_cursor(
        db=FakeDB(),
        connection=connection,
    )

    assert saved["history_id"] == "12345"
    assert (
        connection.gmail_history_id
        == "12345"
    )