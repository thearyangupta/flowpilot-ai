from __future__ import annotations

from textwrap import dedent

import streamlit as st


def render_html(
    content: str,
) -> None:
    st.html(
        dedent(content).strip()
    )


def apply_global_styles() -> None:
    st.markdown(
        """
<style>
:root {
    --fp-accent: #e76f51;
    --fp-accent-strong: #d85b3f;
    --fp-accent-soft: rgba(231, 111, 81, 0.12);

    --fp-radius-sm: 10px;
    --fp-radius-md: 14px;
    --fp-radius-lg: 18px;

    --fp-border:
        color-mix(
            in srgb,
            var(--text-color) 14%,
            transparent
        );

    --fp-border-strong:
        color-mix(
            in srgb,
            var(--text-color) 22%,
            transparent
        );

    --fp-surface:
        color-mix(
            in srgb,
            var(--background-color) 96%,
            var(--text-color) 4%
        );

    --fp-surface-hover:
        color-mix(
            in srgb,
            var(--background-color) 91%,
            var(--text-color) 9%
        );

    --fp-muted:
        color-mix(
            in srgb,
            var(--text-color) 64%,
            transparent
        );
}


/* =========================================================
   APP
   ========================================================= */

.stApp {
    color: var(--text-color);
    background: var(--background-color);
}

.block-container {
    max-width: 1240px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
    padding-left: 3rem;
    padding-right: 3rem;
}


/* =========================================================
   TYPOGRAPHY
   ========================================================= */

h1 {
    letter-spacing: -0.035em;
    font-weight: 760 !important;
}

h2,
h3 {
    letter-spacing: -0.02em;
}

p,
label,
span {
    line-height: 1.55;
}


/* =========================================================
   LINKS
   ========================================================= */

a {
    color: var(--fp-accent);
}

a:hover {
    color: var(--fp-accent-strong);
}


/* =========================================================
   BUTTONS
   ========================================================= */

.stButton > button,
.stLinkButton > a {
    border-radius: var(--fp-radius-sm) !important;
    border: 1px solid var(--fp-border) !important;

    transition:
        transform 120ms ease,
        border-color 120ms ease,
        background 120ms ease;
}

.stButton > button:hover,
.stLinkButton > a:hover {
    transform: translateY(-1px);
    border-color: var(--fp-accent) !important;
}

.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: var(--fp-accent) !important;
    border-color: var(--fp-accent) !important;
    color: white !important;
}

.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
    background: var(--fp-accent-strong) !important;
    border-color: var(--fp-accent-strong) !important;
}


/* =========================================================
   FORM CONTROLS
   ========================================================= */

[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div,
[data-baseweb="select"] > div {
    border-radius: var(--fp-radius-sm) !important;
}

input,
textarea {
    color: var(--text-color) !important;
    caret-color: var(--fp-accent) !important;
}

input::placeholder,
textarea::placeholder {
    color: var(--fp-muted) !important;
    opacity: 1 !important;
}

input:disabled,
textarea:disabled {
    color: var(--text-color) !important;
    -webkit-text-fill-color: var(--text-color) !important;
    opacity: 0.76 !important;
}


/* =========================================================
   GENERAL CONTAINERS
   ========================================================= */

[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: var(--fp-radius-md);
    border-color: var(--fp-border) !important;
}

[data-testid="stExpander"] {
    border: 1px solid var(--fp-border);
    border-radius: var(--fp-radius-md);
    overflow: hidden;
}

[data-testid="stAlert"] {
    border-radius: var(--fp-radius-md);
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--fp-border);
    border-radius: var(--fp-radius-md);
    overflow: hidden;
}


/* =========================================================
   SIDEBAR
   ========================================================= */

[data-testid="stSidebar"] {
    border-right: 1px solid var(--fp-border);
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.2rem;
}

[data-testid="stSidebar"] hr {
    border-color: var(--fp-border);
}

[data-testid="stSidebarNav"] a {
    border-radius: var(--fp-radius-sm);
    margin-bottom: 0.2rem;

    transition:
        background 120ms ease,
        color 120ms ease;
}

[data-testid="stSidebarNav"] a:hover {
    background: var(--fp-surface-hover);
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: var(--fp-accent-soft);
    color: var(--fp-accent);
}


/* =========================================================
   SIDEBAR BRAND
   ========================================================= */

.fp-brand {
    padding: 0.15rem 0 0.35rem 0;
}

.fp-brand-row {
    display: flex;
    align-items: center;
    gap: 0.7rem;
}

.fp-brand-mark {
    width: 2rem;
    height: 2rem;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 10px;

    background: var(--fp-accent);
    color: white;

    font-size: 1rem;
    font-weight: 800;
}

.fp-brand-name {
    color: var(--text-color);

    font-size: 1.08rem;
    font-weight: 750;
    letter-spacing: -0.02em;
}

.fp-brand-copy {
    margin-top: 0.3rem;
    margin-left: 2.7rem;

    color: var(--fp-muted);
    font-size: 0.78rem;
}

.fp-sidebar-label {
    margin-top: 0.25rem;
    margin-bottom: 0.45rem;

    color: var(--fp-muted);

    font-size: 0.68rem;
    font-weight: 750;
    letter-spacing: 0.1em;
}


/* =========================================================
   AGENT HERO
   ========================================================= */

.fp-agent-hero {
    max-width: 780px;
    padding-top: 0.3rem;
    padding-bottom: 0.8rem;
}

.fp-agent-eyebrow {
    display: flex;
    align-items: center;
    gap: 0.55rem;

    margin-bottom: 0.9rem;

    color: var(--fp-accent);

    font-size: 0.7rem;
    font-weight: 750;
    letter-spacing: 0.11em;
}

.fp-agent-status {
    width: 0.5rem;
    height: 0.5rem;

    flex: 0 0 auto;

    border-radius: 999px;
    background: var(--fp-accent);

    box-shadow:
        0 0 0 5px var(--fp-accent-soft);
}

.fp-agent-hero h1 {
    margin: 0;

    color: var(--text-color);

    font-size: clamp(
        2.2rem,
        4.5vw,
        3.7rem
    );

    line-height: 1.04;
}

.fp-agent-hero p {
    max-width: 650px;

    margin-top: 0.9rem;
    margin-bottom: 0;

    color: var(--fp-muted);

    font-size: 1rem;
    line-height: 1.6;
}

.fp-agent-intro {
    max-width: 720px;

    margin-top: 0.35rem;
    margin-bottom: 2rem;

    color: var(--fp-muted);

    font-size: 0.94rem;
    line-height: 1.65;
}


/* =========================================================
   AGENT SECTIONS
   ========================================================= */

.fp-section-heading {
    margin-bottom: 0.9rem;
}

.fp-section-heading h3 {
    margin: 0.18rem 0 0 0;

    color: var(--text-color);

    font-size: 1.25rem;
}

.fp-section-kicker {
    color: var(--fp-muted);

    font-size: 0.67rem;
    font-weight: 750;
    letter-spacing: 0.1em;
}


/* =========================================================
   QUICK ACTION CARDS
   ========================================================= */

.fp-action-title {
    margin-bottom: 0.4rem;

    color: var(--text-color);

    font-size: 1rem;
    font-weight: 720;
}

.fp-action-description {
    min-height: 2.9rem;

    margin-bottom: 0.8rem;

    color: var(--fp-muted);

    font-size: 0.84rem;
    line-height: 1.5;
}

/*
Keep the hover subtle. The page should feel interactive
without looking like a dashboard full of floating cards.
*/

[data-testid="stVerticalBlockBorderWrapper"] {
    transition:
        transform 140ms ease,
        border-color 140ms ease,
        box-shadow 140ms ease;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: var(--fp-border-strong) !important;
    transform: translateY(-2px);

    box-shadow:
        0 8px 24px
        color-mix(
            in srgb,
            var(--text-color) 5%,
            transparent
        );
}


/* =========================================================
   CHAT
   ========================================================= */

.fp-chat-heading {
    margin-top: 0.75rem;
    margin-bottom: 0.4rem;
}

[data-testid="stChatMessage"] {
    background: var(--fp-surface);
    border: 1px solid var(--fp-border);

    border-radius: var(--fp-radius-md);

    padding: 0.35rem 0.65rem;
    margin-bottom: 0.75rem;
}

[data-testid="stChatInput"] {
    border: 1px solid var(--fp-border);
    border-radius: var(--fp-radius-md);

    box-shadow:
        0 8px 28px
        color-mix(
            in srgb,
            var(--text-color) 5%,
            transparent
        );
}

[data-testid="stChatInput"]:focus-within {
    border-color: var(--fp-accent);
}


/* =========================================================
   LIGHT/DARK THEME SAFETY
   ========================================================= */

/*
Do not hard-code dark text on light controls or light text
on dark controls. Streamlit's theme variables remain the
source of truth so both OS themes stay readable.
*/

[data-testid="stMarkdownContainer"],
[data-testid="stCaptionContainer"] {
    color: var(--text-color);
}


/* =========================================================
   RESPONSIVE
   ========================================================= */

@media (max-width: 900px) {
    .block-container {
        padding-left: 1.2rem;
        padding-right: 1.2rem;
    }

    .fp-agent-hero h1 {
        font-size: 2.35rem;
    }

    .fp-action-description {
        min-height: auto;
    }
}
</style>
        """,
        unsafe_allow_html=True,
    )