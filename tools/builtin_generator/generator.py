import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Collection, Dict, TextIO, Tuple

import black
import yaml

from .library import Library
from .tags import Tag, TagKind

Bucket = Dict[str, Tuple[Tag, Library]]
Buckets = Dict[TagKind, Bucket]


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("directory")
    arg_parser.add_argument("--skip-build", dest="build", action="store_false")
    args = arg_parser.parse_args()

    root = Path(args.directory)

    config_path = root / "config.yaml"
    with config_path.open() as config_file:
        config = yaml.load(config_file, Loader=yaml.SafeLoader)

    buckets: Buckets = {
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

    for library, data in config.get("libraries", {}).items():
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


def generate_types(output: TextIO, config: Dict[str, Any], buckets: Buckets):
    translations = {}
    paths = {}
    metatypes = {}
    metatype_connections = {}
    if "core" in config:
        types = config["core"].get("types", {})
        includes = config["core"].get("includes", {})

        for metatype, primitives in types.items():
            rewrittens = []
            if primitives is not None:
                for primitive in primitives:
                    rewritten = translate_typename(primitive)
                    rewrittens.append(rewritten)
                    translations[rewritten] = primitive

                    if primitive in includes:
                        paths[rewritten] = includes[primitive]

            metatypes[metatype] = rewrittens
            metatype_connections[metatype] = (
                config["core"].get("typemap", {}).get(metatype, [])
            )

    metatype_class = "class MetaType(Enum):\n"
    for i, metatype in enumerate(metatypes):
        metatype_class += f"\t{metatype.capitalize()} = {i}\n"

    metatype_graph = "MetaTypeGraph: Dict[MetaType, List[MetaType]] = {\n"
    for metatype, children in metatype_connections.items():
        metatype_children = ", ".join(
            f"MetaType.{child.capitalize()}" for child in children
        )
        metatype_graph += (
            f"\tMetaType.{metatype.capitalize()}: [{metatype_children}],\n"
        )
    metatype_graph += "}\n"

    metas = "{\n"
    for metatype, primitives in metatypes.items():
        for primitive in primitives:
            metas += f'\t"{primitive}": MetaType.{metatype.capitalize()},'
    metas += "}"

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
            translations[name] = f"{tag.kind.value} {tag.name}"
        else:
            translations[name] = tag.name

    contents = ""
    contents += "from enum import Enum\n"
    contents += "from typing import Dict, List\n"
    contents += metatype_class + "\n"
    contents += metatype_graph + "\n"
    contents += f"METAS: Dict[str, MetaType] = {metas}\n"
    contents += f"TRANSLATIONS: Dict[str, str] = {translations}\n"
    contents += f"PATHS: Dict[str, str] = {paths}\n"
    output.write(contents)


def generate_functions(
    output: TextIO, config: Dict[str, Any], buckets: Buckets
):  # pylint: disable=unused-argument
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
    contents += "from typing import Dict, List, Tuple\n"
    contents += f"TRANSLATIONS: Dict[str, str] = {translations}\n"
    contents += f"SIGNATURES: Dict[str, Tuple[List[str], str]] = {signatures}\n"
    contents += f"PATHS: Dict[str, str] = {paths}\n"
    output.write(contents)


def generate_variables(
    output: TextIO, config: Dict[str, Any], buckets: Buckets
):  # pylint: disable=unused-argument
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
    contents += "from typing import Dict\n"
    contents += f"TRANSLATIONS: Dict[str, str] = {translations}\n"
    contents += f"TYPES: Dict[str, str] = {types}\n"
    contents += f"PATHS: Dict[str, str] = {paths}\n"
    output.write(contents)


def translate_typename(name: str) -> str:
    parts = name.split()
    parts.reverse()
    return "_".join(parts)


def extract(buckets: Buckets, kinds: Collection[TagKind]):
    if kinds is None:
        return {}

    types = {}
    for kind in kinds:
        for (tag, lib) in buckets[kind].values():
            types[tag.name] = (tag, lib)

    return types
