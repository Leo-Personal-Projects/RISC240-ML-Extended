#!/usr/bin/env python3
"""
run_tests.py

Automates this flow for every test:
    .asm -> MLASM.py -> .hex -> memory.hex -> VCS RTL -> state dump -> compare

Expected project layout:

RISC240GPU/
├── constants.sv
├── library.sv
├── alu.sv
├── regfile.sv
├── vector_regfile.sv
├── ML_alu.sv
├── dot_product_unit.sv
├── vector_load_unit.sv
├── vector_store_unit.sv
├── accumulator.sv
├── datapath.sv
├── controlpath.sv
├── memory.sv
├── RISC240.sv
├── verification/
│   ├── risc240_tb.sv
│   ├── expected_results.json
│   └── run_tests.py
├── assembler/
│   └── MLASM.py
└── tests/
    └── test01_add.asm ...
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_TEST_DIR = PROJECT_ROOT / "tests"
DEFAULT_ASSEMBLER = PROJECT_ROOT / "assembler" / "MLASM.py"
EXPECTED_FILE = SCRIPT_DIR / "expected_results.json"
TB_FILE = SCRIPT_DIR / "risc240_tb.sv"
BUILD_DIR = SCRIPT_DIR / "build"
SIMV = BUILD_DIR / "simv"

RTL_FILES = [
    "constants.sv",
    "library.sv",
    "alu.sv",
    "regfile.sv",
    "vector_regfile.sv",
    "ML_alu.sv",
    "dot_product_unit.sv",
    "vector_load_unit.sv",
    "vector_store_unit.sv",
    "accumulator.sv",
    "datapath.sv",
    "controlpath.sv",
    "memory.sv",
    "RISC240.sv",
]


class RegressionError(Exception):
    pass


def run_command(
    command: list[str],
    *,
    cwd: Path,
    description: str,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if result.returncode != 0:
        raise RegressionError(
            f"{description} failed with exit code {result.returncode}\n"
            f"{result.stdout}"
        )

    return result


def check_inputs(assembler: Path, test_dir: Path) -> None:
    missing = []

    if not assembler.exists():
        missing.append(str(assembler))

    if not TB_FILE.exists():
        missing.append(str(TB_FILE))

    if not EXPECTED_FILE.exists():
        missing.append(str(EXPECTED_FILE))

    for filename in RTL_FILES:
        path = PROJECT_ROOT / filename
        if not path.exists():
            missing.append(str(path))

    if not test_dir.exists():
        missing.append(str(test_dir))

    if missing:
        raise RegressionError(
            "Missing required files:\n  " + "\n  ".join(missing)
        )


def compile_rtl(force: bool = False) -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    if SIMV.exists() and not force:
        return

    sources = [str(PROJECT_ROOT / name) for name in RTL_FILES]
    sources.append(str(TB_FILE))

    command = [
        "vcs",
        "-full64",
        "-sverilog",
        "-timescale=1ns/1ps",
        "+v2k",
        "-debug_access+all",
        "-top",
        "risc240_tb",
        "-o",
        str(SIMV),
        *sources,
    ]

    result = run_command(
        command,
        cwd=BUILD_DIR,
        description="VCS compilation",
    )

    print(result.stdout)


def assemble_test(assembler: Path, source: Path) -> Path:
    result = run_command(
        [sys.executable, str(assembler), str(source)],
        cwd=source.parent,
        description=f"assembly of {source.name}",
    )

    hex_path = source.with_suffix(".hex")

    if not hex_path.exists():
        raise RegressionError(
            f"assembler did not create {hex_path}"
        )

    return hex_path


def parse_state(path: Path) -> dict[str, str]:
    if not path.exists():
        raise RegressionError(
            f"RTL did not create state dump {path}"
        )

    state: dict[str, str] = {}

    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        text = raw.strip()

        if not text:
            continue

        if "=" not in text:
            raise RegressionError(
                f"{path}:{line_number}: malformed state line '{text}'"
            )

        key, value = text.split("=", 1)
        state[key.strip().upper()] = value.strip().upper()

    return state


def compare_state(
    test_name: str,
    actual: dict[str, str],
    expected: dict[str, str],
) -> list[str]:
    failures: list[str] = []

    # R0 is always checked, regardless of the per-test expectations.
    expected_with_invariants = {"R0": "0000", **expected}

    for key, expected_value in expected_with_invariants.items():
        key = key.upper()
        expected_value = expected_value.upper()
        actual_value = actual.get(key)

        if actual_value is None:
            failures.append(
                f"{key}: missing from RTL state dump"
            )
        elif actual_value != expected_value:
            failures.append(
                f"{key}: expected {expected_value}, got {actual_value}"
            )

    return failures


def run_one_test(
    source: Path,
    assembler: Path,
    expected: dict[str, str],
    max_cycles: int,
    keep_output: bool,
) -> tuple[bool, str]:
    test_name = source.stem
    test_build = BUILD_DIR / test_name
    test_build.mkdir(parents=True, exist_ok=True)

    hex_path = assemble_test(assembler, source)
    shutil.copy2(hex_path, test_build / "memory.hex")

    state_path = test_build / "rtl_state.txt"

    result = subprocess.run(
        [
            str(SIMV),
            f"+STATE={state_path}",
            f"+MAX_CYCLES={max_cycles}",
        ],
        cwd=test_build,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    log_path = test_build / "simulation.log"
    log_path.write_text(result.stdout, encoding="utf-8")

    if result.returncode != 0:
        return (
            False,
            f"simulation exited with code {result.returncode}; "
            f"see {log_path}",
        )

    actual = parse_state(state_path)
    failures = compare_state(test_name, actual, expected)

    if failures:
        return (
            False,
            "; ".join(failures) + f"; see {state_path}",
        )

    if not keep_output:
        # Keep the log/state on failures only. Successful build products may
        # be deleted to keep the verification directory clean.
        shutil.rmtree(test_build)

    return True, "architectural state matched"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run RISC240 VCS RTL regression tests"
    )

    parser.add_argument(
        "--assembler",
        type=Path,
        default=DEFAULT_ASSEMBLER,
        help=f"path to MLASM.py (default: {DEFAULT_ASSEMBLER})",
    )

    parser.add_argument(
        "--tests",
        type=Path,
        default=DEFAULT_TEST_DIR,
        help=f"test directory (default: {DEFAULT_TEST_DIR})",
    )

    parser.add_argument(
        "--test",
        help="run one test by stem, such as test01_add",
    )

    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="force VCS recompilation",
    )

    parser.add_argument(
        "--keep-output",
        action="store_true",
        help="keep state and log files for passing tests",
    )

    parser.add_argument(
        "--max-cycles",
        type=int,
        default=50000,
        help="RTL cycle timeout per test",
    )

    args = parser.parse_args()

    assembler = args.assembler.resolve()
    test_dir = args.tests.resolve()

    try:
        check_inputs(assembler, test_dir)

        expected_all = json.loads(
            EXPECTED_FILE.read_text(encoding="utf-8")
        )

        compile_rtl(force=args.rebuild)

        if args.test:
            sources = [test_dir / f"{args.test}.asm"]
        else:
            sources = sorted(test_dir.glob("test*.asm"))

        if not sources:
            raise RegressionError(
                f"no assembly tests found in {test_dir}"
            )

        passed = 0
        failed = 0

        for source in sources:
            if not source.exists():
                print(f"FAIL  {source.stem}: file not found")
                failed += 1
                continue

            expected = expected_all.get(source.stem)

            if expected is None:
                print(
                    f"FAIL  {source.stem}: no entry in "
                    "expected_results.json"
                )
                failed += 1
                continue

            try:
                ok, message = run_one_test(
                    source,
                    assembler,
                    expected,
                    args.max_cycles,
                    args.keep_output,
                )
            except Exception as exc:
                ok = False
                message = str(exc)

            if ok:
                print(f"PASS  {source.stem}: {message}")
                passed += 1
            else:
                print(f"FAIL  {source.stem}: {message}")
                failed += 1

        print()
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Total : {passed + failed}")

        return 0 if failed == 0 else 1

    except (RegressionError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
