"""
ML Model Manager
Handles loading and managing fraud detection models
"""
import os
from typing import Optional, Dict, Any
import joblib
import numpy as np
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class ModelManager:
    """Manages ML models for fraud detection"""
    
    def __init__(self):
        self.fraud_model = None
        self.anomaly_model = None
        self.feature_scaler = None
        self.models_loaded = False
        self._model_version = "1.0.0"
    
    async def load_models(self):
        """Load all ML models"""
        try:
            model_path = settings.MODEL_PATH
            
            # Check if models exist, otherwise create default ones
            if not os.path.exists(model_path):
                os.makedirs(model_path, exist_ok=True)
                logger.info("Models directory created, using default models")
                self._create_default_models()
            else:
                fraud_path = os.path.join(model_path, settings.FRAUD_MODEL_NAME)
                anomaly_path = os.path.join(model_path, settings.ANOMALY_MODEL_NAME)
                
                if os.path.exists(fraud_path):
                    self.fraud_model = joblib.load(fraud_path)
                    logger.info("Fraud detection model loaded")
                else:
                    self._create_default_fraud_model()
                
                if os.path.exists(anomaly_path):
                    self.anomaly_model = joblib.load(anomaly_path)
                    logger.info("Anomaly detection model loaded")
                else:
                    self._create_default_anomaly_model()
            
            self.models_loaded = True
            
        except Exception as e:
            logger.error("Failed to load models", error=str(e))
            # Create default models as fallback
            self._create_default_models()
            self.models_loaded = True
    
    def _create_default_models(self):
        """Create default models for initial setup"""
        self._create_default_fraud_model()
        self._create_default_anomaly_model()
    
    def _create_default_fraud_model(self):
        """Create a default fraud detection model"""
        from sklearn.ensemble import RandomForestClassifier
        
        # Create a simple default model
        self.fraud_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        # Train on dummy data for initialization
        # In production, this would be trained on historical data
        X_dummy = np.random.rand(1000, 15)
        y_dummy = (np.random.rand(1000) > 0.95).astype(int)  # 5% fraud rate
        self.fraud_model.fit(X_dummy, y_dummy)
        
        logger.info("Default fraud model created")
    
    def _create_default_anomaly_model(self):
        """Create a default anomaly detection model"""
        from sklearn.ensemble import IsolationForest
        
        self.anomaly_model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42
        )
        
        # Train on dummy data
        X_dummy = np.random.rand(1000, 10)
        self.anomaly_model.fit(X_dummy)
        
        logger.info("Default anomaly model created")
    
    @property
    def model_version(self) -> str:
        return self._model_version
    
    def predict_fraud(self, features: np.ndarray) -> np.ndarray:
        """Predict fraud probability"""
        if self.fraud_model is None:
            raise RuntimeError("Fraud model not loaded")
        
        try:
            probabilities = self.fraud_model.predict_proba(features)
            return probabilities[:, 1]  # Return probability of fraud class
        except Exception as e:
            logger.error("Fraud prediction failed", error=str(e))
            return np.array([0.5])  # Return neutral score on error
    
    def detect_anomaly(self, features: np.ndarray) -> np.ndarray:
        """Detect anomalies (returns -1 for anomaly, 1 for normal)"""
        if self.anomaly_model is None:
            raise RuntimeError("Anomaly model not loaded")
        
        try:
            scores = self.anomaly_model.decision_function(features)
            # Normalize to 0-1 range (lower = more anomalous)
            normalized = (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
            return 1 - normalized  # Invert so higher = more suspicious
        except Exception as e:
            logger.error("Anomaly detection failed", error=str(e))
            return np.array([0.0])
    
    async def retrain_fraud_model(self, X: np.ndarray, y: np.ndarray):
        """Retrain fraud model with new data"""
        from sklearn.ensemble import RandomForestClassifier
        
        logger.info("Retraining fraud model", samples=len(y))
        
        self.fraud_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            class_weight='balanced',
            random_state=42
        )
        self.fraud_model.fit(X, y)
        
        # Save updated model
        model_path = os.path.join(settings.MODEL_PATH, settings.FRAUD_MODEL_NAME)
        joblib.dump(self.fraud_model, model_path)
        
        logger.info("Fraud model retrained and saved")
    
    async def retrain_anomaly_model(self, X: np.ndarray):
        """Retrain anomaly detection model"""
        from sklearn.ensemble import IsolationForest
        
        logger.info("Retraining anomaly model", samples=len(X))
        
        self.anomaly_model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42
        )
        self.anomaly_model.fit(X)
        
        # Save updated model
        model_path = os.path.join(settings.MODEL_PATH, settings.ANOMALY_MODEL_NAME)
        joblib.dump(self.anomaly_model, model_path)
        
        logger.info("Anomaly model retrained and saved")


# Global model manager instance
model_manager = ModelManager()

