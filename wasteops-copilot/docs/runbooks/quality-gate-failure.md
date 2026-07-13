# Quality gate failure
## Symptoms
Evaluation regression or critical safety case fails.
## Impact
The candidate release cannot progress.
## Initial checks
Compare datasets, prompt/model versions, configuration and candidate/baseline reports; prohibit live providers unless explicitly approved.
## Safe response
Block deployment and preserve reports. Never lower a threshold merely to pass a release.
## Escalation
Prompt/model/application owners and safety reviewer assess critical failures.
## Recovery
Fix code/prompt/data, create a new immutable prompt version, and rerun full deterministic suites.
## Verification
All thresholds and safety cases pass with no hidden critical failures.
## Post-incident actions
Add regression cases and document reviewed threshold changes.
