# app/models/chain_models.py

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.db_session import Base  # adjust import to your project


class ChainInfoTable(Base):
    __tablename__ = "chain_info_table"

    chain_id = Column(UUID(as_uuid=True), primary_key=True)
    chain_name = Column(String(255), nullable=False)
    chain_type = Column(String(255), nullable=False)
    chain_website_url = Column(Text)
    chain_logo_url = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    deleted_at = Column(DateTime(timezone=True))
    is_deleted = Column(Boolean, server_default="false", nullable=False)

    contacts = relationship(
        "ChainContactTable",
        back_populates="chain",
        lazy="selectin",
    )
    locations = relationship(
        "ChainLocationTable",
        back_populates="chain",
        lazy="selectin",
    )


class ChainContactTable(Base):
    __tablename__ = "chain_contact_table"

    chain_contact_id = Column(UUID(as_uuid=True), primary_key=True)
    chain_id = Column(UUID(as_uuid=True), ForeignKey("chain_info_table.chain_id"))
    contact_type = Column(String(255))
    contact_value = Column(String(255))
    is_primary = Column(Boolean, default=False)
    contact_label = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    deleted_at = Column(DateTime(timezone=True))
    is_deleted = Column(Boolean, server_default="false", nullable=False)

    chain = relationship("ChainInfoTable", back_populates="contacts")


class ChainLocationTable(Base):
    __tablename__ = "chain_location_table"

    chain_location_id = Column(UUID(as_uuid=True), primary_key=True)
    chain_id = Column(UUID(as_uuid=True), ForeignKey("chain_info_table.chain_id"))
    address_line = Column(Text)
    landmark = Column(Text)
    pincode_id = Column(UUID(as_uuid=True), ForeignKey("pincode_table.pincode_id"))
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    deleted_at = Column(DateTime(timezone=True))
    is_deleted = Column(Boolean, server_default="false", nullable=False)

    chain = relationship("ChainInfoTable", back_populates="locations")
    pincode = relationship("PincodeTable", back_populates="chain_locations")
