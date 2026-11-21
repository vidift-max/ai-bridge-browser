# Mission 18 — Staging Deployment Contract

## Objective
Prepare a controlled staging deployment contract for the experimental AI Messenger without deploying it.

## Rounds
1. Define staging deployment contract and gate.
2. Inventory required runtime configuration and secret boundaries.
3. Define startup/health/readiness contract.
4. Define storage and filesystem safety contract.
5. Define network binding and proxy assumptions.
6. Define bounded request/response operational limits.
7. Add a machine-checkable staging configuration validator.
8. Add regression tests for invalid staging configurations.
9. Review the non-deployed Render blueprint against the contract.
10. Verify, document, and close only with same-HEAD Backend + Android CI green.

## Explicitly not authorized
- Render deployment;
- public endpoint activation;
- production database provisioning;
- OAuth/OIDC integration;
- external AI provider connection;
- physical Android activation;
- real internet AI-to-AI communication.

## Evidence rule
CI success proves repository automation only. It does not prove hosted availability or physical-device execution.
