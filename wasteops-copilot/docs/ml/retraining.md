# Retraining

Consider retraining after persistent drift, confirmed degradation, new regions/truck/sensor types, procedure changes, major seasonal changes, or enough new labeled data. Preserve the prior dataset version, training window, code commit, seed, candidate artifacts, and comparison report.

Retraining jobs may be automated, but they produce unapproved candidates. They never change Production stage. Review leakage, calibration, weak subgroups, data completeness, operational trade-offs, and the updated model card before requesting promotion.
