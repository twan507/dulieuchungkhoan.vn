export function listeningPids(netstatOutput, port) {
  const pids = new Set();
  for (const line of netstatOutput.split(/\r?\n/)) {
    const m = line.match(/^\s*TCP6?\s+(\S+)\s+\S+\s+LISTENING\s+(\d+)\s*$/i);
    if (m && m[1].endsWith(`:${port}`)) pids.add(m[2]);
  }
  return [...pids];
}

export function dockerMajor(versionOutput) {
  const m = String(versionOutput).match(/^(\d+)\./);
  return m ? parseInt(m[1], 10) : null;
}

export function shouldPruneAnonVolumes(major) {
  return major !== null && major >= 23;
}

export function assertVolumeSurvived(before, after, name) {
  const had = before.includes(name);
  const has = after.includes(name);
  if (had && !has) return { ok: false, reason: `volume ${name} biến mất` };
  return { ok: true, existed: had };
}

import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const ENV_FILE = path.join(ROOT, ".env");
const INFRA = ["-p", "dlck-infra", "-f", "deploy/infra/docker-compose.yml", "--env-file", ".env"];
const APP = ["-p", "dlck-app", "-f", "deploy/app/docker-compose.yml", "--env-file", ".env"];
const NETWORK = "dlck-net";
const WIN = process.platform === "win32";

function log(m) { console.log(`[stack] ${m}`); }
function die(m) { console.error(`[stack] ${m}`); process.exit(1); }
function run(cmd, args, opts = {}) {
  const r = spawnSync(cmd, args, { cwd: ROOT, stdio: "inherit", shell: WIN, ...opts });
  if (r.status !== 0 && !opts.allowFail) die(`lệnh thất bại: ${cmd} ${args.join(" ")}`);
  return r.status;
}
function capture(cmd, args) {
  const r = spawnSync(cmd, args, { cwd: ROOT, encoding: "utf8", shell: WIN });
  return (r.stdout || "").trim();
}
function volumes() { return capture("docker", ["volume", "ls", "--format", "{{.Name}}"]).split(/\r?\n/); }

function ensureEnv() {
  if (fs.existsSync(ENV_FILE)) return;
  const ex = path.join(ROOT, ".env.example");
  if (!fs.existsSync(ex)) die(".env và .env.example đều không tồn tại");
  fs.copyFileSync(ex, ENV_FILE);
  log("đã tạo .env từ .env.example — nhớ điền giá trị thật");
}
function ensureNetwork() {
  if (!capture("docker", ["network", "ls", "--format", "{{.Name}}"]).split(/\r?\n/).includes(NETWORK))
    run("docker", ["network", "create", NETWORK]);
}
function infraUp() {
  ensureNetwork();
  log("bật Postgres + Redis, chờ healthy…");
  run("docker", ["compose", ...INFRA, "up", "-d", "--wait"]);
}
function pidsOnPort(port) {
  if (WIN) return listeningPids(capture("netstat", ["-ano"]), port);
  return capture("lsof", ["-ti", `tcp:${port}`, "-sTCP:LISTEN"]).split(/\r?\n/).map(s => s.trim()).filter(Boolean);
}
function killPort(port) {
  for (const pid of pidsOnPort(port)) {
    log(`giết PID ${pid} ở cổng ${port}`);
    if (WIN) run("taskkill", ["/PID", pid, "/T", "/F"], { allowFail: true });
    else run("kill", ["-9", pid], { allowFail: true });
  }
}

const children = [];
function spawnLabeled(label, cmd, args, cwd, env) {
  const p = spawn(cmd, args, { cwd, env, shell: WIN });
  const pipe = (s) => s.on("data", (d) => d.toString().split(/\r?\n/).filter(Boolean).forEach(l => console.log(`[${label}] ${l}`)));
  pipe(p.stdout); pipe(p.stderr);
  children.push(p);
}
function killChildren() {
  for (const p of children) {
    if (p.exitCode !== null) continue;
    if (WIN) spawnSync("taskkill", ["/pid", String(p.pid), "/T", "/F"], { stdio: "ignore" });
    else p.kill("SIGTERM");
  }
}

function devStart() {
  ensureEnv();
  if (pidsOnPort(8000).length) die("cổng 8000 đang bận — tắt tiến trình chiếm rồi chạy lại");
  infraUp();
  const env = { ...process.env, POSTGRES_HOST: "127.0.0.1", REDIS_HOST: "127.0.0.1", APP_ENV: "dev" };
  const be = path.join(ROOT, "backend");
  log("bật api :8000 (uvicorn --reload) và etl — Ctrl+C để tắt cả hai (Postgres+Redis vẫn chạy)");
  spawnLabeled("api", "uv", ["run", "uvicorn", "api.main:app", "--reload", "--port", "8000"], be, env);
  spawnLabeled("etl", "uv", ["run", "python", "-m", "etl"], be, env);
  let closing = false;
  process.on("SIGINT", () => {
    if (closing) return; closing = true;
    console.log(""); log("đang tắt api + etl… (dùng dev-stop để tắt hẳn infra)");
    killChildren(); setTimeout(() => process.exit(0), 800);
  });
}
function devStop() {
  ensureEnv();
  killPort(8000);
  log("dừng container infra (giữ container + volume)…");
  run("docker", ["compose", ...INFRA, "stop"], { allowFail: true });
}
function dockerUp() {
  ensureEnv(); infraUp();
  log("build + chạy tầng app…");
  run("docker", ["compose", ...APP, "up", "-d", "--build"]);
  log("xong — API: http://localhost:8000/api/healthz");
}
function dockerDown() {
  ensureEnv();
  const before = volumes();
  run("docker", ["compose", ...APP, "down"], { allowFail: true });
  run("docker", ["compose", ...INFRA, "down"], { allowFail: true });
  for (const name of ["dlck-infra_pgdata", "dlck-infra_redisdata"]) {
    const r = assertVolumeSurvived(before, volumes(), name);
    if (!r.ok) die(`CẢNH BÁO: ${r.reason} — kiểm tra ngay`);
  }
  log("đã gỡ container. Volume dữ liệu còn nguyên.");
}
function dockerClean() {
  const before = volumes();
  run("docker", ["system", "df"]);
  run("docker", ["builder", "prune", "-f"], { allowFail: true });
  run("docker", ["image", "prune", "-f"], { allowFail: true });
  const major = dockerMajor(capture("docker", ["version", "--format", "{{.Server.Version}}"]));
  if (shouldPruneAnonVolumes(major)) run("docker", ["volume", "prune", "-f"], { allowFail: true });
  else log(`Docker Engine ${major ?? "?"}: bỏ qua prune volume vô danh cho an toàn`);
  for (const name of ["dlck-infra_pgdata", "dlck-infra_redisdata"]) {
    const r = assertVolumeSurvived(before, volumes(), name);
    if (!r.ok) die(`CẢNH BÁO: ${r.reason} sau khi dọn — KHÔNG được phép`);
  }
  run("docker", ["system", "df"]);
  log("volume dữ liệu: còn nguyên ✓");
}

const COMMANDS = { "dev-start": devStart, "dev-stop": devStop, "docker-up": dockerUp, "docker-down": dockerDown, "docker-clean": dockerClean };
const cmd = process.argv[2];
if (COMMANDS[cmd]) COMMANDS[cmd]();
else if (cmd === undefined) { /* import cho test — không chạy command */ }
else { console.log(`Lệnh: ${Object.keys(COMMANDS).join(", ")}`); process.exit(1); }
