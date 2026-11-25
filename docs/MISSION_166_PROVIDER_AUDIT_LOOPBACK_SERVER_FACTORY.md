# Mission 166 — Provider Audit Loopback Server Factory

## Objective

Provide an explicit, safe local listener factory for the M165 HTTP transport adapter without mounting it in the main Messenger server or enabling network exposure.

## Design

`create_provider_audit_http_server(service, host="127.0.0.1", port=0)`:

- validates an injected object exposing the service `handle` contract;
- accepts only the exact IPv4 loopback address `127.0.0.1`;
- rejects wildcard, LAN, public, IPv6, and hostname binds;
- validates the port as an integer in 0..65535 (booleans are rejected);
- uses `ThreadingHTTPServer` with daemon request threads;
- binds the socket but does not start `serve_forever()`;
- leaves thread startup, shutdown, and server close to the caller.

Port zero requests an OS-assigned ephemeral port. The factory does not read environment variables, create credentials, or alter the main `MessengerHandler`.

## Validation

Tests create actual loopback HTTP listeners and exercise authenticated requests, missing authentication, concurrent reads, bind restrictions, invalid arguments, and explicit lifecycle shutdown.

## Security and deployment boundary

Python's standard-library `http.server` is documented as unsuitable for production and provides only basic security checks. This factory is for local development and CI only. It is not a TLS server, reverse proxy, public service, or production deployment. No public bind, external network, domain, TLS, cloud resource, production secret, paid API, device activation, or merge is included.

Production exposure requires a production-grade HTTP server/reverse proxy, TLS, robust identity and authorization, distributed rate limiting, monitoring, and independent durable anchor storage. This factory intentionally refuses non-loopback binds.
