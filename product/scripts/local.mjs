import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

// A single local entry point, including Macs whose shell still resolves Node 18.
const [major, minor] = process.versions.node.split(".").map(Number);
if (major < 22 || (major === 22 && minor < 13)) {
  const bundled = `${homedir()}/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node`;
  if (!existsSync(bundled) || process.execPath === bundled) {
    console.error("Swarm Mafia requires Node 22.13 or newer. Install a current Node.js LTS, then run npm run local.");
    process.exit(1);
  }
  const result = spawnSync(bundled, [fileURLToPath(import.meta.url), ...process.argv.slice(2)], { stdio: "inherit" });
  if (result.error) throw result.error;
  process.exit(result.status ?? 1);
}
process.chdir(fileURLToPath(new URL("../", import.meta.url)));
console.log("Swarm Mafia · local workspace\nhttp://127.0.0.1:5173\nSaved investigations stay in this checkout. Trace retrieval uses the configured backend.\n");
process.argv = [process.execPath, fileURLToPath(new URL("./run-framework.mjs", import.meta.url)), "dev", "--hostname", "127.0.0.1", ...process.argv.slice(2)];
await import("./run-framework.mjs");
