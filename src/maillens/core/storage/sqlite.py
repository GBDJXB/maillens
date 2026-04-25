from sqlalchemy import Table, MetaData, Column, String, Text, DateTime, ForeignKey

metadata = MetaData()

contacts = Table(
    "Contacts", metadata,
    Column("email", String, nullable=False, primary_key=True),
    Column("name", String)
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