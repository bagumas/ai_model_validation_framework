import pickle
import numpy as np

class SklearnAdapter:
    def __init__(self, model_path: str):
        with open(model_path, "rb") as f:
            self.model = pickle.load(f)

    def predict(self, X):
        X = np.array(X)
        return self.model.predict(X)

    # Dummy generate for LLM interface compatibility (echoes prompt)
    def generate(self, prompt: str) -> str:
        return f"[MODEL-RESPONSE] {prompt[:200]}"
