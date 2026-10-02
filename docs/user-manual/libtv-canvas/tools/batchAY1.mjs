// Batch AY1 —— 资产管理抽屉**只读盘点** + 视频节点那枚 `📄` 到底打开什么。
//
// 两件事，一件比一件小：
//
// ① 资产管理抽屉：手册里记了「行内动作按钮」「更多操作菜单」「复制/重命名/删除」
//    这些**行级**操作，但抽屉**顶部那一层**（创建默认资产分类 / 新建文件夹 /
//    上传入口 / 筛选 / 排序 / tab）从来没被系统清点过 —— 数量、位置、有没有 aria，
//    全部未知。
//    ⚠️ **只读**：创建/上传/删除都会写账户数据，一个都不点。只点纯导航的
//    tab、筛选下拉、排序下拉（这些不改数据）。
//
// ② 视频节点底部那枚 `📄`（AV1 清点出来 SVG `M10.26 1.67c.32 0 .57.25.57.57`，
//    正文一个字没记）。AW2 点过一次读到 `newPanels: []`，但**那一轮用的是
//    `diffPanels` + 错误的 API**，读数没有判别力。这轮用 AX 批次那套
//    无 class 白名单的全量快照差集重测。
//
// ⚠️ 上一轮在这里翻车，记下来别再犯：
//   `drawerControls` 用「宽≥280 且 x<400 取面积最小」找抽屉，结果选中的是
//   **`react-flow__viewport`** —— 那是画布的变换容器，rect `[82,-62,474,343]`，
//   里面全是画布节点自己的按钮（音频生视频 / 分镜 / 动态 / 打开导演台 …）
//   加 3 个 rect 为 `[0,0,0,0]` 的 `input[type=file]`。
//   **资产管理抽屉的真实控件一个都没读到。**
//   → 教训：**几何条件不能唯一确定容器**。这轮改成先**全量 dump 两侧大容器**
//     （含 class / rect / 按钮数 / 文本头 / 是否在 `.react-flow` 内），
//     让人和判据都能看见候选，再用可解释的规则挑，并且把候选全打出来。
//
// 沿用前几批换来的判据：
//   · 无 class 白名单的全量浮层快照差集
//   · **目标 rect 出视口就不点**，原因记成「按钮仍在视口外」而不是「没反应」
//   · 点之前验 elementFromPoint 落在目标上
//   · 选完节点**断言选中的是哪一类**（`react-flow__node-*`）
//   · 节点要**同时**拖到 (720,150) —— 参数面板以节点为中心居中、宽 660
//   · 拖完**回读**实际位置，够不到就再拖一次（上轮 `g2` 为 null 就是拖完没回读）
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAY1';
const { browser, page } = await launch();

const snap = () => page.evaluate(() => {
  const out = [];
  for (const e of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) continue;
    if (cs.position !== 'fixed' && cs.position !== 'absolute' && cs.position !== 'sticky') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    if (r.bottom < 0 || r.right < 0 || r.y > 810 || r.x > 1440) continue;
    const txt = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!txt) continue;
    out.push({ cls: (e.className || '').toString().slice(0, 55), z: cs.zIndex,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], text: txt.slice(0, 400) });
  }
  const seen = new Set();
  return out.filter((o) => { const k = o.cls + '|' + o.rect.join(','); if (seen.has(k)) return false; seen.add(k); return true; });
});

/**
 * 全量 dump 靠两侧的面板级容器 —— 不猜，只列。
 * 上一轮就是「猜一个容器然后把里面的东西当证据」，结果读到的是画布节点。
 */
const panelDump = () => page.evaluate(() => {
  const rows = [];
  for (const e of document.querySelectorAll('body div,body section,body aside')) {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    if (r.width < 200 || r.height < 250) continue;
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) <= 0.05) continue;
    if (r.x > 1440 || r.x + r.width < 0 || r.y > 810 || r.y + r.height < 0) continue;
    const inFlow = !!e.closest('.react-flow');
    const btns = [...e.querySelectorAll('button,[role="button"]')]
      .filter((b) => { const q = b.getBoundingClientRect(); return q.width > 0 && q.height > 0; });
    // 「这个容器里的按钮是不是全都在它自己里面」——画布 viewport 会漏进别处的按钮
    const br = btns.filter((b) => { const q = b.getBoundingClientRect();
      return q.x >= r.x - 2 && q.x + q.width <= r.x + r.width + 2 && q.y >= r.y - 2 && q.y + q.height <= r.y + r.height + 2; });
    rows.push({
      cls: (e.className || '').toString().slice(0, 64),
      tag: e.tagName,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      pos: cs.position, z: cs.zIndex, inFlow,
      nBtn: btns.length, nBtnInside: br.length,
      head: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 90),
    });
  }
  return rows.sort((a, b) => (b.rect[2] * b.rect[3]) - (a.rect[2] * a.rect[3]));
});

/**
 * 抽屉里所有可点元素 + 输入框。
 * 判据可解释：`不在画布内` + `按钮基本都在自己框里` + `面积不是最大那层` + `有资产相关文案`。
 * 每一项都记进 `why`，挑错了能一眼看出是哪条规则出的问题。
 */
const drawerControls = () => page.evaluate(() => {
  const rows = [];
  for (const e of document.querySelectorAll('body div,body section,body aside')) {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    if (r.width < 200 || r.height < 250) continue;
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) <= 0.05) continue;
    if (r.x > 1440 || r.x + r.width < 0 || r.y > 810 || r.y + r.height < 0) continue;
    const inFlow = !!e.closest('.react-flow');
    const btns = [...e.querySelectorAll('button,[role="button"]')]
      .filter((b) => { const q = b.getBoundingClientRect(); return q.width > 0 && q.height > 0; });
    const br = btns.filter((b) => { const q = b.getBoundingClientRect();
      return q.x >= r.x - 2 && q.x + q.width <= r.x + r.width + 2 && q.y >= r.y - 2 && q.y + q.height <= r.y + r.height + 2; });
    const text = (e.innerText || '').replace(/\s+/g, ' ').trim();
    rows.push({ e, inFlow, btns, br, text,
      cls: (e.className || '').toString().slice(0, 64),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      area: r.width * r.height, nBtn: btns.length, nBtnInside: br.length });
  }
  const ASSET = /素材|资产|文件夹|上传|图片|视频|音频|全部/;
  const scored = rows.map((r) => {
    const why = [];
    if (r.inFlow) why.push('✗在画布内');
    if (r.nBtn && r.nBtnInside / r.nBtn < 0.8) why.push('✗按钮外溢');
    if (!ASSET.test(r.text)) why.push('✗无资产文案');
    return { r, ok: why.length === 0 && r.nBtnInside > 0, why: why.join(' ') || '✓' };
  }).filter((s) => s.ok).sort((a, b) => (a.r.area - b.r.area));

  if (!scored.length) {
    return { err: '没有候选同时满足「不在画布内 + 按钮不外溢 + 有资产文案」', candidates: rows.length };
  }
  // 取最内层（面积最小）的那个；若是 `body`/铺满层则往里退
  const box = scored[0].r;
  const e = box.e;
  const inp = [...e.querySelectorAll('input')].map((n) => { const r = n.getBoundingClientRect();
    return { kind: 'input', type: n.type, aria: n.getAttribute('aria-label'), ph: n.placeholder, value: n.value,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
  const btn = [...e.querySelectorAll('button,[role="button"]')].map((n) => {
    const r = n.getBoundingClientRect();
    const fp = (() => { const s = n.querySelector('svg'); if (!s) return 'nosvg';
      const ds = [...s.querySelectorAll('path')].map((x) => x.getAttribute('d') || '').filter(Boolean);
      return ds.length ? ds.sort((a, b) => b.length - a.length)[0].slice(0, 30) : 'svgonly'; })();
    return { kind: 'button', text: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16),
      aria: n.getAttribute('aria-label'), title: n.getAttribute('title'), fp,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cursor: getComputedStyle(n).cursor,
      inView: r.x >= 0 && r.x + r.width <= 1440 && r.y >= 0 && r.y + r.height <= 810 }; });
  return { boxCls: box.cls, boxRect: box.rect, boxText: box.text.slice(0, 600),
    nButtons: btn.length, nInputs: inp.length, buttons: btn, inputs: inp,
    noTextNoAria: btn.filter((b) => !b.text && !b.aria && !b.title).length,
    runnerUp: scored.slice(1, 3).map((s) => ({ cls: s.r.cls, rect: s.r.rect, nBtn: s.r.nBtn })) };
});

async function clickBottomBar(ariaMatch) {
  const b = await page.evaluate((m) => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => new RegExp(m).test(x.getAttribute('aria-label') || x.getAttribute('title') || ''));
    if (!e) return { err: '底栏没找到 aria 匹配 ' + m };
    const r = e.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), aria: e.getAttribute('aria-label') };
  }, ariaMatch);
  if (b.err) return b;
  await page.mouse.click(b.cx, b.cy);
  await page.waitForTimeout(3000);
  return b;
}

/** 把一个视频节点拖到 (720,150)，拖完回读实际位置；不够就再拖一次。 */
async function dragVideoNodeToCenter(pg, label) {
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    const cur = await pg.evaluate(() => {
      let best = null;
      for (const n of document.querySelectorAll('.react-flow__node')) {
        if (!(n.innerText || '').includes('视频节点')) continue;
        const r = n.getBoundingClientRect();
        const d = Math.hypot(r.x + r.width / 2 - 720, r.y - 150);
        if (!best || d < best.d) best = { d, cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
      }
      return best;
    });
    if (!cur) return { err: `第 ${attempt} 次：页面上找不到任何视频节点` };
    console.log(`  ${label} 第 ${attempt} 次拖前中心`, cur.cx, cur.cy, 'rect', cur.rect);
    if (Math.abs(cur.cx - 720) < 40 && Math.abs(cur.rect[1] - 150) < 40) return { ...cur, moved: false };
    // 先点空白取消选中，否则参数面板会盖住节点上半部分
    await pg.mouse.click(80, 120); await pg.waitForTimeout(900);
    const start = await pg.evaluate(() => {
      let best = null;
      for (const n of document.querySelectorAll('.react-flow__node')) {
        if (!(n.innerText || '').includes('视频节点')) continue;
        const r = n.getBoundingClientRect();
        const d = Math.hypot(r.x + r.width / 2 - 720, r.y - 150);
        if (!best || d < best.d) best = { d, cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
      }
      return best;
    });
    if (!start) return { err: '点空白之后视频节点不见了' };
    const dx = Math.round(720 - start.cx);
    const dy = Math.round(150 - (await pg.evaluate(() => {
      let best = null;
      for (const n of document.querySelectorAll('.react-flow__node')) {
        if (!(n.innerText || '').includes('视频节点')) continue;
        const r = n.getBoundingClientRect();
        const d = Math.hypot(r.x + r.width / 2 - 720, r.y - 150);
        if (!best || d < best.d) best = { d, y: r.y };
      }
      return best ? best.y : 0;
    })));
    await pg.mouse.move(start.cx, start.cy); await pg.mouse.down();
    for (let i = 1; i <= 16; i += 1) { await pg.mouse.move(start.cx + (dx * i) / 16, start.cy + (dy * i) / 16); await pg.waitForTimeout(70); }
    await pg.mouse.up(); await pg.waitForTimeout(2200);
  }
  return { err: '拖了 3 次都没把视频节点挪到画面中间' };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await beginBatch(B, { note: '资产管理抽屉只读盘点（创建/上传/删除一律不点）+ 视频节点 📄 重测' });

  const out = {};

  // ── ① 资产管理抽屉
  console.log('--- AY1 ① 资产管理抽屉 ---');
  const beforeDump = await panelDump();
  console.log(`打开前面板级容器 ${beforeDump.length} 个:`);
  beforeDump.slice(0, 8).forEach((r) => console.log(
    `  [${String(r.rect).padEnd(22)}] ${r.tag} inFlow=${r.inFlow ? 'Y' : 'n'} btn=${String(r.nBtn).padStart(3)} inside=${String(r.nBtnInside).padStart(3)} ${r.cls}\n     "${r.head}"`));
  out.beforeDump = beforeDump.slice(0, 8);

  out.open = await clickBottomBar('资产管理');
  console.log('点底栏:', JSON.stringify(out.open));
  await clearToasts(page); await page.waitForTimeout(1200);

  const afterDump = await panelDump();
  console.log(`\n打开后面板级容器 ${afterDump.length} 个:`);
  afterDump.slice(0, 12).forEach((r) => console.log(
    `  [${String(r.rect).padEnd(22)}] ${r.tag} inFlow=${r.inFlow ? 'Y' : 'n'} btn=${String(r.nBtn).padStart(3)} inside=${String(r.nBtnInside).padStart(3)} ${r.cls}\n     "${r.head}"`));
  out.afterDump = afterDump.slice(0, 12);
  await shot(page, 'M-165-资产管理抽屉.png');
  out.shot = 'M-165-资产管理抽屉.png';

  out.controls = await drawerControls();
  if (out.controls.err) {
    console.log('  ⚠', out.controls.err, '候选数', out.controls.candidates);
  } else {
    console.log(`\n选中容器 [${out.controls.boxRect}] class=${out.controls.boxCls}`);
    console.log(`次选: ${JSON.stringify(out.controls.runnerUp)}`);
    console.log(`按钮 ${out.controls.nButtons} 个（无文字无 aria 的 ${out.controls.noTextNoAria} 个）、输入框 ${out.controls.nInputs} 个`);
    console.log('按钮清单:');
    out.controls.buttons.forEach((b, i) =>
      console.log(` [${String(i).padStart(2)}] [${String(b.rect).padEnd(20)}] text=${(b.text || '-').padEnd(16)} aria=${(b.aria || '-').padEnd(12)} title=${(b.title || '-').padEnd(10)} cur=${(b.cursor || '-').padEnd(11)} fp=${b.fp.slice(0, 20)}`));
    if (out.controls.inputs.length) console.log('输入框:', JSON.stringify(out.controls.inputs));
    console.log('容器文本:', out.controls.boxText.slice(0, 500));
  }

  // 关抽屉
  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await clearToasts(page);
  const closedDump = await panelDump();
  console.log(`\nEsc 后面板级容器 ${closedDump.length} 个`);
  out.closedDump = closedDump.slice(0, 8);

  // ── ② 视频节点那枚 📄
  console.log('\n--- AY1 ② 视频节点 📄 ---');
  await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  const moved = await dragVideoNodeToCenter(page, '视频节点');
  console.log('  拖拽结果:', JSON.stringify(moved));
  out.doc = { moved };
  if (moved.err) {
    console.log('  ⚠', moved.err);
  } else {
    await page.mouse.click(moved.cx, moved.cy);
    await page.waitForTimeout(4200);
    out.doc.selType = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node.selected');
      if (!n) return 'none';
      const m = /react-flow__node-([a-zA-Z-]+)/.exec(n.className || '');
      return m ? m[1] : (n.className || 'unknown').slice(0, 40); });
    const st = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node.selected');
      if (!n) return { err: '没选中任何节点' };
      const c = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
        .filter((o) => o.r.width >= 500 && o.r.height >= 100)
        .filter((o) => o.e.querySelectorAll('button,[role="button"]').length >= 3)
        .sort((a, b) => (b.r.width * b.r.height) - (a.r.width * a.r.height))[0];
      if (!c) return { err: '选中节点里没找到面板容器' };
      const p = c.e;
      const fp = (e) => { const s = e.querySelector('svg'); if (!s) return 'nosvg';
        const ds = [...s.querySelectorAll('path')].map((x) => x.getAttribute('d') || '').filter(Boolean);
        return ds.length ? ds.sort((a, b) => b.length - a.length)[0].slice(0, 34) : 'svgonly'; };
      return { panelRect: [Math.round(c.r.x), Math.round(c.r.y), Math.round(c.r.width), Math.round(c.r.height)],
        panelText: (p.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
        btns: [...p.querySelectorAll('button,[role="button"]')].map((e) => { const q = e.getBoundingClientRect();
          return { text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10), fp: fp(e),
            rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] };
        }).filter((b) => b.rect[2] > 0) };
    });
    out.doc.panel = st;
    console.log('  选中类型:', out.doc.selType, '| 面板:', JSON.stringify(st.panelRect || st.err));
    if (st.btns) st.btns.forEach((b, i) =>
      console.log(`   [${String(i).padStart(2)}] [${String(b.rect).padEnd(20)}] ${(b.text || '-').padEnd(10)} fp=${b.fp.slice(0, 24)}`));
    const doc = st.btns && st.btns.find((b) => b.fp.startsWith('M10.26 1.67'));
    if (!doc) {
      out.doc.err = '面板里没找到那枚 📄';
      console.log('  ⚠', out.doc.err);
    } else {
      out.doc.target = doc.rect;
      console.log('  📄 位置', doc.rect);
      if (doc.rect[0] < 0 || doc.rect[0] + doc.rect[2] > 1440 || doc.rect[1] < 0 || doc.rect[1] + doc.rect[3] > 810) {
        out.doc.skipped = '📄 仍在视口外，不点';
        console.log('  ⚠', out.doc.skipped);
      } else {
        const before = await snap();
        const cx = doc.rect[0] + doc.rect[2] / 2, cy = doc.rect[1] + doc.rect[3] / 2;
        out.doc.hit = await page.evaluate(([x, y]) => {
          const e = document.elementFromPoint(x, y);
          return e ? { tag: e.tagName, inBtn: !!e.closest('button'), btnText: (e.closest('button')?.innerText || '').trim().slice(0, 8) } : null;
        }, [cx, cy]);
        console.log('  elementFromPoint:', JSON.stringify(out.doc.hit));
        await page.mouse.click(cx, cy);
        await page.waitForTimeout(3200);
        await clearToasts(page);
        const after = await snap();
        const bs = new Set(before.map((o) => o.cls + '|' + o.rect.join(',')));
        out.doc.added = after.filter((o) => !bs.has(o.cls + '|' + o.rect.join(',')))
          .sort((a, b) => (b.rect[2] * b.rect[3]) - (a.rect[2] * a.rect[3]));
        out.doc.nAdded = out.doc.added.length;
        console.log('  📄 点击后新增浮层', out.doc.nAdded, '个');
        for (const a of out.doc.added.slice(0, 5)) console.log(`    + [${String(a.rect).padEnd(22)}] z=${a.z} ${a.cls}\n       ${a.text.slice(0, 240)}`);
        if (out.doc.nAdded) {
          await shot(page, 'M-166-视频-第一个图标.png');
          out.doc.shot = 'M-166-视频-第一个图标.png';
        }
        await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
      }
    }
  }

  await logStep(B, {
    id: 'AY1-asset-drawer-and-doc-icon', title: '资产管理抽屉只读盘点 + 视频节点 📄 重测',
    target: '**只读**：创建默认资产分类 / 新建文件夹 / 上传 / 删除一律不点（会写账户数据），'
      + '只点纯导航项。📄 上一轮读到 `newPanels: []` 但那是 `diffPanels` API 用错时的读数，'
      + '**没有判别力**，这轮用无 class 白名单的全量快照差集重测',
    evidence: out,
    visible_text: JSON.stringify({
      drawer: out.controls && { box: out.controls.boxCls, rect: out.controls.boxRect,
        n: out.controls.nButtons, inputs: out.controls.nInputs, text: (out.controls.boxText || '').slice(0, 400) },
      doc: out.doc,
    }).slice(0, 3000),
    shot: out.shot,
  });
  console.log('\nAY1 完成');
} finally {
  await browser.close();
}
