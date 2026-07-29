"""
ORM model for the llm_calls table.

Design choice: this package does NOT run its own database. Each host project
(Activity Tracker, Bill Splitter, AI Chief of Staff) already has its own
Postgres DB — this table gets created there via that project's own Alembic
migrations (see migrations/001_create_llm_calls_table.sql for the raw SQL to
adapt into a migration). The package just provides the model + insert logic.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Integer, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class LLMCallLog(Base):
    __tablename__ = "llm_calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Which project + which feature made this call
    project = Column(String, nullable=False)          # e.g. "activity-tracker"
    feature = Column(String, nullable=False)           # e.g. "rag_qa", "expense_categorize"

    # Provider details
    provider = Column(String, nullable=False)          # "gemini" | "groq"
    model = Column(String, nullable=True)               # e.g. "llama-3.1-8b"

    # Prompt tracking (ties back to prompts/registry.py)
    prompt_name = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)

    # Call content — truncate/redact upstream before logging if it may contain PII
    prompt_text = Column(Text, nullable=True)
    response_text = Column(Text, nullable=True)

    # Performance + cost
    latency_ms = Column(Integer, nullable=False)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    estimated_cost_usd = Column(Float, nullable=True)

    # Outcome
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    guardrail_flagged = Column(Boolean, nullable=False, default=False)

    extra_metadata = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
