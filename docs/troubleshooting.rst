Troubleshooting
===============

- **No analysers run**: ensure desired analysers are enabled in
  ``bumpwright.toml`` and required dependencies are installed.
- **Configuration not found**: pass ``--config`` to specify the file location.
- **Git errors**: run commands inside a git repository with accessible refs.
- **Version keeps incrementing**: commit or revert the version change before
  rerunning, or use ``--dry-run`` to preview.
