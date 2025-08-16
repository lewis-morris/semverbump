Troubleshooting
===============

- **No analysers run**

  *Cause*: All analysers are disabled or their optional dependencies are missing.

  *Fix*: Enable the required analysers in :doc:`../configuration` and install
  their dependencies using the instructions in :doc:`../installation`.

- **Configuration not found**

  *Cause*: ``bumpwright.toml`` is missing or located outside the current
  working directory.

  *Fix*: Create the file or pass ``--config`` to specify its path. See
  :doc:`../configuration` for details.

- **Git errors**

  *Cause*: Commands are executed outside a Git repository or references such as
  ``--base`` and ``--head`` are unreachable.

  *Fix*: Run inside a valid repository and ensure the required references exist.
  Additional setup tips can be found in :doc:`../installation`.

- **Version keeps incrementing**

  *Cause*: The version file was modified by a previous run and has not been
  committed or reverted.

  *Fix*: Commit or discard the change before rerunning, or use ``--dry-run`` to
  preview the bump without writing to disk.

FAQ
---

**Why do I get version conflicts when bumping?**
  Conflicting version numbers in files or Git tags can cause bumps to fail.
  Ensure the version defined in your configuration matches the latest tag. See
  :doc:`../configuration` for controlling version sources.

**Why do I see Git errors about missing references?**
  Bumpwright compares two Git references. Fetch all remote branches and tags so
  the specified ``--base`` and ``--head`` exist. See :doc:`../installation` for
  repository setup tips.

