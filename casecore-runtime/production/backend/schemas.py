"""
Pydantic schemas for API requests and responses
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============ Case Schemas ============

class CaseCreate(BaseModel):
    name: str
    court: Optional[str] = None
    plaintiff: str
    defendant: str


class CaseUpdate(BaseModel):
    name: Optional[str] = None
    court: Optional[str] = None
    plaintiff: Optional[str] = None
    defendant: Optional[str] = None
    status: Optional[str] = None


class CaseResponse(BaseModel):
    id: int
    name: str
    court: Optional[str]
    plaintiff: str
    defendant: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CaseDetailResponse(CaseResponse):
    documents: List["DocumentResponse"] = []
    coas: List["COAResponse"] = []
    weapons: List["WeaponResponse"] = []
    strategies: List["StrategyResponse"] = []


# ============ Document Schemas ============

class DocumentCreate(BaseModel):
    case_id: int
    filename: str
    folder: Optional[str] = None
    file_type: Optional[str] = None
    text_content: Optional[str] = None
    char_count: int = 0
    sha256_hash: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    case_id: int
    filename: str
    folder: Optional[str]
    file_type: Optional[str]
    char_count: int
    sha256_hash: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    text_content: Optional[str]


# ============ COA Schemas ============

class COACreate(BaseModel):
    case_id: int
    name: str
    caci_ref: Optional[str] = None
    strength: float = 0.0
    evidence_count: int = 0
    coverage_pct: float = 0.0
    status: str = "pending"


class BurdenElementResponse(BaseModel):
    id: int
    element_id: str
    description: Optional[str]
    strength: float
    supporting_docs: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class COAResponse(BaseModel):
    id: int
    case_id: int
    name: str
    caci_ref: Optional[str]
    strength: float
    evidence_count: int
    coverage_pct: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class COADetailResponse(COAResponse):
    burden_elements: List[BurdenElementResponse] = []


# ============ Weapon Schemas ============

class WeaponCreate(BaseModel):
    case_id: int
    category: str
    coa_ref: Optional[str] = None
    caci: Optional[str] = None
    element: Optional[str] = None
    strategy: Optional[str] = None
    strategy_type: Optional[str] = None
    question: Optional[str] = None
    strengthens_jeremy: Optional[str] = None
    weakens_david: Optional[str] = None
    perjury_push: Optional[str] = None
    evidence_score: float = 0.0
    perjury_trap: bool = False
    docs_json: Optional[Dict[str, Any]] = None
    opp_prediction: Optional[str] = None
    depo_strategy: Optional[str] = None
    long_game: Optional[str] = None
    responses_json: Optional[Dict[str, Any]] = None
    attorney_question: Optional[str] = None
    attorney_notes: Optional[str] = None
    status: str = "pending"


class WeaponUpdate(BaseModel):
    question: Optional[str] = None
    strengthens_jeremy: Optional[str] = None
    weakens_david: Optional[str] = None
    perjury_push: Optional[str] = None
    attorney_question: Optional[str] = None
    attorney_notes: Optional[str] = None
    status: Optional[str] = None


class WeaponResponse(BaseModel):
    id: int
    case_id: int
    category: str
    coa_ref: Optional[str]
    caci: Optional[str]
    element: Optional[str]
    strategy: Optional[str]
    strategy_type: Optional[str]
    evidence_score: float
    perjury_trap: bool
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class WeaponDetailResponse(WeaponResponse):
    question: Optional[str]
    strengthens_jeremy: Optional[str]
    weakens_david: Optional[str]
    perjury_push: Optional[str]
    docs_json: Optional[Dict[str, Any]]
    opp_prediction: Optional[str]
    depo_strategy: Optional[str]
    long_game: Optional[str]
    responses_json: Optional[Dict[str, Any]]
    attorney_question: Optional[str]
    attorney_notes: Optional[str]


# ============ Strategy Schemas ============

class StrategyCreate(BaseModel):
    case_id: int
    name: str
    emoji: Optional[str] = None
    weapons_json: Optional[Dict[str, Any]] = None
    rationale: Optional[str] = None
    value_score: float = 0.0
    depo_impact: float = 0.0
    trial_impact: float = 0.0
    phases_json: Optional[Dict[str, Any]] = None


class StrategyResponse(BaseModel):
    id: int
    case_id: int
    name: str
    emoji: Optional[str]
    value_score: float
    depo_impact: float
    trial_impact: float
    created_at: datetime

    class Config:
        from_attributes = True


class StrategyDetailResponse(StrategyResponse):
    weapons_json: Optional[Dict[str, Any]]
    rationale: Optional[str]
    phases_json: Optional[Dict[str, Any]]
    weapons: List[WeaponResponse] = []


# ============ Perjury Path Schemas ============

class PerjuryPathCreate(BaseModel):
    case_id: int
    name: str
    desc: Optional[str] = None
    weapons_json: Optional[Dict[str, Any]] = None
    logic: Optional[str] = None
    trap_springs: Optional[str] = None


class PerjuryPathResponse(BaseModel):
    id: int
    case_id: int
    name: str
    desc: Optional[str]
    weapons_json: Optional[Dict[str, Any]]
    logic: Optional[str]
    trap_springs: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Deposition Schemas ============

class DepositionSessionCreate(BaseModel):
    case_id: int
    witness_name: Optional[str] = None


class DepositionSessionResponse(BaseModel):
    id: int
    case_id: int
    witness_name: Optional[str]
    started_at: datetime
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DepositionTranscriptUpdate(BaseModel):
    transcript_text: str


# ============ Attorney Edit Schemas ============

class AttorneyEditCreate(BaseModel):
    weapon_id: int
    field_name: str
    original_value: Optional[str] = None
    edited_value: Optional[str] = None


class AttorneyEditResponse(BaseModel):
    id: int
    weapon_id: int
    field_name: str
    original_value: Optional[str]
    edited_value: Optional[str]
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True


# ============ Simulation Schemas ============

class SimulateResponse(BaseModel):
    """Response from opponent simulation"""
    david_says: str
    counter: str
    delta: str
    perjury_evidence: Optional[str] = None


class SimulationRequest(BaseModel):
    weapon_id: int
    scenario: Optional[str] = None


# Update forward references
CaseDetailResponse.model_rebuild()
StrategyDetailResponse.model_rebuild()
