# consul-announcer

Service announcer for [Consul](https://www.consul.io/).

Functionality:

* Register/deregister services with checks
* Spawn a subprocess
* Periodically mark all TTL checks as passed (if any)

## Install

For regular usage:

```sh
pip install consul-announcer  # or add it as a requirement
```

## Usage

```sh
consul-announcer --config=path [-h] [--agent=hostname[:port]] [--interval=seconds] [--verbose] -- command [arguments]

Arguments:
  -h, --help               show this help message and exit
  --agent hostname[:port]  Consul agent address: hostname[:port]. Default: localhost (default port is 8500)
  --config path            Consul checks configuration file
  --interval seconds       interval for periodic marking all TTL checks as passed (should be less than min TTL)
  --verbose, -v            verbose output. You can specify -v or -vv
```

Minimal usage:

```sh
consul-announcer --config=conf.json -- some-process --with --arguments
```

### `--config`

It should be a JSON file that contains `{"service": {...}}` or `{"services": [...]}`.

Read [Consul docs about services definition](https://www.consul.io/docs/agent/services.html).

All the services & checks will be registered on process start and deregistered on process termination.

### `--interval`

In the example above, the interval is not specified so it'll be calculated as min TTL / 10 
(if there are TTL checks specified in the config file). But you can provide your own value _(in seconds)_:

```sh
consul-announcer --interval=3 ...
```

If there are no TTL checks and no `--interval` - an error will raise.

### `--address`

Default agent address is `localhost` (with default port `8500`). You can provide your own:

```sh
consul-announcer --agent=1.2.3.4:5678 ...
```

### `--verbose`

Output levels:

* by default only errors and warnings are printed
* `-v` will show info messages
* `-vv` will show info and debug messages

### Usage in Python code

```py
from announcer.service import Service

service = Service('localhost:1234', '/path/to/config.json', ['sleep', '5'], 0.5)
service.run()
```

## Development

### Install

```sh
git clone <this-repo>
cd consul-announcer
pip install -r requirements/test.txt -e .
```

### Test

Test configuration is defined in the `tox.ini` file and includes `py.test` tests
and `flake8` source code checker. You can run all of the tests:

```
python setup.py test
```

To run just the `py.test` tests, not `flake8`, and to re-use the current `virtualenv`:

```sh
py.test
```

### Release

* Tests must be passing
* Don't forget to test all added functionality
* Update `CHANGELOG` with the release info
* Update `README` _(if necessary)_
* Commit all the changes
* Create new version tag _(e.g.)_: `v1.2.3`
* Push commits and tags
* Release new version on PyPI
