# Dependency vulnerability audit

Tracking: #52

Titan audits the authoritative Python lock graph in Full CI with the repository-pinned `uv 0.12.3` release.

## Contract

The `Dependency vulnerability audit` job:

1. checks out the exact workflow head;
2. installs the same `uv 0.12.3` release used by Titan's dependency-sync owner;
3. runs `uv audit --frozen` with only the `audit-command` and `json-output` preview features enabled;
4. audits the project lock graph without changing `uv.lock`;
5. uses uv's OSV service contract and does not carry a repository ignore/allow list;
6. captures the JSON result, its SHA-256, the audit exit code, the `uv` version, OSV endpoint, and `uv.lock` SHA-256;
7. uploads that evidence even when the audit reports a failure;
8. fails the CI job when the audit exits non-zero.

By default `uv audit` covers all project extras and dependency groups. Titan intentionally does not narrow that surface in this lane.

## Evidence semantics

The audit procedure is reproducible from the checked-in lockfile, pinned tool release, and recorded service contract. The evidence artifact is bound to the exact `uv.lock` content through SHA-256.

The OSV advisory database is a live external service. New advisories can therefore change a later audit result for the same lockfile. Titan does **not** claim that vulnerability results are byte-for-byte immutable across different OSV database states. A historical artifact proves what the configured audit service reported for that workflow execution and exact lock hash.

## Fail-closed policy

There are no `--ignore` or `--ignore-until-fixed` entries in this bounded contract. If a future vulnerability requires an exception, that must be a separate explicit, reviewed policy decision with its own scope and evidence; it must not be silently added to this workflow.

Network/service failure is also a failed audit, not a clean result.

## What this does not prove

This Python dependency audit does not prove:

- absence of vulnerabilities in the Docker base image or OS packages;
- a full container/OS SBOM;
- CodeQL or static application security coverage;
- Dependabot/update automation policy;
- byte-for-byte reproducible container images;
- Operator GO, runtime authority, or production authority.

Those remain independent #52 residuals.
