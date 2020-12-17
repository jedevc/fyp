import argparse
from datetime import datetime
from pathlib import Path

import black
import yaml

from .library import Library
from .tags import TagKind


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("directory")
    arg_parser.add_argument("--skip-build", dest="build", action="store_false")
    args = arg_parser.parse_args()

    root = Path(args.directory)

    config_path = root / "config.yaml"
    with config_path.open() as config_file:
        config = yaml.load(config_file, Loader=yaml.SafeLoader)

    buckets = {
        TagKind.MACRO: {},
        TagKind.EXTERN: {},
        TagKind.PROTOTYPE: {},
        TagKind.FUNCTION: {},
        TagKind.TYPEDEF: {},
        TagKind.UNION: {},
        TagKind.STRUCT: {},
        TagKind.MEMBER: {},
        TagKind.ENUM: {},
        TagKind.ENUMERATOR: {},
        TagKind.VARIABLE: {},
    }

    for library, data in config["libraries"].items():
        # TODO: path shouldn't be relative to cwd.
        # would make more sense to be relative to the config.yaml
        lib = Library(library, Path(data["path"]), data["includes"])
        if args.build:
            lib.build()
        tags = lib.tags()

        for tag in tags:
            if tag.name.startswith("__"):
                continue
            bucket = buckets[tag.kind]
            bucket[tag.name] = (tag, lib)

    header = (
        "\n".join(
            [
                "'''",
                f"This file was autogenerated by builtin_generator at {datetime.now()}.",
                "",
                "DO NOT MODIFY IT MANUALLY!",
                "'''",
            ]
        )
        + "\n\n"
    )

    targets = {
        "types.py": generate_types,
        "functions.py": generate_functions,
        "variables.py": generate_variables,
    }
    Path(args.directory, "__init__.py").touch()
    for target, generator in targets.items():
        path = Path(args.directory, target)
        with path.open("w") as f:
            f.write(header)
            generator(f, config, buckets)

        black.format_file_in_place(
            path, fast=True, mode=black.Mode(()), write_back=black.WriteBack.YES
        )


def generate_types(output, config, buckets):
    translations = {}
    paths = {}
    if "types" in config:
        for primitive in config["types"].get("signed"):
            rewritten = translate_typename(primitive)
            translations[rewritten] = primitive
            for prefix in ("signed", "unsigned"):
                translations[f"{rewritten}_{prefix}"] = f"{prefix} {primitive}"

        for primitive in config["types"].get("other"):
            rewritten = translate_typename(primitive)
            translations[rewritten] = primitive

    tags = extract(
        buckets,
        [
            TagKind.UNION,
            TagKind.STRUCT,
            TagKind.ENUM,
            TagKind.TYPEDEF,
        ],
    )
    for (tag, lib) in tags.values():
        paths[tag.name] = tag.path

        name = f"{tag.name}@{lib.name}"
        if tag.kind in (TagKind.UNION, TagKind.STRUCT, TagKind.ENUM):
            translations[name] = f"{tag.kind} {tag.name}"
        else:
            translations[name] = tag.name

    contents = ""
    contents += f"TRANSLATIONS = {translations}\n\n"
    contents += f"PATHS = {paths}\n\n"
    output.write(contents)


def generate_functions(output, config, buckets):  # pylint: disable=unused-argument
    paths = {}
    translations = {}
    signatures = {}

    tags = extract(
        buckets,
        [
            TagKind.FUNCTION,
            TagKind.PROTOTYPE,
        ],
    )
    for (tag, lib) in tags.values():
        paths[tag.name] = tag.path

        name = f"{tag.name}@{lib.name}"
        translations[name] = tag.name
        signatures[name] = (tag.signature, tag.typeref)

    contents = ""
    contents += f"TRANSLATIONS = {translations}\n\n"
    contents += f"SIGNATURES = {signatures}\n\n"
    contents += f"PATHS = {paths}\n\n"
    output.write(contents)


def generate_variables(output, config, buckets):  # pylint: disable=unused-argument
    paths = {}
    translations = {}
    types = {}

    tags = extract(
        buckets,
        [
            TagKind.VARIABLE,
            TagKind.EXTERN,
        ],
    )
    for (tag, lib) in tags.values():
        paths[tag.name] = tag.path

        name = f"{tag.name}@{lib.name}"
        translations[name] = tag.name
        types[name] = tag.typeref

    contents = ""
    contents += f"TRANSLATIONS = {translations}\n\n"
    contents += f"TYPES = {types}\n\n"
    contents += f"PATHS = {paths}\n\n"
    output.write(contents)


def translate_typename(name: str) -> str:
    parts = name.split()
    parts.reverse()
    return "_".join(parts)


def extract(buckets, kinds):
    if kinds is None:
        return {}

    types = {}
    for kind in kinds:
        for (tag, lib) in buckets[kind].values():
            types[tag.name] = (tag, lib)

    return types
