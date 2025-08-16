Integrating with CI pipelines
=============================

1. Add a GitHub Actions workflow to run ``bumpwright`` on pull requests:

.. code-block:: yaml

   name: Version check
   on: [pull_request]
   jobs:
     bumpwright:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: '3.x'
         - run: pip install bumpwright
         - run: bumpwright bump --decide --base origin/main --head ${{ github.sha }}

   ``${{ github.sha }}`` resolves to the commit SHA for the workflow run.
   Workflows that commit or tag must grant ``contents: write`` via
   ``permissions`` and authenticate with the default ``GITHUB_TOKEN``.

2. Review the workflow logs to see the suggested bump:

.. code-block:: text

   **bumpwright** suggests: `patch`
   - [PATCH] util.helper: added optional argument 'verbose'
