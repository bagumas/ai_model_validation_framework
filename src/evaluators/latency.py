from . import Evaluator, EvalResult, register
import time
import numpy as np

@register
class LatencyEvaluator(Evaluator):
    name = "latency_p95"
    def run(self, model, data) -> EvalResult:
        X = data["X"]
        times = []
        n = min(len(X), 200)
        for i in range(n):
            t0 = time.time()
            _ = model.predict([X[i]])
            times.append(time.time() - t0)
        p95 = float(np.percentile(times, 95))
        return EvalResult(p95=p95)
