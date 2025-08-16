GitHub Actions
==============

These minimal examples show how to integrate Bumpwright with
GitHub Actions.  They avoid duplicating coverage jobs and can be
adapted for other CI providers such as GitLab or Jenkins.

Decide and apply on push
------------------------

Runs on pushes to ``main``.  The workflow decides the bump, applies it
when the decision is at least a patch, creates a tag, and pushes it.

.. code-block:: yaml

   name: Bumpwright Decide and Apply
   on:
     push:
       branches: [main]
   jobs:
     bump:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: '3.x'
         - run: pip install bumpwright jq
         - id: decision
           run: |
             bumpwright bump --decide --json > decision.json
             echo "level=$(jq -r '.level' decision.json)" >> "$GITHUB_OUTPUT"
         - name: apply bump
           if: steps.decision.outputs.level != 'none'
           run: |
             bumpwright bump --apply --tag
             git push --tags

Decision only
-------------

Produces a JSON artifact for a manual gate or release job.

.. code-block:: yaml

   name: Bumpwright Decision
   on: [push]
   jobs:
     decide:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: '3.x'
         - run: pip install bumpwright
         - run: bumpwright bump --decide --json > decision.json
         - uses: actions/upload-artifact@v4
           with:
             name: bumpwright-decision
             path: decision.json

To feed the decision into a separate apply job, download the artifact and
parse the level with ``jq``:

.. code-block:: yaml

   - uses: actions/download-artifact@v4
     with:
       name: bumpwright-decision
   - run: |
       level=$(jq -r '.level' decision.json)
       if [ "$level" != "none" ]; then
         bumpwright bump --apply --tag
         git push --tags
       fi

