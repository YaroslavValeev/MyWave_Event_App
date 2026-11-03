#!/usr/bin/env node
import { spawnSync } from "node:child_process";

function has(cmd, args = ["-version"]) {
  const r = spawnSync(cmd, args, { encoding: "utf8" });
  return r.status === 0 || (r.stderr || r.stdout || "").length > 0;
}

const java = has("java", ["-version"]);
const androidHome = Boolean(process.env.ANDROID_HOME || process.env.ANDROID_SDK_ROOT);

console.log("Champ App Android doctor");
console.log(`- Node: ${process.version}`);
console.log(`- Java: ${java ? "FOUND" : "MISSING"}`);
console.log(`- ANDROID_HOME: ${androidHome ? "SET" : "MISSING"}`);

if (!java || !androidHome) {
  console.log("\nAPK build BLOCKED. Install JDK 17+ and Android SDK, then:");
  console.log("  cd apps/mobile && npm install && npx cap add android && npx cap sync");
  process.exit(2);
}

console.log("\nToolchain looks ready for Capacitor Android.");
process.exit(0);
