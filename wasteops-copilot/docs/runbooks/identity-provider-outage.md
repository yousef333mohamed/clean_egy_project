# Identity provider outage
## Symptoms
New sign-ins/JWKS refresh fail while valid sessions may continue.
## Impact
New users cannot authenticate; unknown signing keys fail closed.
## Initial checks
Check provider status, DNS/TLS, JWKS cache, issuer/audience configuration, and token expiry without logging tokens.
## Safe response
Keep existing valid sessions within configured lifetime. Do not enable development auth or skip signature validation.
## Escalation
Contact identity/security owners and provider; declare incident for widespread access loss.
## Recovery
Restore provider/JWKS connectivity, validate key rotation, then test sign-in/sign-out and every privileged role.
## Verification
Confirm failures normalize and audit/metrics contain no token data.
## Post-incident actions
Review cache/lifetime tradeoffs, provider SLA, communications, and access logs.
