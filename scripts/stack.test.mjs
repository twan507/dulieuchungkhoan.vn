import { test } from "node:test";
import assert from "node:assert/strict";

import {
  listeningPids,
  dockerMajor,
  shouldPruneAnonVolumes,
  assertVolumeSurvived,
} from "./stack.mjs";

test("listeningPids: chỉ PID của dòng LISTENING đúng cổng, bỏ TIME_WAIT", () => {
  const out = [
    "  TCP    127.0.0.1:8000    0.0.0.0:0      LISTENING    1234",
    "  TCP    127.0.0.1:8000    10.0.0.2:55    TIME_WAIT    9999",
    "  TCP    127.0.0.1:3000    0.0.0.0:0      LISTENING    5678",
  ].join("\r\n");
  assert.deepEqual(listeningPids(out, 8000), ["1234"]);
  assert.deepEqual(listeningPids(out, 3000), ["5678"]);
  assert.deepEqual(listeningPids(out, 9999), []);
});

test("dockerMajor: lấy major, null nếu không parse được", () => {
  assert.equal(dockerMajor("27.1.1"), 27);
  assert.equal(dockerMajor("20.10.9"), 20);
  assert.equal(dockerMajor("garbage"), null);
});

test("shouldPruneAnonVolumes: chỉ true khi >= 23", () => {
  assert.equal(shouldPruneAnonVolumes(20), false);
  assert.equal(shouldPruneAnonVolumes(23), true);
  assert.equal(shouldPruneAnonVolumes(24), true);
  assert.equal(shouldPruneAnonVolumes(null), false);
});

test("assertVolumeSurvived: die khi volume có trước mà mất sau", () => {
  assert.equal(assertVolumeSurvived(["dlck-infra_pgdata"], [], "dlck-infra_pgdata").ok, false);
  assert.equal(assertVolumeSurvived(["dlck-infra_pgdata"], ["dlck-infra_pgdata"], "dlck-infra_pgdata").ok, true);
  assert.equal(assertVolumeSurvived([], [], "dlck-infra_pgdata").ok, true);
});

test("listeningPids: bắt cả listener IPv6 (dòng TCP6)", () => {
  const out = [
    "  TCP6   [::]:8000    [::]:0    LISTENING    4242",
    "  TCP6   [::1]:3000   [::]:0    TIME_WAIT    7777",
  ].join("\r\n");
  assert.deepEqual(listeningPids(out, 8000), ["4242"]);
  assert.deepEqual(listeningPids(out, 3000), []);
});
