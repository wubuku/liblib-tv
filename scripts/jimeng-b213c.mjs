/**
 * 批次 213 c 轮：**只新建一个空视频节点并检查它有没有上传入口**，不上传、不删除之外的动作。
 *
 * 为什么要走到这一步：批次 212/213 建立的「中招 = `50%` 档渲染 `*-node-empty` 的那一族」
 * 目前只是**相关**，因为本画布上 `audio`(68) 与 `video`(1) 恰好就是仅有的两个 `-empty` 族
 * ⇒ 「节点类型」与「`-empty` 族」**完全共变**，靠点现成节点分不开。
 * 要分开，必须**把一个节点跨族移动**：让某个 video/audio 节点**有媒体**，
 * 于是它改渲染 `-result`，再测它还中不中招。
 *
 * 📌 为何**新建**而不改 `视频 1`：改现有节点的内容比删掉一个自己建的节点难还原得多。
 *   新建 ⇒ 节点数 `76 → 77`，测完删掉 ⇒ 回到 `76`，原画布逐字不动。
 *
 * ⚠️ 本轮**不碰生成**：只要看到任何「生成 / 生图 / 生视频」入口就绕开，
 *   积分必须全程停在 `791`。
 *
 * 本轮只读出新节点的 DOM 有哪些入口（file input / 上传按钮 / 生成按钮），为下一轮决定路线。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b213c.json';

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b213c' };

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
const p = await ctx.newPage();

const 基线 = async () => p.evaluate(() => ({
  节点数: document.querySelectorAll('.react-flow__node').length,
  状态行: (() => { const e = document.querySelector('[data-testid="canvas-status-bar"], .canvas-status-bar'); return e ? e.textContent.trim() : null; })(),
  积分: (() => { const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').startsWith('Credits')); return e ? e.getAttribute('aria-label') : null; })(),
}));
const 节点清单 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'), 画布: t ? [Number(t[1]), Number(t[2])] : null };
}));

try {
  await p.setViewportSize({ width: 1280, height: 720 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(5000);
  out.基线 = await 基线();
  out.基线节点id集合 = (await 节点清单()).map((n) => n.id).sort();
  log('基线 节点数 ' + out.基线.节点数 + ' ｜ ' + out.基线.状态行);

  // —— 找节点面板上的「视频」入口 ——
  const 入口 = await p.evaluate(() => {
    const cands = [];
    for (const e of document.querySelectorAll('button,[role=button],[role=menuitem],li')) {
      const txt = (e.innerText || e.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ');
      if (!txt || txt.length > 6) continue;
      if (!/^(视频|音频|文本|图片|时间线|主体|导演台|图片节点)$/.test(txt)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      cands.push({ 文字: txt, testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
        tag: e.tagName, 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
    }
    return cands;
  });
  out.面板入口 = 入口;
  log('面板上的节点入口：' + JSON.stringify(入口));

  const 视频入口 = 入口.find((x) => x.文字 === '视频');
  if (!视频入口) {
    out.结论 = '面板上没找到「视频」入口 —— 需要先展开节点面板';
    log('⛔ ' + out.结论);
  } else {
    // 🔴 立规 82：点之前先证明这个点在入口里
    const 归属 = await p.evaluate(([x, y, w, h]) => {
      const el = document.elementFromPoint(x + w / 2, y + h / 2);
      return el ? { tag: el.tagName, testid: el.getAttribute('data-testid'), aria: el.getAttribute('aria-label'), 文字: (el.innerText || '').trim().slice(0, 10) } : null;
    }, 视频入口.屏上);
    out.入口落点归属 = 归属;
    log('入口落点归属 ' + JSON.stringify(归属));
    if (!归属 || !/视频/.test((归属.文字 || '') + (归属.aria || '') + (归属.testid || ''))) {
      out.结论 = '落点不属于「视频」入口 —— 无效臂，不点';
      log('⛔ ' + out.结论);
    } else {
      await p.mouse.click(视频入口.屏上[0] + 视频入口.屏上[2] / 2, 视频入口.屏上[1] + 视频入口.屏上[3] / 2);
      await p.waitForTimeout(3500);
      out.点后 = await 基线();
      const after = await 节点清单();
      out.新增节点 = after.filter((n) => !out.基线节点id集合.includes(n.id));
      log('点后 节点数 ' + out.点后.节点数 + ' ｜ 新增 ' + JSON.stringify(out.新增节点));

      if (out.新增节点.length === 1) {
        const id = out.新增节点[0].id;
        out.新节点入口 = await p.evaluate((nid) => {
          const n2 = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
          if (!n2) return null;
          const cands = ['video-node-compact', 'video-node-empty', 'video-node-result',
            'video-flow-node-surface', 'video-node-upload', 'video-primary-preview-viewport'];
          const 变体 = cands.filter((c) => n2.querySelector(`[data-testid="${c}"]`));
          const 全页fileInput = Array.from(document.querySelectorAll('input[type=file]')).map((e) => {
            const r = e.getBoundingClientRect();
            return { accept: e.getAttribute('accept'), 可见: r.width > 0 && r.height > 0, 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
          });
          const 节点内testid = Array.from(n2.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')).slice(0, 25);
          const 节点内按钮 = Array.from(n2.querySelectorAll('button,[role=button]')).map((e) => ({
            aria: e.getAttribute('aria-label'), 文字: (e.innerText || '').trim().slice(0, 12), testid: e.getAttribute('data-testid'),
          })).slice(0, 15);
          return { 变体, 节点内testid, 节点内按钮, 全页fileInput };
        }, id);
        log('新节点变体 ' + JSON.stringify(out.新节点入口.变体));
        log('全页 file input ' + JSON.stringify(out.新节点入口.全页fileInput));
        log('新节点内按钮 ' + JSON.stringify(out.新节点入口.节点内按钮));
        out.有上传入口 = out.新节点入口.全页fileInput.length > 0
          || out.新节点入口.节点内按钮.some((b) => /上传|选择|本地|导入/.test((b.aria || '') + (b.文字 || '')));
        out.有生成入口 = out.新节点入口.节点内按钮.some((b) => /生成|生图|生视频/.test((b.aria || '') + (b.文字 || '')));
        log('⇒ 有上传入口 ' + out.有上传入口 + ' ｜ 有生成入口 ' + out.有生成入口 + '（生成入口一律绕开）');
      }
    }
  }
} catch (e) { out.出错 = e.message; log('🔴 ' + e.message); }
finally {
  out.收尾节点数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  log('收尾（新页即将关闭，共享页签未参与）节点数 ' + out.收尾节点数);
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  log('写入 ' + OUT);
  await p.close();
}
process.exit(0);
