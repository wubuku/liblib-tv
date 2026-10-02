// 批次 102 · a 轮：`assets-and-upload.md`（普查 86）的**只读**探针。
//
// 这页已经写得很厚（批次 52 建结构、64 跑通 PNG 全链路、86 第二次全量复核）。
// 但它自己写着两处**本轮正好有反证 / 缺口**的地方：
//
//   ① 第 210-211 行：「⛔ 本轮未测：……**本地上传**（**文件选择器在 `connectOverCDP` 下会挂住**）」
//      ⇒ 批次 101 **成功跑通了视频上传**，办法是**全局 `p.on('filechooser')`**
//         而不是 `p.waitForEvent('filechooser')`。这条「会挂住」需要收窄。
//   ② 「入口」一节列了**空白右键 → 新建节点 → 本地上传**，但全页**没有任何一句**说这条入口验过。
//
// 本轮三问（全部**只读**，不建节点、不选文件）：
//   A 触发一次 filechooser 但**不 setFiles**，读那个 `<input type=file>` 的
//     **`accept` / `multiple`** —— 这是「支持哪些格式、多选」这两个问题的**机器可读答案**
//     （批次 64 是靠逐个格式试出来的 20 种视频格式；`accept` 能直接说出来）
//   B 空白右键 → 「新建节点」子菜单里**逐字**有哪些项（验证入口 ②）
//   C 资产库模态**第三次**全量对账（与 52 / 86 两次逐字比对）
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };

const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const selN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]');
  return e ? e.getAttribute('aria-label') : null; });
out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits() };
log('起点：', JSON.stringify(out.start));

// ================= A 触发 filechooser 但不选文件 =================
log('\n=== A 触发 filechooser，读 <input type=file> 的属性 ===');
{
  const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role="button"]'))
    .map((e) => { const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'),
        x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
    .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0));
  out.rail = rail;
  log('左栏上传入口：', JSON.stringify(rail));
  if (rail.length) {
    let seen = null;
    // ⚠️ **必须用全局 `p.on`**：`p.waitForEvent('filechooser')` 在 `connectOverCDP` 下会超时（批次 101 实测）
    p.on('filechooser', async (fc) => {
      const el = fc.element();
      const info = await el.evaluate((n) => ({
        tag: n.tagName, type: n.getAttribute('type'), accept: n.getAttribute('accept'),
        multiple: n.hasAttribute('multiple'), name: n.getAttribute('name'),
        displayStyle: getComputedStyle(n).display, w: n.offsetWidth, h: n.offsetHeight,
        parentTag: n.parentElement ? n.parentElement.tagName : null,
        parentCls: n.parentElement ? (n.parentElement.className || '').toString().slice(0, 50) : null,
        inDOM: document.body.contains(n),
      })).catch((e) => ({ err: e.message }));
      seen = { isMultiple: fc.isMultiple(), element: info };
      log('  filechooser 触发：', JSON.stringify(seen));
      // **不 setFiles**：让 Playwright 自动取消这次选择
    });
    const r0 = rail[0];
    await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(600);
    await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);
    await p.waitForTimeout(3000);
    out.chooser = seen;
    log('  3 秒后读到：', JSON.stringify(out.chooser));
  }
}

// ================= B 空白右键 → 新建节点 子菜单 =================
log('\n=== B 空白右键 → 新建节点 子菜单 ===');
{
  const blank = await p.evaluate(() => {
    const bad = (x, y) => { const el = document.elementFromPoint(x, y);
      if (!el || el.closest('.react-flow__node')) return true;
      if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
      if (el.closest('button,[role=button],input,a')) return true; return false; };
    for (let y = 280; y < 620; y += 16) for (let x = 260; x < 1100; x += 16) if (!bad(x, y)) return [x, y];
    return null; });
  log('空白点：', JSON.stringify(blank));
  out.blank = blank;
  if (blank) {
    await p.mouse.move(blank[0], blank[1]); await p.waitForTimeout(400);
    await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
    await p.waitForTimeout(1000);
    out.blankMenu = await p.evaluate(() => Array.from(document.querySelectorAll('[role=menu]')).map((m) => {
      const r = m.getBoundingClientRect();
      return { rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
        aria: m.getAttribute('aria-label'),
        items: Array.from(m.querySelectorAll('[role=menuitem]')).map((e) => { const q = e.getBoundingClientRect();
          return { txt: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
            w: Math.round(q.width), h: Math.round(q.height),
            hasSub: !!e.querySelector('[aria-haspopup],[aria-expanded]') }; }) }; }));
    log('空白右键菜单：', JSON.stringify(out.blankMenu, null, 1));
  }
}

writeFileSync(new URL('./_tmp-b102a.json', import.meta.url), JSON.stringify(out, null, 1));
log('\n终态：', JSON.stringify({ nodes: await nodeN(), sel: await selN(), credits: await credits() }));
await b.close();
