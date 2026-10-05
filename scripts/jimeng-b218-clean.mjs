/**
 * 批次 218 收尾补丁：删掉那个**被拖到画布左侧**、在 `50%` 缩放下**不在视口内**的节点。
 *
 * 🔴 本补丁补的是路径链缺的那一环 —— 批次 218 的主脚本有两条路径：
 *   路径 A「画布直点」与路径 B「搜索面板点结果行」，但它们**各自都想干两件事**：
 *     · 画布直点：既负责「选中」，也负责「把焦点交回画布」—— 节点不在视口内时**两件都做不了**；
 *     · 搜索面板：能把节点**框进视口**，但点完结果行焦点落在**结果行 `BUTTON`** 上
 *       ⇒ 按 `⌫` 无效（批次 190/215/217 已三次复现）。
 *   ⇒ 正确姿势是**把两件事拆开、各用一个工具**：
 *     **先用搜索把节点框进视口 → 再在画布上直点它（焦点就回到 `.react-flow`）→ 才按 `⌫`。**
 *
 * 📌 立规 97（肯定式焦点判据）＋ 立规 98（推进看结果）本补丁全程照做。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b218-clean.json';
const 前 = JSON.parse(fs.readFileSync('/tmp/b218.json', 'utf8'));
const 要删 = (前.清理.要删 || []).slice();
const 基线id = new Set((前.步骤0_前置 || {}).基线id || []);

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b218-clean', 要删, 步: {} };

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
    画布: t ? [Number(t[1]), Number(t[2])] : null };
}));
const 状态行 = (p) => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes, (\d+) edges, (\d+) selected[^\n]*/) || [])[0] || null);
const 积分 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').startsWith('Credits'));
  return e ? e.getAttribute('aria-label') : null;
});
const 还在 = async (p, id) => (await 清单(p)).some((n) => n.id === id);
const 焦点 = (p) => p.evaluate(() => {
  const a = document.activeElement;
  return { tag: a ? a.tagName : null, testid: a ? a.getAttribute('data-testid') : null,
    inRF: !!(a && a.closest && a.closest('.react-flow')) };
});
const 结果行点 = (p, id) => p.evaluate((nid) => {
  const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, id.replace(/^node_/, ''));
const 搜索钮 = async (p) => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
    || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
});

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
const p = await ctx.newPage();
await p.setViewportSize({ width: 1280, height: 720 });
await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForSelector('.react-flow__node', { timeout: 45000 });
await p.waitForTimeout(5000);
out.前置 = { 数: (await 清单(p)).length, 状态行: await 状态行(p), 积分: await 积分(p) };
log('【前置】' + out.前置.数 + ' ｜ ' + out.前置.状态行);

for (const id of 要删) {
  const 步 = { id, 尝试: [] };
  if (!await 还在(p, id)) { 步.备注 = '已不存在'; out.步[id] = 步; log('· ' + id + ' 已不存在'); continue; }
  for (let round = 1; round <= 3 && await 还在(p, id); round++) {
    const 记 = { 轮: round };
    // ① 搜索：把它**框进视口**
    const 钮 = await 搜索钮(p);
    if (!钮) { 记.失败 = '找不到搜索钮'; 步.尝试.push(记); break; }
    await p.mouse.click(钮[0], 钮[1]);
    await p.waitForTimeout(1500);
    const 有框 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input'))
        .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      if (!e) return false;
      e.focus(); e.select(); return true;
    });
    if (!有框) { 记.失败 = '找不到搜索输入框'; 步.尝试.push(记); break; }
    await p.keyboard.press('Backspace');
    await p.waitForTimeout(200);
    const 名 = ((await 清单(p)).find((n) => n.id === id) || {}).aria || '';
    const 词 = (名.split('node: ')[1] || 名).trim();
    await p.keyboard.type(词, { delay: 90 });
    await p.waitForTimeout(2200);
    const 回读 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input'))
        .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      return e ? e.value : null;
    });
    const 行 = await 结果行点(p, id);
    记.词 = 词; 记.回读 = 回读; 记.有行 = !!行;
    if (!行) { 记.失败 = '结果行不在'; 步.尝试.push(记); log(`  轮${round} 词「${词}」没有那一行`); continue; }
    await p.mouse.click(行[0], 行[1]);
    await p.waitForTimeout(2000);
    记.框进来后焦点 = await 焦点(p);
    记.框进来后位置 = (await 清单(p)).find((n) => n.id === id);
    // ② 画布直点：把**焦点交回画布**（这一步现在应该能成，因为节点已在视口内）
    const 格 = await p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      if (!n) return { 失败: '不在 DOM' };
      const r = n.getBoundingClientRect();
      if (r.right < 0 || r.x > innerWidth || r.bottom < 0 || r.y > innerHeight) return { 失败: '不在视口内', 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
      for (let fy = 0.15; fy <= 0.9; fy += 0.125) for (let fx = 0.15; fx <= 0.9; fx += 0.125) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const h = document.elementFromPoint(x, y);
        if (h && h.closest(`.react-flow__node[data-id="${nid}"]`)) return { x, y };
      }
      return { 失败: '候选点全被盖' };
    }, id);
    记.格 = 格;
    if (格.x === undefined) { 记.失败 = '直点失败：' + 格.失败; 步.尝试.push(记); log(`  轮${round} 直点失败 ${格.失败}`); continue; }
    await p.mouse.click(格.x, 格.y);
    await p.waitForTimeout(1500);
    记.直点后焦点 = await 焦点(p);
    记.选中集 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
    // ③ 守卫（肯定式）→ 按 ⌫
    const 守卫过 = !!(记.选中集 && 记.选中集.includes(id) && 记.直点后焦点.inRF);
    记.守卫过 = 守卫过;
    if (!守卫过) { 记.失败 = '守卫没过：选中=' + JSON.stringify(记.选中集) + ' 焦点=' + JSON.stringify(记.直点后焦点); 步.尝试.push(记); log(`  轮${round} 守卫没过`); continue; }
    await p.keyboard.press('Backspace');
    await p.waitForTimeout(2600);
    记.删后仍在 = await 还在(p, id);
    步.尝试.push(记);
    log(`  轮${round} 框进来后焦点inRF=${记.框进来后焦点.inRF} → 直点后焦点inRF=${记.直点后焦点.inRF} → 删后仍在 ${记.删后仍在} ｜ 当前 ${(await 清单(p)).length} 个节点`);
  }
  步.最终还在 = await 还在(p, id);
  out.步[id] = 步;
  log('⇒ ' + id + ' 最终还在 ' + 步.最终还在);
}

const 末 = await 清单(p);
out.后置 = { 数: 末.length, 状态行: await 状态行(p), 积分: await 积分(p),
  缩放: await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; }),
  多出来: 末.filter((n) => !基线id.has(n.id)).map((n) => n.id + ' ' + n.aria),
  少了: [...基线id].filter((x) => !末.some((n) => n.id === x)) };
log('【后置】' + out.后置.数 + ' ｜ 多 ' + JSON.stringify(out.后置.多出来) + ' ｜ 少 ' + JSON.stringify(out.后置.少了));
log('【后置】' + out.后置.状态行 + ' ｜ 缩放 ' + out.后置.缩放 + ' ｜ 积分 ' + out.后置.积分);
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);
