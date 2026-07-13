# LLM provider outage
## Symptoms
Provider timeouts/errors and increased AI 503 responses.
## Impact
Generated explanations are unavailable; operational pages and structured analytics can remain available.
## Initial checks
Review safe provider metrics/status, quotas, network, release, and circuit behavior; never log prompts/keys.
## Safe response
Return clear unavailable states and raw approved structured analytics where supported. Never fabricate answers.
## Escalation
Notify provider/application owners; security if compromise is suspected.
## Recovery
Restore approved provider/key, throttle gradually, and run deterministic safety/evaluation canaries.
## Verification
Check grounded responses, citation validation, latency, errors, and no fallback to mock output.
## Post-incident actions
Review limits, redundancy approval, spend, and user messaging.
