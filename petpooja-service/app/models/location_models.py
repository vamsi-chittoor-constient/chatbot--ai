# app/models/chain_models.py

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.db_session import Base  # adjust import to your project


class CountryTable(Base):
    __tablename__ = "country_table"

    country_id = Column(UUID(as_uuid=True), primary_key=True)
    country_name = Column(String(255), nullable=False)
    iso_code = Column(String(8))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    deleted_at = Column(DateTime(timezone=True))
    is_deleted = Column(Boolean, server_default="false", nullable=False)

    states = relationship("StateTable", back_populates="country")


class StateTable(Base):
    __tablename__ = "state_table"

    state_id = Column(UUID(as_uuid=True), primary_key=True)
    state_name = Column(String(255), nullable=False)
    country_id = Column(UUID(as_uuid=True), ForeignKey("country_table.country_id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    deleted_at = Column(DateTime(timezone=True))
    is_deleted = Column(Boolean, server_default="false", nullable=False)

    country = relationship("CountryTable", back_populates="states")
    cities = relationship("CityTable", back_populates="state")


class CityTable(Base):
    __tablename__ = "city_table"

    city_id = Column(UUID(as_uuid=True), primary_key=True)
    city_name = Column(String(255), nullable=False)
    state_id = Column(UUID(as_uuid=True), ForeignKey("state_table.state_id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    deleted_at = Column(DateTime(timezone=True))
    is_deleted = Column(Boolean, server_default="false", nullable=False)

    state = relationship("StateTable", back_populates="cities")
    pincodes = relationship("PincodeTable", back_populates="city")


class PincodeTable(Base):
    __tablename__ = "pincode_table"

    pincode_id = Column(UUID(as_uuid=True), primary_key=True)
    pincode = Column(String(255), nullable=False)
    city_id = Column(UUID(as_uuid=True), ForeignKey("city_table.city_id"))
    area_name = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    deleted_at = Column(DateTime(timezone=True))
    is_deleted = Column(Boolean, server_default="false", nullable=False)

    city = relationship("CityTable", back_populates="pincodes")
    chain_locations = relationship("ChainLocationTable", back_populates="pincode")
