# semverbump

Static public-API diff and heuristics to suggest semantic version bumps.

## Configuration

Create a `semverbump.toml` file to customize behavior.

### Analyzers

Optional analyzers can be enabled in the `[analyzers]` section. Each key is the
name of an analyzer plugin with a boolean flag indicating whether it should run.

```toml
[analyzers]
flask_routes = true
sqlalchemy = true
```

Only analyzers explicitly set to `true` are enabled.
