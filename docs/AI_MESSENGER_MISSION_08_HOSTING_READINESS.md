# AI MESSENGER — Mission 08 Hosting Readiness

## Objective

Prepare the experimental backend for a possible free-first hosted runtime without deploying it or connecting Android yet.

## Rules

- no paid infrastructure;
- no public deployment in this mission;
- no real credentials in GitHub;
- no Android remote endpoint activation;
- no production claim;
- hosting configuration must remain replaceable.

## Target

A small Python web service that can be started by a managed runtime, with secrets supplied by environment variables and a health endpoint suitable for runtime checks.

## Explicit limitation

An in-memory backend loses messages on restart and is not sufficient for production. Hosting readiness is therefore preparation, not production readiness.
