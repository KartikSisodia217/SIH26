"""
Pydantic Schemas for OceanEmbed Backend API
Defines input and output data models for coordinates, profiles, depth slices, and D26 isotherms.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# Target depth levels as specified by OceanEmbed architecture contract
TARGET_DEPTHS_M = [0.0, 5.0, 10.0, 20.0, 30.0, 50.0, 75.0, 100.0, 125.0, 150.0, 200.0, 300.0, 500.0, 700.0, 1000.0]

# Geographic domain bounds
LAT_MIN, LAT_MAX = 5.0, 30.0
LON_MIN, LON_MAX = 45.0, 105.0


class ProfileRequest(BaseModel):
    """Request payload for point-based vertical subsurface temperature profile."""
    latitude: float = Field(..., description="Latitude in degrees North (5.0 to 30.0)", json_schema_extra={"example": 15.0})
    longitude: float = Field(..., description="Longitude in degrees East (45.0 to 105.0)", json_schema_extra={"example": 65.0})
    date: Optional[str] = Field("latest", description="Target ISO date string (YYYY-MM-DD) or 'latest'")

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not (LAT_MIN <= v <= LAT_MAX):
            raise ValueError(f"Latitude {v} out of bounds. Must be between {LAT_MIN}°N and {LAT_MAX}°N.")
        return round(v, 4)

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not (LON_MIN <= v <= LON_MAX):
            raise ValueError(f"Longitude {v} out of bounds. Must be between {LON_MIN}°E and {LON_MAX}°E.")
        return round(v, 4)


class ProfileResponse(BaseModel):
    """Response payload containing 15 depth levels and temperature predictions."""
    latitude: float
    longitude: float
    depths_m: List[float] = Field(..., description="15 standard ocean depth levels in meters")
    temperatures_c: List[Optional[float]] = Field(..., description="Temperatures in Celsius across 15 depth levels (None for land)")
    d26_depth_m: Optional[float] = Field(None, description="Depth of 26°C isotherm in meters (D26 / TCHP metric)")
    surface_temp_c: Optional[float] = Field(None, description="Surface temperature (0m) in °C")
    bottom_temp_c: Optional[float] = Field(None, description="Bottom temperature (1000m) in °C")
    is_land: bool = Field(..., description="True if coordinate represents land mass")
    units: str = Field("°C", description="Temperature measurement unit")


class SliceRequest(BaseModel):
    """Request payload for 2D horizontal ocean temperature map slice."""
    depth_m: float = Field(0.0, description="Target depth level in meters (e.g. 0, 5, 10, ..., 1000)")
    date: Optional[str] = Field("latest", description="Target ISO date string (YYYY-MM-DD) or 'latest'")

    @field_validator("depth_m")
    @classmethod
    def validate_depth(cls, v: float) -> float:
        closest_depth = min(TARGET_DEPTHS_M, key=lambda d: abs(d - v))
        return closest_depth


class SliceResponse(BaseModel):
    """Response payload containing 2D horizontal temperature grid (101x241)."""
    depth_m: float
    grid_shape: List[int] = Field([101, 241], description="[height (latitudes), width (longitudes)]")
    latitudes: List[float] = Field(..., description="List of 101 latitude points from 5.0 to 30.0")
    longitudes: List[float] = Field(..., description="List of 241 longitude points from 45.0 to 105.0")
    temperatures_2d: List[List[Optional[float]]] = Field(..., description="2D temperature grid [101][241] (null for land)")
    units: str = Field("°C", description="Temperature measurement unit")


class D26Request(BaseModel):
    """Request payload for D26 isotherm calculation."""
    latitude: float = Field(..., description="Latitude in degrees North (5.0 to 30.0)", json_schema_extra={"example": 12.5})
    longitude: float = Field(..., description="Longitude in degrees East (45.0 to 105.0)", json_schema_extra={"example": 85.0})

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not (LAT_MIN <= v <= LAT_MAX):
            raise ValueError(f"Latitude {v} out of bounds. Must be between {LAT_MIN}°N and {LAT_MAX}°N.")
        return round(v, 4)

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not (LON_MIN <= v <= LON_MAX):
            raise ValueError(f"Longitude {v} out of bounds. Must be between {LON_MIN}°E and {LON_MAX}°E.")
        return round(v, 4)


class D26Response(BaseModel):
    """Response payload for D26 isotherm depth."""
    latitude: float
    longitude: float
    d26_depth_m: Optional[float] = Field(..., description="Calculated 26°C isotherm depth in meters")
    is_valid_thermocline: bool = Field(..., description="True if surface >= 26°C and temperature drops below 26°C within 1000m")
    explanation: str = Field(..., description="Human-readable derivation note")


class HealthResponse(BaseModel):
    """Health check payload."""
    status: str = "ok"
    version: str = "1.0.0"
    model_loaded: bool = False
    mode: str = "mock"


class ErrorDetail(BaseModel):
    """Standardized error response payload."""
    detail: str
    code: str = "BAD_REQUEST"
