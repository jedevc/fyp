import re
from typing import Dict, List


def translate_types(typestr: str, type_table: Dict[str, str]) -> List[str]:
    tokens = _tokenize_type(typestr)
    return _translate_types(tokens, type_table)


def translate_type(typestr: str, type_table: Dict[str, str]) -> str:
    tokens = _tokenize_type(typestr)
    return _translate_type(tokens, type_table)


def _tokenize_type(typestr: str) -> List[str]:
    parts = re.split(r"\s|([,*()\[\]])", typestr)
    parts = [p for p in parts if p]
    return parts


def _translate_types(tokens: List[str], type_table: Dict[str, str]) -> List[str]:
    results: List[str] = []
    result: List[str] = []
    while tokens:
        part, tokens = tokens[0], tokens[1:]
        if part in ("const", "volatile", "_Noreturn", "__restrict"):
            continue

        if part == "*":
            result.insert(0, "*")
        elif part == ",":
            results.append(" ".join(result))
            result = []
        elif part.startswith("["):
            array = ["["]
            while part != "]":
                part, tokens = tokens[0], tokens[1:]
                array.append(part)
            result.insert(0, "".join(array))
        elif part == "(":
            rest, tokens = tokens[:3], tokens[3:]
            assert rest == ["*", ")", "("]

            inner = []
            count = 1
            while count > 0 and tokens:
                part, tokens = tokens[0], tokens[1:]
                if part == "(":
                    count += 1
                elif part == ")":
                    count -= 1
                else:
                    inner.append(part)

            ret_type = result.pop()
            arg_types = _translate_types(inner, type_table)
            result.append(f"* fn ({', '.join(arg_types)}) {ret_type}")
        else:
            key = part
            for i, key_piece in enumerate(reversed(result)):
                key = key_piece + " " + key
                if key in type_table:
                    result = result[: -i - 1]

            if key in type_table:
                result.append(type_table[key])
            elif part in type_table:
                result.append(type_table[part])
            else:
                result.append(part)

    if result:
        results.append(" ".join(result))

    if results == ["void"]:
        results = []

    return results


def _translate_type(tokens: List[str], type_table: Dict[str, str]) -> str:
    tps = _translate_types(tokens, type_table)
    if tps:
        return tps[0]
    else:
        return "void"
