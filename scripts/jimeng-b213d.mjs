/**
 * 批次 213 d 轮：**把一个节点跨族移动**，用一次实验把
 * 「判据 = 节点类型」与「判据 = `50%` 档渲染 `*-node-empty`」彻底分开。
 *
 * 🔴 现状（批次 212 + 213 a/b，共 17 个实测节点）：
 *   中招（`w=1212` 终态 `scale` 掉到 `0.260267`）：9 个 audio + 1 个 video
 *   不中招：3 个 text + 2 个 timeline + 1 个 image + 1 个 external
 *   而「中招集合」**恰好就是** `50%` 档渲染 `*-node-empty` 的那一族（audio 68 + video 1）。
 *   ⚠️ 本画布上这两种说法**完全共变**，靠点现成节点永远分不开。
 *
 * 💡 分开它们只需要**跨族移动一个节点**：让某个 video 节点**有媒体**，
 *   它就从 `video-node-empty` 变成 `video-node-result`（跨出 `-empty` 族），**类型不变**。
 *   · 若它随后**不再中招** ⇒ 判据是「**没有媒体 / `-empty` 渲染**」，不是类型 ✅ 假设成立
 *   · 若它**仍然中招** ⇒ 判据是**类型**，`-empty` 只是共变的旁证 ❌ 假设被否
 *
 * 📌 为何新建而不改 `视频 1`：改现有节点内容比删掉自己建的节点难还原。
 *   节点数 `76 → 77 → 76`，原画布逐字不动。
 * ⚠️ ⛔ 不触发任何生成：只走「本地文件上传」，积分必须全程 `791`。
 * 📌 上一轮 c 轮已确认：节点面板「视频」入口 `40×40@16,277`；页面有两个不可见 file input，
 *   **第 2 个**的 `accept` 含 `video/mp4` ⇒ 用它。
 * 📌 删除走手册既有做法：**选中后按 `Backspace`**（不是 `Delete`），且按之前先过焦点守卫。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 上传文件 = '/tmp/jimeng-b196-probe.mp4';
const 宽集 = [1212, 1210];   // 1212 是中招档，1210 是对照
const OUT = '/tmp/b213d.json';

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b213d', 上传文件, 宽集, 档: {} };

const 节点清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'), 画布: t ? [Number(t[1]), Number(t[2])] : null };
}));
const 积分读 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').startsWith('Credits'));
  return e ? e.getAttribute('aria-label') : null;
});
const 变体读 = (p, id) => p.evaluate((nid) => {
  const n2 = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n2) return null;
  const cands = ['video-node-compact', 'video-node-empty', 'video-node-result',
    'video-flow-node-surface', 'video-primary-preview-viewport'];
  const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n2.style.transform || '');
  const r = n2.getBoundingClientRect();
  return { 变体: cands.filter((c) => n2.querySelector(`[data-testid="${c}"]`)),
    画布: t ? [Number(t[1]), Number(t[2])] : null, 屏上: [Math.round(r.width), Math.round(r.height)] };
}, id);
const 焦点 = (p) => p.evaluate(() => {
  const a = document.activeElement;
  return { tag: a ? a.tagName : null, inCE: !!(a && (a.closest('[contenteditable]') || a.isContentEditable)),
    isInput: !!(a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA')) };
});

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
let 新节点id = null;

try {
  // ============ 步骤 1：新建视频节点 ============
  const p1 = await ctx.newPage();
  await p1.setViewportSize({ width: 1280, height: H });
  await p1.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p1.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p1.waitForTimeout(5000);
  out.步骤1_新建 = {};
  out.步骤1_新建.基线数 = (await 节点清单(p1)).length;
  out.步骤1_新建.积分前 = await 积分读(p1);
  const 基线id = (await 节点清单(p1)).map((n) => n.id);

  const 入口 = await p1.evaluate(() => {
    const e = Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '视频');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  });
  out.步骤1_新建.视频入口盒 = 入口;
  // 立规 82：先证归属
  const 归属 = await p1.evaluate(([x, y, w, h]) => {
    const el = document.elementFromPoint(x + w / 2, y + h / 2);
    return el ? { tag: el.tagName, aria: el.getAttribute('aria-label') } : null;
  }, 入口);
  out.步骤1_新建.落点归属 = 归属;
  if (!归属 || 归属.aria !== '视频') throw new Error('「视频」入口落点归属不对：' + JSON.stringify(归属));
  await p1.mouse.click(入口[0] + 入口[2] / 2, 入口[1] + 入口[3] / 2);
  await p1.waitForTimeout(3500);
  const 新增 = (await 节点清单(p1)).filter((n) => !基线id.includes(n.id));
  out.步骤1_新建.新增 = 新增;
  if (新增.length !== 1) throw new Error('新建节点数不是 1：' + JSON.stringify(新增));
  新节点id = 新增[0].id;
  out.步骤1_新建.上传前变体 = await 变体读(p1, 新节点id);
  log('新建 ' + JSON.stringify(新增[0]) + ' 上传前变体 ' + JSON.stringify(out.步骤1_新建.上传前变体));

  // ============ 步骤 2：上传本地 mp4（第 2 个 file input，accept 含 video/mp4）============
  const files = p1.locator('input[type=file]');
  const nFile = await files.count();
  out.步骤2_上传 = { fileInput数: nFile };
  let 上传到哪个 = -1;
  for (let i = 0; i < nFile; i++) {
    const acc = await files.nth(i).getAttribute('accept');
    if (acc && /video\/mp4|\.mp4/.test(acc)) { 上传到哪个 = i; break; }
  }
  out.步骤2_上传.选中第几个 = 上传到哪个;
  if (上传到哪个 < 0) throw new Error('没有接受 mp4 的 file input');
  await files.nth(上传到哪个).setInputFiles(上传文件);
  log('已投递文件到第 ' + 上传到哪个 + ' 个 file input');
  // 等处理完：轮询变体直到出现 -result 或超时 60s
  let 上传后变体 = null;
  for (let t = 0; t < 30; t++) {
    await p1.waitForTimeout(2000);
    上传后变体 = await 变体读(p1, 新节点id);
    if (上传后变体 && 上传后变体.变体.includes('video-node-result')) break;
  }
  out.步骤2_上传.上传后变体 = 上传后变体;
  out.步骤2_上传.积分后 = await 积分读(p1);
  out.步骤2_上传.节点数 = (await 节点清单(p1)).length;
  log('上传后变体 ' + JSON.stringify(上传后变体));
  log('积分 ' + out.步骤2_上传.积分前 + ' → ' + out.步骤2_上传.积分后 + ' ｜ 节点数 ' + out.步骤2_上传.节点数);
  await p1.close();

  // ============ 步骤 3：在中招档与对照档各取景一次 ============
  const 词 = (新增[0].aria || '').split('node: ')[1] || '视频 2';
  for (const w of 宽集) {
    const p2 = await ctx.newPage();
    try {
      await p2.setViewportSize({ width: w, height: H });
      await p2.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await p2.waitForSelector('.react-flow__node', { timeout: 45000 });
      await p2.waitForTimeout(4500);
      out.档[w] = { 上传后变体: await 变体读(p2, 新节点id) };
      const 搜索钮 = await p2.evaluate(() => {
        const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
          || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      });
      await p2.mouse.click(搜索钮[0], 搜索钮[1]);
      await p2.waitForTimeout(1500);
      const 有输入框 = await p2.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        if (!e) return false;
        e.focus(); e.select(); return true;
      });
      await p2.keyboard.press('Backspace');
      await p2.waitForTimeout(250);
      await p2.keyboard.type(词, { delay: 90 });
      await p2.waitForTimeout(2200);
      const 输入回读 = await p2.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        return e ? e.value : null;
      });
      const tid = 'canvas-search-result-node_' + 新节点id.replace(/^node_/, '');
      const 前置 = await p2.evaluate((t) => {
        const e = document.querySelector(`[data-testid="${t}"]`);
        if (!e) return { 存在: false, 现存: Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).slice(0, 8).map((x) => x.getAttribute('data-testid')) };
        const r = e.getBoundingClientRect();
        return { 存在: true, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
      }, tid);
      out.档[w].输入回读 = 输入回读;
      if (!前置.存在 || 输入回读 !== 词) {
        out.档[w].无效臂 = !前置.存在 ? '目标行不在 ' + JSON.stringify(前置.现存) : '输入没进去';
        log(`${w} ⛔ 无效臂 ${out.档[w].无效臂}`);
      } else {
        await p2.mouse.click(前置.点[0], 前置.点[1]);
        await p2.waitForTimeout(4000);
        const 采样 = [];
        for (let k = 0; k < 3; k++) {
          采样.push(await p2.evaluate((id) => {
            const n2 = document.querySelector(`.react-flow__node[data-id="${id}"]`);
            const vp = document.querySelector('.react-flow__viewport');
            const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
            const r = n2 ? n2.getBoundingClientRect() : null;
            return { 中心: r ? [Math.round((r.x + r.width / 2) * 1000) / 1000, Math.round((r.y + r.height / 2) * 1000) / 1000] : null,
              屏上: r ? [Math.round(r.width), Math.round(r.height)] : null,
              vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null };
          }, 新节点id));
          await p2.waitForTimeout(500);
        }
        const ss = [...new Set(采样.map((x) => x.vp && x.vp[2]))];
        out.档[w].采样 = 采样;
        out.档[w].末 = 采样[2];
        out.档[w].断言 = { 判据: '3 次采样 scale 相同', 通过: ss.length === 1 };
        log(`${w} 变体 ${JSON.stringify(out.档[w].上传后变体.变体)} → s=${JSON.stringify(ss)} 中心=${JSON.stringify(采样[2].中心)} 屏上=${JSON.stringify(采样[2].屏上)}`);
      }
    } catch (e) { out.档[w] = { 出错: e.message }; log(`${w} 🔴 ${e.message}`); }
    finally { await p2.close(); }
  }

  // ============ 步骤 4：删掉自建节点，回到 76 ============
  const p3 = await ctx.newPage();
  await p3.setViewportSize({ width: 1280, height: H });
  await p3.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p3.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p3.waitForTimeout(4500);
  out.步骤4_删除 = {};
  out.步骤4_删除.删前数 = (await 节点清单(p3)).length;
  // 用搜索精确定位并选中，再按 Backspace
  const 搜索钮4 = await p3.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
      || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
    const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  await p3.mouse.click(搜索钮4[0], 搜索钮4[1]);
  await p3.waitForTimeout(1500);
  await p3.evaluate(() => {
    const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
    if (e) { e.focus(); e.select(); }
  });
  await p3.keyboard.press('Backspace');
  await p3.waitForTimeout(200);
  await p3.keyboard.type('视频 2', { delay: 90 });
  await p3.waitForTimeout(2200);
  const 行点 = await p3.evaluate((id) => {
    const e = document.querySelector(`[data-testid="canvas-search-result-node_${id}"]`);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  }, 新节点id.replace(/^node_/, ''));
  out.步骤4_删除.定位点 = 行点;
  if (行点) {
    await p3.mouse.click(行点[0], 行点[1]);
    await p3.waitForTimeout(1500);
  }
  out.步骤4_删除.选中数 = await p3.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
  out.步骤4_删除.焦点 = await 焦点(p3);
  const 焦点安全 = !out.步骤4_删除.焦点.inCE && !out.步骤4_删除.焦点.isInput;
  out.步骤4_删除.焦点安全 = 焦点安全;
  log('删除前 选中数 ' + out.步骤4_删除.选中数 + ' ｜ 焦点 ' + JSON.stringify(out.步骤4_删除.焦点) + ' ｜ 安全 ' + 焦点安全);
  if (out.步骤4_删除.选中数 >= 1 && 焦点安全) {
    await p3.keyboard.press('Backspace');
    await p3.waitForTimeout(2500);
  }
  out.步骤4_删除.删后数 = (await 节点清单(p3)).length;
  out.步骤4_删除.仍在 = (await 节点清单(p3)).some((n) => n.id === 新节点id);
  out.步骤4_删除.积分 = await 积分读(p3);
  log('删除后 节点数 ' + out.步骤4_删除.删后数 + ' ｜ 目标仍在 ' + out.步骤4_删除.仍在 + ' ｜ 积分 ' + out.步骤4_删除.积分);
  await p3.close();
} catch (e) { out.出错 = e.message; log('🔴 ' + e.message); }
finally {
  out.新节点id = 新节点id;
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  log('写入 ' + OUT);
}
process.exit(0);
