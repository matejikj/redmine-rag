# Contributing

## Development setup

```bash
cp .env.example .env
make bootstrap
make migrate
```

## Workflow

1. Create a branch.
2. Implement a focused change.
3. Run `make check`.
4. Update docs/migrations if needed.
5. Open PR using the template.

## Quality gates

- Linting and formatting must pass.
- Public API changes require tests.
- Schema changes require Alembic migration.
- Behavior changes require docs update.
