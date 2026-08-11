from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.cipher import get_token_cipher
from app.core.oauth import (
    GOOGLE_GMAIL_SCOPES,
    GOOGLE_IDENTITY_SCOPES,
    OAuthPurpose,
)
from app.db.session import get_db
from app.schemas.auth import (
    GoogleOAuthCallbackRead,
    GoogleOAuthStartRead,
)
from app.services.auth.oauth_callback_service import (
    OAuthCallbackError,
    complete_google_oauth_callback,
)
from app.services.auth.oauth_start_service import (
    OAuthStartError,
    create_google_oauth_start,
)
from app.api.dependencies import get_current_user
from app.models.user import User


router = APIRouter()


@router.get(
    "/auth/google/start",
    response_model=GoogleOAuthStartRead,
    tags=["authentication"],
)
def start_google_oauth(
    db: Session = Depends(get_db),
) -> GoogleOAuthStartRead:
    try:
        result = create_google_oauth_start(
            db=db,
            cipher=get_token_cipher(),
            purpose=OAuthPurpose.LOGIN,
            requested_scopes=GOOGLE_IDENTITY_SCOPES,
        )

        db.commit()

        return GoogleOAuthStartRead(
            authorization_url=result.authorization_url,
            expires_at=result.expires_at,
        )

    except OAuthStartError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authorization could not be started.",
        ) from error


@router.get(
    "/integrations/gmail/connect",
    response_model=GoogleOAuthStartRead,
    tags=["integrations"],
)
def connect_gmail(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GoogleOAuthStartRead:
    requested_scopes = (
        GOOGLE_IDENTITY_SCOPES
        + GOOGLE_GMAIL_SCOPES
    )

    try:
        result = create_google_oauth_start(
            db=db,
            cipher=get_token_cipher(),
            purpose=OAuthPurpose.GMAIL_CONNECT,
            requested_scopes=requested_scopes,
            user_id=current_user.id,
        )

        db.commit()

        return GoogleOAuthStartRead(
            authorization_url=result.authorization_url,
            expires_at=result.expires_at,
        )

    except OAuthStartError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Gmail authorization could not be started."
            ),
        ) from error


@router.get(
    "/auth/google/callback",
    response_model=GoogleOAuthCallbackRead,
    tags=["authentication"],
)
def finish_google_oauth(
    code: str | None = None,
    state_value: str | None = Query(
        default=None,
        alias="state",
    ),
    error: str | None = None,
    db: Session = Depends(get_db),
) -> GoogleOAuthCallbackRead:
    if error is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google authorization was not completed.",
        )

    if not code or not state_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Google authorization code and state are required."
            ),
        )

    try:
        result = complete_google_oauth_callback(
            db=db,
            code=code,
            state=state_value,
            cipher=get_token_cipher(),
        )

        db.commit()

        if result.purpose == OAuthPurpose.LOGIN:
            return GoogleOAuthCallbackRead(
                status="authenticated",
                access_token=result.flowpilot_access_token,
                token_type="bearer",
                user=result.user,
            )

        return GoogleOAuthCallbackRead(
            status="gmail_connected",
            user=result.user,
        )

    except OAuthCallbackError as callback_error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Google OAuth callback could not be completed."
            ),
        ) from callback_error