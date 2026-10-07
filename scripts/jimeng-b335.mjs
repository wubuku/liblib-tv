#!/usr/bin/env node
/**
 * 批次 335 —— 查两件事：
 *   ① 🔴 那 13 次「放大键」在批次 334 里**没生效**（落点 `0.260267` = 未缩放默认值），
 *      而批次 331/332/333 每臂 `点之前` 都逐字 `2.779` ⇒ 到底哪个按键组合能放大？
 *   ② 🔴🔴 **更重**：在放大态 `2.779` 下，**完全不拖**、只选 `音频 1`，落点是不是就已经是 `1.125`？
 *      若是 ⇒ 🔴 批次 325–333 整条「拖多少才锁」的实验，测的是一个**拖之前就已经成立**的性质。
 *
 * 臂：
 *   `找键`   —— 逐个试按键组合，逐次记录 scale，找出能把画布放大的那个
 *   `大不拖` —— 放大态 + 选 `音频 1` + **不拖** ⇒ 落点 / A / 锁
 *   `大拖120` —— 放大态 + 选 `音频 1` + 拖 `120` ⇒ 复现批次 333 的 P1
 *   `小拖120` —— **不放大** + 选 `音频 1` + 拖 `120` ⇒ 复现批次 334 的对照
 *
 * ⛔ 不点任何生成/购买/保存主体库/分享。
 */
import { chromium } from 'playwright';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const STATE = path.join(os.homedir(), '.jimeng-automation', 'state.json');
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const VW = 1212, VH = 720;

const log = (s) => console.log(s);
const 节 = (x) => (x === undefined || x === null ? null : Math.round(x * 1000000) / 1000000);

const 读缩放 = () => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  return m ? Number(m[1]) : null;
};

const 读画布 = () => {
  const e = document.querySelector('.react-flow__viewport');
  const t = e ? (e.style.transform || '') : '';
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(t);
  return { x: m ? Number(m[1]) : null, y: m ? Number(m[2]) : null };
};

const 找节点 = (aria) => {
  const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
    .find((x) => x.getAttribute('aria-label') === aria);
  return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight, tf: e.style.transform || '' } : null;
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
  const 锁 = A === null ? 'n/a' : (Math.abs(A - 200) < 0.002 ? '锁定' : '未锁');
  return {
    kind, 名, 盒: { W: 找.W, H: 找.H }, 点后首读, 读1, 读2, 读3, 落定, 落点: 读3,
    A, 锁定与否: 锁, 节点画布坐标未变: (后 === 找.tf),
  };
};

// 📌 逐个试按键组合，逐次记 scale —— 立规 217 的反面：不要假设某个键「肯定有效」，要**量**
const 试按键 = async (p) => {
  const 组合表 = [
    { 名: 'Equal', keys: ['Equal'] },
    { 名: 'Meta+Equal', keys: ['Meta', 'Equal'] },
    { 名: 'Control+Equal', keys: ['Control', 'Equal'] },
    { 名: 'Shift+Equal', keys: ['Shift', 'Equal'] },
    { 名: 'NumpadAdd', keys: ['NumpadAdd'] },
    { 名: 'Meta+NumpadAdd', keys: ['Meta', 'NumpadAdd'] },
    { 名: 'Equal 连按两次', keys: ['Equal', 'Equal'] },
    { 名: 'Minus', keys: ['Minus'] },
    { 名: 'Meta+Minus', keys: ['Meta', 'Minus'] },
    { 名: 'NumpadSubtract', keys: ['NumpadSubtract'] },
  ];
  const out = [];
  let 起点 = null;
  for (const c of 组合表) {
    const 前 = await p.evaluate(读缩放);
    if (起点 === null) 起点 = 前;
    for (const k of c.keys) { await p.keyboard.press(k); await p.waitForTimeout(260); }
    await p.waitForTimeout(900);
    const 后 = await p.evaluate(读缩放);
    out.push({ 名: c.名, 前, 后, 变了: (前 !== 后) });
    if (前 === 后) {
      // 📌 组合没生效，把可能残留的修饰键状态清掉再继续
      for (const k of ['Meta', 'Control', 'Shift', 'Alt']) { await p.keyboard.up(k).catch(() => {}); }
      await p.waitForTimeout(200);
    }
  }
  return { 起点, 试过: out };
};

const 找空白 = () => {
  for (let y = 60; y < innerHeight - 60; y += 40) {
    for (let x = 40; x < innerWidth - 40; x += 40) {
      const e = document.elementFromPoint(x, y);
      if (e && !e.closest('.react-flow__node') && !e.closest('[data-testid="canvas-search-panel"]')) return { x, y };
    }
  }
  return null;
};

const 拖一次 = async (p, dx) => {
  const 起点 = await p.evaluate(找空白);
  if (!起点) return { 错: '找不到空白起点' };
  const 终x = Math.max(2, Math.min(起点.x + dx, VW - 2));
  await p.mouse.move(起点.x, 起点.y);
  await p.mouse.down();
  await p.mouse.move(终x, 起点.y, { steps: Math.max(2, Math.round(Math.abs(dx) / 2)) });
  await p.mouse.up();
  await p.waitForTimeout(1400);
  return { 起点, 终x, 真实行程: 终x - 起点.x, 截断量: Math.max(0, 起点.x + dx - (VW - 2)) };
};

const 出报告 = {
  轮次: 335,
  问: '① 批次 334 的 13 次放大键为什么没生效？② 放大态下「不拖」是不是就已经锁了？',
  接334: '批次 334 查到 find空白 首点 = div.react-flow__pane（缺口二排除），但 13 次放大键没生效、落点停在 0.260267',
  判据: {
    P0: '逐个试按键组合、逐次记 scale，找出能把画布放大的那个（不假设「Equal 肯定有效」）',
    P1: '🔴 放大态下选 音频 1、**完全不拖** ⇒ 落点 / A / 锁 —— 若已是 1.125 / 200 / 锁定，则整条「拖多少才锁」实验测的是拖之前就成立的性质',
    P2: '放大态 + 拖 120 ⇒ 复现批次 333 的 P1（1.125 / 200 / 锁定）',
    P3: '不放大 + 拖 120 ⇒ 复现批次 334 的对照（应未锁）',
  },
  臂表: [],
  臂: [],
  判定: {},
  末态: {},
};

const 臂表 = [
  { 键: '找键', 组: 'P0', 放大: false, dx: null },
  { 键: '大不拖', 组: 'P1', 放大: true, dx: null },
  { 键: '大拖120', 组: 'P2', 放大: true, dx: 120 },
  { 键: '小拖120', 组: 'P3', 放大: false, dx: 120 },
];
出报告.臂表 = 臂表.map((a) => a.键 + '（' + a.组 + '｜放大=' + a.放大 + '｜拖=' + a.dx + '）');

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
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      const s = m ? Number(m[1]) : null;
      if (typeof s !== 'number' || !Number.isFinite(s)) return { 错: 'scale 读不到' };
      return { scale: s, 节点数: document.querySelectorAll('.react-flow__node').length };
    });
    if (冒烟.错) throw new Error(冒烟.错);
    log('✅ 启动前自检通过：默认 scale = ' + 冒烟.scale + '、节点数 = ' + 冒烟.节点数);
  } catch (e) {
    log('🔴 启动前自检失败（脚本跑不起来，先修再跑）：' + e.message);
    process.exit(2);
  } finally {
    try { if (brs) await brs.close(); } catch (e) { /* 忽略 */ }
  }
}

for (const 臂 of 臂表) {
  let br = null; let p = null;
  const 记 = { 键: 臂.键, 组: 臂.组, 放大: 臂.放大, 命令dx: 臂.dx, vw: VW, vh: VH };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: VW, height: VH } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);

    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== VW || 实际.h !== VH) throw new Error('轴向自检失败：' + 实际.w + 'x' + 实际.h);

    记.默认scale = await p.evaluate(读缩放);

    if (臂.键 === '找键') {
      const 试 = await 试按键(p);
      记.试按键 = 试;
      log('\n【找键】默认 scale = ' + 试.起点);
      for (const r of 试.试过) {
        log('   ' + (r.变了 ? '✅' : '  ') + ' ' + r.名 + '：' + r.前 + ' ⇒ ' + r.后);
      }
      const 有效 = 试.试过.filter((r) => r.变了);
      记.有效组合 = 有效.map((r) => r.名);
      log('   ⇒ 有效组合 ' + 有效.length + ' 个：' + JSON.stringify(记.有效组合));
      throw new Error('【找键】是探针臂，按设计到此为止（不进入选点流程）');
    }

    if (臂.放大) {
      // 📌 用探针臂找到的组合；此处先用 Meta+Equal，失败再退回到裸 Equal
      const 组合 = [[ 'Meta', 'Equal' ], [ 'Equal' ], [ 'Control', 'Equal' ], [ 'NumpadAdd' ]];
      const 逐次 = [];
      for (let i = 0; i < 13; i++) {
        const 前 = await p.evaluate(读缩放);
        for (const k of 组合) { await p.keyboard.press(k); await p.waitForTimeout(220); }
        await p.waitForTimeout(320);
        const 后 = await p.evaluate(读缩放);
        逐次.push({ 次: i + 1, 前, 后 });
        if (前 === 后) { for (const k of ['Meta', 'Control']) await p.keyboard.up(k).catch(() => {}); }
      }
      记.放大逐次 = 逐次;
      const 末 = 逐次.length ? 逐次[逐次.length - 1].后 : null;
      log('\n【' + 臂.键 + '】放大逐次 scale：' + 逐次.map((r) => r.后).join(' → '));
    }
    await p.waitForTimeout(1600);
    const 点之前 = await p.evaluate(读缩放);
    记.点之前 = 点之前;
    if (点之前 === null) throw new Error('点之前读不到 scale');
    log('   点之前 scale = ' + 点之前);

    if (臂.dx !== null) {
      const 起画布 = await p.evaluate(读画布);
      const 拖 = await 拖一次(p, 臂.dx);
      if (拖.错) throw new Error(拖.错);
      const 末画布 = await p.evaluate(读画布);
      记.拖 = {
        起: 起画布, 末: 末画布,
        行程: 拖,
        净dy: (起画布.y !== null && 末画布.y !== null) ? 节(末画布.y - 起画布.y) : null,
        净dx: (起画布.x !== null && 末画布.x !== null) ? 节(末画布.x - 起画布.x) : null,
      };
      log('   拖 ' + 臂.dx + '：起点 x=' + 拖.起点.x + '、真实行程 ' + 拖.真实行程
        + '、截断 ' + 拖.截断量 + '｜净 Δx=' + 记.拖.净dx + '、净 Δy=' + 记.拖.净dy);
    }

    const 选 = await 选一次(p, '音频', '音频 1', VH);
    记.选择 = 选;
    记.锁 = 选.锁定与否;
    log('   选 `音频 1` ⇒ 落点 ' + 选.读3 + '、A = ' + 选.A + '、落定=' + 选.落定
      + '、节点画布坐标未变=' + 选.节点画布坐标未变 + ' ⇒ ' + 选.锁定与否);

    出报告.臂.push(记);
  } catch (e) {
    记.错 = e.message;
    出报告.臂.push(记);
    if (!String(e.message).startsWith('【找键】')) log('   🔴 臂失败：' + e.message);
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
  const 找键臂 = 出报告.臂.find((a) => a.键 === '找键');
  const 不拖 = 出报告.臂.find((a) => a.键 === '大不拖');
  const 大拖 = 出报告.臂.find((a) => a.键 === '大拖120');
  const 小拖 = 出报告.臂.find((a) => a.键 === '小拖120');
  const J = 出报告.判定;
  J.P0 = 找键臂 && 找键臂.试按键
    ? '📌 P0 逐组合试按：默认 scale ' + 找键臂.试按键.起点 + '；有效组合 ' + JSON.stringify(找键臂.有效组合 || [])
    : '🔴 P0 未取到试按键数据';
  J.P1 = 不拖 && 不拖.选择
    ? '📌 P1 放大态（点之前 ' + 不拖.点之前 + '）+ 选 `音频 1` + **不拖** ⇒ 落点 ' + 不拖.选择.读3
      + '、A = ' + 不拖.选择.A + ' ⇒ **' + 不拖.选择.锁定与否 + '**'
    : '🔴 P1 未取到不拖臂数据';
  J.P2 = 大拖 && 大拖.选择
    ? '📌 P2 放大态（点之前 ' + 大拖.点之前 + '）+ 拖 120（净 Δx=' + (大拖.拖 && 大拖.拖.净dx)
      + '、净 Δy=' + (大拖.拖 && 大拖.拖.净dy) + '）⇒ 落点 ' + 大拖.选择.读3 + '、A = ' + 大拖.选择.A
      + ' ⇒ **' + 大拖.选择.锁定与否 + '**'
    : '🔴 P2 未取到大拖臂数据';
  J.P3 = 小拖 && 小拖.选择
    ? '📌 P3 不放大（点之前 ' + 小拖.点之前 + '）+ 拖 120（净 Δx=' + (小拖.拖 && 小拖.拖.净dx)
      + '、净 Δy=' + (小拖.拖 && 小拖.拖.净dy) + '）⇒ 落点 ' + 小拖.选择.读3 + '、A = ' + 小拖.选择.A
      + ' ⇒ **' + 小拖.选择.锁定与否 + '**'
    : '🔴 P3 未取到小拖臂数据';
  if (不拖 && 不拖.选择 && 大拖 && 大拖.选择) {
    J.判决 = (不拖.选择.锁定与否 === '锁定' && 大拖.选择.锁定与否 === '锁定')
      ? '🔴🔴 **不拖就已经是 `1.125` / `A = 200` / 锁定** ⇒ 批次 325–333 那条「拖多少才锁」的实验线，📌 **测的是一个在拖之前就已经成立的性质**'
      : (不拖.选择.锁定与否 === '未锁' && 大拖.选择.锁定与否 === '锁定')
        ? '✅ **不拖未锁、拖 120 锁定** ⇒ 「拖才锁」成立，📌 但它只在**放大态**下成立'
        : '📌 两者落点/锁态见上，📌 不下判决';
  } else {
    J.判决 = '🔴 臂不全，本批判不下判决';
  }
  J.可比性 = '🔴 **批次 334 的落点停在 `0.260267`（未缩放默认值），📌 而批次 331/332/333 每臂 `点之前` 逐字 `2.779`** '
    + '⇒ 📌 批次 334 与前几批**不可比**；📌 本批把「点之前」逐臂落盘，📌 下批可直接按它对齐';
}

fs.writeFileSync('/tmp/b335.json', JSON.stringify(出报告, null, 1));
log('\n════ 判定 ════');
for (const k of Object.keys(出报告.判定)) log(k + ': ' + 出报告.判定[k]);
log('\n写入 /tmp/b335.json');
process.exit(0);
