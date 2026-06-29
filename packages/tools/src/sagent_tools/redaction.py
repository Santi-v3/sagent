"""Shared output redaction for logs and reviewable diffs."""

import re

_QUOTED_ASSIGNMENT = re.compile(
    r"(?im)\b(api[_-]?key|password|secret|token)(\s*[:=]\s*)([\"'])([^\"'\r\n]+)(\3)"
)
_UNQUOTED_ASSIGNMENT = re.compile(
    r"(?im)\b(api[_-]?key|password|secret|token)(\s*[:=]\s*)([A-Za-z0-9_./+=-]{4,})"
)
_SECRET_PATTERNS = (
    re.compile(r"\b(?:gh[pousr]_|github_pat_|sk-)[A-Za-z0-9_\-]{16,}\b"),
    re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?"
        r"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        re.DOTALL,
    ),
)


def redact_secrets(output: str) -> tuple[str, bool]:
    """Redact known secret shapes and report whether anything was hidden."""

    redacted, quoted_assignments = _QUOTED_ASSIGNMENT.subn(
        lambda match: f"{match.group(1)}{match.group(2)}{match.group(3)}[REDACTED]{match.group(5)}",
        output,
    )
    redacted, unquoted_assignments = _UNQUOTED_ASSIGNMENT.subn(
        lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]",
        redacted,
    )
    redacted, tokens = _SECRET_PATTERNS[0].subn("[REDACTED]", redacted)
    redacted, private_keys = _SECRET_PATTERNS[1].subn(
        "[REDACTED PRIVATE KEY]",
        redacted,
    )
    return redacted, bool(quoted_assignments or unquoted_assignments or tokens or private_keys)
