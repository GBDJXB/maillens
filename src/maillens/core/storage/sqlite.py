from typing import Iterable
import json

from sqlalchemy import Table, MetaData, Column, String, Text, DateTime, ForeignKey, Integer, Engine, \
    create_engine, text, Connection, insert
from pathlib import Path

from maillens.core.models import Message


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

message_recipients = Table(
    "Message_recipients", metadata,
    Column("message_id", ForeignKey("Messages.message_id"), primary_key=True),
    Column("email", ForeignKey("Contacts.email"), primary_key=True),
    Column("name", String),
    Column("kind", String)
)

attachments = Table(
    "Attachments", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("message_id", ForeignKey("Messages.message_id")),
    Column("filename", String),
    Column("content_type", String),
    Column("size_bytes", Integer)
)


_engine: Engine | None = None

def init_db(path: Path) -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(f"sqlite:///{path.as_posix()}")
        with _engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.execute(text("PRAGMA journal_mode=WAL"))
        metadata.create_all(_engine)
    return _engine

def save_message(conn: Connection, msg: Message) -> None:
    conn.execute(
        insert(contacts).prefix_with("OR IGNORE"),
        {"email": msg.sender.email, "name": msg.sender.name}
    )

    if msg.recipients:
        conn.execute(
            insert(contacts).prefix_with("OR IGNORE"),
            [{"email": t[0].email, "name": t[0].email} for t in msg.recipients]
        )

    conn.execute(
        insert(messages).prefix_with("OR REPLACE"),
        {
            "message_id": msg.message_id,
            "source": msg.source,
            "source_ref": msg.source_ref,
            "sender_email": msg.sender.email,
            "sender_name": msg.sender.name,
            "in_reply_to": msg.in_reply_to,
            "references": json.dumps(msg.references),
            "thread_id": msg.thread_id,
            "sent_at": msg.sent_at,
            "subject": msg.subject,
            "body_text": msg.body_text,
            "body_html": msg.body_html,
            "folder": msg.folder,
        }
    )

    pass

def save_messages(conn, msgs: Iterable[Message]) -> int:
    pass

def get_message(conn, msg_id: str) -> Message | None:
    pass
