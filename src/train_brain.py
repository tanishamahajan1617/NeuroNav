import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

# ─── 1. ROAD TYPE MAPPING ─────────────────────────────────
ROAD_TYPE_RISK = {
    "motorway":       0.2,
    "trunk":          0.3,
    "primary":        0.4,
    "secondary":      0.45,
    "tertiary":       0.5,
    "residential":    0.55,
    "unclassified":   0.6,
    "service":        0.65,
    "living_street":  0.4,
    "motorway_link":  0.35,
    "trunk_link":     0.4,
    "primary_link":   0.45,
    "unknown":        0.5,
}


# ─── 2. SYNTHETIC DATA GENERATION ─────────────────────────
def generate_synthetic_data(n_samples: int = 5000) -> pd.DataFrame:
    np.random.seed(42)
    road_types = list(ROAD_TYPE_RISK.keys())

    data = []
    for _ in range(n_samples):
        road_type   = np.random.choice(road_types)
        speed_limit = np.random.choice([20, 30, 40, 50, 60, 80, 100, 120])
        num_lanes   = np.random.randint(1, 5)
        road_length = np.random.uniform(10, 2000)
        is_junction = np.random.randint(0, 2)
        fatigue     = np.random.uniform(0.0, 1.0)
        context     = np.random.uniform(0.0, 1.0)

        base_risk    = ROAD_TYPE_RISK[road_type]
        speed_risk   = np.interp(speed_limit, [20, 120], [0.0, 1.0])
        lane_risk    = np.interp(num_lanes,   [1, 4],    [0.1, 0.4])
        length_risk  = np.interp(road_length, [10, 2000],[0.0, 0.3])
        junction_risk= 0.6 if is_junction else 0.0

        risk = (
            0.20 * base_risk     +
            0.25 * speed_risk    +
            0.10 * lane_risk     +
            0.05 * length_risk   +
            0.15 * junction_risk +
            0.15 * fatigue       +
            0.10 * context
        )

        risk += np.random.normal(0, 0.02)
        risk  = float(np.clip(risk, 0.0, 1.0))

        data.append({
            "road_type":   road_type,
            "speed_limit": speed_limit,
            "num_lanes":   num_lanes,
            "road_length": road_length,
            "is_junction": is_junction,
            "fatigue":     fatigue,
            "context":     context,
            "risk":        risk
        })

    return pd.DataFrame(data)


# ─── 3. TRAIN MODEL ───────────────────────────────────────
def train_model(save_path: str    = "risk_model.pkl",
                encoder_path: str = "road_type_encoder.pkl") -> XGBRegressor:

    print("Generating synthetic training data...")
    df = generate_synthetic_data(n_samples=5000)

    le = LabelEncoder()
    df["road_type_enc"] = le.fit_transform(df["road_type"])

    features = ["road_type_enc", "speed_limit", "num_lanes",
                "road_length",   "is_junction", "fatigue", "context"]
    X = df[features]
    y = df["risk"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = XGBRegressor(
        n_estimators    = 300,
        max_depth       = 5,
        learning_rate   = 0.05,
        subsample       = 0.8,
        colsample_bytree= 0.8,
        random_state    = 42,
        n_jobs          = -1
    )

    print("Training XGBoost model...")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(f"\n✅ Model Performance:")
    print(f"   MAE : {mean_absolute_error(y_test, y_pred):.4f}")
    print(f"   R²  : {r2_score(y_test, y_pred):.4f}")

    joblib.dump(model, save_path)
    joblib.dump(le, encoder_path)
    print(f"\n💾 Saved → {save_path}, {encoder_path}")

    return model


# ─── 4. LOAD MODEL ────────────────────────────────────────
def load_model(save_path: str    = "risk_model.pkl",
               encoder_path: str = "road_type_encoder.pkl"):
    model   = joblib.load(save_path)
    encoder = joblib.load(encoder_path)
    return model, encoder


# ─── 5. PREDICT SINGLE SEGMENT ────────────────────────────
def predict_risk(road_type:   str,
                 speed_limit: int,
                 num_lanes:   int,
                 road_length: float,
                 is_junction: int,
                 fatigue:     float,
                 context:     float,
                 model=None,
                 encoder=None) -> float:

    if model is None or encoder is None:
        model, encoder = load_model()

    if road_type not in encoder.classes_:
        road_type = "unknown"

    road_type_enc = encoder.transform([road_type])[0]

    features = np.array([[road_type_enc, speed_limit, num_lanes,
                          road_length,   is_junction, fatigue, context]])

    risk = model.predict(features)[0]
    return round(float(np.clip(risk, 0.0, 1.0)), 4)


# ─── 6. PREDICT BATCH (ALL ROUTE SEGMENTS) ────────────────
def predict_batch(segments: list[dict],
                  fatigue:  float,
                  context:  float,
                  model=None,
                  encoder=None) -> list[float]:

    if model is None or encoder is None:
        model, encoder = load_model()

    rows = []
    for seg in segments:
        road_type = seg.get("highway", "unknown")
        if isinstance(road_type, list):
            road_type = road_type[0]
        if road_type not in encoder.classes_:
            road_type = "unknown"

        rows.append({
            "road_type_enc": encoder.transform([road_type])[0],
            "speed_limit":   int(seg.get("maxspeed", 50)),
            "num_lanes":     int(seg.get("lanes", 1)),
            "road_length":   float(seg.get("length", 100)),
            "is_junction":   int(seg.get("junction", 0)),
            "fatigue":       fatigue,
            "context":       context,
        })

    X    = pd.DataFrame(rows)
    risks= model.predict(X)
    return [round(float(np.clip(r, 0.0, 1.0)), 4) for r in risks]


# ─── 7. ENTRY POINT ───────────────────────────────────────
if __name__ == "__main__":
    if not os.path.exists("risk_model.pkl"):
        train_model()
    else:
        print("Model already exists. Loading...")

    model, encoder = load_model()

    risk = predict_risk(
        road_type   = "residential",
        speed_limit = 50,
        num_lanes   = 2,
        road_length = 300.0,
        is_junction = 1,
        fatigue     = 0.6,
        context     = 0.4,
        model       = model,
        encoder     = encoder
    )
    print(f"\nTest Prediction → Risk Score: {risk}")