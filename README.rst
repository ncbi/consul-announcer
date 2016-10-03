consul-announcer
================

Service announcer for `Consul`_.

Functionality:

-  Register/deregister services with checks
-  Spawn a subprocess
-  Periodically mark all TTL checks as passed (if any)

Install
-------

For regular usage:

.. code:: sh

    pip install consul-announcer  # or add it as a requirement

Usage
-----

.. code:: sh

    consul-announcer --config="JSON or @path" [-h] [--agent=hostname[:port]] [--token=acl-token] [--interval=seconds] [--verbose] -- command [arguments]

    Arguments:

        -h, --help                Show this help message and exit.
        --agent hostname[:port]   Consul agent address: hostname[:port].
                                  Default: localhost (default port is 8500).
                                  You can also use CONSUL_ANNOUNCER_AGENT env variable.
        --config "JSON or @path"  Consul configuration JSON (required).
                                  If starts with @ - considered as file path.
                                  You can also use CONSUL_ANNOUNCER_CONFIG env variable.
        --token acl-token         Consul ACL token.
                                  You can also use CONSUL_ANNOUNCER_TOKEN env variable.
        --interval seconds        Interval for periodic marking all TTL checks as passed, in seconds.
                                  Should be less than min TTL.
                                  You can also use CONSUL_ANNOUNCER_INTERVAL env variable.
        --verbose, -v             Verbose output. You can specify -v or -vv.

Minimal usage:

.. code:: sh

    consul-announcer --config=conf.json -- some-process --with --arguments

``--config``
~~~~~~~~~~~~

It should be valid JSON that contains ``{"service": {...}}`` or ``{"services": [...]}``. If starts with ``@`` - considered as file path.

Read `Consul docs about services definition`_.

All the services & checks will be registered on process start and deregistered on process termination.

You can also use ``CONSUL_ANNOUNCER_CONFIG`` env variable.

``--interval``
~~~~~~~~~~~~~~

In the example above, the interval is not specified so it'll be calculated as min TTL / 10 (if there are TTL checks specified in the config). But you can provide your own value *(in seconds)*:

.. code:: sh

    consul-announcer --interval=3 ...

If there are no TTL checks and no ``--interval`` - an error will raise.

You can also use ``CONSUL_ANNOUNCER_INTERVAL`` env variable.

``--address``
~~~~~~~~~~~~~

Default agent address is ``localhost`` (with default port ``8500``). You can provide your own:

.. code:: sh

    consul-announcer --agent=1.2.3.4:5678 ...

You can also use ``CONSUL_ANNOUNCER_AGENT`` env variable.

``--token``
~~~~~~~~~~~

Consul ACL token. Required only in you've enabled ACL in your Consul agent.

You can also use ``CONSUL_ANNOUNCER_TOKEN`` env variable.

``--verbose``
~~~~~~~~~~~~~

Output levels:

-  by default only errors and warnings are printed
-  ``-v`` will show info messages
-  ``-vv`` will show info and debug messages

Usage in Python code
~~~~~~~~~~~~~~~~~~~~

.. code:: py

    from announcer.service import Service

    service = Service('localhost:1234', '@/path/to/config.json', ['sleep', '5'], 0.5)
    service.run()

Development
-----------

Install
~~~~~~~

.. code:: sh

    git clone <this-repo>
    cd consul-announcer
    pip install -r requirements/test.txt -e .

Test
~~~~

Test configuration is defined in the ``tox.ini`` file and includes ``py.test`` tests and ``flake8`` source code checker. You can run all of the tests:

.. code:: sh

    python setup.py test

To run just the ``py.test`` tests, not ``flake8``, and to re-use the current ``virtualenv``:

.. code:: sh

    py.test

Release
~~~~~~~

- Tests must be passing
- Don't forget to test all added functionality
- Update ``CHANGELOG`` with the release info
- Update ``README`` *(if necessary)*
- Commit all the changes
- Create new version tag *(e.g.)*: ``v1.2.3``
- Push commits and tags
- Release new version on PyPI

.. _Consul: https://www.consul.io/
.. _Consul docs about services definition: https://www.consul.io/docs/agent/services.html
