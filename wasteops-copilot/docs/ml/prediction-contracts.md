# Prediction contracts

Private endpoints cover bin overflow, collection priority, truck anomalies, missed collections, workforce requirements, active models, safe model detail, and aggregate monitoring. They require signed bearer service identity, request IDs, fixed model names, bounded batches, supported horizons, known assets, feature/model compatibility, and freshness validation.

Every prediction includes model name/version, prediction and feature timestamps, data age, and warnings. Probabilities are bounded `[0,1]`; workforce counts are non-negative. Small top-factor lists describe association and direction, never cause. Serialized artifacts, training rows, credentials, full feature vectors, stack traces, and arbitrary model URLs are not API outputs.

Stale inputs are rejected or clearly degraded according to model policy. Baseline fallback is always labeled. Prediction probability is separate from Decision Intelligence confidence.
