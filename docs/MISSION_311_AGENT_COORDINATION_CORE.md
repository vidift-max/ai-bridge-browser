# M311 — GPT-6 agent coordination core

Date: 2026-11-28  
Branch: `feat/mission-311-agent-coordination-core`  
Base: `feat/mission-295-m241-ai-first-contact-integration` at `b76024e5335837cedfba83474ec4f56aa8e60599`.

## Scope
Only logical agent coordination. GPT-6 is the central coordinator. AI-01 and AI-02 are the only provider-session identities in the current operational phase. The roster may represent up to 20 logical identities, but this does not activate additional accounts, WebViews, providers, or credentials.

No Tool Hub work, paid hosting, merge, Release, deployment, installation, credential changes, or device operation is included.

## Ten rounds
1. Audit the current agent code and branch baseline.
2. Reconcile the M310 report against the actual branch tree; missing classes were not treated as implemented.
3. Create an isolated M311 branch from the audited M310 head.
4. Implement a bounded logical-agent registry.
5. Implement strict versioned JSON serialization and restore validation.
6. Implement FIFO mission scheduling with a two-session cap and AI-01/AI-02-only activation.
7. Add roster tests for capacity, duplicate IDs, status and session scope.
8. Add codec and queue tests for round-trip, malformed snapshots, FIFO, idempotent IDs and cancellation rules.
9. Add GPT-6 AgentCoordinator to register agents, assign missions, dispatch eligible work and track completion.
10. Run Android CI on the exact final commit, fix failures, and record evidence. Pending until the workflow result is observed.

## Evidence boundaries
- Logical registration is not a connected model/provider.
- BUSY means a scheduler-owned active task, not proof of a live ChatGPT login.
- AI-03 through AI-20 remain logical/queued only.
- The queue and roster are currently in-process models; persistence integration and physical-device recovery remain separate work.
- No autonomous model-to-model conversation is claimed by this mission.

## Final verification
To be completed after CI on the exact final HEAD.
