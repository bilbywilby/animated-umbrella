from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
import hashlib
import os

class ProvenanceEntry(BaseModel):
    """Lineage of a data source with automated SHA-256 verification."""
    url: str = Field(..., description="Source URL from CMS")
    file_path: str = Field(..., description="Local path where file was saved")
    last_modified: Optional[str] = Field(None, description="HTTP Last-Modified header")
    sha256_hash: Optional[str] = Field(None, description="SHA-256 checksum")

    @validator('sha256_hash', always=True)
    def compute_hash(cls, v, values):
        if v: return v
        path = values.get('file_path')
        if not path or not os.path.exists(path):
            return None
        try:
            with open(path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            raise ValueError(f"Hash computation failed for {path}: {e}")

    class Config:
        extra = 'forbid'

class CarrierData(BaseModel):
    """Actuarial payload extracted from CMS crosswalk."""
    carrier_name: str
    plan_code: str
    metal_level: str 
    premium_usd: float
    deductible_usd: float
    effective_date: str 
    state: str = "PA"

    @validator('premium_usd', 'deductible_usd', always=True)
    def non_negative(cls, v):
        if v < 0:
            raise ValueError("Financial values must be non-negative")
        return v

class RatingAreaMapping(BaseModel):
    """Strict mapping for Rating Area verification."""
    area_id: int
    counties: List[str]
    verified_source: str = "CMS_CROSSWALK"

    class Config:
        extra = 'forbid'
