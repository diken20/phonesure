import base64
import io

import qrcode
from django.conf import settings


def problem_report_url(item):
    return f"{settings.FRONTEND_URL}/report-problem/{item.public_id}"


def qr_data_uri(text):
    """PNG QR code as a data: URI, so React can show it with a plain <img>."""
    image = qrcode.make(text, box_size=6, border=2)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
