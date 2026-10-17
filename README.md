# QueryPilot — local AI SQL assistant prototype

This is a zero-dependency, locally runnable demo for presenting an AWS-style AI SQL assistant before an AWS account is available.

## Run it

1. Open PowerShell in this folder.
2. Run `python app.py`.
3. Your browser opens automatically. If it does not, use the `http://127.0.0.1:PORT` address shown in the terminal.

No package installation, API key, or AWS credentials are required. The app creates a small synthetic SQLite retail database on its first run.

The app uses the first available port from 8012 through 8022.

## Demo flow

1. Ask: **Which city generated the most revenue?**
2. Point out the generated SQL and that it is restricted to read-only statements.
3. Try **Top products by units sold** and **Show low stock inventory**.
4. Use the architecture card to explain the migration path: local rule-based agent → Amazon Bedrock; Python API → AWS Lambda/API Gateway; SQLite → Athena, Aurora, or RDS; logs → CloudWatch.

## What this proves

- Natural-language analytics workflow
- Schema-aware SQL generation
- Explicit SQL visibility for trust and review
- A database execution layer with a simple read-only guardrail

## Next AWS increment

Replace `generate_sql()` in `app.py` with a Bedrock call that receives `SCHEMA_DESCRIPTION`, deploy the handler as Lambda behind API Gateway, and point the query layer at Athena or a read replica in RDS/Aurora. Keep SQL validation, least-privilege database permissions, logging, and query-cost limits as production guardrails.
