# Final Year Project

## Running

To synthesize a program:

```bash
python -m vulnspec synth <target-file> <c-file>
```

Then to build it:

```bash
python -m vulnspec build <c-file>
```

## Development

To regenerate the libraries:

```bash
PYTHONPATH=./tools python -m builtin_generator synth/builtins
```

