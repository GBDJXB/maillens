import unittest
from datetime import datetime

import pytest
from pydantic import ValidationError

from maillens.core.models import RecipientKind, Contact, Attachment, Message


class Test_models(unittest.TestCase):
    def test_recipient_kind(self):
        assert RecipientKind.TO == "to"
        assert RecipientKind.CC == "cc"
        assert RecipientKind.BCC == "bcc"

    def test_contact(self):
        c = Contact(email = "test@example.com")
        assert c.email == "test@example.com"
        assert c.name is None
        c.name = "ABC"
        assert c.name == "ABC"

    def test_attachment(self):
        a = Attachment(filename = "testfile", content_type = "test type", size_bytes = 128)
        assert a.filename == "testfile"
        assert a.content_type == "test type"
        assert  a.size_bytes == 128

    def test_message_minimal(self):
        m = Message(
            sender = Contact(email = "test@example.com"),
            sent_at = datetime(2026, 4, 16),
            message_id = "<some@example.com>",
            source = "mbox"
        )
        assert type(m.sender) == Contact
        assert m.sent_at == datetime(2026, 4, 16)
        assert m.message_id is not None
        assert m.source is not None
        assert m.recipients == []
        assert m.in_reply_to is None
        assert m.body_text == ""

    def test_message_missing_source(self):
        with pytest.raises(ValidationError):
            Message(
                sender = Contact(email = "test@example.com"),
                sent_at = datetime(2026, 4, 16),
                message_id = "<some@example.com>"
            )

    def test_message_w_recipients(self):
        m = Message(
            sender = Contact(email = "test@example.com"),
            recipients = [(Contact(email = "test@example.com"), RecipientKind.TO)],
            sent_at = datetime(2026, 4, 16),
            message_id = "<some@example.com>",
            source = "mbox"
        )
        assert m.recipients[0] == (Contact(email = "test@example.com"), "to")


if __name__ == '__main__':
    unittest.main()
