#!/usr/bin/env python3
"""Integration tests for the Codex notify handoff and playback policy."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
NOTIFIER = REPO / ".local/bin/codex-touchbar-notify"
DAEMON = REPO / ".local/bin/codex-touchbar-daemon"


def wait_for(predicate, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError("condition was not met before timeout")


class CodexTouchbarTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.state = self.root / "state"
        self.assets = self.root / "assets"
        self.assets.mkdir()
        (self.assets / "codex-train.mkv").touch()
        (self.assets / "codex-vines.mkv").touch()
        self.log = self.root / "plays.log"
        self.player = self.root / "fake-touchbar"
        self.player.write_text(
            """#!/usr/bin/env python3
import os
import pathlib
import sys
import time

if os.environ.get("FAKE_PLAYER_FAIL") == "1":
    raise SystemExit(9)
with pathlib.Path(os.environ["FAKE_PLAYER_LOG"]).open("a", encoding="utf-8") as log:
    log.write(pathlib.Path(sys.argv[-1]).name + "\\n")
pathlib.Path(os.environ["TOUCHBAR_STARTED_FILE"]).touch()
time.sleep(0.28)
""",
            encoding="utf-8",
        )
        self.player.chmod(0o755)
        self.environment = os.environ.copy()
        self.environment.update(
            {
                "CODEX_TOUCHBAR_STATE_DIR": str(self.state),
                "CODEX_TOUCHBAR_ASSET_DIR": str(self.assets),
                "CODEX_TOUCHBAR_COMMAND": str(self.player),
                "FAKE_PLAYER_LOG": str(self.log),
            }
        )
        self.daemons: list[subprocess.Popen[bytes]] = []

    def tearDown(self) -> None:
        for daemon in self.daemons:
            if daemon.poll() is None:
                daemon.terminate()
                daemon.wait(timeout=2)
        self.temporary.cleanup()

    def notify(self, payload: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run([str(NOTIFIER), payload], env=self.environment, check=False)

    def start_daemon(self, extra_environment: dict[str, str] | None = None) -> subprocess.Popen[bytes]:
        environment = self.environment.copy()
        if extra_environment:
            environment.update(extra_environment)
        daemon = subprocess.Popen([str(DAEMON)], env=environment)
        self.daemons.append(daemon)
        time.sleep(0.12)
        return daemon

    def plays(self) -> list[str]:
        if not self.log.exists():
            return []
        return self.log.read_text(encoding="utf-8").splitlines()

    def test_notifier_accepts_only_completion_objects(self) -> None:
        for payload in ("not-json", "[]", '{"type":"approval-requested"}'):
            self.assertEqual(self.notify(payload).returncode, 0)
        self.assertFalse((self.state / "events").exists())

        self.assertEqual(
            self.notify('{"type":"agent-turn-complete","thread-id":"thread","turn-id":"turn"}').returncode,
            0,
        )
        events = list((self.state / "events").glob("*.event"))
        self.assertEqual(len(events), 1)
        record = json.loads(events[0].read_text(encoding="utf-8"))
        self.assertEqual(record["type"], "agent-turn-complete")
        self.assertIsInstance(record["received_ns"], int)

    def test_stale_and_busy_events_are_skipped_and_idle_events_alternate(self) -> None:
        self.notify('{"type":"agent-turn-complete"}')
        self.start_daemon()
        self.assertEqual(self.plays(), [])

        self.notify('{"type":"agent-turn-complete"}')
        wait_for(lambda: len(self.plays()) == 1)
        self.notify('{"type":"agent-turn-complete"}')
        time.sleep(0.38)
        self.assertEqual(self.plays(), ["codex-train.mkv"])

        self.notify('{"type":"agent-turn-complete"}')
        wait_for(lambda: len(self.plays()) == 2)
        self.assertEqual(self.plays(), ["codex-train.mkv", "codex-vines.mkv"])
        wait_for(
            lambda: (self.state / "next-animation").exists()
            and (self.state / "next-animation").read_text().strip() == "train"
        )
        self.assertEqual((self.state / "next-animation").read_text().strip(), "train")

    def test_failed_player_does_not_advance_selection(self) -> None:
        self.start_daemon({"FAKE_PLAYER_FAIL": "1"})
        self.notify('{"type":"agent-turn-complete"}')
        time.sleep(0.25)
        self.assertEqual(self.plays(), [])
        self.assertFalse((self.state / "next-animation").exists())


if __name__ == "__main__":
    unittest.main()
