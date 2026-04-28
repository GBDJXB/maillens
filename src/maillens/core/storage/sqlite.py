from sqlalchemy import Table, MetaData, Column, String, Text, DateTime, ForeignKey, Integer


metadata = MetaData()

contacts = Table(
    "Contacts", metadata,
    Column("email", String, nullable=False, primary_key=True),
    Column("name", String)
)

attachments = Table(
    "Attachments", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("message_id", ForeignKey("Messages.message_id")),
    Column("filename", String),
    Column("content_type", String),
    Column("size_bytes", Integer)
)

messages = Table(
    "Messages", metadata,
    # Identity
    Column("message_id", String, primary_key=True),
    Column("source", String, nullable=False),
    Column("source_ref", String),
    # Sender (Contact flattened)
    Column("sender_email", String, ForeignKey("Contacts.email")),
    Column("sender_name", String),
    # Threading
    Column("in_reply_to", String),
    Column("references", Text),   # JSON-encoded list[str]
    Column("thread_id", String),
    # Date
    Column("sent_at", DateTime, nullable=False),
    # Content
    Column("subject", String),
    Column("body_text", Text),
    Column("body_html", Text),
    # Labels
    Column("folder", String),
)

message_recipients = Table(
    "Message_recipients", metadata,
    Column("message_id", ForeignKey("Messages.message_id"), primary_key=True),
    Column("email", ForeignKey("Contacts.email"), primary_key=True),
    Column("name", String),
    Column("kind", String)
)