Glossary
========

.. glossary::

   public API
       Symbols and behaviours considered part of the supported interface for consumers.

   major
       Version increment signalling incompatible changes.

   minor
       Version increment for backwards-compatible feature additions.

   patch
       Version increment for backwards-compatible bug fixes.

   decision
       The bump level and confidence derived from analysing API changes.

   base/head
       Git references used for comparison; ``base`` is the earlier commit and ``head`` the later.

   analyser
       Plugin that inspects a specific domain for API-impacting changes.

   rule severity
       Mapping from a detected change to the bump level it triggers.
