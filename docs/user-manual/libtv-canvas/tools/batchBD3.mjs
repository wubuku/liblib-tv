// Batch BD3 —— BD2 挖出两件必须分清「产品行为」还是「我没点中」的事，外加补上蓝点。
//
// BD2 的结果：
//   · 网格吸附：进场是「关」，点 1 下变「开」，**再点 8 下纹丝不动**，重试 5 次仍是开。
//   · `H` 键：按一次进抓手，**再按一次不回来**；按 `V` 能回来。
//
// 「点了没反应」有两种完全不同的成因，手册里必须分开写：
//   (a) 产品就是这样（点了真的没反应）；
//   (b) 落点不归我（我其实点在了别的东西上）。
// 所以 BD3 的核心是**对照实验** —— 拿同一组里**别的开关**做对照：
//
//   1. `隐藏节点连线` / `切换小地图` / `网格吸附` 三枚**挨在一起、同一套代码**。
//      如果前两枚能来回切、第三枚不能 → 是「网格吸附」自己的行为，不是我的点击方式。
//      三枚的**当前态判据必须统一**（BD1 教训：用 regex alternation 会抓到 DOM 里更靠前的邻居）。
//   2. 同一枚按钮换**三种触发方式**各点一次：坐标 mouse.click / DOM el.click() /
//      手动派发 mousedown+mouseup+click 全序列。三种都无效 → 排除「点不中」。
//   3. `H` 单向：再验一轮，并补测「点按钮本身」和「`Shift`+`H`」。
//   4. 蓝点 tooltip：用**正确路径**打开预设面板（选中图片节点 → 点参数条 `预设`），
//      这是 BA1 的老路数，BD1/BD2 用 `Tab` 找「预设工作流」入口根本没那个东西。
//
// ⚠️ 只读或可复原：不动生成、不上传、不创建。开关点完**必须复原**
//    （网格吸附如果真的关不掉，BD3 会把这个「关不掉」当成正式结论记进手册）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBD3';
const { browser, page } = await launch();

/** 底栏按钮的坐标（aria **全等**匹配）。 */
async function btn(pg, aria) {
  return pg.evaluate((name) => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => x.getAttribute('aria-label') === name);
    if (!e) return { err: '没找到 ' + name };
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }, aria);
}

/** 三枚开关的当前态：背景色 + 透明度 + class + aria 全读。
 *  ⚠️ 判据**三枚共用**（BD1 踩过：regex alternation 会抓到更靠前的 `切换小地图`）。 */
const state3 = (pg) => pg.evaluate(() => {
  const names = ['切换小地图', '隐藏节点连线', '网格吸附'];
  const out = {};
  for (const n of names) {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => x.getAttribute('aria-label') === n);
    if (!e) { out[n] = { err: 'not found' }; continue; }
    const cs = getComputedStyle(e);
    out[n] = { bg: cs.backgroundColor, color: cs.color, opacity: cs.opacity,
      cls: (e.className || '').toString(), ariaPressed: e.getAttribute('aria-pressed') };
  }
  return out;
});

/** 「开着」= 背景不是透明的（`rgba(0,0,0,0)`）。三枚统一判据。 */
const on = (st) => !!st && !/rgba\(0, 0, 0, 0\)/.test(st.bg || '');

const listNodes = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id') || '?',
    name: ((n.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] || '').slice(0, 12),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }));

async function exclusivePoint(pg, id) {
  return pg.evaluate((nid) => {
    const t = [...document.querySelectorAll('.react-flow__node')].find((n) => n.getAttribute('data-id') === nid);
    if (!t) return { err: 'no node' };
    const r = t.getBoundingClientRect();
    for (let fy = 0.2; fy <= 0.8; fy += 0.15) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === t) return { x, y };
    }
    return { err: 'no exclusive point' };
  }, id);
}

/** 落点归属校验：这个坐标上到底是什么？（AZ 的教训：坐标对 ≠ 落点归你） */
const ownerAt = (pg, x, y) => pg.evaluate(([px, py]) => {
  const o = document.elementFromPoint(px, py);
  if (!o) return { err: 'elementFromPoint 返回 null' };
  const b = o.closest('button,[role="button"]');
  return { tag: o.tagName, cls: (o.className || '').toString().slice(0, 50),
    btnAria: b ? b.getAttribute('aria-label') : null,
    isTarget: !!b };
}, [x, y]);

/** 三种触发方式点同一枚按钮，每种点完都回读。 */
const clickBy = async (pg, aria, how) => {
  const p = await btn(pg, aria);
  if (p.err) return { err: p.err };
  if (how === 'mouse') {
    await pg.mouse.move(p.x, p.y); await pg.waitForTimeout(220);
    await pg.mouse.click(p.x, p.y);
  } else if (how === 'dom') {
    await pg.evaluate((name) => {
      const e = [...document.querySelectorAll('button,[role="button"]')]
        .find((x) => x.getAttribute('aria-label') === name);
      e && e.click();
    }, aria);
  } else if (how === 'events') {
    await pg.evaluate((name) => {
      const e = [...document.querySelectorAll('button,[role="button"]')]
        .find((x) => x.getAttribute('aria-label') === name);
      if (!e) return;
      for (const t of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
        e.dispatchEvent(new MouseEvent(t, { bubbles: true, cancelable: true, view: window }));
      }
    }, aria);
  }
  await pg.waitForTimeout(1900);
  return (await state3(pg))[aria];
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '网格吸附关不掉是产品行为还是没点中（三开关对照 + 三种触发方式）/ H 单向复验 / 预设蓝点 tooltip' });

  const out = {};

  // ═══ 1：三枚开关的对照实验
  console.log('--- BD3-1 三枚开关对照 ---');
  const s0 = await state3(page);
  console.log('初始:', JSON.stringify(s0, null, 1));
  out.toggles = { start: s0 };

  // 落点归属：三个坐标分别是谁
  const owners = {};
  for (const n of ['切换小地图', '隐藏节点连线', '网格吸附']) {
    const p = await btn(page, n);
    owners[n] = { coord: [p.x, p.y], ...(await ownerAt(page, p.x, p.y)) };
  }
  console.log('落点归属:', JSON.stringify(owners, null, 1));
  out.toggles.owners = owners;
  out.toggles.ownerOk = Object.values(owners).every((o) => o.btnAria && Object.keys(owners).some((k) => k === o.btnAria));

  // 对照组：先看 `隐藏节点连线` 能不能来回切
  console.log('\n  对照组：隐藏节点连线 点两下');
  const h1 = await clickBy(page, '隐藏节点连线', 'mouse');
  const h2 = await clickBy(page, '隐藏节点连线', 'mouse');
  console.log('  连线 点1 →', on(h1) ? '开' : '关', ' 点2 →', on(h2) ? '开' : '关',
    h2 ? JSON.stringify(h2.bg) : '');
  out.toggles.edge = { after1: h1, after2: h2, togglesBack: on(h1) !== on(h2) };
  // 复原连线
  if (on(h2)) await clickBy(page, '隐藏节点连线', 'mouse');

  // 对照组：小地图 点两下
  console.log('\n  对照组：切换小地图 点两下');
  const m1 = await clickBy(page, '切换小地图', 'mouse');
  const m2 = await clickBy(page, '切换小地图', 'mouse');
  console.log('  小地图 点1 →', on(m1) ? '开' : '关', ' 点2 →', on(m2) ? '开' : '关');
  out.toggles.mini = { after1: m1, after2: m2, togglesBack: on(m1) !== on(m2) };
  if (on(m2)) await clickBy(page, '切换小地图', 'mouse');

  // 实验组：网格吸附，三种触发方式各点一次
  console.log('\n  实验组：网格吸附（三种触发方式）');
  const g1 = await clickBy(page, '网格吸附', 'mouse');
  console.log('  mouse.click →', on(g1) ? '开' : '关');
  const g2 = await clickBy(page, '网格吸附', 'dom');
  console.log('  el.click()   →', on(g2) ? '开' : '关');
  const g3 = await clickBy(page, '网格吸附', 'events');
  console.log('  派发五事件   →', on(g3) ? '开' : '关');
  out.toggles.grid = { byMouse: g1, byDomClick: g2, byEvents: g3,
    turnedOn: on(g1), turnedOff: !on(g1) && !on(g2) && !on(g3) };

  // 再补 5 次 mouse.click，看是不是完全不动
  const seq = [];
  for (let i = 0; i < 5; i += 1) seq.push(on(await clickBy(page, '网格吸附', 'mouse')));
  console.log('  连续 5 次 mouse.click 的态:', JSON.stringify(seq));
  out.toggles.grid.sequence = seq;
  out.toggles.grid.stuckOn = seq.every(Boolean);
  await shot(page, 'M-184-网格吸附-开启态.png');
  out.shot = 'M-184-网格吸附-开启态.png';

  const gEnd = (await state3(page))['网格吸附'];
  console.log('  最终态:', on(gEnd) ? '开（关不掉）⚠️' : '关 ✅');
  out.toggles.grid.finalOn = on(gEnd);

  // ═══ 2：`H` 单向复验
  console.log('\n--- BD3-2 H 单向复验 ---');
  const toolMode = () => page.evaluate(() => {
    const b = document.querySelector('[data-sidebar-btn="tool-mode"]');
    if (!b) return { err: 'no tool-mode' };
    const e = document.elementFromPoint(900, 300) || document.body;
    const c = getComputedStyle(e).cursor;
    return { aria: b.getAttribute('aria-label'),
      cursor: c.startsWith('url(') ? 'custom-arrow' : c };
  });

  await page.mouse.click(720, 300); await page.waitForTimeout(1000);
  const k0 = await toolMode();
  console.log('  初始:', JSON.stringify(k0));
  const trail = [k0.aria];
  await page.keyboard.press('h'); await page.waitForTimeout(1700); trail.push((await toolMode()).aria);
  await page.keyboard.press('h'); await page.waitForTimeout(1700); trail.push((await toolMode()).aria);
  await page.keyboard.press('h'); await page.waitForTimeout(1700); trail.push((await toolMode()).aria);
  console.log('  连按三次 H:', JSON.stringify(trail));
  await shot(page, 'M-181-抓手模式.png');
  out.shot2 = 'M-181-抓手模式.png';

  const tries = [];
  await page.keyboard.down('Shift'); await page.keyboard.press('h'); await page.keyboard.up('Shift');
  await page.waitForTimeout(1700);
  tries.push({ how: 'Shift+H', ...(await toolMode()) });
  // 点按钮本身
  const cur = await toolMode();
  if (cur.aria !== '移动') {
    const p = await btn(page, cur.aria);
    await page.mouse.click(p.x, p.y); await page.waitForTimeout(1800);
    tries.push({ how: '点按钮本身', ...(await toolMode()) });
  }
  await page.keyboard.press('v'); await page.waitForTimeout(1700);
  tries.push({ how: '按 V', ...(await toolMode()) });
  for (const t of tries) console.log('  ', t.how, '→', t.aria, '/', t.cursor);
  out.tool = { start: k0, threeH: trail, tries,
    hIsOneWay: trail.filter((x) => x === '抓手工具').length === 3,
    vBringsBack: tries.some((t) => t.aria === '移动') };

  if ((await toolMode()).aria !== '移动') {
    const p = await btn(page, '抓手工具');
    await page.mouse.click(p.x, p.y); await page.waitForTimeout(1800);
  }
  await fitView(page); await page.waitForTimeout(1500);

  // ═══ 3：预设工作流蓝点 tooltip（走 BA1 的老路：选中图片节点 → 点参数条 `预设`）
  console.log('\n--- BD3-3 预设工作流蓝点 ---');
  await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  await fitView(page); await page.waitForTimeout(1400);
  // 选中第一个图片节点
  let selOk = null;
  for (const n of (await listNodes()).filter((x) => x.id.startsWith('i-'))) {
    const pt = await exclusivePoint(page, n.id);
    if (pt.err) continue;
    await page.mouse.click(pt.x, pt.y); await page.waitForTimeout(1800);
    const isSel = await page.evaluate(() => !!document.querySelector('.react-flow__node.selected'));
    if (isSel) { selOk = n.id; break; }
  }
  console.log('  选中图片节点:', selOk);
  if (!selOk) {
    out.blueDot = { err: '没选中图片节点' };
  } else {
    const pre = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node.selected');
      const b = [...n.querySelectorAll('button,[role="button"]')].find((x) => x.getAttribute('aria-label') === '预设');
      if (!b) return { err: '参数条上没有 aria=预设' };
      const r = b.getBoundingClientRect();
      return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
    });
    if (pre.err) { console.log('  ', pre.err); out.blueDot = pre; }
    else {
      await page.mouse.click(pre.x, pre.y); await page.waitForTimeout(2800); await clearToasts(page);
      // 蓝点：极小、无子元素、偏蓝的实心圆
      const dots = await page.evaluate(() => {
        const all = [...document.querySelectorAll('body *')].filter((e) => {
          const r = e.getBoundingClientRect();
          if (r.width < 3 || r.width > 16 || r.height < 3 || r.height > 16) return false;
          if (e.children.length) return false;
          const m = /rgba?\((\d+),\s*(\d+),\s*(\d+)/.exec(getComputedStyle(e).backgroundColor);
          if (!m) return false;
          const [r0, g0, b0] = [+m[1], +m[2], +m[3]];
          return b0 > 140 && b0 - r0 > 40;
        });
        return all.map((e) => {
          const r = e.getBoundingClientRect();
          const p = e.parentElement;
          return { tag: e.tagName, cls: (e.className || '').toString().slice(0, 60),
            rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
            bg: getComputedStyle(e).backgroundColor, radius: getComputedStyle(e).borderRadius,
            parentText: (p?.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 26),
            parentCls: (p?.className || '').toString().slice(0, 50) };
        }); });
      console.log('  蓝点候选', dots.length, '个:');
      dots.slice(0, 8).forEach((d) => console.log('   ', JSON.stringify(d)));

      const tips = [];
      for (const d of dots.slice(0, 6)) {
        const [x, y, w, h] = d.rect;
        await page.mouse.move(x + w / 2, y + h / 2); await page.waitForTimeout(1500);
        const tip = await page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip-tooltip"]')]
          .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
          .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()));
        // 归属校验：tooltip 必须真的在鼠标附近
        const near = await page.evaluate(([px, py]) => {
          const t = [...document.querySelectorAll('[class*="Tooltip-tooltip"]')]
            .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
            .map((e) => { const r = e.getBoundingClientRect();
              return { text: (e.innerText || '').replace(/\s+/g, ' ').trim(),
                d: Math.round(Math.hypot((r.x + r.width / 2) - px, (r.y + r.height / 2) - py)) }; })
            .sort((a, b) => a.d - b.d);
          return t[0] || null;
        }, [x + w / 2, y + h / 2]);
        tips.push({ parentText: d.parentText, near, all: tip });
        console.log('   hover', JSON.stringify(d.parentText), '→', JSON.stringify(near));
      }
      out.blueDot = { dots, tips, anyTooltip: tips.some((t) => t.near && t.near.text) };
      if (out.blueDot.anyTooltip) {
        await shot(page, 'M-183-预设蓝点提示.png');
        out.shot3 = 'M-183-预设蓝点提示.png';
      }
      await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
    }
  }

  await logStep(B, {
    id: 'BD3-stuck-toggle-oneway-h-bluedot',
    title: '网格吸附关不掉（三开关对照）/ H 单向复验 / 预设蓝点 tooltip',
    target: '把「点了没反应」拆成「产品就这样」与「我没点中」两件事。'
      + '手段：拿同一组里另外两枚同代码的开关做对照，并用坐标点击 / DOM click / 派发五事件三种触发方式各点一次。',
    evidence: out,
    visible_text: JSON.stringify({ toggles: out.toggles, tool: out.tool, blueDot: out.blueDot }).slice(0, 3500),
    shot: out.shot2,
  });
  console.log('\nBD3 完成');
} finally {
  await browser.close();
}
