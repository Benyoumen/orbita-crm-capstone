// The access guard of a public deploy (Render or a tunnel), end to end through the HTTP port.
// A shared link carries the code (/?code=...): the server swaps it for an HttpOnly cookie and opens the CRM, so whoever
// gets the link is in with one click; a browser without the code sees a form, never the native sign-in popup; the old
// Basic sign-in still works for scripts. Runs server.mjs --mock (no model call), prints one line per check, exits 1 on a miss.
//   node mockups/access_test.mjs
import { spawn } from "node:child_process";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const CODE = "t3stc0de7";
const free = () => new Promise((ok) => { const s = net.createServer().listen(0, "127.0.0.1", () => { const p = s.address().port; s.close(() => ok(p)); }); });
const port = await free();
const base = `http://127.0.0.1:${port}`;
const tmp = path.join(os.tmpdir(), `orbita-access-${process.pid}`);
const proc = spawn(process.execPath, ["server.mjs", "--mock", "--port", String(port)], {
  cwd: HERE, stdio: ["ignore", "pipe", "pipe"],
  env: { ...process.env, ORBITA_ACCESS_CODE: CODE, ORBITA_FEEDBACK_FILE: path.join(tmp, "feedback.jsonl"), ORBITA_EVALS_DIR: tmp, ARIZE_SPACE_ID: "", ARIZE_API_KEY: "" },
});
let stderr = "";
proc.stderr.on("data", (c) => { stderr += c; });

const results = [];
const check = (name, ok, detail = "") => { results.push(ok); console.log(`${ok ? "ok  " : "FAIL"} ${name}${ok || !detail ? "" : `  (${detail})`}`); };
const get = (p, headers = {}) => fetch(base + p, { headers, redirect: "manual" });
const HTML = { accept: "text/html,application/xhtml+xml" };

try {
  let up = false;
  for (let i = 0; i < 100 && !up; i++) {
    try { up = (await fetch(base + "/api/health")).ok; } catch { await new Promise((r) => setTimeout(r, 100)); }
  }
  if (!up) throw new Error("server did not start: " + stderr.slice(0, 400));

  let r = await get("/api/health");
  check("health stays open for the host's probe", r.status === 200);

  r = await get("/", HTML);
  let body = await r.text();
  check("a browser without the code gets a form, not the sign-in popup",
    r.status === 401 && /text\/html/.test(r.headers.get("content-type") || "") && /name="code"/.test(body) && !r.headers.get("www-authenticate"),
    `status ${r.status}, www-authenticate ${r.headers.get("www-authenticate")}`);

  r = await fetch(base + "/api/granola/status");
  check("the API without the code answers 401 with Basic sign-in", r.status === 401 && /^Basic/.test(r.headers.get("www-authenticate") || ""), `status ${r.status}`);

  r = await get("/?code=wrong", HTML);
  check("a wrong code in the link opens nothing and sets no cookie", r.status === 401 && !r.headers.get("set-cookie"), `status ${r.status}`);

  r = await get(`/?code=${CODE}&view=meetings`, HTML);
  const cookie = r.headers.get("set-cookie") || "";
  check("the code in the link becomes a cookie and the link drops it",
    r.status === 302 && r.headers.get("location") === "/?view=meetings" && /orbita_access=[0-9a-f]{64}/.test(cookie) && /HttpOnly/i.test(cookie) && /SameSite=Lax/i.test(cookie) && !/Secure/i.test(cookie),
    `status ${r.status}, location ${r.headers.get("location")}, cookie ${cookie}`);
  check("the cookie holds no copy of the code", !cookie.includes(CODE));
  const jar = cookie.split(";")[0];

  r = await get(`/?code=${CODE}`, { ...HTML, "x-forwarded-proto": "https" });
  check("behind https (Render, tunnel) the cookie is Secure", /;\s*Secure/i.test(r.headers.get("set-cookie") || ""), r.headers.get("set-cookie") || "no cookie");

  r = await get("/", { ...HTML, cookie: jar });
  body = await r.text();
  check("with the cookie the CRM page opens", r.status === 200 && /Orbita/.test(body), `status ${r.status}`);

  r = await get("/api/granola/status", { cookie: jar });
  check("with the cookie the page reaches the API", r.status === 200, `status ${r.status}`);

  r = await get("/api/granola/status", { cookie: "orbita_access=" + "0".repeat(64) });
  check("a forged cookie is refused", r.status === 401, `status ${r.status}`);

  r = await get("/api/granola/status", { authorization: "Basic " + Buffer.from("anyone:" + CODE).toString("base64") });
  check("Basic sign-in still works for scripts", r.status === 200, `status ${r.status}`);
} catch (err) {
  check("server run", false, err.message);
} finally {
  proc.kill();
}
const failed = results.filter((x) => !x).length;
console.log(`${results.length - failed}/${results.length} access checks ok`);
process.exit(failed ? 1 : 0);
