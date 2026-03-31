"""
Train the deal risk XGBoost classifier.
Logs parameters and metrics to MLflow and registers the model.

Usage (from project root):
    python -m models.deal_risk.train
"""

import os
import mlflow
import mlflow.xgboost
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score,
    f1_score, classification_report
)
from xgboost import XGBClassifier

from models.deal_risk.features import load_features

load_dotenv()

EXPERIMENT_NAME = "deal_risk"
MODEL_NAME      = "deal_risk_model"
TEST_SIZE       = 0.20
RANDOM_STATE    = 42

XGB_PARAMS = {
    "n_estimators":     200,
    "max_depth":        4,
    "learning_rate":    0.05,
    "subsample":        0.8,
    "colsample_bytree": 0.8,
    "use_label_encoder": False,
    "eval_metric":      "logloss",
    "random_state":     RANDOM_STATE,
}


def train():
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    mlflow.set_experiment(EXPERIMENT_NAME)

    X, y, feature_cols = load_features()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE
    )

    # Compute class weight from training data to handle imbalance
    neg, pos = (y_train == 0).sum(), (y_train == 1).sum()
    scale_pos_weight = neg / pos

    with mlflow.start_run():
        model = XGBClassifier(**XGB_PARAMS, scale_pos_weight=scale_pos_weight)
        model.fit(X_train, y_train)

        y_pred  = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        metrics = {
            "roc_auc":   roc_auc_score(y_test, y_proba),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall":    recall_score(y_test, y_pred, zero_division=0),
            "f1":        f1_score(y_test, y_pred, zero_division=0),
        }

        mlflow.log_params(XGB_PARAMS)
        mlflow.log_metrics(metrics)
        mlflow.log_dict(
            dict(zip(feature_cols, model.feature_importances_.tolist())),
            "feature_importances.json"
        )

        mlflow.xgboost.log_model(
            model,
            artifact_path="model",
            registered_model_name=MODEL_NAME,
        )

        print(f"\nDeal Risk Model — {EXPERIMENT_NAME}")
        print(f"  Train rows: {len(X_train)}  Test rows: {len(X_test)}")
        print(f"  ROC-AUC:   {metrics['roc_auc']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall:    {metrics['recall']:.4f}")
        print(f"  F1:        {metrics['f1']:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=["won", "at_risk"]))
        print("\nFeature Importances:")
        for col, imp in zip(feature_cols, model.feature_importances_):
            print(f"  {col:<30} {imp:.4f}")

        return metrics


if __name__ == "__main__":
    metrics = train()
    if metrics["roc_auc"] < 0.70:
        print(f"\nWARNING: ROC-AUC {metrics['roc_auc']:.4f} is below the 0.70 target.")
