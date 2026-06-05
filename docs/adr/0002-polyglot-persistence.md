# ADR-0002: Polyglot persistence

## Status

Accepted.

## Context

The system stores different kinds of data: transactional task state, flexible reports, audit/event history, hot counters and cold artifacts. One database can store everything, but that would hide the platform requirement to justify RDBMS, NoSQL and cache choices.

## Decision

Use multiple storage types:

- PostgreSQL for projects and analysis task status.
- MongoDB for generated reports and flexible documents.
- Valkey/Redis for rate limit counters and hot cache.
- S3-compatible cold storage such as MinIO in the target architecture for archived reports and raw agent outputs.

## Alternatives

- PostgreSQL only: simpler, but less aligned with NoSQL/cold storage criteria.
- MongoDB only: flexible, but weaker for transactional task state and relational constraints.
- Redis only for all state: not appropriate for durable business data.

## Consequences

Benefits:

- each data type uses a suitable storage model;
- rate limiting has atomic TTL counters;
- report documents can evolve without schema churn;
- task status remains transactional.

Costs:

- more infrastructure components;
- more connection configuration;
- more operational monitoring.

