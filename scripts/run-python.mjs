import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";

const virtualEnvironmentPython =
  process.platform === "win32"
    ? ".venv/Scripts/python.exe"
    : ".venv/bin/python";
const executable = existsSync(virtualEnvironmentPython)
  ? virtualEnvironmentPython
  : process.platform === "win32"
    ? "python"
    : "python3";

const result = spawnSync(executable, process.argv.slice(2), {
  stdio: "inherit",
  shell: false,
});

if (result.error) {
  console.error(`Falha ao executar ${executable}: ${result.error.message}`);
  process.exit(1);
}

process.exit(result.status ?? 1);
