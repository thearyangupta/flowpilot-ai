from copy import deepcopy

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.approval_decision import ApprovalDecision
from app.models.enums import ReplyDraftStatus
from app.models.reply_draft_revision import ReplyDraftRevision
from app.models.user import User
from app.services import reply_draft_service
from app.services.reply_draft_service import (
    ReplyDraftNotFoundError,
)
from app.services.reply_draft_revision_service import (
    hash_content,
)


def create_user(
    db_session: Session,
    *,
    email: str,
) -> User:
    user = User(
        email=email,
        display_name=email,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_edit_creates_new_revision_and_preserves_old_content(
    db_session: Session,
) -> None:
    user = create_user(
        db_session,
        email="revision-owner@example.com",
    )

    original_content = {
        "to": "customer@example.com",
        "subject": "Refund",
        "body": "Your refund is ?500.",
    }

    draft = reply_draft_service.create_pending(
        db=db_session,
        user_id=user.id,
        gmail_draft_id="gmail-draft-1",
        source_message={
            "id": "source-1",
        },
        draft_message=original_content,
    )

    revision_1 = db_session.execute(
        select(ReplyDraftRevision).where(
            ReplyDraftRevision.reply_draft_id
            == draft.id,
            ReplyDraftRevision.revision_number == 1,
        )
    ).scalar_one()

    revision_1_content = deepcopy(
        revision_1.content
    )
    revision_1_hash = revision_1.content_hash

    edited_content = {
        "to": "customer@example.com",
        "subject": "Refund approved",
        "body": "Your refund of ?500 has been approved.",
    }

    revision_2 = reply_draft_service.create_revision(
        db=db_session,
        draft_id=draft.id,
        user_id=user.id,
        expected_revision=1,
        content=edited_content,
    )

    db_session.refresh(revision_1)
    db_session.refresh(draft)

    assert revision_1.revision_number == 1
    assert revision_2.revision_number == 2

    assert revision_1.content == revision_1_content
    assert revision_1.content_hash == revision_1_hash

    assert revision_1.content_hash == hash_content(
        original_content
    )
    assert revision_2.content_hash == hash_content(
        edited_content
    )

    assert draft.current_revision_number == 2
    assert draft.draft_message == edited_content


def test_prior_approval_does_not_authorize_new_revision(
    db_session: Session,
) -> None:
    user = create_user(
        db_session,
        email="approval-owner@example.com",
    )

    draft = reply_draft_service.create_pending(
        db=db_session,
        user_id=user.id,
        gmail_draft_id="gmail-draft-2",
        source_message={
            "id": "source-2",
        },
        draft_message={
            "subject": "Refund",
            "body": "Refund ?500.",
        },
    )

    reply_draft_service.approve(
        db=db_session,
        draft_id=draft.id,
        user_id=user.id,
        expected_revision=1,
    )

    revision_1 = db_session.execute(
        select(ReplyDraftRevision).where(
            ReplyDraftRevision.reply_draft_id
            == draft.id,
            ReplyDraftRevision.revision_number == 1,
        )
    ).scalar_one()

    decision_r1 = db_session.execute(
        select(ApprovalDecision).where(
            ApprovalDecision.revision_id
            == revision_1.id
        )
    ).scalar_one()

    assert decision_r1.action == "approved"

    revision_2 = reply_draft_service.create_revision(
        db=db_session,
        draft_id=draft.id,
        user_id=user.id,
        expected_revision=1,
        content={
            "subject": "Refund",
            "body": "Refund ?5,000.",
        },
    )

    db_session.refresh(draft)

    decisions_for_r2 = list(
        db_session.scalars(
            select(ApprovalDecision).where(
                ApprovalDecision.revision_id
                == revision_2.id
            )
        ).all()
    )

    assert decisions_for_r2 == []
    assert draft.current_revision_number == 2
    assert draft.status == ReplyDraftStatus.PENDING_APPROVAL
    assert draft.approved_by is None
    assert draft.approved_at is None


def test_approval_bundle_identifies_exact_revision_and_history(
    db_session: Session,
) -> None:
    user = create_user(
        db_session,
        email="bundle-owner@example.com",
    )

    draft = reply_draft_service.create_pending(
        db=db_session,
        user_id=user.id,
        gmail_draft_id="gmail-draft-3",
        source_message={
            "id": "source-3",
        },
        draft_message={
            "subject": "Hello",
            "body": "Version one",
        },
    )

    reply_draft_service.approve(
        db=db_session,
        draft_id=draft.id,
        user_id=user.id,
        expected_revision=1,
    )

    bundle = reply_draft_service.get_approval_bundle(
        db=db_session,
        draft_id=draft.id,
        user_id=user.id,
        revision_number=1,
    )

    assert bundle["revision"].revision_number == 1
    assert (
        bundle["revision"].content_hash
        == hash_content(
            bundle["revision"].content
        )
    )

    assert len(bundle["decisions"]) == 1
    assert bundle["decisions"][0].action == "approved"
    assert (
        bundle["decisions"][0].revision_id
        == bundle["revision"].id
    )


def test_another_user_cannot_read_revision_or_decision_history(
    db_session: Session,
) -> None:
    owner = create_user(
        db_session,
        email="owner@example.com",
    )

    attacker = create_user(
        db_session,
        email="other-user@example.com",
    )

    draft = reply_draft_service.create_pending(
        db=db_session,
        user_id=owner.id,
        gmail_draft_id="gmail-draft-4",
        source_message={
            "id": "source-4",
        },
        draft_message={
            "subject": "Private",
            "body": "Owner-only content.",
        },
    )

    reply_draft_service.approve(
        db=db_session,
        draft_id=draft.id,
        user_id=owner.id,
        expected_revision=1,
    )

    with pytest.raises(
        ReplyDraftNotFoundError
    ):
        reply_draft_service.get_approval_bundle(
            db=db_session,
            draft_id=draft.id,
            user_id=attacker.id,
            revision_number=1,
        )