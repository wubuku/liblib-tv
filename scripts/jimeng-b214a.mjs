/**
 * 批次 214：对批次 213 的「必要条件」做**第二次独立检验** —— 换成 `audio` 类型。
 *
 * 批次 213 得到的只是一条**必要条件**：
 *   `w=1212` 时，凡 `50%` 档渲染 `*-node-empty` 的节点必取 `scale = 0.260267`（中招）；
 *   凡渲染 `-result` / `-full` / 不变的（timeline、external）都**不取** `0.260267`。
 * ⚠️ 但媒体视频节点不中招却也**不等于 `0.5`**（它是 `0.371397`）⇒ 还有一个未隔离的因子。
 *
 * 🔴 为什么非做不可：批次 213 那次「跨族移动」**只有一个样本**（video）。
 *   一次干预、一次结果，**不足以把一条必要条件说成规律**（📕 立规 93 的第 3 条）。
 *   本轮换一个**类型**（`audio`）做同样的干预 ——
 *   若 audio 带媒体后也落在「**不取 `0.260267`、但也不到 `0.5`**」的中间带，
 *   那就是这条必要条件的**第二次独立复现**。
 *
 * 📌 严格照抄批次 213 的流程，只换**类型**与**媒体类型**这一个变量：
 *   ① 节点面板点「音频」新建空节点（它会自动选中）
 *   ② 给它上传一个本地 **mp3**（页面第 2 个 file input 的 `accept` 含 `audio/mpeg`/`audio/mp3`）
 *   ③ 确认新节点在 `50%` 档渲染成什么
 *   ④ 在 `w=1212`（中招档）与 `w=1210`（对照档）各取景一次
 *   ⑤ **无条件清理**到 `76 节点 / 0 多 0 少`
 *
 * 📌 立规 94/95（本批**一开始**就做，批次 213 就是栽在这两件上）：
 *   · **积分**在任何操作之前先读一次（立规 95）
 *   · **全部节点 id 快照**在任何操作之前先存（立规 94），
 *     收尾拿它逐个比对，而不是靠肉眼数
 *
 * ⛔ 不触发任何生成：只走本地文件上传。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 上传文件 = '/tmp/jimeng-b214-probe.mp3';
const 宽集 = [1212, 1210];
const OUT = '/tmp/b214a.json';

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b214a', 上传文件, 宽集 };

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
    画布: t ? [Number(t[1]), Number(t[2])] : null, 屏上: [Math.round(r.width), Math.round(r.height)] };
}));
const 积分 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').startsWith('Credits'));
  return e ? e.getAttribute('aria-label') : null;
});
const 状态行 = (p) => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes, (\d+) edges, (\d+) selected[^\n]*/) || [])[0] || null);
const 变体 = (p, id) => p.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const cands = ['audio-node-compact', 'audio-node-empty', 'audio-node-result',
    'audio-flow-node-surface', 'audio-primary-preview-viewport', 'audio-node-status-icon',
    'audio-node-empty-placeholder', 'text-node-empty-placeholder'];
  const r = n.getBoundingClientRect();
  return { 变体: cands.filter((c) => n.querySelector(`[data-testid="${c}"]`)), 屏上: [Math.round(r.width), Math.round(r.height)] };
}, id);
const 焦点 = (p) => p.evaluate(() => {
  const a = document.activeElement;
  return { tag: a ? a.tagName : null, inCE: !!(a && (a.closest('[contenteditable]') || a.isContentEditable)), isInput: !!(a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA')) };
});

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
const 自建 = [];

try {
  // ============ 步骤 0：任何操作之前，先记积分与 id 基线（立规 94 / 95）============
  const p0 = await ctx.newPage();
  await p0.setViewportSize({ width: 1280, height: H });
  await p0.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p0.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p0.waitForTimeout(5000);
  out.步骤0_前置 = {};
  out.步骤0_前置.积分 = await 积分(p0);
  const 基线 = await 清单(p0);
  out.步骤0_前置.基线数 = 基线.length;
  out.步骤0_前置.基线id = 基线.map((n) => n.id).sort();
  out.步骤0_前置.状态行 = await 状态行(p0);
  log('【前置】节点数 ' + 基线.length + ' ｜ ' + out.步骤0_前置.状态行 + ' ｜ 积分 ' + out.步骤0_前置.积分);
  await p0.close();

  // ============ 步骤 1：新建空音频节点 ============
  const p1 = await ctx.newPage();
  await p1.setViewportSize({ width: 1280, height: H });
  await p1.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p1.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p1.waitForTimeout(5000);
  out.步骤1_新建 = {};
  const 入口 = await p1.evaluate(() => {
    const e = Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '音频');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  });
  out.步骤1_新建.音频入口盒 = 入口;
  if (!入口) throw new Error('面板上找不到「音频」入口');
  // 立规 82：先证归属
  const 归属 = await p1.evaluate(([x, y, w, h]) => {
    const el = document.elementFromPoint(x + w / 2, y + h / 2);
    return el ? { tag: el.tagName, aria: el.getAttribute('aria-label') } : null;
  }, 入口);
  out.步骤1_新建.落点归属 = 归属;
  if (!归属 || 归属.aria !== '音频') throw new Error('「音频」入口落点归属不对：' + JSON.stringify(归属));
  const 建前 = (await 清单(p1)).map((n) => n.id);
  await p1.mouse.click(入口[0] + 入口[2] / 2, 入口[1] + 入口[3] / 2);
  await p1.waitForTimeout(3500);
  const 新增 = (await 清单(p1)).filter((n) => !建前.includes(n.id));
  out.步骤1_新建.新增 = 新增;
  if (新增.length !== 1) throw new Error('新建节点数不是 1：' + JSON.stringify(新增));
  const 空节点id = 新增[0].id;
  自建.push(空节点id);
  out.步骤1_新建.上传前变体 = await 变体(p1, 空节点id);
  out.步骤1_新建.上传前积分 = await 积分(p1);
  log('【新建】' + JSON.stringify(新增[0]) + ' ｜ 上传前变体 ' + JSON.stringify(out.步骤1_新建.上传前变体));

  // ============ 步骤 2：上传 mp3（第 2 个 file input）============
  out.步骤2_上传 = {};
  const files = p1.locator('input[type=file]');
  const nFile = await files.count();
  out.步骤2_上传.fileInput数 = nFile;
  let 目标 = -1;
  for (let i = 0; i < nFile; i++) {
    const acc = await files.nth(i).getAttribute('accept');
    if (acc && /audio\/(mpeg|mp3|wav)|\.mp3/.test(acc)) { 目标 = i; break; }
  }
  out.步骤2_上传.选中第几个 = 目标;
  if (目标 < 0) throw new Error('没有接受音频的 file input');
  await files.nth(目标).setInputFiles(上传文件);
  log('【上传】已投递 ' + 上传文件 + ' 到第 ' + 目标 + ' 个 file input');
  let 上传后变体 = null;
  for (let t = 0; t < 25; t++) {
    await p1.waitForTimeout(2000);
    const now = await 清单(p1);
    const 新出来 = now.filter((n) => !建前.includes(n.id) && n.id !== 空节点id);
    if (新出来.length) {
      for (const nn of 新出来) if (!自建.includes(nn.id)) 自建.push(nn.id);
      上传后变体 = await 变体(p1, 新出来[0].id);
      out.步骤2_上传.新产物 = 新出来;
      break;
    }
  }
  out.步骤2_上传.上传后变体 = 上传后变体;
  out.步骤2_上传.上传后积分 = await 积分(p1);
  out.步骤2_上传.节点数 = (await 清单(p1)).length;
  log('【上传】新产物 ' + JSON.stringify(out.步骤2_上传.新产物) + ' ｜ 变体 ' + JSON.stringify(上传后变体));
  log('【积分】' + out.步骤1_新建.上传前积分 + ' → ' + out.步骤2_上传.上传后积分 + ' ｜ 节点数 ' + out.步骤2_上传.节点数);
  await p1.close();
} catch (e) { out.出错 = e.message; log('🔴 ' + e.message); }

// ============ 步骤 3：50% 档读变体 + 两个宽度取景 ============
const 媒体节点 = (out.步骤2_上传 && out.步骤2_上传.新产物 && out.步骤2_上传.新产物[0] && out.步骤2_上传.新产物[0].id) || null;
out.媒体节点 = 媒体节点;
if (媒体节点) {
  try {
    const pz = await ctx.newPage();
    await pz.setViewportSize({ width: 1280, height: H });
    await pz.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await pz.waitForSelector('.react-flow__node', { timeout: 45000 });
    await pz.waitForTimeout(5000);
    out.变体读数 = {};
    out.变体读数.变体26 = await 变体(pz, 媒体节点);
    await pz.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); const r = e.getBoundingClientRect(); window.__z = [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    const zb = await pz.evaluate(() => window.__z);
    await pz.mouse.click(zb[0], zb[1]);
    await pz.waitForTimeout(1200);
    await pz.fill('[data-testid="canvas-zoom-percent-input"]', '50');
    await pz.keyboard.press('Enter');
    await pz.waitForTimeout(2500);
    out.变体读数.变体50 = await 变体(pz, 媒体节点);
    out.变体读数.缩放aria = await pz.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
    log('【变体】26 档 ' + JSON.stringify(out.变体读数.变体26) + ' ｜ 50 档 ' + JSON.stringify(out.变体读数.变体50));
    await pz.close();
  } catch (e) { out.变体读数 = { 出错: e.message }; log('🔴 变体 ' + e.message); }

  const 词 = (out.步骤2_上传.新产物[0].aria || '').split('node: ')[1] || 'jimeng-b214-probe';
  out.档 = {};
  for (const w of 宽集) {
    const p2 = await ctx.newPage();
    try {
      await p2.setViewportSize({ width: w, height: H });
      await p2.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await p2.waitForSelector('.react-flow__node', { timeout: 45000 });
      await p2.waitForTimeout(4500);
      out.档[w] = { 变体: await 变体(p2, 媒体节点) };
      const 钮 = await p2.evaluate(() => {
        const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
          || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      });
      await p2.mouse.click(钮[0], 钮[1]);
      await p2.waitForTimeout(1500);
      const 有框 = await p2.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        if (!e) return false;
        e.focus(); e.select(); return true;
      });
      if (!有框) throw new Error('找不到搜索输入框');
      await p2.keyboard.press('Backspace');
      await p2.waitForTimeout(200);
      await p2.keyboard.type(词, { delay: 90 });
      await p2.waitForTimeout(2200);
      const 输入回读 = await p2.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        return e ? e.value : null;
      });
      const 行 = await p2.evaluate((nid) => {
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
        await p2.mouse.click(行.点[0], 行.点[1]);
        await p2.waitForTimeout(4000);
        const 采样 = [];
        for (let k = 0; k < 3; k++) {
          采样.push(await p2.evaluate((id) => {
            const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
            const vp = document.querySelector('.react-flow__viewport');
            const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
            const r = n ? n.getBoundingClientRect() : null;
            return { 中心: r ? [Math.round((r.x + r.width / 2) * 1000) / 1000, Math.round((r.y + r.height / 2) * 1000) / 1000] : null,
              屏上: r ? [Math.round(r.width), Math.round(r.height)] : null,
              vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null };
          }, 媒体节点));
          await p2.waitForTimeout(500);
        }
        const ss = [...new Set(采样.map((x) => x.vp && x.vp[2]))];
        out.档[w].末 = 采样[2];
        out.档[w].断言 = { 判据: '3 次采样 scale 相同', 通过: ss.length === 1 };
        log(`${w} 变体 ${JSON.stringify(out.档[w].变体.变体)} → s=${JSON.stringify(ss)} 中心=${JSON.stringify(采样[2].中心)} 屏上=${JSON.stringify(采样[2].屏上)}`);
      }
    } catch (e) { out.档[w] = { 出错: e.message }; log(`${w} 🔴 ${e.message}`); }
    finally { await p2.close(); }
  }
}

// ============ 步骤 4：无条件清理，对照步骤 0 的 id 基线逐个核（立规 94）============
try {
  const p3 = await ctx.newPage();
  await p3.setViewportSize({ width: 1280, height: H });
  await p3.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p3.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p3.waitForTimeout(5000);
  out.清理 = {};
  out.清理.要删 = 自建;
  out.清理.删前数 = (await 清单(p3)).length;
  for (const id of 自建) {
    const 步 = { id };
    const now = await 清单(p3);
    if (!now.some((n) => n.id === id)) { 步.备注 = '已不存在'; out.清理[id] = 步; log('清理 ' + id + ' 已不存在'); continue; }
    const 行 = await p3.evaluate((nid) => {
      const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    }, id.replace(/^node_/, ''));
    if (行) {
      const 钮 = await p3.evaluate(() => {
        const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
          || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      });
      await p3.mouse.click(钮[0], 钮[1]);
      await p3.waitForTimeout(1400);
      await p3.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        if (e) { e.focus(); e.select(); }
      });
      await p3.keyboard.press('Backspace');
      await p3.waitForTimeout(200);
      const 名 = (now.find((n) => n.id === id) || {}).aria || '';
      await p3.keyboard.type((名.split('node: ')[1] || '').trim(), { delay: 90 });
      await p3.waitForTimeout(2200);
      const 行2 = await p3.evaluate((nid) => {
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      }, id.replace(/^node_/, ''));
      if (行2) { await p3.mouse.click(行2[0], 行2[1]); await p3.waitForTimeout(1400); }
      步.行 = 行2 || 行;
    }
    步.选中数 = await p3.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
    步.焦点 = await 焦点(p3);
    const 安全 = !步.焦点.inCE && !步.焦点.isInput && 步.选中数 >= 1;
    步.焦点安全 = 安全;
    if (安全) { await p3.keyboard.press('Backspace'); await p3.waitForTimeout(2500); 步.按了Backspace = true; }
    else {
      await p3.keyboard.press('Escape'); await p3.waitForTimeout(1200);
      const f2 = await 焦点(p3);
      const s2 = await p3.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
      步.逃生后 = { 焦点: f2, 选中数: s2 };
      if (!f2.inCE && !f2.isInput && s2 >= 1) { await p3.keyboard.press('Backspace'); await p3.waitForTimeout(2500); 步.逃生后按了 = true; }
    }
    步.删后仍在 = (await 清单(p3)).some((n) => n.id === id);
    out.清理[id] = 步;
    log('清理 ' + id + ' 选中数=' + 步.选中数 + ' 安全=' + 安全 + ' → 仍在 ' + 步.删后仍在);
  }
  const 末清单 = await 清单(p3);
  const 基线集 = new Set(out.步骤0_前置 ? out.步骤0_前置.基线id : []);
  out.清理.最终数 = 末清单.length;
  out.清理.多出来 = 末清单.filter((n) => !基线集.has(n.id)).map((n) => n.id + ' ' + n.aria);
  out.清理.少了 = (out.步骤0_前置 ? out.步骤0_前置.基线id : []).filter((x) => !末清单.some((n) => n.id === x));
  out.清理.最终状态行 = await 状态行(p3);
  out.清理.最终积分 = await 积分(p3);
  log('【收尾】节点数 ' + out.清理.最终数 + ' ｜ 多 ' + JSON.stringify(out.清理.多出来) + ' ｜ 少 ' + JSON.stringify(out.清理.少了));
  log('【收尾】' + out.清理.最终状态行 + ' ｜ 积分 ' + out.清理.最终积分);
  await p3.close();
} catch (e) { out.清理 = { 出错: e.message }; log('🔴 清理 ' + e.message); }

out.自建清单 = 自建;
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);
