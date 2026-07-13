# Model registry

MLflow records experiments and registry history; local serving metadata is the fail-closed deployment manifest. It includes model/version/stage, training period, feature version, commit, parameters, metrics, threshold, checksum, approval, and promotion identity/time.

Stages are None, Staging, Production, and Archived. Serving accepts only a fixed model-name allow-list and approved Production metadata. Artifact paths must remain below the configured model directory, identity must match metadata, and SHA-256 must match both metadata and the production allow-list. Untrusted pickle/joblib files are never loaded.
