"""
Monitoring and Model Management Endpoints
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status

from app.ml.model_manager import model_manager

router = APIRouter()


@router.get("/model-status", response_model=dict)
async def get_model_status():
    """
    Get status of loaded ML models.
    """
    return {
        "models_loaded": model_manager.models_loaded,
        "model_version": model_manager.model_version,
        "fraud_model_loaded": model_manager.fraud_model is not None,
        "anomaly_model_loaded": model_manager.anomaly_model is not None
    }


@router.post("/reload-models", response_model=dict)
async def reload_models():
    """
    Reload ML models from disk.
    """
    try:
        await model_manager.load_models()
        return {
            "success": True,
            "message": "Models reloaded successfully",
            "model_version": model_manager.model_version
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload models: {str(e)}"
        )


@router.get("/metrics", response_model=dict)
async def get_detection_metrics():
    """
    Get fraud detection performance metrics.
    """
    # In production, these would be calculated from actual detection history
    return {
        "total_analyzed_today": 0,
        "suspicious_detected": 0,
        "alerts_generated": 0,
        "false_positive_rate": 0.0,
        "detection_rate": 0.0,
        "average_processing_time_ms": 0.0
    }

