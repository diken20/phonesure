"""eSewa ePay v2 helpers: sign the payment form and verify eSewa's reply.

Flow: we POST a signed form to eSewa -> buyer pays -> eSewa redirects the buyer back with
?data=<base64 JSON> -> we check the signature, status, amount and transaction id.
Docs: https://developer.esewa.com.np/pages/Epay-V2
"""
import base64
import hashlib
import hmac
import json
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings

REQUEST_SIGNED_FIELDS = "total_amount,transaction_uuid,product_code"
# A reply MUST sign at least these fields. Otherwise a buyer could reuse the signature we put in
# the payment form (which signs only amount, id and code) to forge a "COMPLETE" reply.
REQUIRED_REPLY_FIELDS = {"status", "total_amount", "transaction_uuid", "product_code"}


def sign(message, secret):
    digest = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def signature_message(fields, names):
    return ",".join(f"{name}={fields[name]}" for name in names)


def build_payment_form(order):
    """The URL and hidden fields the browser must POST to eSewa."""
    amount = str(order.total)
    fields = {
        "amount": amount,
        "tax_amount": "0",
        "total_amount": amount,
        "transaction_uuid": order.transaction_uuid,
        "product_code": settings.ESEWA_PRODUCT_CODE,
        "product_service_charge": "0",
        "product_delivery_charge": "0",
        "success_url": f"{settings.FRONTEND_URL}/payment/success",
        "failure_url": f"{settings.FRONTEND_URL}/payment/failure",
        "signed_field_names": REQUEST_SIGNED_FIELDS,
    }
    fields["signature"] = sign(
        signature_message(fields, REQUEST_SIGNED_FIELDS.split(",")), settings.ESEWA_SECRET_KEY
    )
    return {"url": settings.ESEWA_FORM_URL, "fields": fields}


def decode_reply(encoded):
    """base64 -> dict. Numbers stay as the exact text eSewa sent (e.g. '1000.0'), because the
    signature was computed over that exact text."""
    try:
        raw = base64.b64decode(encoded + "=" * (-len(encoded) % 4))
        data = json.loads(raw.decode("utf-8"), parse_float=str, parse_int=str)
    except Exception as exc:
        raise ValueError("Unreadable payment reply.") from exc
    if not isinstance(data, dict):
        raise ValueError("Unreadable payment reply.")
    return data


def verify_signature(data):
    names = str(data.get("signed_field_names", "")).split(",")
    if not REQUIRED_REPLY_FIELDS.issubset(names) or any(n not in data for n in names):
        return False
    expected = sign(signature_message(data, names), settings.ESEWA_SECRET_KEY)
    return hmac.compare_digest(expected, str(data.get("signature", "")))


def amount_matches(data, order):
    try:
        return Decimal(str(data["total_amount"]).replace(",", "")) == Decimal(order.total)
    except (InvalidOperation, KeyError):
        return False


def fetch_status(order):
    """Ask eSewa directly whether this payment is COMPLETE. Returns the JSON, or None if
    eSewa cannot be reached (then we rely on the verified signature alone)."""
    query = urlencode({
        "product_code": settings.ESEWA_PRODUCT_CODE,
        "total_amount": order.total,
        "transaction_uuid": order.transaction_uuid,
    })
    try:
        with urlopen(f"{settings.ESEWA_STATUS_URL}?{query}", timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None
