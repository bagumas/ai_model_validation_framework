from . import Evaluator, EvalResult, register
from sklearn.metrics import f1_score

@register
class F1Evaluator(Evaluator):
    name = "f1"
    def run(self, model, data) -> EvalResult:
        y_true = data["y"]
        y_pred = model.predict(data["X"])
        score = f1_score(y_true, y_pred, average="macro")
        return EvalResult(score=float(score))
