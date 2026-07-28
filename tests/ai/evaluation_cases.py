from app.ai.schemas import Intent, Urgency


LABELLED_EMAIL_CASES = [
    (
        "I was charged twice for invoice 19.",
        Intent.billing,
        Urgency.medium,
    ),
    (
        "My payment failed, but money was deducted from my account.",
        Intent.billing,
        Urgency.high,
    ),
    (
        "Can you send me a copy of last month's invoice?",
        Intent.billing,
        Urgency.low,
    ),
    (
        "I cannot reset my password.",
        Intent.account,
        Urgency.medium,
    ),
    (
        "My account has been locked after several login attempts.",
        Intent.account,
        Urgency.high,
    ),
    (
        "Please update the email address linked to my account.",
        Intent.account,
        Urgency.low,
    ),
    (
        "The production API is down for all customers.",
        Intent.technical,
        Urgency.critical,
    ),
    (
        "The dashboard shows an error whenever I upload a file.",
        Intent.technical,
        Urgency.high,
    ),
    (
        "How do I enable the workflow integration?",
        Intent.technical,
        Urgency.low,
    ),
    (
        "The new workflow editor is much easier to use.",
        Intent.feedback,
        Urgency.low,
    ),
    (
        "The latest update made the dashboard confusing.",
        Intent.feedback,
        Urgency.medium,
    ),
    (
        "Your support team resolved my issue very quickly.",
        Intent.feedback,
        Urgency.low,
    ),
    (
        "Can someone explain what FlowPilot does?",
        Intent.other,
        Urgency.low,
    ),
    (
        "I would like to discuss a business partnership.",
        Intent.other,
        Urgency.medium,
    ),
    (
        "Please delete all information associated with my account immediately.",
        Intent.account,
        Urgency.high,
    ),
]