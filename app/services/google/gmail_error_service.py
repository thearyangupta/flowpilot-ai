from dataclasses import dataclass


class GmailErrorClassification:
    pass


@dataclass(frozen=True)
class RefreshOnceThenRetry(GmailErrorClassification):
    pass


@dataclass(frozen=True)
class MissingScopeOrPermission(GmailErrorClassification):
    pass


@dataclass(frozen=True)
class RetryWithBackoff(GmailErrorClassification):
    pass


@dataclass(frozen=True)
class PermanentProviderFailure(GmailErrorClassification):
    pass


from googleapiclient.errors import HttpError


def classify_gmail_error(
    exc: HttpError,
) -> GmailErrorClassification:
    status = exc.resp.status

    if status == 401:
        return RefreshOnceThenRetry()

    if status == 403:
        return MissingScopeOrPermission()

    if status == 429 or status >= 500:
        return RetryWithBackoff()

    return PermanentProviderFailure()