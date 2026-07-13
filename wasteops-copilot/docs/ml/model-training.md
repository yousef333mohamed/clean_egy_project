# Model training

Training accepts reviewed point-in-time feature datasets. `training/splits.py` sorts by time and creates chronological train, validation, and test periods. Random temporal splitting is prohibited. Each run records dataset hash/version, period, feature version, commit, parameters, seed, metrics, and artifacts through the training command and optional MLflow run.

Start with current-fill, historical-rate, robust-deviation, and rolling-average baselines. Candidate models are logistic regression, Isolation Forest, and histogram gradient boosting. Deep learning is out of scope until evidence demonstrates a material operational advantage.

`python scripts/train_all.py --dataset-directory PATH` orchestrates prepared data. Full production training is intentionally not run in pull requests.
