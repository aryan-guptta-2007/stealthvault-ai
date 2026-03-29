"""
StealthVault AI - Anomaly Detection Engine
Uses Isolation Forest for detecting unknown/zero-day attacks.
Anomalies are packets that deviate significantly from normal traffic patterns.
"""

import numpy as np
import os
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from app.models.alert import AnomalyResult
from app.config import settings


class AnomalyDetector:
    """
    Isolation Forest-based anomaly detector.
    
    How it works:
    1. Trained on 'normal' network traffic data
    2. Learns the pattern of normal behavior
    3. Flags anything that deviates as anomalous
    4. Can detect zero-day attacks it has never seen before
    """

    def __init__(self):
        self.model: IsolationForest | None = None
        self.scaler: StandardScaler | None = None
        self.is_trained: bool = False
        self._model_path = os.path.join(settings.MODELS_DIR, "anomaly_model.joblib")
        self._scaler_path = os.path.join(settings.MODELS_DIR, "anomaly_scaler.joblib")

    def train(self, normal_data: np.ndarray) -> dict:
        """
        Train the anomaly detector on normal traffic.
        
        Args:
            normal_data: numpy array of shape (n_samples, n_features)
                         containing NORMAL traffic feature vectors
        
        Returns:
            Training metrics dict
        """
        # Scale features
        self.scaler = StandardScaler()
        scaled_data = self.scaler.fit_transform(normal_data)

        # Train Isolation Forest
        self.model = IsolationForest(
            n_estimators=200,
            contamination=settings.ANOMALY_CONTAMINATION,
            max_samples="auto",
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(scaled_data)
        self.is_trained = True

        # Compute training metrics
        predictions = self.model.predict(scaled_data)
        anomaly_count = int(np.sum(predictions == -1))
        scores = self.model.decision_function(scaled_data)

        self.save()

        return {
            "samples_trained": len(normal_data),
            "anomalies_in_training": anomaly_count,
            "anomaly_rate": anomaly_count / len(normal_data),
            "avg_score": float(np.mean(scores)),
            "std_score": float(np.std(scores)),
        }

    def predict(self, features: np.ndarray) -> AnomalyResult:
        """
        Predict whether a packet is anomalous.
        
        Args:
            features: numpy array of shape (1, n_features)
        
        Returns:
            AnomalyResult with is_anomaly flag and scores
        """
        if not self.is_trained:
            # If not trained, return a moderate anomaly score
            return AnomalyResult(
                is_anomaly=False,
                anomaly_score=0.3,
                confidence=0.1,
            )

        # Scale the input
        scaled = self.scaler.transform(features)

        # Get prediction (-1 = anomaly, 1 = normal)
        prediction = self.model.predict(scaled)[0]
        
        # Get anomaly score (more negative = more anomalous)
        raw_score = self.model.decision_function(scaled)[0]
        
        # Convert to 0-1 range (higher = more anomalous)
        # Isolation Forest scores: negative = anomaly, positive = normal
        anomaly_score = max(0.0, min(1.0, 0.5 - raw_score))
        
        # Confidence based on how extreme the score is
        confidence = min(1.0, abs(raw_score) * 2)

        is_anomaly = prediction == -1 or anomaly_score > settings.ANOMALY_THRESHOLD

        return AnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_score=round(anomaly_score, 4),
            confidence=round(confidence, 4),
        )

    def save(self):
        """Save model and scaler to disk."""
        if self.model and self.scaler:
            joblib.dump(self.model, self._model_path)
            joblib.dump(self.scaler, self._scaler_path)

    def load(self) -> bool:
        """Load model and scaler from disk."""
        if os.path.exists(self._model_path) and os.path.exists(self._scaler_path):
            self.model = joblib.load(self._model_path)
            self.scaler = joblib.load(self._scaler_path)
            self.is_trained = True
            return True
        return False


# Singleton
anomaly_detector = AnomalyDetector()
