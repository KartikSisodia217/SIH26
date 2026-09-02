"""
FastAPI Router for OceanEmbed Prediction Endpoints (/predict/*).
Executes preprocessor -> ConvFormer PyTorch inference engine -> postprocessor pipeline.
"""

import numpy as np
from fastapi import APIRouter, HTTPException, Query, status
from api.schemas import (
    ProfileRequest, ProfileResponse,
    SliceRequest, SliceResponse,
    D26Request, D26Response,
    LAT_MIN, LAT_MAX, LON_MIN, LON_MAX
)
from src.inference.preprocessor import OceanDataPreprocessor
from src.inference.engine import get_inference_engine
from src.inference.postprocessor import OceanDataPostprocessor
from src.inference.mock_engine import calculate_d26

router = APIRouter(prefix="/predict", tags=["Prediction & Metrics"])

# Initialize pipeline components
_preprocessor = OceanDataPreprocessor()
_postprocessor = OceanDataPostprocessor()


def _validate_bounds(latitude: float, longitude: float):
    """Utility to validate coordinate bounds and raise HTTP 400 if out of domain."""
    if not (LAT_MIN <= latitude <= LAT_MAX):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Latitude {latitude}°N is out of bounds. Must be within [{LAT_MIN}, {LAT_MAX}]°N."
        )
    if not (LON_MIN <= longitude <= LON_MAX):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Longitude {longitude}°E is out of bounds. Must be within [{LON_MIN}, {LON_MAX}]°E."
        )


def _generate_raw_surface_sequence(latitude: float = 15.0, longitude: float = 65.0) -> np.ndarray:
    """Generates synthetic 5-day sequence of 7 raw surface variables for inference execution."""
    seq = np.zeros((5, 7, 101, 241), dtype=np.float32)
    # Channel 0: SST ~ 28.5°C
    seq[:, 0, :, :] = 28.5
    # Channel 1: SSS ~ 34.5 psu
    seq[:, 1, :, :] = 34.5
    # Channel 2: SLA ~ 0.05 m
    seq[:, 2, :, :] = 0.05
    # Channel 3: U ~ 0.02 m/s
    seq[:, 3, :, :] = 0.02
    # Channel 4: V ~ -0.01 m/s
    seq[:, 4, :, :] = -0.01
    # Channel 5: ERA5_U10 ~ 1.2 m/s
    seq[:, 5, :, :] = 1.2
    # Channel 6: ERA5_V10 ~ -0.8 m/s
    seq[:, 6, :, :] = -0.8
    return seq


@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="Get Vertical Subsurface Temperature Profile (GET)",
    description="Returns predicted temperatures across 15 depth levels (0m to 1000m) for a given (lat, lon) coordinate."
)
def get_profile(
    latitude: float = Query(..., description="Latitude 5.0 to 30.0 °N"),
    longitude: float = Query(..., description="Longitude 45.0 to 105.0 °E"),
    date: str = Query("latest", description="Target ISO date string (YYYY-MM-DD) or 'latest'")
):
    _validate_bounds(latitude, longitude)
    
    # Preprocessor -> Inference Engine -> Postprocessor pipeline execution
    raw_seq = _generate_raw_surface_sequence(latitude, longitude)
    input_tensor = _preprocessor.prepare_input_tensor(raw_seq)
    
    engine = get_inference_engine()
    output_tensor = engine.predict(input_tensor)
    
    profile = _postprocessor.extract_point_profile(output_tensor, latitude, longitude)
    return ProfileResponse(**profile)


@router.post(
    "/profile",
    response_model=ProfileResponse,
    summary="Get Vertical Subsurface Temperature Profile (POST)",
    description="Returns predicted temperatures across 15 depth levels (0m to 1000m) via JSON request body."
)
def post_profile(payload: ProfileRequest):
    _validate_bounds(payload.latitude, payload.longitude)
    
    raw_seq = _generate_raw_surface_sequence(payload.latitude, payload.longitude)
    input_tensor = _preprocessor.prepare_input_tensor(raw_seq)
    
    engine = get_inference_engine()
    output_tensor = engine.predict(input_tensor)
    
    profile = _postprocessor.extract_point_profile(output_tensor, payload.latitude, payload.longitude)
    return ProfileResponse(**profile)


@router.get(
    "/slice",
    response_model=SliceResponse,
    summary="Get 2D Horizontal Depth Map Slice (GET)",
    description="Returns 101x241 grid of ocean temperatures at a chosen depth level."
)
def get_slice(
    depth_m: float = Query(0.0, description="Depth level in meters (0, 5, 10, ..., 1000)"),
    date: str = Query("latest", description="Target ISO date string (YYYY-MM-DD) or 'latest'")
):
    raw_seq = _generate_raw_surface_sequence()
    input_tensor = _preprocessor.prepare_input_tensor(raw_seq)
    
    engine = get_inference_engine()
    output_tensor = engine.predict(input_tensor)
    
    slice_data = _postprocessor.extract_depth_slice(output_tensor, depth_m)
    return SliceResponse(**slice_data)


@router.post(
    "/slice",
    response_model=SliceResponse,
    summary="Get 2D Horizontal Depth Map Slice (POST)",
    description="Returns 101x241 grid of ocean temperatures at a chosen depth level via JSON request body."
)
def post_slice(payload: SliceRequest):
    raw_seq = _generate_raw_surface_sequence()
    input_tensor = _preprocessor.prepare_input_tensor(raw_seq)
    
    engine = get_inference_engine()
    output_tensor = engine.predict(input_tensor)
    
    slice_data = _postprocessor.extract_depth_slice(output_tensor, payload.depth_m)
    return SliceResponse(**slice_data)


@router.get(
    "/d26",
    response_model=D26Response,
    summary="Get D26 Isotherm Depth (GET)",
    description="Returns exact depth (in meters) where temperature drops to 26°C for TCHP calculation."
)
def get_d26(
    latitude: float = Query(..., description="Latitude 5.0 to 30.0 °N"),
    longitude: float = Query(..., description="Longitude 45.0 to 105.0 °E")
):
    _validate_bounds(latitude, longitude)
    
    raw_seq = _generate_raw_surface_sequence(latitude, longitude)
    input_tensor = _preprocessor.prepare_input_tensor(raw_seq)
    
    engine = get_inference_engine()
    output_tensor = engine.predict(input_tensor)
    
    profile = _postprocessor.extract_point_profile(output_tensor, latitude, longitude)
    
    if profile["is_land"]:
        return D26Response(
            latitude=latitude,
            longitude=longitude,
            d26_depth_m=None,
            is_valid_thermocline=False,
            explanation="Land coordinate mass - D26 is undefined."
        )

    d26_depth, is_valid, explanation = calculate_d26(profile["depths_m"], profile["temperatures_c"])
    return D26Response(
        latitude=latitude,
        longitude=longitude,
        d26_depth_m=d26_depth,
        is_valid_thermocline=is_valid,
        explanation=explanation
    )


@router.post(
    "/d26",
    response_model=D26Response,
    summary="Get D26 Isotherm Depth (POST)",
    description="Returns exact depth (in meters) where temperature drops to 26°C via JSON request body."
)
def post_d26(payload: D26Request):
    _validate_bounds(payload.latitude, payload.longitude)
    
    raw_seq = _generate_raw_surface_sequence(payload.latitude, payload.longitude)
    input_tensor = _preprocessor.prepare_input_tensor(raw_seq)
    
    engine = get_inference_engine()
    output_tensor = engine.predict(input_tensor)
    
    profile = _postprocessor.extract_point_profile(output_tensor, payload.latitude, payload.longitude)
    
    if profile["is_land"]:
        return D26Response(
            latitude=payload.latitude,
            longitude=payload.longitude,
            d26_depth_m=None,
            is_valid_thermocline=False,
            explanation="Land coordinate mass - D26 is undefined."
        )

    d26_depth, is_valid, explanation = calculate_d26(profile["depths_m"], profile["temperatures_c"])
    return D26Response(
        latitude=payload.latitude,
        longitude=payload.longitude,
        d26_depth_m=d26_depth,
        is_valid_thermocline=is_valid,
        explanation=explanation
    )
