# Feature registry

The executable registry is `ml-service/app/features/feature_registry.py`, version `1.0.0`. Every definition records source, transformation/aggregation, lookback, null strategy, validation range, availability delay, consumers, and leakage risk.

Missing observations stay missing. Nullable numeric features receive explicit missing indicators during validation; they are not converted to zero. Categorical candidates use an explicit unknown category. Feature timestamps must be no later than prediction timestamps. Daily outcomes are available only after their operational day, and closed-trip features are scored only after trip close.

Adding a feature requires a registry entry, availability analysis, temporal leakage test, range/null validation, updated model card, and a feature-version change when compatibility changes.
