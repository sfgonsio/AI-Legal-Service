"""
SQLAlchemy ORM models for CaseCore
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    court = Column(String(255), nullable=True)
    plaintiff = Column(String(255), nullable=False)
    defendant = Column(String(255), nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    coas = relationship("COA", back_populates="case", cascade="all, delete-orphan")
    weapons = relationship("Weapon", back_populates="case", cascade="all, delete-orphan")
    strategies = relationship("Strategy", back_populates="case", cascade="all, delete-orphan")
    perjury_paths = relationship("PerjuryPath", back_populates="case", cascade="all, delete-orphan")
    deposition_sessions = relationship("DepositionSession", back_populates="case", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    folder = Column(String(255), nullable=True)
    file_type = Column(String(50), nullable=True)
    text_content = Column(Text, nullable=True)
    char_count = Column(Integer, default=0)
    sha256_hash = Column(String(64), nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="documents")


class COA(Base):
    __tablename__ = "coas"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    name = Column(String(255), nullable=False)
    caci_ref = Column(String(50), nullable=True)
    strength = Column(Float, default=0.0)
    evidence_count = Column(Integer, default=0)
    coverage_pct = Column(Float, default=0.0)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="coas")
    burden_elements = relationship("BurdenElement", back_populates="coa", cascade="all, delete-orphan")


class BurdenElement(Base):
    __tablename__ = "burden_elements"

    id = Column(Integer, primary_key=True, index=True)
    coa_id = Column(Integer, ForeignKey("coas.id"), nullable=False)
    element_id = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    strength = Column(Float, default=0.0)
    supporting_docs = Column(JSON, nullable=True)

    # Relationships
    coa = relationship("COA", back_populates="burden_elements")


class Weapon(Base):
    __tablename__ = "weapons"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    category = Column(String(50), nullable=False)  # DISCOVER, UNCOVER, WEAPONIZE
    coa_ref = Column(String(255), nullable=True)
    caci = Column(String(50), nullable=True)
    element = Column(String(255), nullable=True)
    strategy = Column(String(255), nullable=True)
    strategy_type = Column(String(50), nullable=True)
    question = Column(Text, nullable=True)
    strengthens_jeremy = Column(Text, nullable=True)
    weakens_david = Column(Text, nullable=True)
    perjury_push = Column(Text, nullable=True)
    evidence_score = Column(Float, default=0.0)
    perjury_trap = Column(Boolean, default=False)
    docs_json = Column(JSON, nullable=True)
    opp_prediction = Column(Text, nullable=True)
    depo_strategy = Column(Text, nullable=True)
    long_game = Column(Text, nullable=True)
    responses_json = Column(JSON, nullable=True)
    attorney_question = Column(Text, nullable=True)
    attorney_notes = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="weapons")
    attorney_edits = relationship("AttorneyEdit", back_populates="weapon", cascade="all, delete-orphan")


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    name = Column(String(255), nullable=False)
    emoji = Column(String(10), nullable=True)
    weapons_json = Column(JSON, nullable=True)
    rationale = Column(Text, nullable=True)
    value_score = Column(Float, default=0.0)
    depo_impact = Column(Float, default=0.0)
    trial_impact = Column(Float, default=0.0)
    phases_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="strategies")


class PerjuryPath(Base):
    __tablename__ = "perjury_paths"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    name = Column(String(255), nullable=False)
    desc = Column(Text, nullable=True)
    weapons_json = Column(JSON, nullable=True)
    logic = Column(Text, nullable=True)
    trap_springs = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="perjury_paths")


class AttorneyEdit(Base):
    __tablename__ = "attorney_edits"

    id = Column(Integer, primary_key=True, index=True)
    weapon_id = Column(Integer, ForeignKey("weapons.id"), nullable=False)
    field_name = Column(String(100), nullable=False)
    original_value = Column(Text, nullable=True)
    edited_value = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    weapon = relationship("Weapon", back_populates="attorney_edits")


class DepositionSession(Base):
    __tablename__ = "deposition_sessions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    witness_name = Column(String(255), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="active")
    transcript_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    case = relationship("Case", back_populates="deposition_sessions")
