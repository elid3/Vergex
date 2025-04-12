import requests
from bs4 import BeautifulSoup
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque
import argparse

WINDOWS_VERSION_MAP = {
    "10": "windows 10",
    "11": "windows 11",
    "7": "windows 7",
    "8": "windows 8",
    "81": "windows 8.1",
    "vista": "windows vista",
    "xp": "windows xp",
}

PRIMITIVES = """
typedef void* PVOID;
typedef unsigned long ULONG;
typedef unsigned short USHORT;
typedef unsigned char UCHAR;
typedef unsigned long long ULONG64;
typedef long LONG;
typedef long long LONGLONG;
typedef unsigned long long ULONGLONG;
typedef wchar_t* PWSTR;
typedef char CHAR;
typedef short SHORT;
typedef unsigned int UINT;
typedef unsigned char BOOLEAN;
typedef void VOID;
typedef void* HANDLE;
typedef long NTSTATUS;
typedef unsigned long long ULONG_PTR;
"""

visited = set()
structs = {}
lock = threading.Lock()

def resolve_version(alias):
    version = WINDOWS_VERSION_MAP.get(alias.lower())
    if not version:
        raise ValueError(f"Unsupported Windows version: {alias}")
    return version

def get_struct_url(version, release):
    return f"https://www.vergiliusproject.com/kernels/x64/{version.replace(' ', '-')}/{release}/"

def clean_definition(raw_def):
    lines = raw_def.splitlines()
    out = []
    for line in lines:
        line = re.sub(r"//\s*0x[0-9a-fA-F]+ bytes \(sizeof\)", "", line).strip()
        if line.lower() == "copy" or not line:
            continue
        out.append(line)
    return "\n".join(out)

def normalize_tokens(defn):
    return (defn.replace("unionvolatile", "union")
                .replace("volatileunion", "union")
                .replace("structunion", "struct union")
                .replace("unionstruct", "union struct"))

def fetch_struct(name, base_url):
    with lock:
        if name in visited:
            return
        visited.add(name)

    url = base_url + name
    print(f"Fetching {name}...")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as err:
        print(f"Failed to get {name}: {err}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    pre = soup.find("pre")
    if not pre:
        print(f"No struct definition found for {name}")
        return

    raw = pre.get_text()
    cleaned = normalize_tokens(clean_definition(raw))

    with lock:
        structs[name] = cleaned

    deps = re.findall(r"struct (_[A-Za-z0-9_]+)", cleaned)
    return [d for d in deps if d != name]

def generate_struct_header(entry_struct, version, release, output_file, thread_count):
    base_url = get_struct_url(version, release)
    queue = deque([entry_struct])
    with ThreadPoolExecutor(thread_count) as executor:
        futures = {}

        while queue or futures:
            while queue:
                name = queue.popleft()
                if name not in visited:
                    futures[executor.submit(fetch_struct, name, base_url)] = name

            for future in list(as_completed(futures)):
                name = futures.pop(future)
                try:
                    nested = future.result()
                    if nested:
                        for dep in nested:
                            if dep not in visited:
                                queue.append(dep)
                except Exception as err:
                    print(f"Error while processing {name}: {err}")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("// Generated using VergiliusProject.com\n")
        f.write(f"// Version: {version}\n")
        f.write(f"// Release: {release}\n\n")
        f.write("#pragma once\n\n")
        f.write(PRIMITIVES)
        f.write("\n")

        for name in sorted(structs.keys()):
            f.write(f"// {name}\n")
            f.write(structs[name])
            f.write("\n\n")

        # Pointer typedefs
        f.write("// Pointer types\n")
        for name in sorted(structs.keys()):
            base = name.lstrip("_")
            f.write(f"typedef struct {name}* P{base};\n")

    print(f"Header written to: {output_file} ({len(structs)} structs)")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch Windows kernel structs from Vergilius Project for use in Ghidra or similar tools."
    )
    parser.add_argument("-s", "--struct", required=True, help="Struct name to start from, e.g. _EPROCESS")
    parser.add_argument("-v", "--version", default="10", help="Windows version (10, 11, 7, xp, etc.)")
    parser.add_argument("-r", "--release", required=True, help="Windows release (e.g. 1809, 22H2)")
    parser.add_argument("-o", "--output", help="Output filename (.h)")
    parser.add_argument("-t", "--threads", type=int, default=10, help="Number of threads (default: 10)")
    parser.add_argument("--list-versions", action="store_true", help="Show available Windows version aliases")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    if args.list_versions:
        print("Available version aliases:")
        for k, v in WINDOWS_VERSION_MAP.items():
            print(f"  {k:<5} → {v}")
        exit()

    try:
        full_version = resolve_version(args.version)
    except ValueError as err:
        print(err)
        exit(1)

    output = args.output or f"{args.struct.strip('_').lower()}_{args.version}_{args.release}.h"
    generate_struct_header(args.struct, full_version, args.release.lower(), output, args.threads)
