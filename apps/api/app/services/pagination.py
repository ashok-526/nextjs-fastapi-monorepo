from __future__ import annotations

import base64
import uuid
from datetime import datetime


def encode_keyset(created_at: datetime, id_: uuid.UUID) -> str:
    raw = f"{created_at.isoformat()}|{id_}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def decode_keyset(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        ts_str, id_str = raw.split("|", 1)
        ts = datetime.fromisoformat(ts_str)
        return ts, uuid.UUID(id_str)
    except Exception as e:  # noqa: BLE001
        raise ValueError("Invalid cursor") from e

