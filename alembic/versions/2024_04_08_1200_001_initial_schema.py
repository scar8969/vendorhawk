"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2024-04-08 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create factories table
    op.create_table(
        "factories",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("phone", sa.String(length=15), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("udyam_number", sa.String(length=20), nullable=True),
        sa.Column("materials_json", postgresql.JSONB(), nullable=False),
        sa.Column("onboarded_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone")
    )
    op.create_index("idx_factories_phone", "factories", ["phone"])

    # Create invoices table
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("factory_id", postgresql.UUID(), nullable=False),
        sa.Column("vendor_name", sa.String(length=255), nullable=False),
        sa.Column("item_name", sa.String(length=255), nullable=False),
        sa.Column("item_description", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("gstin", sa.String(length=15), nullable=True),
        sa.Column("raw_ocr_text", sa.Text(), nullable=True),
        sa.Column("parsed_json", postgresql.JSONB(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["factory_id"], ["factories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("idx_invoices_factory_created", "invoices", ["factory_id", "created_at"])

    # Create commodity_prices table
    op.create_table(
        "commodity_prices",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("commodity_code", sa.String(length=20), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("idx_prices_lookup", "commodity_prices", ["commodity_code", "city", "expires_at"])

    # Create vendors table
    op.create_table(
        "vendors",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=15), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("commodities_json", postgresql.JSONB(), nullable=False),
        sa.Column("rating", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("total_negotiations", sa.Integer(), nullable=False),
        sa.Column("avg_response_hours", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("response_rate", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("idx_vendors_location", "vendors", ["city", "state"])

    # Create negotiations table
    op.create_table(
        "negotiations",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(), nullable=False),
        sa.Column("factory_id", postgresql.UUID(), nullable=False),
        sa.Column("commodity", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("target_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("winning_vendor_id", postgresql.UUID(), nullable=True),
        sa.Column("final_price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("saving_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.ForeignKeyConstraint(["factory_id"], ["factories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["winning_vendor_id"], ["vendors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("idx_negotiations_factory_status", "negotiations", ["factory_id", "status"])

    # Create negotiation_vendor_messages table
    op.create_table(
        "negotiation_vendor_messages",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("negotiation_id", postgresql.UUID(), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(), nullable=False),
        sa.Column("message_sent", sa.Text(), nullable=False),
        sa.Column("message_sent_at", sa.DateTime(), nullable=False),
        sa.Column("response_received", sa.Text(), nullable=True),
        sa.Column("response_received_at", sa.DateTime(), nullable=True),
        sa.Column("quoted_price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("counter_offered", sa.Boolean(), nullable=False),
        sa.Column("final_status", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["negotiation_id"], ["negotiations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("idx_messages_negotiation", "negotiation_vendor_messages", ["negotiation_id"])


def downgrade() -> None:
    # Drop tables in reverse order due to foreign key constraints
    op.drop_index("idx_messages_negotiation", table_name="negotiation_vendor_messages")
    op.drop_table("negotiation_vendor_messages")

    op.drop_index("idx_negotiations_factory_status", table_name="negotiations")
    op.drop_table("negotiations")

    op.drop_index("idx_vendors_location", table_name="vendors")
    op.drop_table("vendors")

    op.drop_index("idx_prices_lookup", table_name="commodity_prices")
    op.drop_table("commodity_prices")

    op.drop_index("idx_invoices_factory_created", table_name="invoices")
    op.drop_table("invoices")

    op.drop_index("idx_factories_phone", table_name="factories")
    op.drop_table("factories")
