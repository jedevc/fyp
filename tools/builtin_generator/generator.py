import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Collection, Dict, TextIO, Tuple

import black
import yaml

from .library import Library
from .tags import Tag, TagKind
from .translate import translate_type, translate_types

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

    gen = Generator(config, build=args.build)
    targets = {
        "types.py": gen.generate_types,
        "functions.py": gen.generate_functions,
        "variables.py": gen.generate_variables,
    }
    Path(args.directory, "__init__.py").touch()
    for target, generator in targets.items():
        path = Path(args.directory, target)
        with path.open("w") as f:
            f.write(header)
            generator(f)

        black.format_file_in_place(
            path, fast=True, mode=black.Mode(()), write_back=black.WriteBack.YES
        )


class Generator:
    def __init__(self, config: Dict[str, Any], build=True):
        self.libraries = config.get("libraries", {})

        core = config.get("core", {})
        self.core_types = core.get("types", {})
        self.core_includes = core.get("includes", {})
        self.core_typemap = core.get("typemap", {})

        self.buckets = self._generate_buckets(build=build)
        self.type_table = self._generate_type_table()

    def generate_types(self, output: TextIO):
        translations = {}
        paths = {}
        metatypes = {}
        metatype_connections = {}

        # Find core types
        for metatype, primitives in self.core_types.items():
            rewrittens = []
            if primitives is not None:
                for primitive in primitives:
                    rewritten = convert_basetype(primitive)
                    rewrittens.append(rewritten)
                    translations[rewritten] = primitive

                    if primitive in self.core_includes:
                        paths[primitive] = self.core_includes[primitive]

            metatypes[metatype] = rewrittens
            metatype_connections[metatype] = self.core_typemap.get(metatype, [])

        # Generate meta-type code
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

        # Extract types from libc
        tags = self._extract_tags(
            (TagKind.UNION, TagKind.STRUCT, TagKind.ENUM, TagKind.TYPEDEF)
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

    def generate_functions(self, output: TextIO):
        paths = {}
        translations = {}
        signatures = {}

        tags = self._extract_tags((TagKind.FUNCTION, TagKind.PROTOTYPE))
        for (tag, lib) in tags.values():
            paths[tag.name] = tag.path

            name = f"{tag.name}@{lib.name}"
            translations[name] = tag.name

            args = translate_types(tag.signature, self.type_table)
            ret = translate_type(tag.typeref, self.type_table)
            signatures[name] = f"fn ({', '.join(args)}) {ret}"

        contents = ""
        contents += "from typing import Dict\n"
        contents += f"TRANSLATIONS: Dict[str, str] = {translations}\n"
        contents += f"SIGNATURES: Dict[str, str] = {signatures}\n"
        contents += f"PATHS: Dict[str, str] = {paths}\n"
        output.write(contents)

    def generate_variables(self, output: TextIO):
        paths = {}
        translations = {}
        types = {}

        tags = self._extract_tags((TagKind.VARIABLE, TagKind.EXTERN))
        for (tag, lib) in tags.values():
            paths[tag.name] = tag.path

            name = f"{tag.name}@{lib.name}"
            translations[name] = tag.name
            types[name] = translate_type(tag.typeref, self.type_table)

        contents = ""
        contents += "from typing import Dict\n"
        contents += f"TRANSLATIONS: Dict[str, str] = {translations}\n"
        contents += f"TYPES: Dict[str, str] = {types}\n"
        contents += f"PATHS: Dict[str, str] = {paths}\n"
        output.write(contents)

    def _generate_type_table(self) -> Dict[str, str]:
        type_table: Dict[str, str] = {}

        for primitives in self.core_types.values():
            if primitives:
                for primitive in primitives:
                    rewritten = convert_basetype(primitive)
                    type_table[primitive] = rewritten

        type_tags = self._extract_tags(
            (TagKind.UNION, TagKind.STRUCT, TagKind.ENUM, TagKind.TYPEDEF)
        )
        for (tag, lib) in type_tags.values():
            if tag.kind in (TagKind.UNION, TagKind.STRUCT, TagKind.ENUM):
                original = f"{tag.kind.value} {tag.name}"
            else:
                original = tag.name

            new = f"{tag.name}@{lib.name}"
            type_table[original] = new

        return type_table

    def _generate_buckets(self, build=True) -> Buckets:
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

        for library, data in self.libraries.items():
            # TODO: path shouldn't be relative to cwd.
            # would make more sense to be relative to the config.yaml
            lib = Library(library, Path(data["path"]), data["includes"])
            if build:
                lib.build()
            tags = lib.tags()

            for tag in tags:
                if tag.name.startswith("__"):
                    continue
                bucket = buckets[tag.kind]
                bucket[tag.name] = (tag, lib)

        return buckets

    def _extract_tags(
        self, kinds: Collection[TagKind]
    ) -> Dict[str, Tuple[Tag, Library]]:
        if kinds is None:
            return {}

        types = {}
        for kind in kinds:
            for (tag, lib) in self.buckets[kind].values():
                types[tag.name] = (tag, lib)

        return types


def convert_basetype(name: str) -> str:
    parts = name.split()
    parts.reverse()
    return "_".join(parts)
