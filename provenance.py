"""Provenance discipline for the GEO pipeline (mirrors app.core.provenance rules).

Every user-visible claim carries a tier. There is no validated source
connected, so nothing in this pipeline may emit a `validated` verdict.
"""
from enum import Enum


class Provenance(str, Enum):
    OBSERVED = "observed"              # client-authored brand copy (the docx)
    INFERRED = "inferred"              # our local scoring/labelling of observed rows
    SYNTHETIC_PRETEST = "synthetic"    # LLM persona output — never shown as consumer voice
    VALIDATED = "validated"            # real respondent — NOT AVAILABLE in this pipeline


DEFAULT_VERDICT = "insufficient"


def readiness_caveat() -> str:
    """Must accompany every ranking/affinity score that leaves the pipeline."""
    return (
        "Scores are ordinal indices derived from on-page structural signals "
        "and brand-authored copy (provenance: observed/inferred). No outcome "
        "or consumer-validated data exists; do not read these as probabilities, "
        "CTR predictions or conversion likelihoods."
    )


# Claims that must not be rendered until formulation/data is confirmed
# (source: Kathai_Flavours.docx 'Additional Requirement' notes).
BLOCKED_CLAIMS = [
    "high protein",
    "low sugar",
    "vegan",
    "natural",
    "preservative-free",
    "aggregateRating",   # no reviews exist yet — never fabricate
    "review",
]


def claim_is_blocked(text: str) -> bool:
    low = text.lower()
    return any(c.lower() in low for c in BLOCKED_CLAIMS)
