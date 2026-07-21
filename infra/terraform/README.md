# Infrastructure (Terraform)

Skeleton IaC for the Afridock SaaS environments, targeting AWS `af-south-1` (Cape Town) per the execution plan (§2.3, §5.4): staging and production, ECS Fargate for the API/web, RDS Postgres, ElastiCache Redis, S3 for object storage, and Cloudflare in front.

## Status

This is Phase 0 scaffolding only — it defines structure and variables but does not provision real resources yet. Before running `terraform init`/`plan`/`apply`:

1. Create the remote state bucket + DynamoDB lock table by hand (or via a bootstrap module) and fill in `backend.tf`.
2. Populate `terraform.tfvars` (gitignored) with real account/region values — see `variables.tf` for required inputs.
3. Confirm AWS credentials are configured for the target account (`aws configure` / SSO profile).

## Layout

- `main.tf` — provider configuration and root module wiring (resources to be added per work package as each phase needs them).
- `variables.tf` — input variables shared across environments.
- `outputs.tf` — root-level outputs.
- `backend.tf` — remote state configuration (placeholder; requires a real bucket/table before use).

## Environments

Use a `terraform.tfvars` per environment (e.g. `staging.tfvars`, `production.tfvars`) and select with `-var-file` rather than separate state files per directory, until the infra footprint justifies a workspace-per-environment split.
