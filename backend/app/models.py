import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, Text, ForeignKey, DateTime
)
from sqlalchemy.orm import relationship
from app.database import Base


class ScanRun(Base):
    __tablename__ = "scan_runs"

    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String, nullable=False)  # repo | zip | image | binary | local
    target_ref = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending | running | completed | failed
    progress_message = Column(String, default="Queued")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    assets = relationship("CryptoAsset", back_populates="scan_run", cascade="all, delete-orphan")


class CryptoAsset(Base):
    __tablename__ = "crypto_assets"

    id = Column(Integer, primary_key=True, index=True)
    scan_run_id = Column(Integer, ForeignKey("scan_runs.id"), nullable=False)
    asset_type = Column(String)  # algorithm | certificate | protocol | library | binary_embedded_lib | container_library
    name = Column(String)
    algorithm = Column(String)
    category = Column(String)  # symmetric | asymmetric | hash | protocol | library
    key_size = Column(Integer, nullable=True)
    mode = Column(String, nullable=True)
    language = Column(String, nullable=True)
    source_file = Column(String, nullable=True)
    line_number = Column(Integer, nullable=True)
    raw_snippet = Column(Text, nullable=True)
    criticality_tag = Column(String, default="internal_only")

    scan_run = relationship("ScanRun", back_populates="assets")
    finding = relationship("Finding", back_populates="asset", uselist=False, cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("crypto_assets.id"), nullable=False)
    quantum_vulnerable = Column(Boolean, default=False)
    broken_by = Column(String, nullable=True)  # shor | grover | classical | null
    risk_level = Column(String, default="Low")  # Critical | High | Medium | Low
    mosca_x = Column(Float, default=5)
    mosca_y = Column(Float, default=1)
    mosca_z = Column(Float, default=10)
    at_risk = Column(Boolean, default=False)
    explanation = Column(Text, nullable=True)
    recommendation_summary = Column(String, nullable=True)
    recommendation_detail = Column(Text, nullable=True)  # JSON string

    asset = relationship("CryptoAsset", back_populates="finding")


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)
