"""
A hand-tailored algorithm for extracting global values and functions out of
musl libc.
"""

import argparse
import glob
import json
import os
import re
import shlex
import subprocess
import sys

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("outfile", type=argparse.FileType("w"))
    args = arg_parser.parse_args()

    prepare()

    functions = {}
    externs = {}
    for path in glob.iglob("./include/*.h"):
        output = preprocess(path)
        lines = output.split("\n")
        funcs = []
        exts = []

        for line in lines:
            line = line.strip()
            line = line.rstrip(";")
            if not line or line.startswith("#"):
                continue
            line = line.replace("\n", " ")

            line = line.split("__attribute__")[0]

            if "(" in line and line.endswith(")"):
                func = line
                if func.startswith("_Noreturn "):
                    func = func[len("_Noreturn "):]
                if func.startswith("static "):
                    func = func[len("static "):]
                if func.startswith("inline "):
                    func = func[len("inline "):]
                funcs.append(func)
            elif line.startswith("extern "):
                exts.append(line[len("extern "):])
        
        if funcs:
            functions[os.path.basename(path)] = funcs
        if exts:
            externs[os.path.basename(path)] = exts

    json.dump({
        "externs": externs,
        "functions": functions,
    }, args.outfile, indent=2)

def prepare():
    cwd = os.path.basename(os.getcwd())
    if re.match(r"musl-\d+\.\d+\.\d+", cwd) is None:
        print("error: not currently in a libmusl directory", file=sys.stderr)
        sys.exit(1)

    run_cmd("./configure")
    run_cmd("make -j")

def preprocess(path: str):
    cflags = ["-std=c99"]
    cflags = " ".join(cflags)

    includes = ["./", "./include/", "./obj/include/", "./arch/generic", "./arch/x86_64/"]
    includes = " ".join(f"-I {include}" for include in includes)

    return run_cmd(f"gcc -E {cflags} {includes} '{path}'", capture_output=True)

def run_cmd(cmd: str, capture_output=False):
    print(f"$ {cmd}")
    cmd_words = shlex.split(cmd)
    if capture_output:
        proc = subprocess.run(cmd_words, check=True, stdout=subprocess.PIPE)
        return proc.stdout.decode()
    else:
        subprocess.run(cmd_words, check=True)
        print()
        return None

if __name__ == "__main__":
    main()
