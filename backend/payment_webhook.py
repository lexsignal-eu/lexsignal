"""M10 TEST-MODE-only Stripe snapshot webhook verification and idempotency.

Pure backend building block, NOT a deployed route, checkout or payment service.
Never grant entitlements based on this primitive; subscription state requires
verified server-side event semantics, seller setup, tenant mapping and review.
Reference: https://docs.stripe.com/events/manage-webhook-endpoints
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import re
import sqlite3
import time


class WebhookRejected(ValueError):
    """Reject signature, timestamp, format and live-mode violations."""


@dataclass(frozen=True)
class VerifiedTestEvent:
    event_id: str
    event_type: str
    created: int | None


def verify_test_webhook(raw_body, signature_header, endpoint_secret, now=None, tolerance=300):
    """Check the raw HTTP body with Stripe t/v1 signature (snapshot events).

    This deliberately refuses all live events. Test data only and no privileges.
    """
    if not isinstance(raw_body, bytes) or len(raw_body) == 0 or len(raw_body) > 1024*1024:
        raise WebhookRejected("Invalid raw webhook payload size")
    if not isinstance(signature_header, str) or len(signature_header) > 1000:
        raise WebhookRejected("Missing/invalid signature header")
    if not isinstance(endpoint_secret, str) or not endpoint_secret.startswith("whsec_") or len(endpoint_secret) < 10:
        raise WebhookRejected("Missing configured endpoint secret")
    if not isinstance(tolerance, int) or not 0 < tolerance <= 300:
        raise WebhookRejected("Unsafe timestamp tolerance")
    fields = {}
    for part in signature_header.split(","):
        if "=" not in part:
            raise WebhookRejected("Malformed signature header")
        key, value = part.strip().split("=", 1)
        fields.setdefault(key, []).append(value)
    if len(fields.get("t", [])) != 1 or not fields["t"][0].isdigit():
        raise WebhookRejected("Invalid signature timestamp")
    ts = int(fields["t"][0])
    instant = int(time.time() if now is None else now)
    if ts > instant+tolerance or instant-ts > tolerance:
        raise WebhookRejected("Expired or future signature")
    signatures = fields.get("v1", [])
    if not signatures or len(signatures) > 10:
        raise WebhookRejected("Missing supported signature")
    signed = str(ts).encode("ascii") + b"." + raw_body
    expected = hmac.new(endpoint_secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    if not any(re.fullmatch(r"[0-9a-f]{64}", sig) and hmac.compare_digest(sig, expected)
               for sig in signatures):
        raise WebhookRejected("Signature verification failed")
    try:
        event = json.loads(raw_body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise WebhookRejected("Malformed signed event payload") from exc
    if not isinstance(event, dict) or event.get("object") != "event" or event.get("livemode") is not False:
        raise WebhookRejected("Only Stripe test-mode event objects are accepted")
    event_id, kind = event.get("id"), event.get("type")
    if not isinstance(event_id, str) or not re.fullmatch(r"evt_[A-Za-z0-9]{3,120}", event_id):
        raise WebhookRejected("Invalid event identifier")
    if not isinstance(kind, str) or not re.fullmatch(r"[a-z][a-z0-9_.]{2,100}", kind):
        raise WebhookRejected("Invalid event type")
    created = event.get("created")
    if created is not None and (type(created) is not int or created < 0):
        raise WebhookRejected("Invalid event creation time")
    return VerifiedTestEvent(event_id=event_id, event_type=kind, created=created)


def record_verified_test_event(connection, event):
    """Atomically record a verified test event once, using existing schema.

    Return True on first insert; False for an already-seen event. Neither
    case grants access or updates any billing entitlement.
    """
    if not isinstance(connection, sqlite3.Connection) or not isinstance(event, VerifiedTestEvent):
        raise WebhookRejected("Expected SQLite connection and verified test event")
    with connection:
        result = connection.execute(
            "INSERT OR IGNORE INTO payment_events (provider,event_id) VALUES (?,?)",
            ("stripe_test", event.event_id),
        )
    return result.rowcount == 1
