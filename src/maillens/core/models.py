from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class RecipientKind(str, Enum):
    TO = "to"
    CC = "cc"
    BCC = "bcc"

class Contact(BaseModel):
    email: str
    name: str | None = None

class Attachment(BaseModel):
    filename: str
    content_type: str
    size_bytes: int

class Message(BaseModel):
    #Contacts
    sender: Contact
    recipients: list[tuple[Contact, RecipientKind]] = Field(default_factory = list)

    #Threading
    in_reply_to: str | None = None
    references: list[str] = Field(default_factory = list)
    thread_id: str | None = None

    #Date
    sent_at: datetime

    #Identity
    message_id: str
    source: str = Field(..., description = "mbox/IMAP/PST")
    source_ref: str | None = None

    #Content
    subject: str | None = None
    body_text: str = ""
    body_html: str | None = None

    #Attachments
    attachments: list[Attachment] = Field(default_factory = list)

    #Labels
    folder: str | None = None