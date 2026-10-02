// 批次 106 · a 轮：**抓手态下 dock 的其它按钮还能不能点**。
//
// 🎯 `navigate-canvas.md:366` 挂着本页唯一一条「未验证」：
//   「抓手态下 dock 的其它按钮还能不能点」—— 并注明「本轮有一版脚本本想测这条，
//     但因格子串扰那几格实际跑在选择工具态，**不作数、故不写结论**」。
//   ⇒ 这条不是「做不了」，是**上一次的实验设计错了**。本轮把工具态做成**每格强制前置**。
//
// 设计要点（对着上一轮的错法改）：
//   · 每格开头都**重新读一次工具态**，不是靠继承上一格；
//   · 读到与本格要求不符 ⇒ **记「串扰」并跳过该格**，绝不拿串扰数据写结论。
//
// dock 真身（批次 99/103 两次独立测得，4 个后代按钮）：
//   canvas-pointer-tool-toggle / canvas-display-toggle-minimap
//   canvas-display-toggle-connections / canvas-zoom-percent
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
const DOCK = '[data-testid="canvas-navigation-dock"]';

const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

// ---- 工具态：aria 就是当前模式（dock 最左那颗钮的 aria-label） ----
const tool = () => safeEval((sel) => {
  const t = document.querySelector(`${sel} [data-testid="canvas-pointer-tool-toggle"]`);
  return t ? t.getAttribute('aria-label') : null;
}, DOCK);
const zoom = () => safeEval((sel) => {
  const t = document.querySelector(`${sel} [data-testid="canvas-zoom-percent"]`);
  return t ? t.getAttribute('aria-label') : null;
}, DOCK);

// ---- dock 全量读数：4 个按钮的 aria + 尺寸 + 关键状态 ----
const dockRead = async (tag) => {
  const r = await safeEval((sel) => {
    const d = document.querySelector(sel);
    if (!d) return { __err: 'dock-null' };
    const btns = Array.from(d.querySelectorAll('button,[role=button]')).map((e) => {
      const q = e.getBoundingClientRect();
      return { tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
        x: Math.round(q.x), y: Math.round(q.y), w: Math.round(q.width), h: Math.round(q.height),
        pressed: e.getAttribute('aria-pressed'), disabled: e.getAttribute('aria-disabled') };
    });
    // 附属面板：小地图 / 连线可见性都在 dock 之外，所以单列
    const mini = document.querySelector('[data-testid="canvas-minimap-portal-target"]');
    const miniVisible = mini ? (mini.getBoundingClientRect().width > 0 && getComputedStyle(mini).visibility !== 'hidden') : null;
    const edges = Array.from(document.querySelectorAll('.react-flow__edge')).length;
    const t = document.body.innerText;
    return { btns, n: btns.length, miniVisible, edges,
      status: (t.match(/(\d+) nodes?/) || [])[1] + ' nodes, ' + (t.match(/(\d+) edges?/) || [])[1] + ' edges, ' + (t.match(/(\d+) selected/) || [])[1] + ' selected' };
  }, DOCK);
  out[tag] = r;
  log(`\n──── ${tag} ────`);
  log('  dock 按钮数：', r.n);
  for (const x of r.btns) log('   ·', JSON.stringify(x));
  log('  小地图可见：', r.miniVisible, '｜ .react-flow__edge 数：', r.edges, '｜', r.status);
  return r;
};

out.start = { tool: await tool(), zoom: await zoom() };
log('起点：', JSON.stringify(out.start));
const base = await dockRead('0-起点');

// ---- 切到抓手态 ----
const tg = base.btns.find((x) => x.tid === 'canvas-pointer-tool-toggle');
log('\n>>> 切到抓手态（点', tg.x + ',' + tg.y, '）');
await p.mouse.move(tg.x + tg.w / 2, tg.y + tg.h / 2); await p.waitForTimeout(400);
await p.mouse.click(tg.x + tg.w / 2, tg.y + tg.h / 2);
await p.waitForTimeout(1200);
out.toolAfterToggle = await tool();
log('切换后工具态 =', out.toolAfterToggle);
const isPan = /抓手/.test(out.toolAfterToggle || '');
if (!isPan) { log('🔴 没进抓手态，脚本不继续（不拿错状态的读数写结论）'); writeFileSync(new URL('./_tmp-b106a.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }

const pan = await dockRead('1-抓手态-点之前');

// ---- 抓手态下逐个点其余三个按钮 ----
const trials = [
  { tid: 'canvas-display-toggle-minimap', name: '小地图' },
  { tid: 'canvas-display-toggle-connections', name: '显示连线' },
  { tid: 'canvas-zoom-percent', name: '缩放值按钮' },
];
out.trials = [];
for (const t of trials) {
  // 🔴 每格都重新确认工具态（上一轮就栽在这）
  const now = await tool();
  if (now !== out.toolAfterToggle) { log(`\n>>> ${t.name}：🔴 工具态串扰（${now} ≠ ${out.toolAfterToggle}），跳过`); out.trials.push({ ...t, skipped: 'tool-crosstalk', now }); continue; }
  const btn = (await dockRead('_tmp_' + t.tid)).btns.find((x) => x.tid === t.tid);
  if (!btn) { log(`\n>>> ${t.name}：🔴 找不到按钮`); out.trials.push({ ...t, skipped: 'not-found' }); continue; }
  const before = { mini: pan.miniVisible, edges: pan.edges, zoom: await zoom() };
  log(`\n>>> 抓手态下点「${t.name}」（${btn.x},${btn.y}）｜ 点前：`, JSON.stringify(before));
  await p.mouse.move(btn.x + btn.w / 2, btn.y + btn.h / 2); await p.waitForTimeout(450);
  await p.mouse.click(btn.x + btn.w / 2, btn.y + btn.h / 2);
  await p.waitForTimeout(1400);
  const after = await dockRead('t_' + t.tid);
  const now2 = await tool();
  const rec = { ...t, btn, before, after: { mini: after.miniVisible, edges: after.edges, zoom: after.zoom, status: after.status },
    toolBefore: now, toolAfter: now2,
    // 响应判据必须逐项写死，不能靠「看起来变了」
    resp: t.tid === 'canvas-display-toggle-minimap' ? (String(after.miniVisible) !== String(before.mini))
        : t.tid === 'canvas-display-toggle-connections' ? (after.edges !== before.edges)
        : (String(after.zoom) !== String(before.zoom)) };
  out.trials.push(rec);
  log('   点后：', JSON.stringify(rec.after), '｜ 工具态', now2, '｜ 响应 =', rec.resp ? '✅' : '🔴 无变化');
  // 缩放菜单如果被打开了，先关掉，别挡下一格
  const menuOpen = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('div,ul,section')).find((x) => {
      const q = x.getBoundingClientRect(); const tt = x.innerText || '';
      return q.x < 260 && q.y > 540 && q.width > 150 && q.height > 120 && getComputedStyle(x).visibility !== 'hidden' && /缩放至200%/.test(tt); });
    return !!e;
  });
  if (menuOpen) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); log('   （缩放菜单已用 Esc 关掉）'); }
}

out.end = { tool: await tool(), zoom: await zoom() };
log('\n终点：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b106a.json', import.meta.url), JSON.stringify(out, null, 1));
log('已落盘');
await b.close();
