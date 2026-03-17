import os
import random
import tempfile
import time

from .logger import get_logger

logger = get_logger("utils.file_handler")


def create_temp_sol_file(code: str) -> str:
    timestamp = int(time.time() * 1000)
    suffix_random = random.randint(1000, 9999)
    filename = f"smartpatch_{timestamp}_{suffix_random}.sol"
    path = os.path.join(tempfile.gettempdir(), filename)

    with open(path, "w", encoding="utf-8") as handle:
        handle.write(code)

    logger.info("Created temp solidity file at %s", path)
    return os.path.abspath(path)


def cleanup_temp_file(filepath: str) -> None:
    try:
        os.remove(filepath)
        logger.info("Deleted temp file %s", filepath)
    except FileNotFoundError:
        logger.warning("Temp file already removed: %s", filepath)


def validate_solidity_syntax(code: str) -> tuple[bool, str]:
    stripped = code.strip()
    if not stripped:
        return False, "Empty Solidity code provided"

    first_statement = ""
    in_block_comment = False
    for line in code.splitlines():
        candidate = line.strip().lstrip("\ufeff")
        if not candidate:
            continue

        if in_block_comment:
            if "*/" in candidate:
                in_block_comment = False
                candidate = candidate.split("*/", 1)[1].strip()
            else:
                continue

        while candidate.startswith("/*"):
            if "*/" in candidate:
                candidate = candidate.split("*/", 1)[1].strip()
            else:
                in_block_comment = True
                candidate = ""
                break

        if not candidate or candidate.startswith("//"):
            continue

        if candidate.lower().startswith("spdx-license-identifier:"):
            continue

        first_statement = candidate
        break

    if not first_statement.lower().startswith("pragma solidity"):
        return False, "Solidity code must start with a pragma solidity declaration"

    if "contract" not in stripped:
        return False, "Solidity code must include at least one contract declaration"

    balance = 0
    for char in stripped:
        if char == "{":
            balance += 1
        elif char == "}":
            balance -= 1
            if balance < 0:
                return False, "Unbalanced braces in Solidity code"

    if balance != 0:
        return False, "Unbalanced braces in Solidity code"

    return True, ""
