/**
 * 批次 225：**两件事，都由批次 224 的读数直接逼出来。**
 *
 * 🔴 ① **批次 223 有一条结论必须自查**：那里写「`文本 3` 实测**没有**取景带，
 *   它永远是『居中 `50%』」。但批次 224 的同宽重复复核（`12` 臂）显示
 *   `文本 3` 的落点是 `0.5` 而**中心 Y 在 `390.18`–`391.29`** ——
 *   🔴 **不是 `360`**！按立规 104，「`0.5` **且** `Y = 360`」才是「居中 50%」那一支，
 *   所以 `文本 3` **在斜坡分支上**（只是缩放被 `0.5` 顶住了）。
 *   ⇒ **「`文本 3` 没有带子」这个结论站不住**，它只是**带子不在 `1210`–`1234` 这一段**。
 *   📌 本批要把带子**真的找出来**：粗扫 `1100`–`1300` 步长 `4`，
 *   用**中心 Y**当探针（`Y = 360` ⇒ 带子左边；`Y ≈ 390` ⇒ 斜坡分支）。
 *
 * 📌 ② **族标识到底有没有「机器可读」的形式？** 批次 224 的只读清点钉死了：
 *   `class` 里有 `react-flow__node-{audio|text|timeline|image|external|video}` 六种，
 *   每种内部**结构签名唯一**，`data-*` 只有 `data-testid` 与 `data-first-content-source`
 *   （全部 `"node"`）。
 *   ⚠️ 但批次 218/221 把「空节点」与「上传结果节点」分成两个族
 *   （`w*` 分别是 `1212` 与 `1202`）——**这两种在画布上 CSS 尺寸就不同**
 *   （`320×569` vs `569×320`），本批要**新建一个上传结果节点并清点它的指纹**，
 *   看它与 `视频 1` 到底差在哪一个字段上。
 *
 * 📌 立规 106：逐臂记录「开页时的当前缩放」，确认本批测的是 `0.260267` 而不是别的。
 * 📌 立规 99：判可复现须同宽重复开页（`1216`/`1218`/`1224`/`1230` 各 `3` 次已在 224 做过，
 *   本批的粗扫是**定位**，定位完再用重复开页确认）。
 *
 * ⛔ 不触发任何生成；只走本地文件上传；新建的节点**必须删干净**（立规 97/98/101）。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 上传文件 = '/tmp/jimeng-b196-probe.mp4';
const 文本档 = [];
for (let w = 1100; w <= 1300; w += 4) 文本档.push(w);
const OUT = '/tmp/b225.json';

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b225', 文本档 };

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
  const 候选 = [...new Set([词, 去扩, String(词 || '').split('-').slice(0, 2).join('-')].filter(Boolean))];
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

// ============ 步骤 0：前置 ============
try {
  const p0 = await 开页(1280);
  out.步骤0_前置 = { 积分: await 积分(p0), 基线id: (await 清单(p0)).map((n) => n.id).sort(),
    基线数: (await 清单(p0)).length, 状态行: await 状态行(p0), 缩放标签: await 缩放标签(p0), 当前缩放: await 当前缩放(p0) };
  log('【前置】节点 ' + out.步骤0_前置.基线数 + ' ｜ 缩放 ' + out.步骤0_前置.缩放标签 + '（实际 ' + out.步骤0_前置.当前缩放 + '）');
  out.视频1指纹 = await 指纹(p0, 'node_236ctpehgg');
  log('【参照】视频 1 指纹：' + JSON.stringify(out.视频1指纹));
  await p0.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤0: ' + e.message]); log('🔴 步骤0 ' + e.message); }

// ============ 步骤 1：新建上传结果节点并清点指纹 ============
try {
  const p1 = await 开页(1280);
  const 入口 = await p1.evaluate(() => {
    const e = Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '视频');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  });
  if (!入口) throw new Error('面板上找不到「视频」入口');
  const 归属 = await p1.evaluate(([x, y, w, h]) => {
    const el = document.elementFromPoint(x + w / 2, y + h / 2);
    return el ? el.getAttribute('aria-label') : null;
  }, 入口);
  if (归属 !== '视频') throw new Error('「视频」入口落点归属不对：' + 归属);
  const 建前 = (await 清单(p1)).map((n) => n.id);
  await p1.mouse.click(入口[0] + 入口[2] / 2, 入口[1] + 入口[3] / 2);
  await p1.waitForTimeout(3500);
  const 新增 = (await 清单(p1)).filter((n) => !建前.includes(n.id));
  if (新增.length !== 1) throw new Error('新建节点数不是 1：' + JSON.stringify(新增));
  自建.push(新增[0].id);
  out.空节点 = 新增[0];
  out.空节点指纹 = await 指纹(p1, 新增[0].id);
  log('【新建】' + JSON.stringify(新增[0]));
  log('【空节点指纹】' + JSON.stringify(out.空节点指纹));
  await p1.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤1: ' + e.message]); log('🔴 步骤1 ' + e.message); }

try {
  const p1 = await 开页(1280);
  const files = p1.locator('input[type=file]');
  let 目标i = -1;
  for (let i = 0, n = await files.count(); i < n; i++) {
    const acc = await files.nth(i).getAttribute('accept');
    if (acc && /video\/(mp4|quicktime)|\.mp4/.test(acc)) { 目标i = i; break; }
  }
  if (目标i < 0) throw new Error('没有接受视频的 file input');
  const 上传前 = (await 清单(p1)).map((n) => n.id);
  await files.nth(目标i).setInputFiles(上传文件);
  let 新出来 = null;
  for (let t = 0; t < 30; t++) {
    await p1.waitForTimeout(2000);
    const 出来的 = (await 清单(p1)).filter((n) => !上传前.includes(n.id) && !自建.includes(n.id));
    if (出来的.length) { for (const nn of 出来的) 自建.push(nn.id); 新出来 = 出来的; break; }
  }
  if (!新出来 || !新出来.length) throw new Error('30 次轮询都没等到新产物');
  out.媒体节点 = 新出来[0];
  await p1.waitForTimeout(2500);
  out.媒体节点指纹 = await 指纹(p1, 新出来[0].id);
  log('【上传】新产物 ' + JSON.stringify(新出来[0]));
  log('【媒体节点指纹】' + JSON.stringify(out.媒体节点指纹));
  await p1.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤2: ' + e.message]); log('🔴 步骤2 ' + e.message); }

// ============ 步骤 3：文本 3 粗扫（用中心 Y 当探针）============
log(`\n【扫描】文本 3 粗扫 ${文本档.length} 档（1100–1300 步长 4），中心 Y 当探针`);
out.文本扫描 = [];
let 臂序号 = 0;
for (const w of 文本档) {
  臂序号 += 1;
  const p2 = await ctx.newPage();
  try {
    await p2.setViewportSize({ width: w, height: H });
    await p2.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p2.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p2.waitForTimeout(4500);
    const 当前 = await 当前缩放(p2);
    const 取 = await 取景(p2, '文本 3', 'node_5gftn3dnt1');
    if (!取.ok) { log(`  w=${w} ⛔ ${取.无效臂}`); out.文本扫描.push({ w, 臂: 臂序号, 无效臂: 取.无效臂 }); await p2.close(); continue; }
    const 读 = await 采样(p2, 'node_5gftn3dnt1');
    out.文本扫描.push({ w, 臂: 臂序号, 当前缩放: 当前, scale: 读.vp ? 读.vp[2] : null,
      中心Y: 读.中心 ? 读.中心[1] : null, 屏上: 读.屏上, 分支: 读.中心 && 读.中心[1] === 360 ? '居中50' : '斜坡' });
    log(`  w=${w} z0=${当前} → s=${读.vp ? 读.vp[2] : null} 中心Y=${读.中心 ? 读.中心[1] : null} 分支=${读.中心 && 读.中心[1] === 360 ? '居中50' : '斜坡'}`);
  } catch (e) { log(`  w=${w} 🔴 ${e.message}`); }
  finally { try { await p2.close(); } catch (e) { /* 页签可能被别的会话关掉 */ } }
}

// ============ 步骤 4：收尾（删自建节点 + 缩放归位）============
try {
  const p3 = await 开页(1280);
  out.清理 = { 要删: 自建.slice() };
  await 设缩放(p3, 50);
  for (const id of 自建) out.清理[id] = await 删一个(p3, id);
  const 归位 = await 设缩放(p3, 26);
  out.清理.缩放归位 = 归位;
  const 末清单 = await 清单(p3);
  const 基线集 = new Set(out.步骤0_前置.基线id || []);
  out.清理.最终数 = 末清单.length;
  out.清理.多出来 = 末清单.filter((n) => !基线集.has(n.id)).map((n) => n.id + ' ' + n.aria);
  out.清理.少了 = (out.步骤0_前置.基线id || []).filter((x) => !末清单.some((n) => n.id === x));
  out.清理.最终状态行 = await 状态行(p3);
  out.清理.最终积分 = await 积分(p3);
  out.清理.最终缩放 = await 缩放标签(p3);
  out.清理.最终当前缩放 = await 当前缩放(p3);
  log('\n【收尾】节点 ' + out.清理.最终数 + ' ｜ 多 ' + JSON.stringify(out.清理.多出来) + ' ｜ 少 ' + JSON.stringify(out.清理.少了));
  log('【收尾】' + out.清理.最终状态行 + ' ｜ 缩放 ' + out.清理.最终缩放 + ' ｜ 积分 ' + out.清理.最终积分);
  await p3.close();
} catch (e) { out.清理 = { 出错: e.message }; log('🔴 清理 ' + e.message); }

out.自建清单 = 自建;
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);