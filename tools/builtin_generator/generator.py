import argparse
import json
from pathlib import Path
from typing import Any, Collection, Dict, List, Tuple

import yaml

from .library import Library
from .tags import Tag, TagKind
from .translate import translate_type, translate_types

Bucket = List[Tuple[Tag, Library]]
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

    gen = Generator(config, build=args.build)
    targets = {
        "types": gen.generate_types,
        "functions": gen.generate_functions,
        "variables": gen.generate_variables,
    }
    for target, generator in targets.items():
        path = Path(args.directory, f"{target}.json")
        with path.open("w") as f:
            json.dump(generator(), f, indent=4)


class Generator:
    def __init__(self, config: Dict[str, Any], build=True):
        self.libraries = config.get("libraries", {})

        core = config.get("core", {})
        self.core_types = core.get("types", {})
        self.core_includes = core.get("include", {})
        self.core_typemap = core.get("typemap", {})

        self.buckets = self._generate_buckets(build=build)
        self.type_table = self._generate_type_table()

    def generate_types(self) -> Dict[str, Any]:
        translations = {}
        paths = {}
        metatypes = {}
        metatype_graph = {}

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
            metatype_graph[metatype] = self.core_typemap.get(metatype, [])

        # Extract types from libc
        tags = self._extract_tags(
            (TagKind.UNION, TagKind.STRUCT, TagKind.ENUM, TagKind.TYPEDEF)
        )
        for (tag, lib) in tags:
            name = f"{tag.name}@{lib.name}.{tag.shortpath}"
            paths[name] = tag.path
            if tag.kind in (TagKind.UNION, TagKind.STRUCT, TagKind.ENUM):
                translations[name] = f"{tag.kind.value} {tag.name}"
            else:
                translations[name] = tag.name

        return {
            "metas": list(metatypes.keys()),
            "meta_graph": metatype_graph,
            "meta_parents": {
                primitive: metatype
                for metatype, primitives in metatypes.items()
                for primitive in primitives
            },
            "translations": translations,
            "paths": paths,
        }

    def generate_functions(self) -> Dict[str, Any]:
        paths = {}
        translations = {}
        signatures = {}

        tags = self._extract_tags((TagKind.FUNCTION, TagKind.PROTOTYPE))
        for (tag, lib) in tags:
            name = f"{tag.name}@{lib.name}.{tag.shortpath}"

            paths[name] = tag.path
            translations[name] = tag.name

            args = translate_types(tag.signature, self.type_table)
            ret = translate_type(tag.typeref, self.type_table)
            signatures[name] = f"fn ({', '.join(args)}) {ret}"

        return {
            "translations": translations,
            "signatures": signatures,
            "paths": paths,
        }

    def generate_variables(self) -> Dict[str, Any]:
        paths = {}
        translations = {}
        types = {}

        tags = self._extract_tags((TagKind.VARIABLE, TagKind.EXTERN))
        for (tag, lib) in tags:
            name = f"{tag.name}@{lib.name}.{tag.shortpath}"

            paths[name] = tag.path

            translations[name] = tag.name
            types[name] = translate_type(tag.typeref, self.type_table)

        return {
            "translations": translations,
            "types": types,
            "paths": paths,
        }

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
        for (tag, lib) in type_tags:
            if tag.kind in (TagKind.UNION, TagKind.STRUCT, TagKind.ENUM):
                original = f"{tag.kind.value} {tag.name}"
            else:
                original = tag.name

            new = f"{tag.name}@{lib.name}.{tag.shortpath}"
            type_table[original] = new

        return type_table

    def _generate_buckets(self, build=True) -> Buckets:
        buckets: Buckets = {
            TagKind.MACRO: [],
            TagKind.EXTERN: [],
            TagKind.PROTOTYPE: [],
            TagKind.FUNCTION: [],
            TagKind.TYPEDEF: [],
            TagKind.UNION: [],
            TagKind.STRUCT: [],
            TagKind.MEMBER: [],
            TagKind.ENUM: [],
            TagKind.ENUMERATOR: [],
            TagKind.VARIABLE: [],
        }

        for library, data in self.libraries.items():
            # TODO: path shouldn't be relative to cwd.
            # would make more sense to be relative to the config.yaml
            lib = Library(
                library, Path(data["root"]), data["include"], data["include_paths"]
            )
            if build:
                lib.build()
            tags = lib.tags()

            for tag in tags:
                if tag.name.startswith("__"):
                    continue
                bucket = buckets[tag.kind]
                bucket.append((tag, lib))

        return buckets

    def _extract_tags(self, kinds: Collection[TagKind]) -> List[Tuple[Tag, Library]]:
        if kinds is None:
            return []

        types = []
        for kind in kinds:
            for (tag, lib) in self.buckets[kind]:
                types.append((tag, lib))

        return types


def convert_basetype(name: str) -> str:
    parts = name.split()
    parts.reverse()
    return "_".join(parts)
