# AI MESSENGER — Hosting Guardrails

Before any hosted deployment is authorized:

1. inspect the generated service configuration;
2. supply secrets only through the hosting provider's secret/environment facility;
3. verify TLS is provided by the platform;
4. replace in-memory storage with durable storage;
5. establish a real identity provider and token validation;
6. configure rate limits and abuse controls;
7. add audit and monitoring;
8. verify restart/recovery behavior;
9. run an end-to-end authenticated test;
10. only then consider connecting an Android client.

The current Render blueprint is a preparation artifact. It does not mean a Render service exists or is running.
