REGISTRY = {}

class EvalResult(dict):
    """Simple dict-like container for metrics from an evaluator."""
    pass

class Evaluator:
    name = "base"
    def run(self, model, data) -> EvalResult:
        raise NotImplementedError

def register(cls):
    REGISTRY[cls.name] = cls()
    return cls
