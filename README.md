# Final Year Project

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

To synthesize a program:

```bash
vulnspec synth <target-file> <out-file>.c
```

Then to build it:

```bash
vulnspec build <out-file>.c
```

## Development

### Installation in development mode

Install the package again using the following command:

```bash
pip install --user --editable .
```

Changes to the local copy of the code should now be reflected to the
installation.

### Generating data files

To regenerate the libraries:

```bash
PYTHONPATH=./tools python -m builtin_generator vulnspec/data/builtins
```

To regenerate the markov chains:

```
PYTHONPATH=./tools python -m markov_generator ../musl-1.2.1/ > vulnspec/data/markov.json
```

