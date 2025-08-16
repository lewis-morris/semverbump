gRPC Analyser
=============

Detects gRPC service and method changes in ``.proto`` files.

Dependencies
~~~~~~~~~~~~

* None

Enable or disable
~~~~~~~~~~~~~~~~~

Set ``grpc`` under ``[analysers]``.

.. code-block:: toml

   [analysers]
   grpc = true  # set to false to disable

Severity rules
~~~~~~~~~~~~~~

* Added service → minor
* Removed service → major
* Added RPC method → minor
* Removed RPC method → major

Detectable change
~~~~~~~~~~~~~~~~~

.. code-block:: diff

   @@
    service Foo {
   -    rpc Ping (Req) returns (Res);
   +    rpc Ping (Req) returns (Res);
   +    rpc Pong (Req) returns (Res);
    }

Example output
~~~~~~~~~~~~~~

.. code-block:: text

   - [MINOR] Foo.Pong: Added RPC method
