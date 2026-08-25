export function listeningPids(netstatOutput, port) {
  const pids = new Set();
  for (const line of netstatOutput.split(/\r?\n/)) {
    const m = line.match(/^\s*TCP\s+(\S+)\s+\S+\s+LISTENING\s+(\d+)\s*$/i);
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
