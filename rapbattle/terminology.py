"""Downstream presentation vocabulary. Never rewrites upstream objects or grants access."""
from copy import deepcopy
from html import escape
from types import MappingProxyType


TERMS=MappingProxyType({
    "event":("battle","battles"),
    "competition":("battle","battles"),
    "stage":("match","matches"),
    "round":("round","rounds"),
    "performer":("emcee","emcees"),
    "producer":("promoter","promoters"),
    "judge":("judge","judges"),
    "organization":("league","leagues"),
    "winner":("champion","champions"),
    "score":("score","scores"),
})


def term(kind, count=1):
    if not isinstance(kind,str) or kind not in TERMS:
        raise ValueError("Unsupported engine presentation kind")
    if type(count) is not int or count<0:
        raise ValueError("Count must be a nonnegative integer")
    return TERMS[kind][0 if count==1 else 1]


def presentation(record,kind):
    """Caller must authorize the engine record before passing it here.

    The original keys, IDs, enums, score values and nested objects are preserved.
    Presentation metadata is outside the upstream record, not a renamed schema.
    """
    label=term(kind)
    if not isinstance(record,dict):
        raise ValueError("An authorized engine record object is required")
    return {"label":label,"record":deepcopy(record)}


def heading(kind,count=1):
    # Return only a label; this never accepts arbitrary user markup or a record.
    return "<h2>"+escape(term(kind,count).capitalize())+"</h2>"
