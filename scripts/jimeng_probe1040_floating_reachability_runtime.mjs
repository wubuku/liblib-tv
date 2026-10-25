/**
 * 1032-⑬ 运行时探针：**浮层可达性**（浮层必须落在视口内、控件必须点得到）。
 *
 * 为什么要有这道探针：
 *   1032-⑬ 查出的根因是「**全音色**」面板开到**视口外**
 *   （面板 `700×884`、顶边 y=-318、4 枚筛选芯片 y=-278 ⇒ `elementFromPoint` 落空
 *     ⇒ 鼠标点不到 ⇒ 整个「音色筛选」功能在那处**不可用**）。
 *   ⇒ ⇒ 而这类缺陷**不会报错、不会红**：面板照样渲染、DOM 照样有节点、
 *   ⇒ ⇒ ⇒ 只有「它到底在不在屏内、点不点得到」能判出来。
 *
 * 纪律：
 *   · 产物里**不许出现随机量**（时间戳 / 耗时 / pid）⇒ 只落**布尔**与计数；
 *   · 只点**本地**控件；**绝不点生成 / 发送 / 购买 / 充值**；
 *   · 定位节点一律用 `.react-flow__node`（**恒在**的结构）。
 */
import pw from '/Users/yangjiefeng/node_modules/playwright/index.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const { chromium } = pw;
const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, '..');
const OUT = process.env.JIMENG_REACH_JSON
  || resolve(REPO_ROOT, 'docs/research/jimeng-canvas/inputs/floating-reachability-1040.json');
fs.mkdirSync(path.dirname(OUT), { recursive: true });

const URL = 'http://localhost:4317/jimeng/canvas/demo';

const MEASURE = `() => {
  const vw = window.innerWidth, vh = window.innerHeight;
  const inView = (el) => {
    if (!el) return false;
    const b = el.getBoundingClientRect();
    return b.width > 0 && b.height > 0
      && b.top >= 0 && b.bottom <= vh && b.left >= 0 && b.right <= vw;
  };
  const hitOk = (el) => {
    if (!el) return false;
    const b = el.getBoundingClientRect();
    const hit = document.elementFromPoint(Math.round(b.x + b.width / 2),
                                          Math.round(b.y + b.height / 2));
    return !!hit && !!hit.closest('button') && hit.closest('button') === el;
  };
  const panel = document.querySelector('[data-testid="audio-all-voices-listbox"]');
  const chips = ['性别', '年龄', '语言', '声音特点'].map((lab) => {
    const c = [...document.querySelectorAll('button')]
      .find((b) => (b.getAttribute('aria-label') || '').startsWith(lab + ':'));
    return { label: lab, present: !!c, in_viewport: inView(c), hittable: hitOk(c) };
  });
  return {
    vw, vh,
    panel_present: !!panel,
    panel_in_viewport: inView(panel),
    panel_hits_itself: panel ? (() => {
      const b = panel.getBoundingClientRect();
      const hit = document.elementFromPoint(Math.round(b.x + b.width / 2),
                                            Math.round(b.y + Math.min(40, b.height / 2)));
      return !!hit && !!hit.closest('[data-testid="audio-all-voices-listbox"]');
    })() : false,
    chips,
    n_dropdowns_open: document.querySelectorAll('[data-testid="audio-voice-filter-listbox"]').length,
  };
}`;

const out = { generated_by: 'scripts/jimeng_probe1040_floating_reachability_runtime.mjs',
              pageerrors: [] };
const browser = await chromium.launch({ headless: true, viewport: { width: 1280, height: 720 } });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
page.on('pageerror', (e) => out.pageerrors.push(String(e).slice(0, 200)));

await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(5000);

// 选中音频节点 → 开「音色」面板
await page.locator('.react-flow__node[data-testid="rf__node-audio-1"]')
  .click({ position: { x: 20, y: 20 } }).catch(() => { out.select_failed = true; });
await page.waitForTimeout(800);
const trig = page.locator('.react-flow__node-toolbar button[aria-label^="音色"]');
if (await trig.count()) {
  await trig.first().click({ timeout: 8000 }).catch(() => { out.open_failed = true; });
}
await page.waitForTimeout(1200);

out.panel_open = await page.evaluate(eval(MEASURE));

// 点一枚芯片 ⇒ 它自己那枚下拉必须开得出来（这才是「可达」的落点）
await page.locator('button[aria-label^="性别:"]').first()
  .click({ timeout: 8000 }).catch(() => { out.chip_click_failed = true; });
await page.waitForTimeout(900);
out.after_chip_click = await page.evaluate(eval(MEASURE));

fs.writeFileSync(OUT, JSON.stringify(out, null, 1) + '\n', 'utf8');
console.log(JSON.stringify(out, null, 1));
await browser.close();
console.log('FLOATING_REACHABILITY_DONE ->', OUT);
