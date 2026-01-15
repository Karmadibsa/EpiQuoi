from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class ScrapyRunError(RuntimeError):
    pass


class ScrapyRunner:
    """
    Runs Scrapy spiders via subprocess using the current Python interpreter.

    Notes:
    - We serialize runs with a lock to avoid overlapping Scrapy executions in the same project.
    - We write output to a unique temp file to avoid stdout pollution and concurrency issues.
    """

    def __init__(self, project_dir: Path, timeout_sec: int = 90) -> None:
        self._project_dir = project_dir
        self._timeout_sec = timeout_sec
        self._lock = asyncio.Lock()

    async def run_spider_json(self, spider_name: str) -> Tuple[List[Dict[str, Any]], str, int]:
        """
        Returns: (items, stderr, duration_ms)
        """
        if not self._project_dir.exists():
            raise ScrapyRunError(f"Scrapy project dir not found: {self._project_dir}")

        async with self._lock:
            start = time.time()

            tmp = NamedTemporaryFile(
                mode="w+b",
                suffix=".json",
                delete=False,
                dir=str(self._project_dir),
            )
            tmp_path = Path(tmp.name)
            tmp.close()

            cmd = [
                sys.executable,
                "-m",
                "scrapy",
                "crawl",
                spider_name,
                "-O",
                tmp_path.name,  # write into project dir (cwd)
                "--nolog",
            ]

            logger.info("Running Scrapy: %s (cwd=%s)", " ".join(cmd), self._project_dir)
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self._project_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=self._timeout_sec)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                self._safe_unlink(tmp_path)
                raise ScrapyRunError(f"Scrapy timeout after {self._timeout_sec}s (spider={spider_name})")

            duration_ms = int((time.time() - start) * 1000)
            stderr = (stderr_b or b"").decode("utf-8", errors="replace")

            if proc.returncode != 0:
                self._safe_unlink(tmp_path)
                raise ScrapyRunError(f"Scrapy failed (code={proc.returncode}). Stderr: {stderr[-500:]}")

            try:
                data = json.loads(tmp_path.read_text(encoding="utf-8"))
            except Exception as e:
                raw_head = tmp_path.read_text(encoding="utf-8", errors="replace")[:1000]
                self._safe_unlink(tmp_path)
                raise ScrapyRunError(f"Invalid JSON output: {e}. Raw head: {raw_head}")
            finally:
                self._safe_unlink(tmp_path)

            if not isinstance(data, list):
                raise ScrapyRunError(f"Unexpected Scrapy output type: {type(data)} (expected list)")

            return data, stderr, duration_ms

    @staticmethod
    def _safe_unlink(path: Path) -> None:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            logger.debug("Failed to delete temp file: %s", path, exc_info=True)

