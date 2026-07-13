# ML architecture

Operational records flow through point-in-time feature builders, chronological training and validation, an approval-gated registry, checksum-verified production loading, a private prediction API, typed backend providers, and Decision Intelligence `[M#]` evidence.

The ML service owns prediction, validation, and monitoring. The decision engine owns deterministic option comparison. GenAI may explain returned evidence but cannot calculate a prediction. An authorized operations manager owns the final decision. No component dispatches trucks, assigns workers, removes vehicles from service, or optimizes routes.

Inference uses a read-only analytics connection. Training uses separately controlled access. MLflow is private on the internal network, with PostgreSQL metadata and private S3-compatible artifacts. Model artifacts are local allow-listed files; arbitrary URLs and arbitrary model names are rejected.
