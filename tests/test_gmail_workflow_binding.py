from uuid import uuid4

import pytest

from app.core.oauth import OAuthPurpose
from app.services.auth.oauth_start_service import (
    OAuthStartError,
    _validate_oauth_start,
)


GOOGLE_SCOPES = (
    "openid",
    "email",
    "profile",
)


def test_gmail_oauth_requires_workflow():
    with pytest.raises(
        OAuthStartError,
        match="requires a workflow",
    ):
        _validate_oauth_start(
            purpose=OAuthPurpose.GMAIL_CONNECT,
            requested_scopes=GOOGLE_SCOPES,
            user_id=uuid4(),
            workflow_id=None,
        )


def test_gmail_oauth_accepts_user_and_workflow():
    _validate_oauth_start(
        purpose=OAuthPurpose.GMAIL_CONNECT,
        requested_scopes=GOOGLE_SCOPES,
        user_id=uuid4(),
        workflow_id=uuid4(),
    )


def test_login_oauth_rejects_workflow_binding():
    with pytest.raises(
        OAuthStartError,
        match="must not be bound to a workflow",
    ):
        _validate_oauth_start(
            purpose=OAuthPurpose.LOGIN,
            requested_scopes=GOOGLE_SCOPES,
            user_id=None,
            workflow_id=uuid4(),
        )