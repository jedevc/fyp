# Vulnspec

This repository contains the source code and associated tooling for `vulnspec`,
a domain specific programming language for designing pwnable and
reverse-engineering CTF challenges that I designed and built for the Final Year
Project at the University of Birmingham.

## Installation

To install the project using pip (use the latest possible version of python 3.x
for best results):

```bash
https://github.com/jedevc/fyp.git
cd fyp
pip install --user .
```

To uninstall the package later (for whatever reason):

```bash
pip uninstall vulnspec
```

## Running

Create a hello world specification:

```
// hello.spec
block main {
    puts@libc.stdio("Hello world!")
}
```

To synthesize it:

```bash
vulnspec synth hello.spec hello.c
```

Then to build it:

```bash
vulnspec build hello.c
```

Finally, to run it:

```bash
./hello
```

For more examples, see the `examples/protostar/` directory for adapted versions
of some of the protostar exercises. Or, see `examples/server/` for an example
integration of vulnspec into a minimal CTF platform.

## Development

### Installation in development mode

Install the package again using the following command:

```bash
pip install --user --editable .
```

Changes to the local copy of the code should now be reflected to the
installation.

### Run tests

Integration tests using the examples can be run using pytest:

```bash
pytest
```

### Use the dev scripts

Install the pre-commit git hook:

```bash
./tools/dev/install_hooks.sh
```

Now the code will be checked for formatting, typing and that it passes tests
before allowing a commit.

To autoformat the code:

```bash
./tools/dev/autoformat.sh
```

### Generating data files

Firstly, ensure that libmusl 1.2.1 (available [here](https://musl.libc.org/releases.html))
is download into `../musl-1.2.1`.

To regenerate the libraries:

```bash
PYTHONPATH=./tools python -m builtin_generator vulnspec/data/builtins
```

To regenerate the markov chains:

```
PYTHONPATH=./tools python -m markov_generator ../musl-1.2.1/ > vulnspec/data/markov.json
```

