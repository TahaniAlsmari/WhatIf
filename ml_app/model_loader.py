import joblib
import shap


model = joblib.load(
    "ml_app/models/catboost_model.pkl"
)


decision_encoder = joblib.load(
    "ml_app/models/decision_encoder.pkl"
)


explainer = shap.TreeExplainer(model)

print(model.classes_)
