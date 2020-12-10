import argparse
import glob
import json

from . import libc
from .tags import TagKind


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("outfile", type=argparse.FileType("w"))
    args = arg_parser.parse_args()

    libc.prepare()

    targets = []
    targets += glob.glob("./include/**/*.h", recursive=True)
    targets += glob.glob("./obj/include/**/*.h", recursive=True)
    targets += glob.glob("./arch/x86_64/**/*.h", recursive=True)

    tags = []
    for target in targets:
        tags += libc.ctags(target)

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
    for tag in tags:
        if tag.name.startswith("__"):
            continue

        bucket = buckets[tag.kind]
        bucket[tag.name] = tag

    types = extract(
        buckets,
        [
            TagKind.UNION,
            TagKind.STRUCT,
            TagKind.ENUM,
            TagKind.TYPEDEF,
        ],
        LangType,
    )
    variables = extract(
        buckets,
        [
            TagKind.VARIABLE,
            TagKind.EXTERN,
        ],
        LangVariable,
    )
    functions = extract(
        buckets,
        [
            TagKind.FUNCTION,
            TagKind.PROTOTYPE,
        ],
        LangFunction,
    )

    result = {
        "types": types,
        "variables": variables,
        "functions": functions,
    }
    json.dump(result, args.outfile, indent=4, cls=CustomEncoder)


class LangType:
    def __init__(self, tag):
        self.name = tag.name
        if tag.kind in (TagKind.UNION, TagKind.STRUCT, TagKind.ENUM):
            self.prefix = tag.kind
        elif tag.kind == TagKind.TYPEDEF:
            self.prefix = None
        else:
            raise RuntimeError(f"tag kind {tag.kind} cannot be made a type")

        self.path = tag.path

    def asdict(self):
        return {
            "name": self.name,
            "prefix": self.prefix,
            "path": self.path,
        }


class LangVariable:
    def __init__(self, tag):
        self.name = tag.name
        self.type = " ".join(tag.typeref.split(":")).removeprefix("typename ")
        self.path = tag.path

    def asdict(self):
        return {
            "name": self.name,
            "type": self.type,
            "path": self.path,
        }


class LangFunction:
    def __init__(self, tag):
        self.name = tag.name
        self.path = tag.path
        try:
            self.type = " ".join(tag.typeref.split(":")).removeprefix("typename ")
        except AttributeError:
            self.type = "void"
        self.args = tag.signature

    def asdict(self):
        return {
            "name": self.name,
            "type": self.type,
            "args": self.args,
            "path": self.path,
        }


def extract(buckets, kinds, constructor):
    if kinds is None:
        return {}

    types = {}
    for kind in kinds:
        for tag in buckets[kind].values():
            types[tag.name] = constructor(tag)

    return types


class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, LangType):
            return o.asdict()
        if isinstance(o, LangVariable):
            return o.asdict()
        if isinstance(o, LangFunction):
            return o.asdict()
        else:
            return super().default(o)
