from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.main import app
from app.models.approval_decision import ApprovalDecision
from app.models.enums import ReplyDraftStatus
from app.models.reply_draft_audit_event import ReplyDraftAuditEvent
from app.models.user import User
from app.services import reply_draft_service
from app.services.reply_draft_service import (
    InvalidReplyDraftStateError,
    StaleReplyDraftRevisionError,
)


def create_user(
    db_session: Session,
    *,
    prefix: str,
) -> User:
    user = User(
        email=f"{prefix}-{uuid4()}@example.com",
        display_name=prefix,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def create_draft(
    db_session: Session,
    user: User,
    *,
    suffix: str,
):
    return reply_draft_service.create_pending(
        db=db_session,
        user_id=user.id,
        gmail_draft_id=f"gmail-{suffix}",
        source_message={
            "id": f"source-{suffix}",
        },
        draft_message={
            "recipient": "customer@example.com",
            "subject": "Version one",
            "body": "Original content",
        },
    )


def test_stale_approval_is_denied_and_audited(
    db_session: Session,
) -> None:
    user = create_user(
        db_session,
        prefix="stale",
    )

    draft = create_draft(
        db_session,
        user,
        suffix="stale",
    )

    reply_draft_service.create_revision(
        db=db_session,
        draft_id=draft.id,
        user_id=user.id,
        expected_revision=1,
        content={
            "recipient": "customer@example.com",
            "subject": "Version two",
            "body": "Changed content",
        },
    )

    with pytest.raises(
        StaleReplyDraftRevisionError
    ):
        reply_draft_service.approve(
            db=db_session,
            draft_id=draft.id,
            user_id=user.id,
            expected_revision=1,
        )

    db_session.refresh(draft)

    assert draft.current_revision_number == 2
    assert draft.status == ReplyDraftStatus.PENDING_APPROVAL

    decisions = list(
        db_session.scalars(
            select(ApprovalDecision).where(
                ApprovalDecision.user_id == user.id
            )
        ).all()
    )

    assert decisions == []

    stale_count = db_session.scalar(
        select(func.count())
        .select_from(ReplyDraftAuditEvent)
        .where(
            ReplyDraftAuditEvent.reply_draft_id
            == draft.id,
            ReplyDraftAuditEvent.event_type
            == "stale_action_denied",
        )
    )

    assert stale_count == 1


def test_repeated_approval_is_safe_replay(
    db_session: Session,
) -> None:
    user = create_user(
        db_session,
        prefix="replay",
    )

    draft = create_draft(
        db_session,
        user,
        suffix="replay",
    )

    reply_draft_service.approve(
        db=db_session,
        draft_id=draft.id,
        user_id=user.id,
        expected_revision=1,
    )

    reply_draft_service.approve(
        db=db_session,
        draft_id=draft.id,
        user_id=user.id,
        expected_revision=1,
    )

    decision_count = db_session.scalar(
        select(func.count())
        .select_from(ApprovalDecision)
        .where(
            ApprovalDecision.user_id == user.id
        )
    )

    assert decision_count == 1


def test_unapproved_content_never_calls_gmail(
    db_session: Session,
    monkeypatch,
) -> None:
    user = create_user(
        db_session,
        prefix="unapproved",
    )

    draft = create_draft(
        db_session,
        user,
        suffix="unapproved",
    )

    called = False

    def forbidden_client(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError(
            "Gmail must not be called."
        )

    monkeypatch.setattr(
        reply_draft_service,
        "build_gmail_client",
        forbidden_client,
    )

    with pytest.raises(
        InvalidReplyDraftStateError
    ):
        reply_draft_service.send_approved(
            db=db_session,
            draft_id=draft.id,
            user_id=user.id,
            expected_revision=1,
        )

    assert called is False


def test_duplicate_send_produces_one_external_effect(
    db_session: Session,
    monkeypatch,
) -> None:
    user = create_user(
        db_session,
        prefix="send-once",
    )

    draft = create_draft(
        db_session,
        user,
        suffix="send-once",
    )

    reply_draft_service.approve(
        db=db_session,
        draft_id=draft.id,
        user_id=user.id,
        expected_revision=1,
    )

    send_calls = 0

    class FakeExecute:
        def execute(self):
            nonlocal send_calls
            send_calls += 1

            return {
                "id": "gmail-message-123",
            }

    class FakeDrafts:
        def send(self, **kwargs):
            return FakeExecute()

    class FakeUsers:
        def drafts(self):
            return FakeDrafts()

    class FakeGmail:
        def users(self):
            return FakeUsers()

    monkeypatch.setattr(
        reply_draft_service,
        "build_gmail_client",
        lambda **kwargs: FakeGmail(),
    )

    first = reply_draft_service.send_approved(
        db=db_session,
        draft_id=draft.id,
        user_id=user.id,
        expected_revision=1,
    )

    second = reply_draft_service.send_approved(
        db=db_session,
        draft_id=draft.id,
        user_id=user.id,
        expected_revision=1,
    )

    assert send_calls == 1

    assert first.gmail_message_id == "gmail-message-123"
    assert second.gmail_message_id == "gmail-message-123"

    assert second.status == ReplyDraftStatus.SENT


def test_stale_http_approval_returns_409(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(
        db_session,
        prefix="api-stale",
    )

    app.dependency_overrides[
        get_current_user
    ] = lambda: user

    draft = create_draft(
        db_session,
        user,
        suffix="api-stale",
    )

    reply_draft_service.create_revision(
        db=db_session,
        draft_id=draft.id,
        user_id=user.id,
        expected_revision=1,
        content={
            "recipient": "customer@example.com",
            "subject": "Version two",
            "body": "Changed",
        },
    )

    response = client.post(
        (
            f"/api/v1/reply-drafts/"
            f"{draft.id}/approve"
        ),
        json={
            "expected_revision": 1,
        },
    )

    assert response.status_code == 409

    detail = response.json()["detail"]

    assert "revision 1" in detail
    assert "revision 2" in detail
    assert "Refresh" in detail
