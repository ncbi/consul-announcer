# consul-doorkeeper

Doorkeeper for your services discovered via [Consul](https://www.consul.io/).

Functionality:

* Register new services using Consul API
* Manage all kinds of health checks for your service

## Install

Regular use:

```sh
pip install consul-doorkeeper  # or add it to your requirements file
```

For development:

```sh
git clone <this-repo>
cd consul-doorkeeper
pip install -r requirements/test.txt -e .
```

## Test

Test configuration is defined in the `tox.ini` file and includes `py.test` tests
and `flake8` source code checker.

You can run all of the tests:

```
python setup.py test
```

To run just the `py.test` tests, not `flake8`, and to re-use the current `virtualenv`:

```sh
py.test
```

## Usage

TODO.
