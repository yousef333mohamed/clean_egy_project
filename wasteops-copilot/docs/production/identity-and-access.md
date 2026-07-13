# Identity and access

Register the frontend as an authorization-code OIDC client with PKCE and exact HTTPS callback/logout URLs. Configure API audience `wasteops-api`, issuer, JWKS, RS256, and the documented role/permission claims. Assign roles in the IdP through approved groups and periodically recertify SYSTEM_ADMIN, PROMPT_ADMIN, AUDITOR, and ingestion access.

FastAPI role mappings are in `app/auth/permissions.py`; backend checks are authoritative. A 401 means no valid identity; 403 means the identity lacks permission. Frontend hiding is only usability. Test each role against the generated endpoint matrix.

Development auth is off by default, requires an explicit header and configuration when used locally, and makes production startup fail. During IdP outage, existing unexpired sessions may continue; never enable a bypass.
