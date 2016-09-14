# consul-doorkeeper

Doorkeeper for services discovered by [Consul](https://www.consul.io/).

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

## Usage

```sh
consul-doorkeeper [-h] [--agent hostname[:port]] --config path [--interval seconds] [--verbose] -- command [arguments]

Arguments:
  -h, --help               show this help message and exit
  --agent hostname[:port]  Consul agent address: hostname[:port]. Default: localhost (default port is 8500)
  --config path            Consul checks configuration file
  --interval seconds       Interval for periodic marking all TTL checks as passed (should be less than min TTL)
  --verbose, -v            Verbose output. You can specify -v or -vv
```

Minimal usage:

```sh
consul-doorkeeper --config=conf.json -- some-sub-process --with --arguments
```

In this case polling interval will be calculated as min TTL / 10. But you can provide your own:

```sh
consul-doorkeeper --interval=3 ...
```

Default agent address is `localhost` (with default port `8500`). You can provide your own:

```sh
consul-doorkeeper --agent=1.2.3.4:5678 ...
```

Output levels:

* by default only errors and warnings will be printed
* `-v` will show info messages
* `-vv` will show info and debug messages

## Test

Test configuration is defined in the `tox.ini` file and includes `py.test` tests
and `flake8` source code checker. You can run all of the tests:

```
python setup.py test
```

To run just the `py.test` tests, not `flake8`, and to re-use the current `virtualenv`:

```sh
py.test
```
