/**
 * 批次 213 f 轮：补做被打空的那一测 —— 测**真正带媒体**的那个节点；然后**无条件清理**画布。
 *
 * 🔴 批次 213 d 轮的三条实锤（本轮之前只知道结果、不知道机制）：
 *   ① 上传**不是**「把媒体填进当前空节点」，而是**新建一个以文件命名的节点**：
 *      节点数 `77 → 78`（新建「视频 3」）→ 上传 → **`79`**，
 *      多出来的是 `node_d1kty96xmb`，aria 逐字 **`视频 node: jimeng-b196-probe`**，
 *      而 `视频 3`（`node_fv64q8ys02`）**仍然是空的**。
 *      ⇒ d 轮那次 `w=1212 → s=0.260267` **测的还是空节点**，跨族实验**没做成**。
 *   ② `积分 791 → 813`（`+22`）。⚠️ 这是**账号状态真的变了**，本批必须如实记。
 *      （批次 195 记的上传是 `791 → 791`，所以这次不是恒等行为。）
 *   ③ 删除被焦点守卫正确拦下：`焦点 = INPUT`（还在搜索框里）⇒ 不按 `Backspace`。
 *
 * 本轮做两件事：
 *   **甲** 在 `50%` 档读 `node_d1kty96xmb` 的渲染变体 ——
 *        若它已是 `video-node-result`，说明它**跨出了 `-empty` 族**，跨族实验可以真的做。
 *        然后在 `w=1212`（中招档）与 `w=1210`（对照档）各取景一次。
 *   **乙 无论甲成败都执行**：把本批自己新建的 3 个节点
 *      （`node_7nnpspb7t5` 视频 2、`node_fv64q8ys02` 视频 3、`node_d1kty96xmb` 上传产物）
 *      全部删掉，把画布**还原到 76 个节点**。
 *      ⚠️ 删除走手册既有做法：**选中后按 `Backspace`**（不是 `Delete`），
 *         且按之前**必须**过焦点守卫；守卫不过就换路径（右键菜单），不硬按。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 媒体节点 = 'node_d1kty96xmb';
const 自建 = ['node_7nnpspb7t5', 'node_fv64q8ys02', 'node_d1kty96xmb'];
const 宽集 = [1212, 1210];
const OUT = '/tmp/b213f.json';

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b213f', 媒体节点, 自建, 档: {}, 清理: {} };

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'), 画布: t ? [Number(t[1]), Number(t[2])] : null };
}));
const 变体 = (p, id) => p.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const cands = ['video-node-compact', 'video-node-empty', 'video-node-result', 'video-flow-node-surface',
    'video-primary-preview-viewport', 'video-node-status-icon'];
  const r = n.getBoundingClientRect();
  return { 变体: cands.filter((c) => n.querySelector(`[data-testid="${c}"]`)), 屏上: [Math.round(r.width), Math.round(r.height)] };
}, id);
const 焦点 = (p) => p.evaluate(() => {
  const a = document.activeElement;
  return { tag: a ? a.tagName : null, inCE: !!(a && (a.closest('[contenteditable]') || a.isContentEditable)), isInput: !!(a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA')) };
});
const 积分 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').startsWith('Credits'));
  return e ? e.getAttribute('aria-label') : null;
});
const 状态行 = (p) => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes, (\d+) edges, (\d+) selected[^\n]*/) || [])[0] || null);

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];

/** 选中某节点：优先「在画布上按立规 82 网格找一个真在它里面的点」，其次走搜索。 */
const 选中 = async (p, id, aria) => {
  // 路径 A：画布上直接点（先按 6×4 网格找点在节点内）
  const pt = await p.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    for (let fy = 0.15; fy <= 0.9; fy += 0.15) for (let fx = 0.15; fx <= 0.9; fx += 0.15) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const h = document.elementFromPoint(x, y);
      if (h && h.closest(`.react-flow__node[data-id="${nid}"]`)) return { x, y, 相对: [Math.round(fx * 100), Math.round(fy * 100)] };
    }
    return { 不在视口内: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }, id);
  if (pt && pt.x) {
    await p.mouse.click(pt.x, pt.y);
    await p.waitForTimeout(1200);
    const 选中数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
    if (选中数 >= 1) return { 路径: '画布直点', 点: pt, 选中数 };
    return { 路径: '画布直点', 点: pt, 选中数, 失败: '点了但没选中' };
  }
  // 路径 B：搜索
  const 词 = (aria || '').split('node: ')[1];
  if (!词) return { 失败: '不在视口内且没有可搜的名字', pt };
  const 钮 = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
      || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  if (!钮) return { 失败: '找不到搜索钮', pt };
  await p.mouse.click(钮[0], 钮[1]);
  await p.waitForTimeout(1500);
  const 有框 = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
    if (!e) return false;
    e.focus(); e.select(); return true;
  });
  if (!有框) return { 失败: '找不到搜索输入框' };
  await p.keyboard.press('Backspace');
  await p.waitForTimeout(200);
  await p.keyboard.type(词, { delay: 90 });
  await p.waitForTimeout(2200);
  const 行 = await p.evaluate((nid) => {
    const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  }, id.replace(/^node_/, ''));
  if (!行) return { 失败: '搜索结果里没有目标行' };
  await p.mouse.click(行[0], 行[1]);
  await p.waitForTimeout(1200);
  const 选中数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
  return { 路径: '搜索', 行, 选中数 };
};

try {
  // ============ 甲：50% 档读变体 + 两个宽度取景 ============
  {
    const p = await ctx.newPage();
    await p.setViewportSize({ width: 1280, height: H });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(5000);
    out.甲 = {};
    out.甲.变体26 = await 变体(p, 媒体节点);
    // 切到 50%：走缩放按钮
    await p.evaluate(() => {
      const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
      const r = e.getBoundingClientRect();
      window.__z = [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    });
    const zb = await p.evaluate(() => window.__z);
    await p.mouse.click(zb[0], zb[1]);
    await p.waitForTimeout(1200);
    await p.fill('[data-testid="canvas-zoom-percent-input"]', '50');
    await p.keyboard.press('Enter');
    await p.waitForTimeout(2500);
    out.甲.变体50 = await 变体(p, 媒体节点);
    out.甲.缩放aria = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
    log('媒体节点 26 档变体 ' + JSON.stringify(out.甲.变体26) + ' ｜ 50 档变体 ' + JSON.stringify(out.甲.变体50) + ' ｜ ' + out.甲.缩放aria);
    await p.close();
  }
  for (const w of 宽集) {
    const p = await ctx.newPage();
    try {
      await p.setViewportSize({ width: w, height: H });
      await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await p.waitForSelector('.react-flow__node', { timeout: 45000 });
      await p.waitForTimeout(4500);
      out.档[w] = { 变体: await 变体(p, 媒体节点) };
      const 词 = 'jimeng-b196-probe';
      const 钮 = await p.evaluate(() => {
        const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
          || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      });
      await p.mouse.click(钮[0], 钮[1]);
      await p.waitForTimeout(1500);
      const 有框 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        if (!e) return false;
        e.focus(); e.select(); return true;
      });
      await p.keyboard.press('Backspace');
      await p.waitForTimeout(200);
      await p.keyboard.type(词, { delay: 90 });
      await p.waitForTimeout(2200);
      const 输入回读 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        return e ? e.value : null;
      });
      const 行 = await p.evaluate((nid) => {
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
        if (!e) return { 有: false, 现存: Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).slice(0, 6).map((x) => x.getAttribute('data-testid')) };
        const r = e.getBoundingClientRect();
        return { 有: true, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
      }, 媒体节点.replace(/^node_/, ''));
      out.档[w].输入回读 = 输入回读;
      out.档[w].行 = 行;
      if (!行.有 || 输入回读 !== 词) {
        out.档[w].无效臂 = !行.有 ? '目标行不在 ' + JSON.stringify(行.现存) : '输入没进去';
        log(`${w} ⛔ 无效臂 ${out.档[w].无效臂}`);
      } else {
        await p.mouse.click(行.点[0], 行.点[1]);
        await p.waitForTimeout(4000);
        const 采样 = [];
        for (let k = 0; k < 3; k++) {
          采样.push(await p.evaluate((id) => {
            const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
            const vp = document.querySelector('.react-flow__viewport');
            const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
            const r = n ? n.getBoundingClientRect() : null;
            return { 中心: r ? [Math.round((r.x + r.width / 2) * 1000) / 1000, Math.round((r.y + r.height / 2) * 1000) / 1000] : null,
              屏上: r ? [Math.round(r.width), Math.round(r.height)] : null,
              vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null };
          }, 媒体节点));
          await p.waitForTimeout(500);
        }
        const ss = [...new Set(采样.map((x) => x.vp && x.vp[2]))];
        out.档[w].末 = 采样[2];
        out.档[w].断言 = { 判据: '3 次采样 scale 相同', 通过: ss.length === 1 };
        log(`${w} 变体 ${JSON.stringify(out.档[w].变体.变体)} → s=${JSON.stringify(ss)} 中心=${JSON.stringify(采样[2].中心)} 屏上=${JSON.stringify(采样[2].屏上)}`);
      }
    } catch (e) { out.档[w] = { 出错: e.message }; log(`${w} 🔴 ${e.message}`); }
    finally { await p.close(); }
  }
} catch (e) { out.甲出错 = e.message; log('🔴 甲 ' + e.message); }

// ============ 乙：无条件清理 ============
try {
  const p = await ctx.newPage();
  await p.setViewportSize({ width: 1280, height: H });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(5000);
  out.清理.删前 = (await 清单(p)).length;
  out.清理.删前状态行 = await 状态行(p);
  for (const id of 自建) {
    const 步骤 = { id, 存在: (await 清单(p)).some((n) => n.id === id) };
    if (!步骤.存在) { 步骤.备注 = '已不存在'; out.清理[id] = 步骤; continue; }
    const s = await 选中(p, id, (await 清单(p)).find((n) => n.id === id).aria);
    步骤.选中 = s;
    if (s.选中数 >= 1) {
      const f = await 焦点(p);
      步骤.焦点 = f;
      const 安全 = !f.inCE && !f.isInput;
      步骤.焦点安全 = 安全;
      if (安全) {
        await p.keyboard.press('Backspace');
        await p.waitForTimeout(2500);
        步骤.按了Backspace = true;
      } else {
        // 守卫不过：先 Esc 关掉浮层/输入焦点，再复核
        await p.keyboard.press('Escape');
        await p.waitForTimeout(1200);
        const f2 = await 焦点(p);
        const s2 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
        步骤.逃生后焦点 = f2;
        步骤.逃生后选中数 = s2;
        const 安全2 = !f2.inCE && !f2.isInput && s2 >= 1;
        步骤.逃生后安全 = 安全2;
        if (安全2) { await p.keyboard.press('Backspace'); await p.waitForTimeout(2500); 步骤.逃生后按了Backspace = true; }
      }
    }
    步骤.删后仍在 = (await 清单(p)).some((n) => n.id === id);
    步骤.删后数 = (await 清单(p)).length;
    out.清理[id] = 步骤;
    log('清理 ' + id + ' → 仍在 ' + 步骤.删后仍在 + ' ｜ 当前节点数 ' + 步骤.删后数);
  }
  out.清理.最终数 = (await 清单(p)).length;
  out.清理.最终状态行 = await 状态行(p);
  out.清理.积分 = await 积分(p);
  log('清理后 节点数 ' + out.清理.最终数 + ' ｜ ' + out.清理.最终状态行 + ' ｜ 积分 ' + out.清理.积分);
  await p.close();
} catch (e) { out.清理.出错 = e.message; log('🔴 乙 ' + e.message); }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);
