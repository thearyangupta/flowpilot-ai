import threading
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.gmail_command import GmailCommand
from app.models.user import User
from app.services import reply_draft_service
from app.services.google.gmail_command_service import (
    GmailCommandConflictError,
)


settings = get_settings()

engine = create_engine(
    settings.test_database_url
)

ConcurrentSession = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class GmailCallCounter:
    def __init__(self) -> None:
        self.calls = 0
        self.lock = threading.Lock()

    def increment(self) -> None:
        with self.lock:
            self.calls += 1


def fake_gmail(
    counter: GmailCallCounter,
):
    class Execute:
        def execute(self):
            counter.increment()

            # Keep the first request inside the
            # external-effect window long enough
            # for the second caller to overlap.
            time.sleep(0.15)

            return {
                "id":
                    "gmail-concurrent-123",
            }

    class Drafts:
        def send(self, **kwargs):
            return Execute()

    class Users:
        def drafts(self):
            return Drafts()

    class Gmail:
        def users(self):
            return Users()

    return Gmail()


def create_approved_draft(
    *,
    session,
    user_id,
    suffix: str,
):
    draft = (
        reply_draft_service
        .create_pending(
            db=session,
            user_id=user_id,
            gmail_draft_id=(
                f"gmail-{suffix}"
            ),
            source_message={
                "id":
                    f"source-{suffix}",
            },
            draft_message={
                "recipient":
                    "customer@example.com",
                "subject":
                    "Approved reply",
                "body":
                    f"Body {suffix}",
            },
        )
    )

    reply_draft_service.approve(
        db=session,
        draft_id=draft.id,
        user_id=user_id,
        expected_revision=1,
    )

    return draft


def test_concurrent_same_key_causes_one_gmail_effect(
    monkeypatch,
) -> None:
    setup = ConcurrentSession()

    try:
        user = User(
            email=(
                f"concurrent-{uuid4()}"
                "@example.com"
            ),
            display_name="Concurrent",
        )

        setup.add(user)
        setup.commit()
        setup.refresh(user)

        draft = create_approved_draft(
            session=setup,
            user_id=user.id,
            suffix=str(uuid4()),
        )

        user_id = user.id
        draft_id = draft.id

    finally:
        setup.close()

    counter = GmailCallCounter()

    monkeypatch.setattr(
        reply_draft_service,
        "build_gmail_client",
        lambda **kwargs:
            fake_gmail(counter),
    )

    command_key = (
        f"concurrent-send-{uuid4()}"
    )

    barrier = threading.Barrier(2)

    def send_once():
        session = ConcurrentSession()

        try:
            barrier.wait()

            result = (
                reply_draft_service
                .send_approved(
                    db=session,
                    draft_id=draft_id,
                    user_id=user_id,
                    expected_revision=1,
                    idempotency_key=
                        command_key,
                )
            )

            return (
                result.status,
                result.gmail_message_id,
            )

        finally:
            session.close()

    with ThreadPoolExecutor(
        max_workers=2
    ) as pool:
        results = list(
            pool.map(
                lambda _: send_once(),
                range(2),
            )
        )

    assert counter.calls == 1

    assert all(
        message_id
        == "gmail-concurrent-123"
        for _, message_id in results
    )

    verify = ConcurrentSession()

    try:
        commands = list(
            verify.scalars(
                select(GmailCommand)
                .where(
                    GmailCommand.user_id
                    == user_id,
                    GmailCommand.idempotency_key
                    == command_key,
                )
            ).all()
        )

        assert len(commands) == 1
        assert commands[0].state == "completed"

        assert (
            commands[0].outcome[
                "gmail_message_id"
            ]
            == "gmail-concurrent-123"
        )

        user = verify.get(
            User,
            user_id,
        )

        verify.delete(user)
        verify.commit()

    finally:
        verify.close()


def test_same_key_different_command_is_rejected(
    monkeypatch,
) -> None:
    session = ConcurrentSession()

    counter = GmailCallCounter()

    monkeypatch.setattr(
        reply_draft_service,
        "build_gmail_client",
        lambda **kwargs:
            fake_gmail(counter),
    )

    try:
        user = User(
            email=(
                f"conflict-{uuid4()}"
                "@example.com"
            ),
            display_name="Conflict",
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        first = create_approved_draft(
            session=session,
            user_id=user.id,
            suffix="first",
        )

        second = create_approved_draft(
            session=session,
            user_id=user.id,
            suffix="second",
        )

        shared_key = (
            f"shared-{uuid4()}"
        )

        reply_draft_service.send_approved(
            db=session,
            draft_id=first.id,
            user_id=user.id,
            expected_revision=1,
            idempotency_key=shared_key,
        )

        with pytest.raises(
            GmailCommandConflictError
        ):
            reply_draft_service.send_approved(
                db=session,
                draft_id=second.id,
                user_id=user.id,
                expected_revision=1,
                idempotency_key=shared_key,
            )

        assert counter.calls == 1

    finally:
        session.rollback()

        user = session.get(
            User,
            user.id,
        )

        if user is not None:
            session.delete(user)
            session.commit()

        session.close()