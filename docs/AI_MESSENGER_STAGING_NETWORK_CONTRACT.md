# Staging Network Contract

The future hosted process must bind to the hosting-provided port and an externally reachable interface only when deployment is explicitly authorized.

Current repository preparation uses `0.0.0.0` and the Render-provided port in the non-deployed blueprint.

Rules:
- no hard-coded production hostname;
- no assumption of localhost reachability from Android;
- TLS termination must be explicitly provided by the hosting boundary;
- a successful local bind is not evidence of public reachability;
- no public activation is performed by this mission.
