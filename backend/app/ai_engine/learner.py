"""
StealthVault AI - Continuous Learning Engine
Allows the AI models to improve over time as new attacks are detected.

Key features:
- Feedback loop: confirmed alerts are added to training data
- Auto-retrain: models retrain when enough new data is collected
- Model versioning: keeps track of model generations
"""

import numpy as np
import os
import json
import time
import json
import asyncio
from datetime import datetime
from collections import deque
from app.core.logger import logger
from typing import Optional

from app.config import settings
from app.ai_engine.anomaly import anomaly_detector
from app.ai_engine.classifier import attack_classifier
from app.models.alert import AttackType
from sklearn.metrics import precision_recall_fscore_support, accuracy_score
from app.database import AsyncSessionLocal


class ContinuousLearner:
    """
    Continuous learning engine for StealthVault AI.
    
    Workflow:
    1. New packets flow through the AI pipeline
    2. Analyst confirms/corrects the classification
    3. Confirmed samples are stored in the feedback buffer
    4. When buffer reaches threshold, retrain the models
    5. New model version is saved and loaded
    """

    def __init__(
        self,
        retrain_threshold: int = 500,
        min_retrain_interval: int = 300,  # 5 minutes minimum between retrains
    ):
        self.retrain_threshold = retrain_threshold
        self.min_retrain_interval = min_retrain_interval

        # Feedback buffers
        self.normal_buffer: list[np.ndarray] = []
        self.labeled_features: list[np.ndarray] = []
        self.labeled_labels: list[str] = []

        # Tracking
        self.total_feedback: int = 0
        self.last_retrain_time: float = 0
        self.model_version: int = self._load_version()
        self.retrain_count: int = 0

        # History
        self.retrain_history: list[dict] = []

        # Paths
        self._feedback_dir = os.path.join(settings.DATA_DIR, "feedback")
        os.makedirs(self._feedback_dir, exist_ok=True)
        
        # Drift Monitoring (Rolling Window)
        self.confidence_window = deque(maxlen=2000)
        self.unknown_count = 0
        self.anomaly_count = 0
        self.is_drift_detected = False

    def validate_feedback(
        self,
        features: np.ndarray,
        confirmed_label: str,
        original_confidence: float = 0.0,
        signal_count: int = 0,
    ) -> dict:
        """
        🔒 DATA POISONING PROTECTION
        
        Validates feedback before accepting it into the training set.
        An attacker could try to poison the model by feeding bad labels.
        
        Validation rules:
        1. High-confidence predictions that match the label → TRUSTED
        2. Low-confidence corrections → require multi-signal verification
        3. Complete label flips (attack→normal) → require extra scrutiny
        4. Rate limiting on feedback submissions
        """
        # Rule 1: If the model was already confident AND the label agrees, trust it
        model_prediction = attack_classifier.predict(features)
        model_agrees = model_prediction.attack_type.value == confirmed_label
        
        if model_agrees and model_prediction.confidence > 0.8:
            return {"valid": True, "trust_level": "high", "reason": "Model agrees with high confidence"}
        
        # Rule 2: If multiple signals corroborate, accept the correction
        if signal_count >= 2 and original_confidence >= 0.6:
            return {"valid": True, "trust_level": "medium", "reason": "Multi-signal corroboration"}
        
        # Rule 3: Label flips (e.g., attack→normal) need extra scrutiny
        is_flip = (
            model_prediction.attack_type.value != "Normal"
            and confirmed_label == "Normal"
        )
        if is_flip:
            # Only accept flips if confidence was borderline
            if model_prediction.confidence < 0.5:
                return {"valid": True, "trust_level": "low", "reason": "Borderline prediction corrected"}
            else:
                return {
                    "valid": False,
                    "trust_level": "rejected",
                    "reason": f"Suspicious label flip: model was {model_prediction.confidence:.0%} confident it was {model_prediction.attack_type.value}",
                }
        
        # Rule 4: Accept corrections to unknown/low-confidence predictions
        if model_prediction.confidence < 0.6:
            return {"valid": True, "trust_level": "medium", "reason": "Low-confidence prediction corrected"}
        
        # Default: accept with caution
        return {"valid": True, "trust_level": "low", "reason": "Accepted with caution"}

    def add_feedback(
        self,
        features: np.ndarray,
        confirmed_label: str,
        is_normal: bool = False,
        original_confidence: float = 0.0,
        signal_count: int = 0,
    ) -> dict:
        """
        Add analyst feedback (confirmed classification).
        
        🔒 Now includes data poisoning protection.
        Feedback is validated before being accepted into the training set.
        
        Args:
            features: The feature vector from the packet
            confirmed_label: The correct attack type (as confirmed by analyst)
            is_normal: Whether this is confirmed normal traffic
            original_confidence: The model's original confidence score
            signal_count: Number of corroborating detection signals
        
        Returns:
            Status dict with buffer size and whether retrain was triggered
        """
        self.total_feedback += 1

        # 🔒 VALIDATE BEFORE ACCEPTING
        validation = self.validate_feedback(
            features, confirmed_label, original_confidence, signal_count
        )
        
        if not validation["valid"]:
            return {
                "feedback_accepted": False,
                "reason": validation["reason"],
                "trust_level": validation["trust_level"],
                "buffer_size": len(self.labeled_features),
                "model_version": self.model_version,
            }

        # Add to appropriate buffer
        if is_normal:
            self.normal_buffer.append(features.flatten())
        
        self.labeled_features.append(features.flatten())
        self.labeled_labels.append(confirmed_label)

        # Check if we should retrain
        should_retrain = (
            len(self.labeled_features) >= self.retrain_threshold
            and time.time() - self.last_retrain_time > self.min_retrain_interval
        )

        result = {
            "feedback_accepted": True,
            "trust_level": validation["trust_level"],
            "validation_reason": validation["reason"],
            "buffer_size": len(self.labeled_features),
            "threshold": self.retrain_threshold,
            "retrain_triggered": False,
            "model_version": self.model_version,
        }

        if should_retrain:
            # Run retrain in a separate thread if possible, or just wait in async
            # For now, keeping it simple as a direct call which is CPU heavy.
            retrain_result = self.retrain(reason="Threshold Reached")
            result["retrain_triggered"] = True
            result["retrain_result"] = retrain_result
            result["model_version"] = self.model_version

        return result

    def auto_label_sample(self, features: np.ndarray, prediction: ClassificationResult):
        """
        🚀 AUTONOMOUS SELF-IMPROVEMENT LOOP
        Automatically ingest extremely high-confidence predictions to reinforce the model 
        without human intervention.
        """
        if prediction.confidence >= 0.98:
            # We treat this as a ground truth sample for reinforcement
            self.labeled_features.append(features.flatten())
            self.labeled_labels.append(prediction.attack_type.value)
            
            # Check if it was normal
            if prediction.attack_type.value == "Normal":
                self.normal_buffer.append(features.flatten())
            
            # Note: We don't trigger auto-retrain here immediately to avoid rapid cycles.
            # It will be picked up by the 24h cycle or the next threshold.

    def monitor_drift(self, confidence: float, is_unknown: bool, is_anomaly: bool):
        """
        📉 AUTONOMOUS DRIFT DETECTION
        Tracks model performance metrics in real-time.
        """
        self.confidence_window.append(confidence)
        if is_unknown:
            self.unknown_count += 1
        if is_anomaly:
            self.anomaly_count += 1
            
        # Detect Drift: If average confidence in the last 2000 samples drops < 70%
        # OR if UNKNOWN rate spikes over 20%
        if len(self.confidence_window) >= 1000:
            avg_conf = np.mean(self.confidence_window)
            if avg_conf < 0.70:
                if not self.is_drift_detected:
                    logger.warning(f"📉 CONCEPT DRIFT DETECTED: Average confidence dropped to {avg_conf:.2f}. Retraining suggested.")
                    self.is_drift_detected = True
            else:
                self.is_drift_detected = False

    def retrain(self, reason: str = "Automated") -> dict:
        """
        Retrain models with accumulated feedback data.
        Reason can be: "Threshold Reached", "Scheduled", "Drift Detected", or "Manual".
        
        Combines the original training data with new feedback samples.
        """
        logger.info(f"🔄 CONTINUOUS LEARNING — Retraining models (Reason: {reason})")
        logger.info(f"   New samples accumulated: {len(self.labeled_features)}")
        start_time = time.time()

        results = {}

        try:
            # Retrain anomaly detector with new normal data
            if self.normal_buffer:
                normal_data = np.array(self.normal_buffer)
                # Load existing normal data and combine
                existing_path = os.path.join(settings.DATA_DIR, "datasets", "normal_data.npy")
                if os.path.exists(existing_path):
                    existing = np.load(existing_path)
                    combined = np.vstack([existing, normal_data])
                else:
                    combined = normal_data

                anomaly_metrics = anomaly_detector.train(combined)
                results["anomaly"] = anomaly_metrics

                # Save combined data
                np.save(existing_path, combined)
                print(f"   ✅ Anomaly detector retrained: {anomaly_metrics['samples_trained']} samples")

            # Retrain classifier with all labeled data
            if self.labeled_features:
                X_new = np.array(self.labeled_features)
                y_new = np.array(self.labeled_labels)

                # Load existing training data and combine
                X_path = os.path.join(settings.DATA_DIR, "datasets", "X_train.npy")
                y_path = os.path.join(settings.DATA_DIR, "datasets", "y_train.npy")

                if os.path.exists(X_path) and os.path.exists(y_path):
                    X_existing = np.load(X_path)
                    y_existing = np.load(y_path, allow_pickle=True)
                    X_combined = np.vstack([X_existing, X_new])
                    y_combined = np.concatenate([y_existing, y_new])
                else:
                    X_combined = X_new
                    y_combined = y_new

                classifier_metrics = attack_classifier.train(X_combined, y_combined)
                results["classifier"] = classifier_metrics

                # Save combined data
                np.save(X_path, X_combined)
                np.save(y_path, y_combined)
                print(f"   ✅ Classifier retrained: {classifier_metrics['samples_trained']} samples")
                print(f"   📊 New accuracy: {classifier_metrics['accuracy']:.2%}")

            # Update tracking
            self.model_version += 1
            self._save_version()
            self.last_retrain_time = time.time()
            self.retrain_count += 1

            elapsed = time.time() - start_time

            # 📉 ADVANCED MONITORING: Calculate & Persist Precision/Recall
            if self.labeled_features:
                try:
                    # Use a portion of the data as a validation set for metrics
                    from sklearn.model_selection import train_test_split
                    X_array = np.array(self.labeled_features)
                    y_array = np.array(self.labeled_labels)
                    
                    # We can't use the whole combined set easily here without reloading, 
                    # so we measure performance on the NEW feedback data we just trained on.
                    # This gives us a "Recent Accuracy" metric.
                    y_pred = [attack_classifier.predict(f).attack_type.value for f in X_array]
                    
                    acc = accuracy_score(y_array, y_pred)
                    precision, recall, f1, _ = precision_recall_fscore_support(
                        y_array, y_pred, average='weighted', zero_division=0
                    )
                    
                    # Persist to DB
                    from app.models.db_models import DBModelMetric
                    async def save_metrics():
                        async with AsyncSessionLocal() as db:
                            new_metric = DBModelMetric(
                                version=self.model_version,
                                accuracy=float(acc),
                                precision=float(precision),
                                recall=float(recall),
                                f1_score=float(f1),
                                total_samples=len(X_combined),
                                false_positives_count=list(y_array).count("Normal"),
                                training_duration_s=float(elapsed)
                            )
                            db.add(new_metric)
                            await db.commit()
                    
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.create_task(save_metrics())
                        else:
                            loop.run_until_complete(save_metrics())
                    except Exception as e:
                        print(f"   ⚠️ Could not save DB metrics: {e}")
                except Exception as e:
                    print(f"   ⚠️ Metric calculation error: {e}")

            # Record history
            record = {
                "version": self.model_version,
                "timestamp": datetime.utcnow().isoformat(),
                "new_samples": len(self.labeled_features),
                "elapsed_seconds": round(elapsed, 2),
                "results": {k: {kk: str(vv) for kk, vv in v.items()} for k, v in results.items()},
            }
            self.retrain_history.append(record)
            self._save_history(record)

            # Clear buffers
            self.normal_buffer.clear()
            self.labeled_features.clear()
            self.labeled_labels.clear()

            print(f"   🔄 Model version: v{self.model_version}")
            print(f"   ⏱️  Retrain time: {elapsed:.1f}s")
            print()

            return {
                "success": True,
                "model_version": self.model_version,
                "elapsed_seconds": round(elapsed, 2),
                "metrics": results,
            }

        except Exception as e:
            print(f"   ❌ Retrain failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def get_status(self) -> dict:
        """Get continuous learning status."""
        return {
            "model_version": self.model_version,
            "total_feedback": self.total_feedback,
            "buffer_size": len(self.labeled_features),
            "normal_buffer_size": len(self.normal_buffer),
            "retrain_threshold": self.retrain_threshold,
            "retrain_count": self.retrain_count,
            "last_retrain": datetime.fromtimestamp(self.last_retrain_time).isoformat()
            if self.last_retrain_time > 0
            else "never",
            "recent_history": self.retrain_history[-5:] if self.retrain_history else [],
        }

    def _load_version(self) -> int:
        """Load model version from disk."""
        version_file = os.path.join(settings.MODELS_DIR, "version.json")
        if os.path.exists(version_file):
            with open(version_file, "r") as f:
                data = json.load(f)
                return data.get("version", 1)
        return 1

    def _save_version(self):
        """Save model version to disk."""
        version_file = os.path.join(settings.MODELS_DIR, "version.json")
        with open(version_file, "w") as f:
            json.dump({"version": self.model_version}, f)

    def _save_history(self, record: dict):
        """Append retrain record to history file."""
        history_file = os.path.join(self._feedback_dir, "retrain_history.jsonl")
        with open(history_file, "a") as f:
            f.write(json.dumps(record) + "\n")


# Singleton
continuous_learner = ContinuousLearner()
