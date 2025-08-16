GitHub Actions workflows
========================

Bumpwright integrates easily with GitHub Actions. The example workflows below
show how to suggest the next semantic version and how to apply a release.
Place these files in the ``.github/workflows`` directory of your project to
use them.

Pull request check
------------------

The ``bumpwright-check.yml`` workflow runs Bumpwright in read-only mode to
suggest the next version. Trigger it manually with the ``workflow_dispatch``
event, or adapt it to run on pull requests.

.. literalinclude:: _static/workflows/bumpwright-check.yml
   :language: yaml
   :caption: bumpwright-check.yml

Download the file: :download:`bumpwright-check.yml <_static/workflows/bumpwright-check.yml>`.

Release automation
------------------

The ``bumpwright-release.yml`` workflow applies a version bump, commits the
updated files, and pushes a tag. Provide the desired bump level when triggering
this workflow.

.. literalinclude:: _static/workflows/bumpwright-release.yml
   :language: yaml
   :caption: bumpwright-release.yml

Download the file: :download:`bumpwright-release.yml <_static/workflows/bumpwright-release.yml>`.
