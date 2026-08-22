from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from redis import Redis
from sqlalchemy import text

from app.api.router import router
from app.core.config import get_settings
from app.core.middleware import request_id_middleware
from app.db.session import engine


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
    )

    app.middleware("http")(request_id_middleware)

    app.include_router(
        router,
        prefix="/api/v1",
    )

    @app.api_route(
        "/home",
        methods=["GET", "HEAD"],
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    def public_home() -> str:
        return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FlowPilot AI</title>
  <meta
    name="description"
    content="FlowPilot AI is an AI-powered Gmail workflow automation application for email classification, knowledge-grounded reply drafting, and human approval."
  >
</head>
<body>
  <main>
    <h1>FlowPilot AI</h1>

    <p>
      FlowPilot AI is an AI-powered email workflow automation
      application for Gmail.
    </p>

    <p>
      It helps users process incoming Gmail messages, classify
      emails, retrieve relevant knowledge, generate grounded reply
      drafts, and review AI-generated actions before approval.
    </p>

    <h2>How FlowPilot AI works</h2>

    <ul>
      <li>Reads authorized Gmail messages required for workflows.</li>
      <li>Classifies and processes incoming email.</li>
      <li>Uses user-provided knowledge to prepare grounded replies.</li>
      <li>Creates Gmail reply drafts.</li>
      <li>Supports human approval before guarded actions.</li>
    </ul>

    <p>
      FlowPilot AI only accesses Google data after the user grants
      permission through Google OAuth.
    </p>

    <p>
      <a href="/privacy">Privacy Policy</a>
      &nbsp;|&nbsp;
      <a href="/terms">Terms of Service</a>
    </p>
  </main>
</body>
</html>
"""

    @app.api_route(
        "/privacy",
        methods=["GET", "HEAD"],
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    def privacy_policy() -> str:
        return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FlowPilot AI Privacy Policy</title>
</head>
<body>
  <main>
    <h1>FlowPilot AI Privacy Policy</h1>

    <p>Effective: August 20, 2026</p>

    <p>
      FlowPilot AI is an AI-assisted email workflow application.
      This policy explains how information is handled when users
      connect a Google account.
    </p>

    <h2>Google data accessed</h2>

    <p>
      FlowPilot AI may use Gmail read-only access to read messages
      needed for workflows and Gmail compose access to create or
      manage email drafts.
    </p>

    <h2>How data is used</h2>

    <p>
      Google user data is used only to provide FlowPilot AI features,
      including processing incoming email, generating contextual
      drafts, and supporting user review and approval.
    </p>

    <p>
      FlowPilot AI does not sell Google user data or use it for
      advertising.
    </p>

    <h2>Data protection and security</h2>

    <p>
      FlowPilot AI uses technical and organizational safeguards to
      protect Google user data. OAuth access tokens and refresh tokens
      are encrypted before storage. Access to application data is
      restricted to the authenticated user who owns the corresponding
      FlowPilot resources. Production traffic is transmitted over
      HTTPS, and application credentials and secrets are stored in
      protected service configuration rather than exposed to users.
    </p>

    <p>
      FlowPilot AI limits Google user data access to the permissions
      required for the requested Gmail workflow. The application does
      not sell Google user data or use Google user data for advertising.
    </p>

    <h2>Data retention and deletion</h2>

    <p>
      FlowPilot AI retains Gmail-derived application data only for as
      long as necessary to provide the requested workflow functionality,
      maintain workflow state, and support user-visible execution and
      approval records.
    </p>

    <p>
      When a user disconnects or revokes Google access, FlowPilot AI
      stops accessing new Google user data. Users may request deletion
      of retained Google-derived application data by contacting
      aryangwork@gmail.com. Deletion requests will remove the applicable
      retained Google-derived data from active application storage,
      except where limited information must be retained temporarily for
      security, fraud-prevention, legal, or operational integrity
      purposes.
    </p>

    <h2>Google API Services User Data Policy</h2>

    <p>
      FlowPilot AI's use and transfer of information received from
      Google APIs adheres to the Google API Services User Data Policy,
      including the Limited Use requirements.
    </p>

    <h2>User control</h2>

    <p>
      Users can revoke FlowPilot AI's Google Account access at any
      time through their Google Account security settings.
    </p>

    <h2>Contact</h2>

    <p>aryangwork@gmail.com</p>

    <p><a href="/home">Back to FlowPilot AI</a></p>
  </main>
</body>
</html>
"""

    @app.api_route(
        "/terms",
        methods=["GET", "HEAD"],
        response_class=HTMLResponse,
        include_in_schema=False,
    )
    def terms_of_service() -> str:
        return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FlowPilot AI Terms of Service</title>
</head>
<body>
  <main>
    <h1>FlowPilot AI Terms of Service</h1>

    <p>Effective: August 20, 2026</p>

    <p>
      FlowPilot AI provides AI-assisted email workflow automation,
      including Gmail processing, knowledge retrieval, reply drafting,
      and human approval workflows.
    </p>

    <h2>AI-generated content</h2>

    <p>
      AI-generated drafts may contain mistakes. Users are responsible
      for reviewing content before approving or sending it.
    </p>

    <h2>Google account access</h2>

    <p>
      Some features require Google OAuth authorization. Users may
      revoke access at any time from their Google Account.
    </p>

    <h2>Acceptable use</h2>

    <p>
      Users must not use FlowPilot AI for unlawful, abusive,
      fraudulent, or unauthorized activity.
    </p>

    <h2>Availability</h2>

    <p>
      FlowPilot AI may be changed, suspended, or discontinued and
      uninterrupted availability is not guaranteed.
    </p>

    <h2>Contact</h2>

    <p>aryangwork@gmail.com</p>

    <p>
      <a href="/privacy">Privacy Policy</a>
      &nbsp;|&nbsp;
      <a href="/home">Back to FlowPilot AI</a>
    </p>
  </main>
</body>
</html>
"""

    @app.get(
        "/health",
        tags=["system"],
    )
    def health() -> dict[str, str]:
        """
        Process-level liveness.

        This endpoint deliberately does not test external
        dependencies. It answers only whether the API process
        is alive and serving requests.
        """
        return {
            "status": "ok",
            "service": "flowpilot-api",
        }

    @app.get(
        "/ready",
        tags=["system"],
    )
    def readiness() -> dict[str, str]:
        """
        Dependency-aware readiness.

        FlowPilot is ready only when PostgreSQL and Redis are
        reachable. Do not expose connection details or secrets
        in the response.
        """

        try:
            with engine.connect() as connection:
                connection.execute(
                    text("SELECT 1")
                )

            redis_client = Redis.from_url(
                settings.redis_broker_url,
                socket_connect_timeout=2,
                socket_timeout=2,
            )

            try:
                redis_client.ping()
            finally:
                redis_client.close()

        except Exception as error:
            raise HTTPException(
                status_code=(
                    status.HTTP_503_SERVICE_UNAVAILABLE
                ),
                detail="FlowPilot dependencies are not ready.",
            ) from error

        return {
            "status": "ready",
            "service": "flowpilot-api",
        }

    return app


app = create_app()
