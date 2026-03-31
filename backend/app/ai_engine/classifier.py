"""
StealthVault AI - Attack Classifier
Random Forest classifier for categorizing network attacks.
Classifies traffic into: Normal, DDoS, PortScan, BruteForce, Malware, SQLInjection, XSS.
"""

import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from app.models.alert import ClassificationResult, AttackType, NetworkPacket
from app.config import settings

CONFIDENCE_THRESHOLD = 0.65


class AttackClassifier:
    """
    Random Forest attack classifier.
    
    Trained on labeled network traffic data to distinguish between
    different types of network attacks.
    """

    ATTACK_LABELS = [
        AttackType.NORMAL,
        AttackType.DDOS,
        AttackType.PORT_SCAN,
        AttackType.BRUTE_FORCE,
        AttackType.MALWARE,
        AttackType.SQL_INJECTION,
        AttackType.XSS,
    ]

    def __init__(self):
        self.model: RandomForestClassifier | None = None
        self.scaler: StandardScaler | None = None
        self.label_encoder: LabelEncoder | None = None
        self.is_trained: bool = False
        self._model_path = os.path.join(settings.MODELS_DIR, "classifier_model.joblib")
        self._scaler_path = os.path.join(settings.MODELS_DIR, "classifier_scaler.joblib")
        self._encoder_path = os.path.join(settings.MODELS_DIR, "classifier_encoder.joblib")

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        """
        Train the attack classifier.
        
        Args:
            X: Feature vectors, shape (n_samples, n_features)
            y: Attack labels, shape (n_samples,) - string labels
        
        Returns:
            Training metrics dict
        """
        # Encode labels
        self.label_encoder = LabelEncoder()
        y_encoded = self.label_encoder.fit_transform(y)

        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Train Random Forest
        base_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced",
        )
        self.model = CalibratedClassifierCV(estimator=base_model, method='sigmoid', cv=3)
        self.model.fit(X_scaled, y_encoded)
        self.is_trained = True
        
        # We can't use base metrics directly for calibrated model easily, so approximate:
        base_model.fit(X_scaled, y_encoded)
        feature_importance = base_model.feature_importances_
        accuracy = self.model.score(X_scaled, y_encoded)

        self.save()

        return {
            "samples_trained": len(X),
            "classes": list(self.label_encoder.classes_),
            "accuracy": float(accuracy),
            "top_features": {
                f"feature_{i}": float(imp)
                for i, imp in enumerate(feature_importance)
                if imp > 0.05
            },
        }

    def rule_based_classify(self, packet: NetworkPacket) -> ClassificationResult:
        """
        🚀 REAL RULE-BASED CLASSIFICATION (Phase 4 Hardening)
        Deterministic mapping of common network attack signatures.
        """
        if packet.dst_port == 22:
            return ClassificationResult(
                attack_type=AttackType.BRUTE_FORCE,
                confidence=0.9,
                explanation="SSH Targeted Activity Detected (Port 22)"
            )
        elif packet.packet_size > 3000:
            return ClassificationResult(
                attack_type=AttackType.DDOS,
                confidence=0.85,
                explanation="Volumetric Spike (DDoS Signature)"
            )
        elif packet.ttl < 20:
            return ClassificationResult(
                attack_type=AttackType.SQL_INJECTION if packet.packet_size > 1500 else AttackType.XSS, # Generic Fallback 
                confidence=0.75,
                explanation="Suspicious TTL / Signature Deviation"
            )
        
        # Specific user requested logic for Spoofing (not in our Enum yet)
        if hasattr(AttackType, "SPOOFING") or packet.ttl < 20:
             return ClassificationResult(
                attack_type=AttackType.UNKNOWN,
                confidence=0.7,
                explanation="Network Spoofing Signature Detected (Low TTL)"
            )

        return ClassificationResult(
            attack_type=AttackType.NORMAL,
            confidence=0.1,
            explanation="Traffic aligned with normal protocols"
        )

    def predict(self, features: np.ndarray) -> ClassificationResult:
        """
        Classify a network packet.
        
        Args:
            features: Feature vector, shape (1, n_features)
        
        Returns:
            ClassificationResult with attack type and confidence
        """
        if not self.is_trained:
            return ClassificationResult(
                attack_type=AttackType.UNKNOWN,
                confidence=0.1,
                probabilities={},
            )

        # Scale input
        scaled = self.scaler.transform(features)

        # Get prediction and probabilities
        prediction = self.model.predict(scaled)[0]
        probas = self.model.predict_proba(scaled)[0]

        # Decode label
        label = self.label_encoder.inverse_transform([prediction])[0]

        # Map to AttackType enum (handle both enum values and string values)
        attack_type = AttackType.UNKNOWN
        for at in AttackType:
            if at.value == label or at.name == label:
                attack_type = at
                break

        # Build probability dict
        prob_dict = {}
        for i, cls in enumerate(self.label_encoder.classes_):
            for at in AttackType:
                if at.value == cls or at.name == cls:
                    prob_dict[at.value] = round(float(probas[i]), 4)
                    break

        # Confidence is the max probability
        confidence = float(np.max(probas))

        # Explicit Zero-Day / Anomaly mapping
        # If the highest probability class is still under the threshold, it is explicitly UNKNOWN.
        if confidence < CONFIDENCE_THRESHOLD:
            attack_type = AttackType.UNKNOWN

        return ClassificationResult(
            attack_type=attack_type,
            confidence=round(confidence, 4),
            probabilities=prob_dict,
        )

    def save(self):
        """Save model, scaler, and encoder to disk."""
        if self.model and self.scaler and self.label_encoder:
            joblib.dump(self.model, self._model_path)
            joblib.dump(self.scaler, self._scaler_path)
            joblib.dump(self.label_encoder, self._encoder_path)

    def load(self) -> bool:
        """Load model, scaler, and encoder from disk."""
        if all(os.path.exists(p) for p in [self._model_path, self._scaler_path, self._encoder_path]):
            self.model = joblib.load(self._model_path)
            self.scaler = joblib.load(self._scaler_path)
            self.label_encoder = joblib.load(self._encoder_path)
            self.is_trained = True
            return True
        return False


# Singleton
attack_classifier = AttackClassifier()
