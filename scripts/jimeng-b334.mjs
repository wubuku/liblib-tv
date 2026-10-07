#!/usr/bin/env node
/**
 * 批次 334 —— 快探针：先验明探针本身，再谈测量结论。
 *
 * 批次 333 如实记了三条测量缺口，其中**缺口二最重**：
 *   `找空白()` 从 (40,60) 起逐格扫描 `elementFromPoint`，
 *   只排除 `.react-flow__node` 与 `[data-testid="canvas-search-panel"]`，
 *   然后返回**第一个**通过的元素 —— 但**那个元素到底是什么，本批没有记录**。
 *   🔴 若它落在工具条 / 缩放控件 / 小地图 / 顶栏上，
 *      那么批次 325–333 整条「平移实验」测的根本不是平移。
 *
 * 因此本批**不重复 115/116/120**，只回答一个问题：
 *   **P0** 逐格扫描的身份普查 —— 前 N 个「通过」的点分别是什么元素？
 *   **P1** 第一个通过点的完整祖先链 —— 它在 `.react-flow__pane` 里吗？pointer-events 是什么？
 *   **P2** 落一次真拖并全程挂捕获监听 —— 事件打在谁身上？`.react-flow__pane` 的 transform 变了吗？
 *   **P3** 对照 —— 换一个**明确在画布空白处**的点（我自己指定坐标，不靠扫描）再拖一次，
 *        看 Δy 是否同量级 ⇒ 若两者差异巨大，🔴 325–333 的对象就选错了。
 *
 * ⛔ 本批不点任何生成/购买/保存主体库/分享。
 */
import { chromium } from 'playwright';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const STATE = path.join(os.homedir(), '.jimeng-automation', 'state.json');
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 放大键 = process.platform === 'darwin' ? 'Equal' : 'Equal';
const VW = 1212, VH = 720;

const log = (s) => console.log(s);
const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000000) / 1000000);

const 读画布 = () => {
  const e = document.querySelector('.react-flow__viewport');
  const t = e ? (e.style.transform || '') : '';
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(t);
  return { x: m ? Number(m[1]) : null, y: m ? Number(m[2]) : null, tf: t };
};

const 读pane = () => {
  const e = document.querySelector('.react-flow__pane');
  if (!e) return null;
  const cs = getComputedStyle(e);
  const b = e.getBoundingClientRect();
  return { tf: e.style.transform || '', computed: cs.transform, cursor: cs.cursor, pointerEvents: cs.pointerEvents,
           盒: { x: Math.round(b.x), y: Math.round(b.y), W: Math.round(b.width), H: Math.round(b.height) } };
};

const 找节点 = (aria) => {
  const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
    .find((x) => x.getAttribute('aria-label') === aria);
  return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight, tf: e.style.transform || '' } : null;
};

const 读缩放 = () => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  return m ? Number(m[1]) : null;
};

const 备好结果行 = async (p, 词表, 目标id) => {
  const 面板已开 = await p.evaluate(() => !!document.querySelector('[data-testid="canvas-search-panel"] input'));
  if (!面板已开) {
    const 钮 = await p.evaluate(() => {
      const b = document.querySelector('button[aria-label="搜索"]');
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return { 中心: [r.x + r.width / 2, r.y + r.height / 2], 可见: r.width > 0 && r.y >= 0 && r.bottom <= innerHeight };
    });
    if (!钮 || !钮.可见) return { 错: '找不到可见的搜索钮' };
    await p.mouse.click(钮.中心[0], 钮.中心[1]);
    await p.waitForTimeout(1600);
  }
  for (const 词 of 词表) {
    const 有输入框 = await p.evaluate(() => {
      const i = document.querySelector('[data-testid="canvas-search-panel"] input');
      if (!i) return false;
      i.focus(); i.select();
      return true;
    });
    if (!有输入框) return { 错: '搜索面板没有输入框' };
    await p.keyboard.type(词, { delay: 80 });
    await p.waitForTimeout(2000);
    const sel = '[data-testid="canvas-search-result-node_' + String(目标id).replace(/^node_/, '') + '"]';
    let r = await p.evaluate((s) => {
      const e = document.querySelector(s);
      if (!e) return null;
      e.scrollIntoView({ block: 'center' });
      const b = e.getBoundingClientRect();
      return { 中心: [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)], 可见: b.width > 0 && b.y >= 0 && b.bottom <= innerHeight && b.x >= 0 && b.right <= innerWidth };
    }, sel);
    if (r && !r.可见) {
      await p.waitForTimeout(600);
      r = await p.evaluate((s) => { const e = document.querySelector(s); const b = e.getBoundingClientRect(); return { 中心: [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)], 可见: b.width > 0 && b.y >= 0 && b.bottom <= innerHeight && b.x >= 0 && b.right <= innerWidth }; }, sel);
    }
    if (r && r.可见) return { 中心: r.中心 };
  }
  return { 错: '搜不到可见结果行' };
};

const 选一次 = async (p, kind, 名, vh) => {
  const ariaWant = kind + ' node: ' + 名;
  const 找 = await p.evaluate(找节点, ariaWant);
  if (!找) throw new Error('找不到 aria 为「' + ariaWant + '」的节点');
  const r = await 备好结果行(p, [名, ariaWant, kind], 找.id);
  if (r.错) throw new Error(r.错);
  await p.mouse.click(r.中心[0], r.中心[1]);
  const 点后首读 = await p.evaluate(读缩放);
  await p.waitForTimeout(3200);
  const 读1 = await p.evaluate(读缩放);
  await p.waitForTimeout(2600);
  const 读2 = await p.evaluate(读缩放);
  await p.waitForTimeout(2000);
  const 读3 = await p.evaluate(读缩放);
  const 选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id));
  if (!选.includes(找.id)) throw new Error('点击未生效（选中=' + JSON.stringify(选) + '）');
  const 后 = await p.evaluate((id) => {
    const e = document.querySelector('.react-flow__node[data-id="' + id + '"]');
    return e ? e.style.transform || '' : null;
  }, 找.id);
  const 落定 = (读1 === 读2 && 读2 === 读3);
  const A = 读3 === null ? null : 节((vh - 160) - 找.H * 读3);
  return {
    kind, 名, 盒: { W: 找.W, H: 找.H }, 点后首读, 读1, 读2, 读3, 落定, 落点: 读3,
    A, 节点画布坐标未变: (后 === 找.tf),
  };
};

const 装监听 = async (p) => {
  await p.evaluate(() => {
    window.__事 = [];
    const 记 = (名) => (ev) => {
      if (window.__事.length > 400) return;
      const t = ev.target;
      const cls = (t.getAttribute && t.getAttribute('class')) || '';
      window.__事.push({
        事件: 名,
        x: Math.round(ev.clientX), y: Math.round(ev.clientY),
        target: t.tagName ? t.tagName.toLowerCase() : '?',
        targetCls: cls.length > 60 ? cls.slice(0, 60) + '…' : cls,
        targetTestid: (t.getAttribute && t.getAttribute('data-testid')) || null,
        按钮: ev.button === undefined ? null : ev.button,
      });
    };
    for (const n of ['pointerdown', 'mousedown', 'pointermove', 'mousemove', 'pointerup', 'mouseup', 'click', 'wheel']) {
      window.addEventListener(n, 记(n), true);
    }
    // 📌 盯住 pane / viewport 的 style 变化
    window.__变 = [];
    const mo = new MutationObserver((recs) => {
      for (const r of recs) {
        const el = r.target;
        const cls = (el.getAttribute && el.getAttribute('class')) || '';
        if (window.__变.length < 200) {
          window.__变.push({ tag: el.tagName ? el.tagName.toLowerCase() : '?', cls: cls.slice(0, 60), 值: (el.getAttribute('style') || '').slice(0, 120) });
        }
      }
    });
    for (const sel of ['.react-flow__pane', '.react-flow__viewport', '.react-flow__renderer']) {
      const el = document.querySelector(sel);
      if (el) mo.observe(el, { attributes: true, attributeFilter: ['style', 'class'] });
    }
    window.__mo = mo;
  });
};

const 取监听 = async (p) => p.evaluate(() => {
  const 事 = window.__事 || [];
  const 计数 = {};
  for (const e of 事) {
    const k = e.事件 + ' -> ' + e.target + (e.targetTestid ? '[' + e.targetTestid + ']' : '');
    计数[k] = (计数[k] || 0) + 1;
  }
  const 变 = (window.__变 || []).slice(0, 12);
  return { 事件总数: 事.length, 前几件: 事.slice(0, 8), 末几件: 事.slice(-6), 按目标计数: 计数, style变动样本: 变 };
});

const 出报告 = {
  轮次: 334,
  问: '找空白() 抓到的到底是什么元素？我这九批到底在拖什么？',
  接333: '批次 333 缺口二：只排除 node 与搜索面板，抓到的元素身份没记录',
  判据: {
    P0: '逐格扫描 elementFromPoint 的身份普查：前 N 个「通过」的点分别是什么',
    P1: '第一个通过点的完整祖先链 + 是否在 .react-flow__pane 内 + pointer-events',
    P2: '落一次真拖并全程捕获监听：事件打在谁身上、pane/viewport 的 style 变没变',
    P3: '换一个我**自己指定**的画布空白坐标再拖一次，看 Δy 是否同量级',
  },
  臂表: [],
  臂: [],
  判定: {},
  末态: {},
};

const 臂表 = [
  { 键: '查元素', 组: 'P0/P1/P2', 模式: '普查加监听拖', dx: 120 },
  { 键: '定点拖', 组: 'P3', 模式: '定点', 定点: null, dx: 120 },
];
出报告.臂表 = 臂表.map((a) => a.键 + '（' + a.组 + '｜dx=' + a.dx + '）');

// 扫描逻辑放进页面上下文
const 普查 = () => {
  const 通过 = [];
  const 全格 = [];
  let 总格 = 0, 被节点挡 = 0, 被面板挡 = 0;
  for (let y = 60; y < innerHeight - 60; y += 40) {
    for (let x = 40; x < innerWidth - 40; x += 40) {
      总格++;
      const e = document.elementFromPoint(x, y);
      if (!e) continue;
      const 在节点 = !!e.closest('.react-flow__node');
      const 在面板 = !!e.closest('[data-testid="canvas-search-panel"]');
      if (在节点) { 被节点挡++; continue; }
      if (在面板) { 被面板挡++; continue; }
      const cls = e.getAttribute('class') || '';
      const rec = {
        x, y,
        tag: e.tagName.toLowerCase(),
        cls: cls.length > 70 ? cls.slice(0, 70) + '…' : cls,
        testid: e.getAttribute('data-testid') || null,
        在pane里: !!e.closest('.react-flow__pane'),
        在renderer里: !!e.closest('.react-flow__renderer'),
        在viewport里: !!e.closest('.react-flow__viewport'),
        pointerEvents: getComputedStyle(e).pointerEvents,
        cursor: getComputedStyle(e).cursor,
      };
      通过.push(rec);
      if (全格.length < 40) 全格.push(rec);
    }
  }
  return { 总格, 被节点挡, 被面板挡, 通过数: 通过.length, 通过: 通过.slice(0, 14), 首: 通过[0] || null };
};

const 详查 = (arg) => {
  const px = arg.x; const py = arg.y;
  const e = document.elementFromPoint(px, py);
  if (!e) return { 错: '该点没有元素' };
  const cls = e.getAttribute('class') || '';
  const 链 = [];
  let c = e;
  for (let i = 0; i < 9 && c; i++) {
    const cc = c.getAttribute ? (c.getAttribute('class') || '') : '';
    链.push({
      级: i,
      tag: c.tagName ? c.tagName.toLowerCase() : '?',
      cls: cc.length > 80 ? cc.slice(0, 80) + '…' : cc,
      testid: c.getAttribute ? c.getAttribute('data-testid') : null,
      role: c.getAttribute ? c.getAttribute('role') : null,
    });
    c = c.parentElement;
  }
  return {
    点: { x: px, y: py },
    本体: {
      tag: e.tagName.toLowerCase(),
      cls: cls.length > 110 ? cls.slice(0, 110) + '…' : cls,
      testid: e.getAttribute('data-testid') || null,
      aria: e.getAttribute('aria-label') || null,
      role: e.getAttribute('role') || null,
      text: (e.textContent || '').trim().slice(0, 60),
      pointerEvents: getComputedStyle(e).pointerEvents,
      cursor: getComputedStyle(e).cursor,
    },
    在pane里: !!e.closest('.react-flow__pane'),
    在renderer里: !!e.closest('.react-flow__renderer'),
    在viewport里: !!e.closest('.react-flow__viewport'),
    在节点里: !!e.closest('.react-flow__node'),
    祖先链: 链,
  };
};

// ───────── 启动前自检 ─────────
{
  let brs = null;
  try {
    brs = await chromium.launch({ headless: true });
    const cs2 = await brs.newContext({ storageState: STATE, viewport: { width: VW, height: VH } });
    const ps = await cs2.newPage();
    await ps.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await ps.waitForSelector('.react-flow__node[data-id]', { timeout: 60000 });
    await ps.waitForTimeout(4000);
    const 冒烟 = await ps.evaluate(() => {
      const e = document.elementFromPoint(40, 60);
      if (!e) return { 错: '(40,60) 没有元素' };
      return { tag: e.tagName.toLowerCase(), cls: (e.getAttribute('class') || '').slice(0, 50) };
    });
    if (冒烟.错) throw new Error(冒烟.错);
    log('✅ 启动前自检通过：(40,60) 上有元素 —— `' + 冒烟.tag + '` / `' + 冒烟.cls + '`');
  } catch (e) {
    log('🔴 启动前自检失败（脚本跑不起来，先修再跑）：' + e.message);
    process.exit(2);
  } finally {
    try { if (brs) await brs.close(); } catch (e) { /* 忽略 */ }
  }
}

for (const 臂 of 臂表) {
  let br = null; let p = null;
  const 记 = { 键: 臂.键, 组: 臂.组, 模式: 臂.模式, vw: VW, vh: VH, 命令dx: 臂.dx };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: VW, height: VH } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);

    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== VW || 实际.h !== VH) throw new Error('轴向自检失败：' + 实际.w + 'x' + 实际.h);

    for (let i = 0; i < 13; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1600);

    // ── P0/P1：普查 + 详查第一个通过点 ──
    const 普 = await p.evaluate(普查);
    记.普查 = 普;
    log('\n【' + 臂.键 + '】普查：总格 ' + 普.总格 + '｜被节点挡 ' + 普.被节点挡
      + '｜被面板挡 ' + 普.被面板挡 + '｜通过 ' + 普.通过数);
    if (!普.首) throw new Error('扫描一个通过点都没有');
    log('   首点 = (' + 普.首.x + ', ' + 普.首.y + ') → ' + 普.首.tag + ' / cls=`' + 普.首.cls
      + '` / testid=' + 普.首.testid + ' / 在pane里=' + 普.首.在pane里
      + ' / pointerEvents=' + 普.首.pointerEvents + ' / cursor=' + 普.首.cursor);
    for (const q of 普.通过.slice(0, 8)) {
      log('     (' + q.x + ',' + q.y + ') ' + q.tag + ' pane=' + q.在pane里 + ' cls=`' + q.cls + '`');
    }
    记.首点详查 = await p.evaluate(详查, { x: 普.首.x, y: 普.首.y });
    log('   祖先链：' + 记.首点详查.祖先链.map((c) => c.tag + (c.cls ? '[' + c.cls + ']' : '')).join(' ← '));

    // ── 选一个节点，走与批次 333 完全相同的落定流程 ──
    const 选 = await 选一次(p, '音频', '音频 1', VH);
    记.选择 = 选;
    log('   选 `音频 1` ⇒ 落点 ' + 选.读3 + '、A = ' + 选.A + '、落定=' + 选.落定
      + '、节点画布坐标未变=' + 选.节点画布坐标未变);

    // ── 选起点 ──
    let 起点 = { x: 普.首.x, y: 普.首.y };
    let 起点来源 = '扫描首点';
    if (臂.模式 === '定点') {
      // 📌 自己指定一个「明显在画布空白处」的坐标：取视口正中，且该点必须在 pane 内且不在节点里
      const 好 = await p.evaluate(() => {
        for (let y = Math.round(innerHeight * 0.5); y < innerHeight - 80; y += 20) {
          for (let x = Math.round(innerWidth * 0.5); x < innerWidth - 80; x += 20) {
            const e = document.elementFromPoint(x, y);
            if (!e) continue;
            if (e.closest('.react-flow__node')) continue;
            if (e.closest('[data-testid="canvas-search-panel"]')) continue;
            const inPane = !!e.closest('.react-flow__pane');
            const cls = e.getAttribute('class') || '';
            return { x, y, inPane, tag: e.tagName.toLowerCase(), cls: cls.slice(0, 70) };
          }
        }
        return null;
      });
      if (!好) throw new Error('视口中找不到空白点');
      起点 = { x: 好.x, y: 好.y };
      起点来源 = '视口正中带（自定）';
      记.自定点 = 好;
      log('   自定点 = (' + 好.x + ', ' + 好.y + ') → ' + 好.tag + ' / cls=`' + 好.cls + '` / 在pane里=' + 好.inPane);
    }
    记.起点 = 起点;
    记.起点来源 = 起点来源;
    记.起点处元素 = await p.evaluate(详查, { x: 起点.x, y: 起点.y });

    // ── P2：带捕获监听拖一次 ──
    const 拖前画布 = await p.evaluate(读画布);
    const 拖前pane = await p.evaluate(读pane);
    await 装监听(p);
    const 终x = Math.max(2, Math.min(起点.x + 臂.dx, VW - 2));
    const 行程 = 终x - 起点.x;
    const 截断 = Math.max(0, 起点.x + 臂.dx - (VW - 2));
    const 步数 = Math.max(2, Math.round(Math.abs(臂.dx) / 2));
    记.行程 = { 起点x: 起点.x, 起点y: 起点.y, 终x, 真实行程: 行程, 截断量: 截断, 步数 };
    log('   行程：起点 x=' + 起点.x + ' ⇒ 终x=' + 终x + '｜真实行程 ' + 行程 + '｜截断 ' + 截断 + '｜步数 ' + 步数);

    await p.mouse.move(起点.x, 起点.y);
    await p.waitForTimeout(200);
    await p.mouse.down();
    await p.waitForTimeout(200);
    await p.mouse.move(终x, 起点.y, { steps: 步数 });
    await p.waitForTimeout(300);
    await p.mouse.up();
    await p.waitForTimeout(1600);

    const 拖后画布 = await p.evaluate(读画布);
    const 拖后pane = await p.evaluate(读pane);
    const 听 = await 取监听(p);
    记.拖 = {
      起: 拖前画布, 末: 拖后画布,
      净dy: (拖前画布.y !== null && 拖后画布.y !== null) ? 节(拖后画布.y - 拖前画布.y) : null,
      净dx: (拖前画布.x !== null && 拖后画布.x !== null) ? 节(拖后画布.x - 拖前画布.x) : null,
      pane前: 拖前pane, pane后: 拖后pane,
      监听: 听,
    };
    log('   拖动：净 Δx=' + 记.拖.净dx + '、净 Δy=' + 记.拖.净dy);
    log('   pane transform：前 `' + (拖前pane ? 拖前pane.tf : 'null') + '` ⇒ 后 `' + (拖后pane ? 拖后pane.tf : 'null') + '`');
    log('   事件总数 ' + 听.事件总数 + '｜按目标：' + JSON.stringify(听.按目标计数));
    if (听.前几件 && 听.前几件.length) {
      const f = 听.前几件[0];
      log('   首个事件：' + f.事件 + ' 打在 ' + f.target + '（testid=' + f.targetTestid + '）');
    }
    log('   viewport style 变动样本数 ' + (听.style变动样本 || []).length);

    // ── 拖完再走一次落定，看锁不锁 ──
    const 选2 = await 选一次(p, '音频', '音频 1', VH);
    记.拖后落定 = 选2;
    log('   拖后再选 `音频 1` ⇒ 落点 ' + 选2.读3 + '、A = ' + 选2.A + '、落定=' + 选2.落定);
    记.锁 = (选2.A !== null && Math.abs(选2.A - 200) < 0.002) ? '锁定' : '未锁';
    log('   ⇒ ' + 记.锁);

    出报告.臂.push(记);
  } catch (e) {
    记.错 = e.message;
    出报告.臂.push(记);
    log('   🔴 臂失败：' + e.message);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
  }
}

// ───────── 末态独立复查 ─────────
{
  let br = null; let p = null;
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: VW, height: VH } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);
    const 末 = await p.evaluate(() => {
      const 行 = document.body.innerText.split('\n').filter((s) => /nodes?, .*edges?/.test(s));
      return {
        节点数: document.querySelectorAll('.react-flow__node').length,
        状态行: 行[0] || null,
        积分: (document.body.innerText.match(/\d+\s*基础会员/) || [null])[0],
      };
    });
    出报告.末态 = 末;
    log('\n末态独立复查：' + JSON.stringify(末));
  } catch (e) {
    出报告.末态 = { 错: e.message };
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
  }
}

// ───────── 判定 ─────────
{
  const 甲 = 出报告.臂.find((a) => a.键 === '查元素');
  const 乙 = 出报告.臂.find((a) => a.键 === '定点拖');
  const J = 出报告.判定;
  J.P0 = 甲 && 甲.普查
    ? '📌 P0 普查：' + 甲.普查.总格 + ' 格里被节点挡 ' + 甲.普查.被节点挡 + '、被搜索面板挡 ' + 甲.普查.被面板挡
      + '，剩下 ' + 甲.普查.通过数 + ' 格「通过」⇒ 扫描器的排除条件**只挡了两类**'
    : '🔴 P0 未取到普查数据';
  J.P1 = 甲 && 甲.首点详查 && !甲.首点详查.错
    ? '📌 P1 首点 (' + 甲.首点详查.点.x + ',' + 甲.首点详查.点.y + ') 本体 = `' + 甲.首点详查.本体.tag
      + '` / cls=`' + 甲.首点详查.本体.cls + '` / 在 pane 里 = ' + 甲.首点详查.在pane里
      + ' / pointerEvents = ' + 甲.首点详查.本体.pointerEvents
    : '🔴 P1 未取到首点详查';
  J.P2 = 甲 && 甲.拖
    ? '📌 P2 捕获监听：事件共 ' + 甲.拖.监听.事件总数 + ' 件、按目标计数 ' + JSON.stringify(甲.拖.监听.按目标计数)
      + '；净 Δx = ' + 甲.拖.净dx + '、净 Δy = ' + 甲.拖.净dy
    : '🔴 P2 未取到监听数据';
  J.P3 = (甲 && 乙 && 甲.拖 && 乙.拖)
    ? '📌 P3 两种起点对拖：扫描首点净 Δy = ' + 甲.拖.净dy + ' vs 视口正中带净 Δy = ' + 乙.拖.净dy
      + ' ⇒ ' + (Math.abs((甲.拖.净dy || 0) - (乙.拖.净dy || 0)) < 2 ? '📌 **同量级** ⇒ 起点位置不改变量级' : '🔴 **量级不同** ⇒ 拖的东西可能不是同一个')
    : '🔴 P3 缺臂';
  J.结论 = (甲 && 甲.首点详查 && !甲.首点详查.错)
    ? (甲.首点详查.在pane里
        ? '✅ 首点在 `.react-flow__pane` 内 ⇒ 325–333 测的**确实是画布平移**'
        : '🔴 首点**不在** `.react-flow__pane` 内 ⇒ 325–333 拖的**不是画布平移**')
    : '🔴 拿不到首点身份，本批判不下结论';
}

fs.writeFileSync('/tmp/b334.json', JSON.stringify(出报告, null, 1));
log('\n════ 判定 ════');
for (const k of Object.keys(出报告.判定)) log(k + ': ' + 出报告.判定[k]);
log('\n写入 /tmp/b334.json');
process.exit(0);
