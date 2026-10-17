# 3-minute presentation script

## 1. The problem — 20 seconds

Business users need answers from operational data, but waiting for an analyst to write SQL slows decisions. QueryPilot lets them ask a question in everyday language while keeping the generated SQL visible and controlled.

## 2. Live demo — 90 seconds

Start the app, then ask: **Which city generated the most revenue?**

Point out three things:

- The assistant translates the business question into SQL.
- The SQL is shown before the result, so analysts can review it.
- The demo only permits read-only database queries.

Then click **Top products by units sold**. Explain that it recognises relationships between orders, order items, and products. Finally, click **Show low stock inventory** to demonstrate that the same interface supports operational questions as well as revenue analytics.

## 3. Architecture — 45 seconds

The screen deliberately shows both the local and target AWS architecture:

| Prototype today | AWS production path |
|---|---|
| Local SQL generation logic | Amazon Bedrock model with schema-aware prompt |
| Python HTTP handler | Amazon API Gateway + AWS Lambda |
| SQLite demo store | Amazon Athena, Aurora, or RDS read replica |
| Console logging | Amazon CloudWatch |

This proves the interaction, guardrails, and data contract before spending time on cloud account setup.

## 4. Trust and next step — 25 seconds

The first production increment is to replace the local generator with Bedrock, use a read-only IAM role, validate generated SQL, and enforce query-cost limits. The user experience stays the same; only the local implementation blocks are swapped for AWS-managed services.

## Suggested answers for questions

- **Why not connect to production data now?** The demo is intentionally isolated and uses synthetic data; it validates the product experience without exposing data or requiring cloud provisioning.
- **Is the generated SQL safe?** The prototype blocks database-changing SQL and shows every statement. Production adds IAM least privilege, audited logs, and stricter validation.
- **Is this actually AI?** The prototype uses deterministic local natural-language patterns to make the demo reproducible without a model account. Its generator is designed as the replacement point for Amazon Bedrock.
