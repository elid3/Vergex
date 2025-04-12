# Vergex

**Vergex** is a recursive header generator for Windows kernel structures, using publicly available data from the [Vergilius Project](https://www.vergiliusproject.com/). It fetches the specified struct and all nested dependencies, generating a clean, ready-to-import C header — especially useful for reverse engineering in **Ghidra**.

---

## Features

- Recursive struct resolution (follows nested definitions)
- Outputs typedef-ready C headers for reverse engineering
- Optimized for Ghidra, IDA Pro, or other RE tools
- Multi-threaded scraping for fast performance
- Supports various Windows versions and releases

---

## Disclaimer

> **Vergex is not affiliated with or endorsed by the Vergilius Project.**  
> It simply automates the retrieval and formatting of publicly available kernel struct data from their site.

---

## Installation

### Requirements

- Python 3.7+
- `requests`
- `beautifulsoup4`

Install dependencies:

```bash
pip install -r requirements.txt
```

Or:

```bash
pip install requests beautifulsoup4
```

---

## Usage

```bash
python generate_structs.py -s <STRUCT_NAME> -v <VERSION> -r <RELEASE> [-o <OUTPUT>] [-t <THREADS>]
```

### Example

```bash
python generate_structs.py -s _EPROCESS -v 10 -r 22H2 -o eprocess_win10_22h2.h
```

### Arguments

| Argument           | Description                                             |
|--------------------|---------------------------------------------------------|
| `-s`, `--struct`   | **(Required)** Root struct name (e.g. `_EPROCESS`)      |
| `-v`, `--version`  | Windows version alias (`10`, `11`, `7`, `xp`, etc.)     |
| `-r`, `--release`  | Windows release string (e.g. `1809`, `22H2`)            |
| `-o`, `--output`   | Output filename (optional; auto-named if omitted)       |
| `-t`, `--threads`  | Max number of threads (default: `10`)                   |
| `--list-versions`  | Print supported version aliases                         |

---

## Output

The output is a single `.h` file containing:

- All resolved kernel structs
- Base typedefs for primitives
- Pointer typedefs (`typedef struct _FOO* PFOO;`)

This header can be directly imported into **Ghidra** using the "Parse C Header File" option to enhance kernel RE analysis.

---

## Example Snippet

```c
typedef struct _EPROCESS {
    // ...
} EPROCESS;

typedef struct _EPROCESS* PEPROCESS;
```

---

## Credits

Built for reverse engineers, by a reverse engineer. Struct data sourced from the excellent [Vergilius Project](https://www.vergiliusproject.com/).
