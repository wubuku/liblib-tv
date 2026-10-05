/**
 * 批次 226b：**换个靶子** —— 批次 226 第一版的两处失效都记在这里。
 *
 * 🔴 失效①：**新建的空节点根本不进搜索索引。**
 *   批次 226 第一版新建空 `视频 2`（`视频 node: 视频 2`），**21 臂全部**报
 *   「候选词都没命中那一行」—— 已把候选词表从 `3` 个加长到 `5` 个
 *   （多去 `node: ` 前缀、多去 kind 前缀）**仍然 `0` 命中**。
 *   ⇒ 📌 **不是命名变体问题**（立规 103 那条），而是**这个节点压根没被索引**。
 *   ⇒ 对照事实：画布上**早就在**的 `音频 68` / `文本 3` / `视频 1` / `时间线 2` **都能搜到**。
 *   ⇒ 推测：**新节点在服务端还没进搜索索引**（本批**不下定论**，只记现象）。
 *   ⚠️ 连带影响：**批次 222/225 的收尾删除其实也没走搜索** ——
 *   日志里那两个新建节点的 `试词` 都是 `有行: false`，
 *   真正删掉它们的是**同一条兜底链里的「画布直点」**（立规 101 的那一步）。
 *   ⇒ 📌 立规 101 的价值第二次被兑现：**兜底链按结果推进**，
 *   即使「搜索框进视口」那一步整条失效，后面两步仍能完成任务。
 *
 * 🔴 失效②：`task_stop` / `pkill` 掉的那次运行**留下了节点**（基线从 `76` 变成 `77`）。
 *   ⇒ 与批次 220/222 的读数同族（**日志里打出过 ≠ 服务端留下了**），
 *   但这次方向相反：**服务端留下了，而本地进程没了** ⇒
 *   📌 **被杀掉的运行必须手工清点**，不能假设「没跑完 = 没留下」。
 *   本批开头就把 `node_t8fz0h7dbm`、`node_w6ythgg12r` 删掉。
 *
 * 📌 换的新靶子：**`图片 node: b22-upload`（`node_gref4sw056`，CSS `569×320`，
 *   `class = react-flow__node-image`）** —— 它是画布上**唯一一个可搜的 `569` 宽节点**。
 *   两个互斥预测（相差 `10px`）：
 *     **P1（CSS 宽度决定）**：`w* ≈ 1202`（与 `569` 宽的上传结果节点一致）
 *     **P2（不是宽度）**：`w* = 1212`（与 `320` 宽的 `音频 68` / `视频 1` 一致）
 *   📌 若 P1 成立，说明**宽度**决定带子、**跨 kind 也成立**（`image` 与 `video` 同答案）
 *   ⇒ 批次 223 那条「CSS 尺寸不决定带子」要再收窄为「**宽度决定、高度不决定、kind 不决定**」。
 *
 * ⛔ 本批**不新建、不上传、不删除别人的节点**；只删本会话自己留下的两个孤儿节点。
 */

import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 上传文件 = '/tmp/jimeng-b196-probe.mp4';
const 图片档 = [];
for (let w = 1195; w <= 1215; w += 1) 图片档.push(w);
const 孤儿 = ['node_t8fz0h7dbm', 'node_w6ythgg12r'];   // 📌 失效②：被杀掉的运行留下的
const 靶子 = { id: 'node_gref4sw056', 词: 'b22-upload' };
const OUT = '/tmp/b226b.json';

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b226b', 图片档, 靶子 };

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'), cls: n.className,
    画布: t ? [Number(t[1]), Number(t[2])] : null };
}));
const 积分 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').startsWith('Credits'));
  return e ? e.getAttribute('aria-label') : null;
});
const 状态行 = (p) => p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
const 还在 = async (p, id) => (await 清单(p)).some((n) => n.id === id);
const 当前缩放 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  return m ? Number(m[1]) : null;
});
const 缩放标签 = (p) => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const 焦点 = (p) => p.evaluate(() => {
  const a = document.activeElement;
  return { tag: a ? a.tagName : null, inRF: !!(a && a.closest && a.closest('.react-flow')) };
});
const 采样 = (p, id) => p.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const r = n ? n.getBoundingClientRect() : null;
  return { 中心: r ? [Math.round((r.x + r.width / 2) * 1000) / 1000, Math.round((r.y + r.height / 2) * 1000) / 1000] : null,
    屏上: r ? [Math.round(r.width), Math.round(r.height)] : null,
    off: n ? [n.offsetWidth, n.offsetHeight] : null,
    vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null };
}, id);
const 搜索钮 = async (p) => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
    || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
});
const 结果行点 = (p, id) => p.evaluate((nid) => {
  const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, id.replace(/^node_/, ''));

async function 取景(p, 词, id) {
  const 钮 = await 搜索钮(p);
  if (!钮) return { ok: false, 无效臂: '找不到搜索钮' };
  await p.mouse.click(钮[0], 钮[1]);
  await p.waitForTimeout(1500);
  const 有框 = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('input'))
      .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
    if (!e) return false;
    e.focus(); e.select(); return true;
  });
  if (!有框) return { ok: false, 无效臂: '找不到搜索输入框' };
  const 去扩 = String(词 || '').replace(/\.(mp4|mp3|mov|webm|png|jpg|jpeg)$/i, '');
  // 📌 立规 103 的加强：再把 `node: ` 前缀与「kind 前缀」也去掉，
  //    因为新节点的完整 aria 形如「视频 node: 视频 2」，搜索索引里往往只登了短名。
  const 去前缀 = String(去扩 || '').replace(/^.*?node:\s*/, '');
  const 去类型 = String(去前缀 || '').replace(/^[^\d]+\s*/, '');
  const 候选 = [...new Set([词, 去扩, 去前缀, 去类型, String(词 || '').split('-').slice(0, 2).join('-')].filter(Boolean))];
  for (const 词2 of 候选) {
    await p.keyboard.press('Backspace');
    await p.waitForTimeout(200);
    await p.keyboard.type(词2, { delay: 90 });
    await p.waitForTimeout(2200);
    const 回读 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input'))
        .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      return e ? e.value : null;
    });
    const 点 = await 结果行点(p, id);
    if (点 && 回读 === 词2) { await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(4500); return { ok: true, 用的词: 词2 }; }
  }
  return { ok: false, 无效臂: '候选词都没命中那一行' };
}

async function 指纹(p, id) {
  return p.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!n) return null;
    const ds = {};
    for (const a of Array.from(n.attributes)) if (a.name.startsWith('data-') && a.name !== 'data-id') ds[a.name] = a.value;
    const 留类名段数 = 2;
    const 签名 = (el, 深) => {
      if (深 <= 0 || !el) return '';
      const 子 = Array.from(el.children).slice(0, 4).map((c) => {
        const 有类 = c.className && typeof c.className === 'string';
        const 类段 = 有类 ? '.' + c.className.trim().split(/\s+/).slice(0, 留类名段数).join('.') : '';
        return c.tagName.toLowerCase() + 类段 + 签名(c, 深 - 1);
      }).join('>');
      return 子 ? '[' + 子 + ']' : '';
    };
    return { id: nid, aria: n.getAttribute('aria-label'), cls: (n.className || '').trim(),
      css: [n.offsetWidth, n.offsetHeight], data: ds, 结构: 签名(n, 2),
      含媒体: ['video', 'audio', 'img', 'canvas'].filter((t) => !!n.querySelector(t)),
      标签统计: Array.from(n.querySelectorAll('*')).reduce((m, e2) => { const t = e2.tagName.toLowerCase(); m[t] = (m[t] || 0) + 1; return m; }, {}) };
  }, id);
}

/** 立规 101：搜索框进视口 → 画布直点交回焦点 → 才按 ⌫。 */
async function 删一个(p, id) {
  const 记 = { id, 尝试: [] };
  for (let round = 1; round <= 3 && await 还在(p, id); round++) {
    const 一轮 = { 轮: round };
    const 现 = (await 清单(p)).find((n) => n.id === id);
    if (!现) { 一轮.备注 = '已不存在'; 记.尝试.push(一轮); break; }
    const 钮 = await 搜索钮(p);
    if (!钮) { 一轮.失败 = '找不到搜索钮'; 记.尝试.push(一轮); break; }
    await p.mouse.click(钮[0], 钮[1]);
    await p.waitForTimeout(1500);
    const 有框 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input'))
        .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      if (!e) return false;
      e.focus(); e.select(); return true;
    });
    if (!有框) { 一轮.失败 = '找不到搜索输入框'; 记.尝试.push(一轮); break; }
    const 去扩 = (现.aria || '').replace(/\.(mp4|mp3|mov|webm|png|jpg|jpeg)$/i, '');
    for (const 词 of [...new Set([去扩, 现.aria || ''].filter(Boolean))]) {
      await p.keyboard.press('Backspace');
      await p.waitForTimeout(200);
      await p.keyboard.type(词, { delay: 90 });
      await p.waitForTimeout(2200);
      const 行 = await 结果行点(p, id);
      一轮.试词 = (一轮.试词 || []).concat([{ 词, 有行: !!行 }]);
      if (!行) continue;
      await p.mouse.click(行[0], 行[1]);
      await p.waitForTimeout(2000);
      break;
    }
    一轮.框进来后焦点 = await 焦点(p);
    const 格 = await p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      if (!n) return { 失败: '不在 DOM' };
      const r = n.getBoundingClientRect();
      if (r.right < 0 || r.x > innerWidth || r.bottom < 0 || r.y > innerHeight) return { 失败: '不在视口内' };
      for (let fy = 0.15; fy <= 0.9; fy += 0.125) for (let fx = 0.15; fx <= 0.9; fx += 0.125) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const h = document.elementFromPoint(x, y);
        if (h && h.closest(`.react-flow__node[data-id="${nid}"]`)) return { x, y };
      }
      return { 失败: '候选点全被盖' };
    }, id);
    if (格.x === undefined) { 一轮.失败 = '直点失败：' + 格.失败; 记.尝试.push(一轮); log(`  轮${round} 直点失败 ${格.失败}`); continue; }
    await p.mouse.click(格.x, 格.y);
    await p.waitForTimeout(1500);
    一轮.直点后焦点 = await 焦点(p);
    一轮.选中集 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
    一轮.守卫过 = !!(一轮.选中集 && 一轮.选中集.includes(id) && 一轮.直点后焦点.inRF);
    if (!一轮.守卫过) { 一轮.失败 = '守卫没过'; 记.尝试.push(一轮); log(`  轮${round} 守卫没过`); continue; }
    await p.keyboard.press('Backspace');
    await p.waitForTimeout(2600);
    一轮.删后仍在 = await 还在(p, id);
    记.尝试.push(一轮);
    log(`  轮${round} 框进来后inRF=${一轮.框进来后焦点.inRF} → 直点后inRF=${一轮.直点后焦点.inRF} → 删后仍在 ${一轮.删后仍在} ｜ 当前 ${(await 清单(p)).length} 个节点`);
  }
  记.最终还在 = await 还在(p, id);
  return 记;
}

async function 设缩放(p, 值) {
  const b = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
    if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!b) return { ok: false, 失败: '找不到缩放按钮' };
  await p.mouse.click(b[0], b[1]);
  await p.waitForTimeout(1200);
  await p.fill('[data-testid="canvas-zoom-percent-input"]', String(值));
  await p.keyboard.press('Enter');
  await p.waitForTimeout(3000);
  return { ok: true, 标签: await 缩放标签(p), 实际: await 当前缩放(p) };
}

const 浏览器 = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = 浏览器.contexts()[0];
const 自建 = [];
async function 开页(w) {
  const p = await ctx.newPage();
  await p.setViewportSize({ width: w, height: H });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(4500);
  return p;
}



// ============ 步骤 0：前置 + 指纹 ============
const p0 = await 开页(1280);
out.步骤0_前置 = { 积分: await 积分(p0), 基线id: (await 清单(p0)).map((n) => n.id).sort(),
  基线数: (await 清单(p0)).length, 状态行: await 状态行(p0), 缩放标签: await 缩放标签(p0), 当前缩放: await 当前缩放(p0) };
log('【前置】节点 ' + out.步骤0_前置.基线数 + ' ｜ 缩放 ' + out.步骤0_前置.缩放标签 + '（实际 ' + out.步骤0_前置.当前缩放 + '）');
out.靶子指纹 = await 指纹(p0, 靶子.id);
log('【靶子】' + JSON.stringify(out.靶子指纹));
const 孤儿实际 = (await 清单(p0)).filter((n) => 孤儿.includes(n.id)).map((n) => n.id + ' ' + n.aria);
log('【孤儿】页面上实际存在的孤儿节点：' + JSON.stringify(孤儿实际));
out.孤儿实际 = 孤儿实际;
await p0.close();

// ============ 步骤 1：删掉孤儿 ============
out.清理孤儿 = [];
try {
  const pc = await 开页(1280);
  await 设缩放(pc, 50);
  for (const id of 孤儿) out.清理孤儿.push(await 删一个(pc, id));
  out.清理孤儿.最终数 = (await 清单(pc)).length;
  log('【孤儿】删除后节点数 ' + out.清理孤儿.最终数);
  await pc.close();
} catch (e) { out.清理孤儿 = { 出错: e.message }; log('🔴 孤儿清理 ' + e.message); }

// ============ 步骤 2：扫描靶子的带子 ============
out.扫描 = [];
let 臂序号 = 0;
log(`\n【扫描】${靶子.词}（569×320）${图片档.length} 档（${图片档[0]}–${图片档[图片档.length-1]} 步长 1）`);
for (const w of 图片档) {
  臂序号 += 1;
  const p2 = await ctx.newPage();
  try {
    await p2.setViewportSize({ width: w, height: H });
    await p2.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p2.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p2.waitForTimeout(4500);
    const 当前 = await 当前缩放(p2);
    const 前置 = await p2.evaluate((nid) => !!document.querySelector(`.react-flow__node[data-id="${nid}"]`), 靶子.id);
    if (!前置) { log(`  w=${w} ⛔ 节点不在`); continue; }
    const 取 = await 取景(p2, 靶子.词, 靶子.id);
    if (!取.ok) { log(`  w=${w} ⛔ ${取.无效臂}`); out.扫描.push({ w, 臂: 臂序号, 无效臂: 取.无效臂 }); await p2.close(); continue; }
    const 三采 = [];
    for (let i = 0; i < 3; i++) { 三采.push(await 采样(p2, 靶子.id)); await p2.waitForTimeout(450); }
    const ss = [...new Set(三采.map((x) => x.vp && x.vp[2]))];
    const 末 = 三采[2];
    out.扫描.push({ w, 臂: 臂序号, 当前缩放: 当前, scale: 末.vp ? 末.vp[2] : null,
      屏上: 末.屏上, off: 末.off, 中心: 末.中心, 页内一致: ss.length === 1,
      分支: 末.中心 && 末.中心[1] === 360 ? '居中50' : '斜坡', 用的词: 取.用的词 });
    log(`  w=${w} z0=${当前} → s=${JSON.stringify(ss)} 屏上=${JSON.stringify(末.屏上)} 中心Y=${末.中心 ? 末.中心[1] : null} 分支=${末.中心 && 末.中心[1] === 360 ? '居中50' : '斜坡'}`);
  } catch (e) { log(`  w=${w} 🔴 ${e.message}`); }
  finally { try { await p2.close(); } catch (e) { } }
}

// ============ 步骤 3：收尾读数 ============
try {
  const p3 = await 开页(1280);
  const 末清单 = await 清单(p3);
  const 基线集 = new Set(out.步骤0_前置.基线id || []);
  out.收尾 = { 最终数: 末清单.length,
    相对前置多出来: 末清单.filter((n) => !基线集.has(n.id)).map((n) => n.id + ' ' + n.aria),
    相对前置少了: (out.步骤0_前置.基线id || []).filter((x) => !末清单.some((n) => n.id === x)),
    状态行: await 状态行(p3), 积分: await 积分(p3), 缩放标签: await 缩放标签(p3), 当前缩放: await 当前缩放(p3) };
  log('\n【收尾】节点 ' + out.收尾.最终数 + ' ｜ 相对前置多 ' + JSON.stringify(out.收尾.相对前置多出来) + ' ｜ 少 ' + JSON.stringify(out.收尾.相对前置少了));
  log('【收尾】' + out.收尾.状态行 + ' ｜ 缩放 ' + out.收尾.缩放标签 + ' ｜ 积分 ' + out.收尾.积分);
  await p3.close();
} catch (e) { out.收尾 = { 出错: e.message }; log('🔴 收尾 ' + e.message); }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);
