from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
)
from app.models.user import User
from app.services import reply_draft_service


def create_user(
    db: Session,
    email: str,
) -> User:
    user = User(
        email=email,
        display_name=email,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def auth_headers(
    user: User,
) -> dict[str, str]:
    return {
        "Authorization":
            f"Bearer {create_access_token(user.id)}",
    }


def test_reply_draft_not_found_does_not_leak_internal_message(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(
        db_session,
        "public-error-draft@example.com",
    )

    internal_secret = (
        "postgres://internal-host/"
        "secret-database"
    )

    with patch(
        "app.api.routers.reply_drafts."
        "reply_draft_service."
        "get_approval_bundle",
        side_effect=(
            reply_draft_service
            .ReplyDraftNotFoundError(
                internal_secret
            )
        ),
    ):
        response = client.get(
            (
                "/api/v1/reply-drafts/"
                f"{uuid4()}/approval-bundle"
            ),
            headers=auth_headers(user),
        )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Reply draft not found."
    }

    assert (
        internal_secret
        not in response.text
    )


def test_stale_revision_does_not_leak_revision_numbers(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(
        db_session,
        "public-error-stale@example.com",
    )

    error = (
        reply_draft_service
        .StaleReplyDraftRevisionError(
            expected_revision=12345,
            current_revision=98765,
        )
    )

    with patch(
        "app.api.routers.reply_drafts."
        "reply_draft_service.approve",
        side_effect=error,
    ):
        response = client.post(
            (
                "/api/v1/reply-drafts/"
                f"{uuid4()}/approve"
            ),
            json={
                "expected_revision": 1,
            },
            headers=auth_headers(user),
        )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Reply draft changed since you "
            "loaded it. Refresh and review "
            "the latest revision before "
            "continuing."
        )
    }

    assert "12345" not in response.text
    assert "98765" not in response.text


def test_invalid_draft_state_uses_stable_public_message(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(
        db_session,
        "public-error-state@example.com",
    )

    internal_message = (
        "Sensitive internal state: "
        "approval row 123 missing"
    )

    with patch(
        "app.api.routers.reply_drafts."
        "reply_draft_service.approve",
        side_effect=(
            reply_draft_service
            .InvalidReplyDraftStateError(
                internal_message
            )
        ),
    ):
        response = client.post(
            (
                "/api/v1/reply-drafts/"
                f"{uuid4()}/approve"
            ),
            json={
                "expected_revision": 1,
            },
            headers=auth_headers(user),
        )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Reply draft state does not "
            "allow this action."
        )
    }

    assert (
        internal_message
        not in response.text
    )


def test_unsupported_upload_does_not_reflect_content_type(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(
        db_session,
        "public-error-upload@example.com",
    )

    malicious_type = (
        "application/x-secret-internal"
    )

    response = client.post(
        "/api/v1/knowledge/documents",
        files={
            "file": (
                "bad.bin",
                b"unsafe",
                malicious_type,
            )
        },
        headers=auth_headers(user),
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Unsupported upload content type."
        )
    }

    assert (
        malicious_type
        not in response.text
    )
