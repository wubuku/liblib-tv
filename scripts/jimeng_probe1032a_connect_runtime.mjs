/**
 * 1032-②a：量「用户拖一条连线」这件事到底有没有发生。
 *
 * ⭐⭐⭐⭐⭐ **为什么必须实测，不能只验「代码里有 onConnect」**
 *   ① `<ReactFlow>` 此前**根本没有 `onConnect`** ⇒ 节点有 `<Handle>`、用户能拖，
 *      **却一条边也建不出来**；
 *   ② 但「代码里写了 onConnect」**不等于**「用户拖得出一条边」——
 *      handle 口径（`<Handle>` 有没有 `id`）、React Flow 的连线事件、
 *      store 的判重，任何一处不对，用户看到的仍然是「拖了没反应」。
 *   ⇒ ⇒ ⇒ 所以这里**真拖**，量四件事：
 *      · 有效拖一次 ⇒ 边数 +1，且新边 id == `e-<源>-<目标>`（⇒ source/target 对）
 *      · **同一对再拖一次** ⇒ 边数**不再增加**（判重生效 ⇒ 也是一条对照）
 *      · 拖到空白处 ⇒ 边数**不变**（负控 ⇒ 证明「+1」不是因为别的原因）
 *      · 拖到空白 ⇒ toast「无法连接这些节点」出现（源站既有行为，顺带验）
 *
 * 纪律：
 *   · 量法照仓里已验证的写法：`waitUntil:'domcontentloaded'` + `waitForTimeout`
 *     + 真实鼠标事件（`page.mouse` ⇒ 会发 pointer 事件，xyflow 靠它连线）
 *   · host 用 `localhost`（不是 127.0.0.1）
 *   · **绝不点击生成 / 发送 / 购买 / 充值**
 *   · 产物里不许出现随机量（时间戳 / pid / 耗时）
 */
import pw from '/Users/yangjiefeng/node_modules/playwright/index.js';
import { writeFileSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

// ⚠️⚠️ Playwright 的入口是 **CommonJS** ⇒ ESM 里必须**默认导入**再解构
const { chromium } = pw;

const URL = 'http://localhost:4317/jimeng/canvas/demo';
const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, '..');
const OUT =
  process.env.JIMENG_CONNECT_JSON ||
  resolve(REPO_ROOT, 'docs/research/jimeng-canvas/inputs/connect-runtime-1032a.json');
mkdirSync(dirname(OUT), { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const pageErrors = [];
page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 200)));

await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(6000);

const readNodes = () =>
  page.evaluate(() => {
    const out = [];
    document.querySelectorAll('.react-flow__node').forEach((n) => {
      const id = n.getAttribute('data-id');
      const pick = (sel) => {
        const h = n.querySelector(sel);
        if (!h) return null;
        const b = h.getBoundingClientRect();
        return { x: b.x + b.width / 2, y: b.y + b.height / 2 };
      };
      out.push({
        id,
        hr: pick('.react-flow__handle-right'),
        hl: pick('.react-flow__handle-left'),
      });
    });
    return out;
  });

const readEdges = () =>
  page.evaluate(() => {
    const g = document.querySelectorAll('.react-flow__edge');
    return {
      n: g.length,
      ids: Array.from(g).map((e) => e.getAttribute('data-id') || e.id || ''),
    };
  });

const readToasts = () =>
  page.evaluate(() =>
    Array.from(document.querySelectorAll('[class*="toast" i], [role="status"], [role="alert"]'))
      .map((e) => (e.textContent || '').trim())
      .filter((t) => t.length > 0),
  );

const drag = async (from, to) => {
  await page.mouse.move(from.x, from.y);
  await page.mouse.down();
  await page.mouse.move((from.x + to.x) / 2, (from.y + to.y) / 2, { steps: 10 });
  await page.mouse.move(to.x, to.y, { steps: 10 });
  await page.mouse.up();
  await page.waitForTimeout(900);
};

const edges0 = await readEdges();
const nodes = await readNodes();
const withHandles = nodes.filter((n) => n.hr && n.hl);
const probes = { n_nodes: nodes.length, n_with_handles: withHandles.length };

const src = withHandles[0];
const dst = withHandles[1];
const out = {
  probes,
  edges_before: edges0,
  drag_valid: null,
  drag_duplicate: null,
  drag_to_void: null,
  toasts_after_void: [],
  pageerrors: [],
};

if (src && dst) {
  // ── 1) 有效拖一次：源右把手 → 目标左把手 ──────────────────────────
  await drag(src.hr, dst.hl);
  const a = await readEdges();
  out.drag_valid = {
    src_node: src.id,
    dst_node: dst.id,
    n_before: edges0.n,
    n_after: a.n,
    delta: a.n - edges0.n,
    ids_after: a.ids,
    expected_id: `e-${src.id}-${dst.id}`,
    expected_id_present: a.ids.includes(`e-${src.id}-${dst.id}`),
  };

  // ── 2) 同一对再拖一次：判重 ⇒ 边数不应再增加 ────────────────────
  const n0 = a.n;
  await drag(src.hr, dst.hl);
  const b = await readEdges();
  out.drag_duplicate = {
    n_before: n0,
    n_after: b.n,
    delta: b.n - n0,
    ids_after: b.ids,
  };

  // ── 3) 负控：拖到画布空白处 ⇒ 边数不变，且 toast 出现 ─────────────
  const n1 = b.n;
  await drag(src.hr, { x: src.hr.x + 260, y: src.hr.y + 220 });
  const c = await readEdges();
  out.drag_to_void = { n_before: n1, n_after: c.n, delta: c.n - n1 };
  out.toasts_after_void = await readToasts();
}

out.pageerrors = [...new Set(pageErrors)];
writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log(
  'n_nodes=%d n_with_handles=%d | valid %s->%s (Δ%s, id_ok=%s) | dup Δ%s | void Δ%s | toasts=%d | errs=%d',
  probes.n_nodes,
  probes.n_with_handles,
  out.drag_valid ? out.drag_valid.n_before : 'NA',
  out.drag_valid ? out.drag_valid.n_after : 'NA',
  out.drag_valid ? out.drag_valid.delta : 'NA',
  out.drag_valid ? out.drag_valid.expected_id_present : 'NA',
  out.drag_duplicate ? out.drag_duplicate.delta : 'NA',
  out.drag_to_void ? out.drag_to_void.delta : 'NA',
  out.toasts_after_void.length,
  out.pageerrors.length,
);
console.log('WROTE', OUT);
await browser.close();
