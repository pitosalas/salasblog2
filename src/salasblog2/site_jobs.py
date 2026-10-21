#!/usr/bin/env python3
# site_jobs — Run site generation in a child process, one at a time
# Author: Pito Salas and Claude Code
# Version: 2
# Created: 2026-10-20
# Updated: 2026-10-20
# Open Source Under MIT license
"""
Site generation off the server process (F56).

Rendering thousands of pages is CPU-bound Python. Run in a server thread, it
holds the GIL and every page request waits behind it. `run_generation` runs
the same work as a `bg` CLI command in a child process instead, so the
server keeps answering requests while it renders.

A module-level lock lets only one generation child run at a time; a second
caller waits for the first to finish, as two writers to `output/` at once
would race. A failed child raises with its stderr.
"""

import logging
import subprocess
import sys
import threading

logger = logging.getLogger(__name__)

GENERATION_LOCK = threading.Lock()


def generation_command(args: list[str]) -> list[str]:
    """The command line that runs `bg <args>` with this interpreter."""
    return [sys.executable, "-m", "salasblog2.cli", *args]


def run_generation(args: list[str]) -> None:
    """Run `bg <args>` (e.g. `["generate"]`) in a child process and wait.

    Raises RuntimeError with the child's stderr when it exits non-zero.
    """
    command = generation_command(args)
    with GENERATION_LOCK:
        logger.info(f"Generation START: bg {' '.join(args)}")
        result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"bg {' '.join(args)} failed ({result.returncode}): "
            f"{result.stderr.strip()[-2000:]}"
        )
    logger.info(f"Generation DONE: bg {' '.join(args)}")
