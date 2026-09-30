/** Share Codex's completion queue, playback policy, and train/vines alternation. */
import { homedir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  // agent_end can be followed by retries, compaction, or queued continuations.
  pi.on("agent_settled", async (_event, ctx) => {
    // Only the interactive parent should notify, not JSON/print/RPC workers.
    if (ctx.mode !== "tui") return;

    try {
      await pi.exec(
        join(homedir(), ".local/bin/codex-touchbar-notify"),
        [JSON.stringify({
          type: "agent-turn-complete",
          "thread-id": ctx.sessionManager.getSessionId(),
          "turn-id": ctx.sessionManager.getLeafId(),
        })],
        { timeout: 2000 },
      );
    } catch {
      // A missing helper or failed notification must not affect the Pi turn.
    }
  });
}
