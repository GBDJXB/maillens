import datetime
import email.message
import hashlib
import logging
import mailbox
from email.header import make_header, decode_header
from email.utils import parseaddr, getaddresses, parsedate_to_datetime
from pathlib import Path
from typing import Iterator

from maillens.core.ingest.base import Ingester
from maillens.core.models import Message, Contact, Attachment, RecipientKind

logger = logging.getLogger(__name__)


def _decode_payload(part: email.message.Message) -> str:
    """Decode a MIME part's payload to str, handling None and unknown charsets."""
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        # Charset name is unrecognized by Python (e.g. "x-mac-roman", "utf8")
        return payload.decode("utf-8", errors="replace")


class MboxIngester(Ingester):
    def __init__(self, path: Path) -> None:
        self.path = path

    def iter_messages(self) -> Iterator[Message]:
        mbox = mailbox.mbox(str(self.path))
        try:
            for raw in mbox:
                try:
                    yield self._parse_message(raw)
                except Exception:
                    logger.exception("Failed to parse message; skipping")
        finally:
            mbox.close()

    def _parse_message(self, raw: mailbox.mboxMessage) -> Message:
        name, addr = parseaddr(str(make_header(decode_header(raw.get("From", "")))))

        recipients = (
            self._parse_contacts(getaddresses(raw.get_all("To", [])), RecipientKind.TO)
            + self._parse_contacts(getaddresses(raw.get_all("Cc", [])), RecipientKind.CC)
            + self._parse_contacts(getaddresses(raw.get_all("Bcc", [])), RecipientKind.BCC)
        )

        sent_at = self._parse_date(raw)

        msg_id = str((raw.get("Message-ID") or "")).strip()
        if not msg_id:
            # Deterministic synthetic ID: hash the raw message bytes so re-runs
            # produce the same ID and avoid duplicate rows in the database.
            digest = hashlib.md5(raw.as_bytes()).hexdigest()
            msg_id = f"<synthetic-{digest}@maillens>"

        subject = str(make_header(decode_header(raw.get("Subject", "")))) or None

        body_text = ""
        body_html = ""
        attachments = []

        # Single pass over the MIME tree
        for part in raw.walk():
            disposition = part.get_content_disposition()
            content_type = part.get_content_type()

            if disposition == "attachment":
                payload = part.get_payload(decode=True) or b""
                attachments.append(Attachment(
                    filename=part.get_filename() or "unnamed",
                    content_type=content_type,
                    size_bytes=len(payload),
                ))
            elif content_type == "text/plain" and not body_text:
                body_text = _decode_payload(part)
            elif content_type == "text/html" and not body_html:
                body_html = _decode_payload(part)

        return Message(
            sender=Contact(email=addr, name=name or None),
            recipients=recipients,

            in_reply_to=str(raw.get("In-Reply-To", "")).strip() or None,
            references=str(raw.get("References", "")).split(),

            sent_at=sent_at,

            message_id=msg_id,
            source="mbox",

            subject=subject,
            body_text=body_text,
            body_html=body_html or None,

            attachments=attachments,
        )

    @staticmethod
    def _parse_date(raw: mailbox.mboxMessage) -> datetime.datetime:
        """Parse sent_at with fallback chain: Date header → Received header → epoch sentinel."""
        date_str = raw.get("Date")
        if date_str:
            try:
                return parsedate_to_datetime(date_str)
            except (ValueError, TypeError):
                pass

        for received in (raw.get_all("Received") or []):
            if ";" in received:
                try:
                    return parsedate_to_datetime(received.rsplit(";", 1)[-1].strip())
                except (ValueError, TypeError):
                    continue

        # Epoch sentinel: makes broken dates visibly wrong when sorting
        return datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)

    @staticmethod
    def _parse_contacts(pairs: list[tuple[str, str]], kind: RecipientKind) -> list[tuple[Contact, RecipientKind]]:
        return [(Contact(email=addr, name=name or None), kind) for name, addr in pairs if addr]
