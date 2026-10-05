/**
 * 批次 215 清理：把本批自己新建的 2 个节点删掉，把画布还原到 76 节点 / 26% / 0 选中。
 *
 * 🔴🔴 本脚本存在的理由：215 主脚本的清理**两条路径都没删掉**（画布停在 78 / 1 选中 / 50%）。
 *   两个根因（本批新发现，写进立规 97）：
 *   ① **焦点守卫漏了 `BUTTON`**：点搜索结果行之后 `document.activeElement` 是那个
 *      `<button>`，**不是 input 也不是 contenteditable** ⇒ 老守卫判成「安全」、
 *      老老实实按了 Backspace ⇒ **按键被这个按钮吃掉**，节点纹丝不动。
 *      （`isInput` / `inCE` 两个判据都过，守卫却漏了最常见的第三种焦点宿主。）
 *   ② **路径链被「前置条件」推进而不是被「结果」推进**：老代码写成
 *      「路径 A 拿到选中 ⇒ 认定路径 A 成功 ⇒ 不再走路径 B」，
 *      而 A 是在**删除那一步**才失败的 ⇒ **另一条路径永远不会被触发**。
 *
 * 📌 本版两条纪律：
 *   · 每条路径之后都问一次「**目标还在吗**」，还在就换下一条 —— 推进看**结果**；
 *   · 焦点守卫补 `BUTTON`，并且选中后**显式 blur** 再按 Backspace。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const OUT = '/tmp/b215-clean.json';
const 前 = JSON.parse(fs.readFileSync('/tmp/b215.json', 'utf8'));
const 要删 = 前.自建清单 || [];
const 基线id = new Set((前.步骤0_前置 || {}).基线id || []);

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b215-clean', 要删, 步: {} };

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
    画布: t ? [Number(t[1]), Number(t[2])] : null, 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}));
const 状态行 = (p) => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes, (\d+) edges, (\d+) selected[^\n]*/) || [])[0] || null);
const 积分 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').startsWith('Credits'));
  return e ? e.getAttribute('aria-label') : null;
});
/** 🔴 立规 97 的加强版：焦点守卫必须覆盖 BUTTON / contenteditable / input 三种宿主。 */
const 焦点 = (p) => p.evaluate(() => {
  const a = document.activeElement;
  return { tag: a ? a.tagName : null, aria: a ? a.getAttribute('aria-label') : null,
    testid: a ? a.getAttribute('data-testid') : null,
    inCE: !!(a && (a.closest('[contenteditable]') || a.isContentEditable)),
    isInput: !!(a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA')),
    isButton: !!(a && (a.tagName === 'BUTTON' || a.getAttribute('role') === 'button')) };
});
const 还在 = async (p, id) => (await 清单(p)).some((n) => n.id === id);

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
const p = await ctx.newPage();
await p.setViewportSize({ width: 1280, height: H });
await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForSelector('.react-flow__node', { timeout: 45000 });
await p.waitForTimeout(5000);

out.前置 = { 数: (await 清单(p)).length, 状态行: await 状态行(p), 积分: await 积分(p) };
log('【前置】' + out.前置.数 + ' 个节点 ｜ ' + out.前置.状态行);

for (const id of 要删) {
  const 步 = { id, 尝试: [] };
  if (!await 还在(p, id)) { 步.备注 = '已不存在'; out.步[id] = 步; log('· ' + id + ' 已不存在'); continue; }

  // ============ 路径链：每条之后都问「还在吗」，**推进看结果不看前置** ============
  for (const 路径 of ['A:画布直点', 'B:搜索面板+blur', 'C:搜索面板+再点一次', 'D:画布直点(缩放到50%)']) {
    if (!await 还在(p, id)) break;
    const 记 = { 路径 };
    if (路径.startsWith('B') || 路径.startsWith('C')) {
      const 钮 = await p.evaluate(() => {
        const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
          || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      });
      if (!钮) { 记.失败 = '找不到搜索钮'; 步.尝试.push(记); continue; }
      await p.mouse.click(钮[0], 钮[1]);
      await p.waitForTimeout(1500);
      const 有框 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input'))
          .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        if (!e) return false;
        e.focus(); e.select(); return true;
      });
      if (!有框) { 记.失败 = '找不到搜索输入框'; 步.尝试.push(记); continue; }
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
      const 行 = await p.evaluate((nid) => {
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      }, id.replace(/^node_/, ''));
      记.词 = 词; 记.回读 = 回读; 记.有行 = !!行;
      if (!行 || 回读 !== 词) { 记.失败 = '没有那一行 / 输入没进去'; 步.尝试.push(记); log('  ' + 路径 + ' 失败：' + 记.失败); continue; }
      await p.mouse.click(行[0], 行[1]);
      await p.waitForTimeout(1500);
      记.点行后焦点 = await 焦点(p);
      if (路径.startsWith('C')) {
        await p.mouse.click(行[0], 行[1]);
        await p.waitForTimeout(1200);
        记.再点一次后焦点 = await 焦点(p);
      }
      记.选中集 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
    } else {
      // 路径 A / D：立规 82 的网格归属判据
      if (路径.startsWith('D')) {
        await p.evaluate(() => {
          const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
          if (e) { const r = e.getBoundingClientRect(); window.__z = [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }
        });
        const zb = await p.evaluate(() => window.__z);
        if (zb) { await p.mouse.click(zb[0], zb[1]); await p.waitForTimeout(1200);
          await p.fill('[data-testid="canvas-zoom-percent-input"]', '50');
          await p.keyboard.press('Enter');
          await p.waitForTimeout(2500); }
      }
      const 格 = await p.evaluate((nid) => {
        const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
        if (!n) return { 失败: '不在 DOM' };
        const r = n.getBoundingClientRect();
        if (r.right < 0 || r.x > innerWidth || r.bottom < 0 || r.y > innerHeight) return { 失败: '不在视口内', 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
        for (let fy = 0.1; fy <= 0.95; fy += 0.142857) for (let fx = 0.1; fx <= 0.95; fx += 0.142857) {
          const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
          const h = document.elementFromPoint(x, y);
          if (h && h.closest(`.react-flow__node[data-id="${nid}"]`)) return { x, y, 相对: [Math.round(fx * 100), Math.round(fy * 100)] };
        }
        return { 失败: '49 个候选点没有一个在节点内（被盖）' };
      }, id);
      记.格 = 格;
      if (格.x === undefined) { 记.失败 = 格.失败; 步.尝试.push(记); log('  ' + 路径 + ' 失败：' + 格.失败); continue; }
      await p.mouse.click(格.x, 格.y);
      await p.waitForTimeout(1400);
      记.点后焦点 = await 焦点(p);
      记.选中集 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
    }

    // ---- 统一删除动作：守卫（含 BUTTON）→ 显式 blur → Backspace → **问结果** ----
    记.焦点 = await 焦点(p);
    const 守卫过 = 记.选中集 && 记.选中集.includes(id) && !记.焦点.inCE && !记.焦点.isInput;
    记.守卫过 = 守卫过;
    if (!守卫过) { 记.失败 = '守卫没过：选中=' + JSON.stringify(记.选中集) + ' 焦点=' + JSON.stringify(记.焦点); 步.尝试.push(记); log('  ' + 路径 + ' 守卫没过'); continue; }
    const blur了 = await p.evaluate(() => { const a = document.activeElement; if (a && a.blur) { a.blur(); return true; } return false; });
    记.blur了 = blur了;
    记.blur后焦点 = await 焦点(p);
    await p.keyboard.press('Backspace');
    await p.waitForTimeout(2600);
    记.删后仍在 = await 还在(p, id);
    步.尝试.push(记);
    log(`  ${路径} 选中=${JSON.stringify(记.选中集)} blur=${blur了} → 删后仍在 ${记.删后仍在} ｜ 当前 ${(await 清单(p)).length} 个节点`);
  }

  步.最终还在 = await 还在(p, id);
  out.步[id] = 步;
  log('⇒ ' + id + ' 最终还在 ' + 步.最终还在);
}

// ---- 收尾：把缩放与选中态也还原 ----
try {
  await p.keyboard.press('Escape');
  await p.waitForTimeout(800);
  const zb = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
    if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (zb) {
    await p.mouse.click(zb[0], zb[1]);
    await p.waitForTimeout(1200);
    await p.fill('[data-testid="canvas-zoom-percent-input"]', '26');
    await p.keyboard.press('Enter');
    await p.waitForTimeout(2500);
  }
} catch (e) { log('🔴 缩放归位 ' + e.message); }

const 末 = await 清单(p);
out.后置 = {
  数: 末.length, 状态行: await 状态行(p), 积分: await 积分(p),
  缩放: await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; }),
  多出来: 末.filter((n) => !基线id.has(n.id)).map((n) => n.id + ' ' + n.aria),
  少了: [...基线id].filter((x) => !末.some((n) => n.id === x)),
};
log('【后置】' + out.后置.数 + ' 个节点 ｜ 多 ' + JSON.stringify(out.后置.多出来) + ' ｜ 少 ' + JSON.stringify(out.后置.少了));
log('【后置】' + out.后置.状态行 + ' ｜ 缩放 ' + out.后置.缩放 + ' ｜ 积分 ' + out.后置.积分);
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);
