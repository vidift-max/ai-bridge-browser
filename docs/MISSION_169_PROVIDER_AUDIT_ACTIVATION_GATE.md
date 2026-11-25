# Mission 169 — Provider Audit Messenger Activation Gate

## Objective

Add a small, testable composition boundary for the optional Provider Audit
service without enabling it in the Messenger production bootstrap.

## Contract

`build_provider_audit_messenger_service()` returns `None` by default.
Construction requires all of the following to be supplied explicitly:

- `enabled=True` (a real boolean, not a truthy string);
- an anchor adapter implementing `read_latest()` and
  `append_checkpoint(expected_sequence, record)`;
- a token authentication callback;
- a principal authorization callback.

There is no default-allow authorization policy. The factory does not create
SQLite files, read credentials from environment variables, mutate
`MessengerHandler`, mount HTTP routes, or start a listener. Invalid or
incomplete enabled configurations fail closed.

## Deliberately not activated

`MessengerHandler.provider_audit_service` remains `None` by default, and
`serve()` does not call this factory. The factory is a code-level composition
contract only. It is not evidence of a running remote anchor, independent
trust domain, TLS termination, deployed credentials, or public availability.

The existing SQLite anchor is a local reference adapter and is not sufficient
proof of an independently administered production trust domain. Production
activation must be a separately reviewed mission covering independent durable
storage, secret provisioning, TLS, operator authorization, backup/recovery,
and deployment approval.

## Verification

The dedicated workflow compiles the server and runs the activation-gate tests
alongside the existing Messenger Provider Audit integration, transport,
remote-service, anchor, and HTTP server suites. Tests use only in-memory fake
dependencies or temporary local SQLite storage; no external network, paid API,
credential, deployment, or device is used.
