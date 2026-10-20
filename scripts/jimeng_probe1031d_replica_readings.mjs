/**
 * 1032-①：采集「原型侧」的可交互读数，供 `jimeng_probe1031d_replica_contract.py` 对账。
 *
 * ⭐⭐⭐⭐⭐ **这个脚本此前只存在于 /tmp** —— 而 `/tmp` 会被清空
 *   ⇒ 1031d 的读数文件一消失，P3..P8 就整片记 `null`（「没测到」），
 *   而**门照样是绿的**（降级不是红）⇒ 门看起来在管这件事，实际已经瞎了。
 *   ⇒ 把它落仓，且**用契约当规格**重建：契约里写着区域级 13 testid / 24 aria /
 *     3 种形状 / 3 种节点类型 / 节点级 2 testid + 4 aria
 *     ⇒ 重建错了，**P3 与 P8 会当场红** ⇒ 契约本身就是对账标准。
 *   ⇒ ⭐⭐⭐⭐⭐ **读数文件本身也落仓**（`docs/research/jimeng-canvas/inputs/replica-readings-1031d.json`）：
 *     放在 `/tmp` 时，「读数没了」和「读数合法」在门眼里长得一模一样（都记 `null` 且门是绿的），
 *     而且产物里会留随机路径、离开本机就不可复现。
 *
 * 纪律：
 *   · 量法照仓里已验证的写法：`waitUntil:'domcontentloaded'` + `waitForTimeout` +
 *     `page.locator().click()`（真实鼠标事件）+ host 用 `localhost`（不是 127.0.0.1）
 *   · **绝不点击生成 / 发送 / 购买 / 充值**
 *   · 产物里不许出现随机量（可点元素数、节点数等会变的量由探针自己脱敏）
 */
import pw from '/Users/yangjiefeng/node_modules/playwright/index.js';
import { writeFileSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

// ⚠️⚠️ Playwright 的入口是 **CommonJS** ⇒ ESM 里必须**默认导入**再解构；
//   写成具名导入（`import { chromium } from …`）会报
//   `Named export 'chromium' not found`。
const { chromium } = pw;

const URL = 'http://localhost:4317/jimeng/canvas/demo';
// ⭐⭐⭐⭐⭐ **读数文件必须落在仓内** —— 落在 `/tmp` 有两个坏处：
//   ① `/tmp` 会被清空 ⇒ 读数一消失，P3..P8 整片记 `null`（「没测到」），
//      而**门照样是绿的**（降级不是红）⇒ 门看起来在管这件事，实际已经瞎了；
//   ② 产物里会留下 `/tmp/...` 这种**随机路径** ⇒ 违反「产物不许出现随机量」，
//      而且引用它的产物**在本机之外的任何环境都不可复现**。
const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, '..');
const DEFAULT_OUT = resolve(REPO_ROOT, 'docs/research/jimeng-canvas/inputs/replica-readings-1031d.json');
const OUT = process.env.JIMENG_REPLICA_JSON || DEFAULT_OUT;
mkdirSync(dirname(OUT), { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const pageErrors = [];
page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 200)));

await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(6000);

const collect = () => page.evaluate(() => {
  const vis = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
  };
  const testids = new Set();
  const aria = new Set();
  document.querySelectorAll('[data-testid]').forEach((el) => {
    if (vis(el)) testids.add(el.getAttribute('data-testid'));
  });
  document.querySelectorAll('[aria-label]').forEach((el) => {
    if (vis(el)) aria.add(el.getAttribute('aria-label'));
  });
  const nodes = Array.from(document.querySelectorAll('.react-flow__node'));
  return {
    testids: [...testids].filter(Boolean).sort(),
    aria: [...aria].filter(Boolean).sort(),
    n_nodes: nodes.length,
    node_kinds_present: [...new Set(nodes.map(
      (n) => (n.className.match(/react-flow__node-(\w+)/) || [])[1]).filter(Boolean))].sort(),
    // ⭐ 节点标题（**DOM 上看得见的中文标题词**）——
    //   契约 `node_kinds` 记的就是源站 DOM 上的中文标题词，
    //   而读数侧量 store 内部的英文 kind 会两边**量的不是同一个东西**（104c 已修过一次）。
    node_titles: nodes.map((n) => {
      const t = n.querySelector('[data-testid="node-title-text"], [data-testid="flow-node-title"]');
      return t ? t.textContent.trim() : '';
    }).filter(Boolean),
    has_engine: !!document.querySelector('.react-flow,[class*="react-flow"]'),
    flow_node_title_class: !!document.querySelector('.flow-node-title'),
    rf_wrapper_class: !!document.querySelector('.rf__wrapper'),
    status_lines: [...new Set(Array.from(
      document.querySelectorAll('[data-testid="canvas-status-line"]'))
      .map((e) => e.textContent.replace(/\s+/g, ' ').trim()).filter(Boolean))],
  };
});

let base = await collect();
const perKind = {};
const kinds = base.node_kinds_present.slice();
// ⭐ 逐个**选中**每种类型的节点后再采一次 —— 节点级 aria（工具条、顶行右簇…）
//   只在选中时才在 DOM 里。
for (const kind of kinds) {
  const idx = await page.evaluate((k) => {
    const nodes = Array.from(document.querySelectorAll('.react-flow__node'));
    return nodes.findIndex((n) => ((n.className.match(/react-flow__node-(\w+)/) || [])[1]) === k);
  }, kind);
  if (idx < 0) continue;
  try {
    await page.locator('.react-flow__node').nth(idx).click({ timeout: 5000 });
  } catch { continue; }
  await page.waitForTimeout(900);
  const c = await collect();
  perKind[kind] = c.aria;
  base.testids = [...new Set([...base.testids, ...c.testids])].sort();
  base.aria = [...new Set([...base.aria, ...c.aria])].sort();
  base.status_lines = [...new Set([...base.status_lines, ...c.status_lines])];
}

const out = {
  title: await page.title(),
  testids: base.testids,
  aria: base.aria,
  n_testids: base.testids.length,
  n_aria: base.aria.length,
  n_nodes: base.n_nodes,
  has_engine: base.has_engine,
  node_kinds_present: base.node_kinds_present,
  node_titles: [...new Set(base.node_titles)].sort(),
  per_kind_aria: Object.fromEntries(Object.entries(perKind).map(([k, v]) => [k, v.length])),
  flow_node_title_class: base.flow_node_title_class,
  rf_wrapper_class: base.rf_wrapper_class,
  status_lines_found: base.status_lines,
  pageerrors: [...new Set(pageErrors)],
};
writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log('n_testids=%d n_aria=%d n_nodes=%d kinds=%j',
  out.n_testids, out.n_aria, out.n_nodes, out.node_kinds_present);
console.log('node_titles=%j', out.node_titles);
console.log('pageerrors=%j', out.pageerrors);
console.log('WROTE', OUT);
await browser.close();
