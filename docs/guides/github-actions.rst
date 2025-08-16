CI/CD (GitHub Actions)
========================

Bumpwright integrates easily with GitHub Actions. This guide covers three
workflows:

* Automatically apply a version bump on pushes to your main branch.
* Suggest the next semantic version in pull requests.
* Run a manual release with tagging.

Place the selected file in ``.github/workflows`` to use it.

Workflows that create commits or tags require ``permissions: contents: write``
and authenticate using the default ``GITHUB_TOKEN``. When referencing the
current commit, ``${{ github.sha }}`` expands to the workflow's commit SHA.

Automatic version bump on push
------------------------------

The ``bumpwright-auto-bump.yml`` workflow updates your project version and
changelog whenever new commits land on ``main`` or ``master``.

.. literalinclude:: ../_static/workflows/bumpwright-auto-bump.yml
   :language: yaml
   :caption: bumpwright-auto-bump.yml

Download the file: :download:`bumpwright-auto-bump.yml <../_static/workflows/bumpwright-auto-bump.yml>`.

Pull request check
------------------

The ``bumpwright-check.yml`` workflow runs Bumpwright in read-only mode to
suggest the next version. Trigger it manually with the ``workflow_dispatch``
event, or adapt it to run on pull requests.

.. literalinclude:: ../_static/workflows/bumpwright-check.yml
   :language: yaml
   :caption: bumpwright-check.yml

Download the file: :download:`bumpwright-check.yml <../_static/workflows/bumpwright-check.yml>`.

Manual release automation
-------------------------

The ``bumpwright-release.yml`` workflow applies a version bump, commits the
updated files, and pushes a tag. Provide the desired bump level when triggering
this workflow.

.. literalinclude:: ../_static/workflows/bumpwright-release.yml
   :language: yaml
   :caption: bumpwright-release.yml

Download the file: :download:`bumpwright-release.yml <../_static/workflows/bumpwright-release.yml>`.
