# AI-Powered Model Validation Framework (Starter Kit)

This is a minimal, **extensible** framework to validate ML/LLM models with **policy-driven gates** suitable for CI/CD (Jenkins/GitHub Actions). It includes:
- Pluggable **evaluators** (performance, latency, jailbreak, PII leakage)
- A simple **policy.yaml** converting metrics to **pass/fail**
- **MLflow** logging of metrics & artifacts
- A sample **scikit-learn** model and dataset for an end-to-end run

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# (Optional) Train a tiny sample model and export data
python scripts/train_sample_model.py

# Run validation (loads model + datasets, executes evaluators, enforces policy gates)
python src/runner.py --model-path models/iris_logreg.pkl --data-path data/iris.csv --suite f1,latency_p95,pii,jailbreak --policy policy.yaml
```

If a gate fails, the script exits non-zero (perfect for CI). Metrics and a text report are logged to **MLflow**.

## Adding an evaluator
1. Create a new class in `src/evaluators/your_eval.py` and register it in the REGISTRY.
2. Emit a dict of metrics (e.g., `{ "score": 0.93 }`).
3. Reference it in `--suite` and add thresholds in `policy.yaml`.

## Security & privacy
- No secrets in code—use env vars / Vault.
- Use synthetic/redacted data for tests.
- For LLMs, integrate a real provider behind a simple adapter with **scoped**, **time-limited** keys.
