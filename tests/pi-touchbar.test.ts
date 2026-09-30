import { describe, expect, mock, test } from "bun:test";
import { mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, rmdirSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import touchbarNotify from "../.pi/agent/extensions/touchbar-notify";

type Handler = (event: { type: "agent_settled" }, ctx: ExtensionContext) => Promise<void>;
const repo = resolve(import.meta.dir, "..");
const notifier = join(repo, ".local/bin/codex-touchbar-notify");
const helper = join(homedir(), ".local/bin/codex-touchbar-notify");
const result = { stdout: "", stderr: "", code: 0, killed: false };

function harness(exec = mock<ExtensionAPI["exec"]>(async () => result)) {
  const handlers = new Map<string, Handler>();
  touchbarNotify({
    on: (event: string, handler: Handler) => handlers.set(event, handler),
    exec,
  } as unknown as ExtensionAPI);
  return { handlers, exec, settle: handlers.get("agent_settled")! };
}

function context(mode = "tui"): ExtensionContext {
  return {
    mode,
    sessionManager: {
      getSessionId: () => 'pi-session; "not a shell command"',
      getLeafId: () => "pi-leaf",
    },
  } as unknown as ExtensionContext;
}

async function waitFor(predicate: () => boolean): Promise<void> {
  const deadline = Date.now() + 3000;
  while (Date.now() < deadline) {
    if (predicate()) return;
    await Bun.sleep(20);
  }
  throw new Error("condition was not met before timeout");
}

describe("Pi Touch Bar completion hook", () => {
  test("registers only final settlement and does nothing during loading", () => {
    const { handlers, exec } = harness();
    expect([...handlers.keys()]).toEqual(["agent_settled"]);
    expect(exec).not.toHaveBeenCalled();
  });

  test("sends only completion metadata as one JSON argument with a timeout", async () => {
    const { exec, settle } = harness();
    await settle({ type: "agent_settled" }, context());
    expect(exec).toHaveBeenCalledTimes(1);
    const [command, args, options] = exec.mock.calls[0];
    expect(command).toBe(helper);
    expect(args).toHaveLength(1);
    expect(JSON.parse(args[0])).toEqual({
      type: "agent-turn-complete",
      "thread-id": 'pi-session; "not a shell command"',
      "turn-id": "pi-leaf",
    });
    expect(options).toEqual({ timeout: 2000 });
  });

  test.each(["json", "print", "rpc"])("does not notify from %s workers", async (mode) => {
    const { exec, settle } = harness();
    await settle({ type: "agent_settled" }, context(mode));
    expect(exec).not.toHaveBeenCalled();
  });

  test("delivery exceptions cannot fail the turn", async () => {
    const { settle } = harness(mock(async () => { throw new Error("missing helper"); }));
    await expect(settle({ type: "agent_settled" }, context())).resolves.toBeUndefined();
  });

  test("nonzero helper exits cannot fail the turn", async () => {
    const { settle } = harness(mock(async () => ({ ...result, code: 1 })));
    await expect(settle({ type: "agent_settled" }, context())).resolves.toBeUndefined();
  });

  test("Pi and Codex share persistent alternation and skip busy completions", async () => {
    const artifacts = join(repo, ".test-artifacts");
    mkdirSync(artifacts, { recursive: true });
    const root = mkdtempSync(join(artifacts, "pi-touchbar-"));
    const state = join(root, "state");
    const assets = join(root, "assets");
    const log = join(root, "plays.log");
    const player = join(root, "fake-touchbar");
    mkdirSync(state);
    mkdirSync(assets);
    for (const asset of ["codex-train.mkv", "codex-vines.mkv"]) {
      writeFileSync(join(assets, asset), "");
    }
    // Preserve an existing Codex selection instead of restarting at train.
    writeFileSync(join(state, "next-animation"), "vines\n");
    writeFileSync(player, `#!/usr/bin/env python3
import os, pathlib, sys, time
with pathlib.Path(os.environ["FAKE_PLAYER_LOG"]).open("a") as log:
    log.write(pathlib.Path(sys.argv[-1]).name + "\\n")
pathlib.Path(os.environ["TOUCHBAR_STARTED_FILE"]).touch()
time.sleep(0.28)
`, { mode: 0o755 });
    const env = {
      ...process.env,
      CODEX_TOUCHBAR_STATE_DIR: state,
      CODEX_TOUCHBAR_ASSET_DIR: assets,
      CODEX_TOUCHBAR_COMMAND: player,
      FAKE_PLAYER_LOG: log,
    };
    const runNotify = async (args: string[]) => {
      const child = Bun.spawn([notifier, ...args], { env, stdout: "ignore", stderr: "pipe" });
      const code = await child.exited;
      return { ...result, code, stderr: await new Response(child.stderr).text() };
    };
    const { settle } = harness(mock(async (command: string, args: string[]) => {
      expect(command).toBe(helper);
      return runNotify(args);
    }));
    const daemon = Bun.spawn([join(repo, ".local/bin/codex-touchbar-daemon")], {
      env, stdout: "ignore", stderr: "ignore",
    });
    const plays = () => {
      try { return readFileSync(log, "utf8").trim().split("\n"); }
      catch { return []; }
    };
    try {
      await waitFor(() => readdirSync(state).includes("events"));
      await Bun.sleep(120); // Allow startup stale-event cleanup to finish.
      await settle({ type: "agent_settled" }, context());
      await waitFor(() => plays().length === 1);
      expect(plays()).toEqual(["codex-vines.mkv"]);

      expect((await runNotify([JSON.stringify({
        type: "agent-turn-complete", "thread-id": "codex-session",
      })])).code).toBe(0);
      await waitFor(() =>
        readdirSync(join(state, "events")).length === 0 &&
        !readdirSync(state).some((name) => name.startsWith("playback-started-")),
      );
      expect(plays()).toEqual(["codex-vines.mkv"]);
      expect(readFileSync(join(state, "next-animation"), "utf8")).toBe("train\n");

      await settle({ type: "agent_settled" }, context());
      await waitFor(() => plays().length === 2 &&
        readFileSync(join(state, "next-animation"), "utf8") === "vines\n");
      expect(plays()).toEqual(["codex-vines.mkv", "codex-train.mkv"]);
    } finally {
      daemon.kill("SIGTERM");
      await daemon.exited;
      rmSync(root, { recursive: true, force: true });
      try { rmdirSync(dirname(root)); } catch { /* Other tests may be using it. */ }
    }
  });
});
