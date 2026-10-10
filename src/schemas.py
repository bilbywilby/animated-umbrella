#!/usr/bin/env python3
"""Pydantic models for PA health insurance audit data."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional

class RatingAreaEntry(BaseModel):
    """A single rating area with counties and carrier data."""
    area_number: int = Field(..., ge=1, le=9)
    counties: list[str] = Field(...)
    carrier_dominance: dict[str, float] = Field(default_factory=dict)
    py2026_baseline: Optional[dict[str, float]] = None
    py2027_forecast: Optional[dict[str, float]] = None
    
    @field_validator("counties")
    @classmethod
    def counties_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Area must have at least one county")
        return v


class PAHealthDataset(BaseModel):
    """Top-level dataset for PA health insurance audit."""
    version: str
    generated_at: str
    rating_areas: list[RatingAreaEntry]
    total_counties: int = Field(..., ge=65, le=67)
    
    @field_validator("rating_areas")
    @classmethod
    def areas_complete(cls, v: list[RatingAreaEntry]) -> list[RatingAreaEntry]:
        if len(v) != 9:
            raise ValueError("Must have exactly 9 rating areas")
        return v


# Quick validation function
def validate_dataset(data: dict) -> bool:
    """Return True if data conforms to PAHealthDataset."""
    try:
        PAHealthDataset(**data)
        return True
    except Exception as e:
        print(f"Validation error: {e}")
        return False

