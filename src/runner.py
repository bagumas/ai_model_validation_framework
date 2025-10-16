import argparse, os, sys, yaml, mlflow, pandas as pd, numpy as np
from evaluators import REGISTRY
import evaluators.performance
import evaluators.latency
import evaluators.pii
# import evaluators.jailbreak  # only if you use it
from models.sklearn_adapter import SklearnAdapter
# Auto-load all evaluators so they self-register into REGISTRY
import pkgutil, importlib, evaluators
for _, modname, _ in pkgutil.iter_modules(evaluators.__path__):
    importlib.import_module(f"evaluators.{modname}")

def load_tabular_dataset(path):
    df = pd.read_csv(path)
    # Expect last column to be target
    X = df.iloc[:, :-1].values
    y = df.iloc[:, -1].values
    return {"X": X, "y": y}

def load_prompts(path):
    import json
    with open(path, "r") as f:
        return json.load(f)

def compare(value: float, rule: str) -> bool:
    op, thr = rule.split()[0], float(rule.split()[1])
    if op == ">=": return value >= thr
    if op == "<=": return value <= thr
    if op == "==": return value == thr
    raise ValueError(f"Unsupported operator in rule: {rule}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--data-path", required=True, help="CSV with features + target (last column)")
    parser.add_argument("--suite", default="f1,latency_p95,pii")
    parser.add_argument("--policy", default="policy.yaml")
    parser.add_argument("--prompts-path", default="data/redteam_prompts.json")
    args = parser.parse_args()

    mlflow.set_experiment("model-validation")
    with mlflow.start_run():
        model = SklearnAdapter(args.model_path)
        base_data = load_tabular_dataset(args.data_path)
        # Extend with optional text/prompts for specific evaluators
        try:
            prompts = load_prompts(args.prompts_path)
        except Exception:
            prompts = []
        base_data["prompts"] = prompts
        base_data["texts"] = [f"Example output {i}" for i in range(10)]  # no PII by default

        suite = [s.strip() for s in args.suite.split(",") if s.strip()]
        results = {}

        for eval_name in suite:
            if eval_name not in REGISTRY:
                raise SystemExit(f"Unknown evaluator: {eval_name}")
            res = REGISTRY[eval_name].run(model, base_data)
            for k, v in res.items():
                key = f"{eval_name}.{k}"
                results[key] = float(v)
                mlflow.log_metric(key, float(v))

        # Policy gating
        policy = yaml.safe_load(open(args.policy))["acceptance"]
        failures = [k for k, rule in policy.items() if not compare(results.get(k, 0.0), rule)]

        # Save a simple text report
        report_lines = ["Validation Results:"]
        for k in sorted(results):
            report_lines.append(f"- {k}: {results[k]:.6f}")
        if failures:
            report_lines.append("\nFAILED GATES: " + ", ".join(failures))
        report = "\n".join(report_lines)
        mlflow.log_text(report, "report.txt")
        print(report)

        if failures:
            sys.exit(1)
        print("Validation passed ✅")

if __name__ == "__main__":
    main()
