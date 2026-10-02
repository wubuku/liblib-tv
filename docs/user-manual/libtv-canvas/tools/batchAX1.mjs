// Batch AW4 之后判据已经换过来了，这一轮直接用：
//   · **无 class 白名单**的全量浮层快照差集（特效广场是 Mantine class、
//     运镜广场是原生 fixed overlay —— 按白名单认浮层会漏）
//   · **每一枚都从同一起点重来**（取消选中 → 拖到画面上部 → 用坐标点它），
//     收场本身会弄丢选中态，AW3 就栽在这
//   · 视口里有**两个图片节点**且其中一个压着两个音频节点，
//     所以先按 `selfHit` 挑没被压住的那个，别按 innerText 取第一个
//
// 本轮目标（AV1 清点出来的图片面板 11 个可点元素，其中 4 个无文字）：
//   `参考` · `标记` · `风格` · `aria=预设` · **一枚连 SVG 都没有的空按钮**
//   外加音频的 `参考` 一枚、文本节点的面板全貌。
//
// 顺带回答一个 AW 留下的疑问：图片节点那枚 `⤢` 是 `cursor: not-allowed`，
// 而视频能点 —— 本轮把「点它会发生什么」也一并验掉（不点提交箭头/文A）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAX1';
const { browser, page } = await launch();

/** 全页可见浮层快照 —— 无尺寸门槛、无 class 白名单。 */
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
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], text: txt.slice(0, 450) });
  }
  const seen = new Set();
  return out.filter((o) => { const k = o.cls + '|' + o.rect.join(','); if (seen.has(k)) return false; seen.add(k); return true; });
});

/** 面板 + 它里面全部可点元素（**含无文字的，带图标指纹**）。 */
const panelState = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没有选中节点' };
  // **判据：宽度 ≥ 500 且至少含 3 个可点元素，取面积最大的那个。**
  // 参数面板是 642/658 宽、节点本体只有 263 宽 —— 宽度是最强的区分信号。
  // 上一版用「含『参考』二字」能选中，但为了兼容文本节点而放宽成「有文字」，
  // 结果选中的是**工具条**（642×128、里面一个 button 都没有）。
  const c = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width >= 500 && o.r.height >= 100)
    .filter((o) => o.e.querySelectorAll('button,[role="button"]').length >= 3)
    .sort((a, b) => (b.r.width * b.r.height) - (a.r.width * a.r.height))[0];
  if (!c) {
    return { err: '没找到面板（宽 ≥500 且 ≥3 个可点元素的容器一个都没有）',
      widths: [...n.querySelectorAll('div')].map((e) => { const r = e.getBoundingClientRect();
        return [Math.round(r.width), Math.round(r.height), e.querySelectorAll('button,[role="button"]').length]; })
        .filter((x) => x[0] > 200).slice(0, 12) };
  }
  const p = c.e;
  const fp = (e) => { const s = e.querySelector('svg'); if (!s) return 'nosvg';
    const ds = [...s.querySelectorAll('path')].map((x) => x.getAttribute('d') || '').filter(Boolean);
    return ds.length ? ds.sort((a, b) => b.length - a.length)[0].slice(0, 34) : 'svgonly'; };
  return { nodeCls: (n.className || '').toString().slice(0, 60),
    panelRect: [Math.round(c.r.x), Math.round(c.r.y), Math.round(c.r.width), Math.round(c.r.height)],
    panelText: (p.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300),
    btns: [...p.querySelectorAll('button,[role="button"]')].map((e) => {
      const q = e.getBoundingClientRect();
      return { text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10),
        aria: e.getAttribute('aria-label'), fp: fp(e),
        rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
        cursor: getComputedStyle(e).cursor };
    }).filter((b) => b.rect[2] > 0 && b.rect[3] > 0) };
});

/** 取消选中 → 拖一个「没被压住」的节点到 y=150 → 用坐标点它。 */
async function freshSelect(textPart) {
  await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  await page.mouse.click(80, 120); await page.waitForTimeout(1400);
  const g = await page.evaluate((t) => {
    const c = [...document.querySelectorAll('.react-flow__node')]
      .filter((n) => (n.innerText || '').includes(t) && !n.classList.contains('selected'))
      .map((n) => { const r = n.getBoundingClientRect();
        const ccx = r.x + r.width / 2, ccy = r.y + r.height / 2;
        const o = (ccx >= 0 && ccy >= 0 && ccx < innerWidth && ccy < innerHeight) ? document.elementFromPoint(ccx, ccy) : null;
        return { n, r, selfHit: !!(o && n.contains(o)) }; })
      .filter((x) => x.r.x >= 5 && x.r.x + x.r.width <= 1435 && x.r.y >= 60 && x.r.y + x.r.height <= 800)
      .sort((a, b) => (b.selfHit - a.selfHit) || (Math.abs(a.r.y - 110) - Math.abs(b.r.y - 110)));
    if (!c.length) return { err: '视口里没有可用的「' + t + '」' };
    const { n, r, selfHit } = c[0];
    for (const [fx, fy] of [[0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.3], [0.5, 0.7], [0.5, 0.2]]) {
      const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
      const o = document.elementFromPoint(cx, cy);
      if (o && n.contains(o) && !o.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
        return { cx: Math.round(cx), cy: Math.round(cy), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], selfHit };
      }
    }
    return { err: '「' + t + '」可点区全被挡住', selfHit };
  }, textPart);
  if (g.err) return g;
  const dy = Math.round(150 - g.rect[1]);
  if (Math.abs(dy) > 4) {
    await page.mouse.move(g.cx, g.cy); await page.mouse.down();
    for (let i = 1; i <= 12; i += 1) { await page.mouse.move(g.cx, g.cy + (dy * i) / 12); await page.waitForTimeout(70); }
    await page.mouse.up(); await page.waitForTimeout(2000);
  }
  const g2 = await page.evaluate((t) => {
    // **必须按 selfHit 排序** —— 上一版按 innerText 取第一个，
    // 结果点到了压在图片节点上面的那个视频节点（断言查出来才发现）。
    const cands = [...document.querySelectorAll('.react-flow__node')]
      .filter((n) => (n.innerText || '').includes(t) && !n.classList.contains('selected'))
      .map((n) => { const r = n.getBoundingClientRect();
        const ccx = r.x + r.width / 2, ccy = r.y + r.height / 2;
        const o = (ccx >= 0 && ccy >= 0 && ccx < innerWidth && ccy < innerHeight) ? document.elementFromPoint(ccx, ccy) : null;
        return { n, r, selfHit: !!(o && n.contains(o)), d: Math.abs(r.y - 150) }; })
      .filter((x) => x.r.x >= 5 && x.r.x + x.r.width <= 1435 && x.r.y >= 60 && x.r.y + x.r.height <= 800)
      .sort((a, b) => (b.selfHit - a.selfHit) || (a.d - b.d));
    for (const { n, r, selfHit } of cands) {
      for (const [fx, fy] of [[0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.3], [0.5, 0.7], [0.5, 0.2]]) {
        const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
        const o = document.elementFromPoint(cx, cy);
        if (o && n.contains(o) && !o.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
          return { cx: Math.round(cx), cy: Math.round(cy), selfHit };
        }
      }
    }
    return null;
  }, textPart);
  if (!g2) return { err: '拖完找不到了' };
  await page.mouse.click(g2.cx, g2.cy);
  await page.waitForTimeout(4200);
  // **点完必须回读「选中的是不是我要的那类节点」** —— 这一步我漏了整整两个批次。
  // 上一版 `freshSelect('图片节点')` 之后读到的是**视频面板**（工具条是
  // 特效/角色库/运镜），因为中心点被压住的那一下点到了压在上面���节点，
  // 而我当时**只 assert 了「有没有选中」，没 assert 「选中的是谁」**。
  const sel = await page.evaluate(() => {
    const n = document.querySelector('.react-flow__node.selected');
    if (!n) return { none: true };
    const m = /react-flow__node-([a-z-]+)/.exec(n.className || '');
    return { type: m ? m[1] : 'unknown',
      text: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
      cls: (n.className || '').toString().slice(0, 60) };
  });
  const want = textPart.replace(/节点.*$/, '');
  return { ...g2, selfHit: g.selfHit, selected: !sel.none, selectedType: sel.type,
    selectedText: sel.text, typeOk: sel.type && sel.type.startsWith(want),
    note: sel.type && sel.type.startsWith(want) ? '类型对得上' : '⚠ **选中的不是「' + textPart + '」，是 ' + (sel.type || '无') + '**' };
}

async function clickOne(pick, label, shotName) {
  const r = { label };
  const st = await panelState();
  if (st.err) { r.err = st.err; return r; }
  if (!Array.isArray(st.btns)) { r.err = 'panelState 没返回 btns'; r.raw = JSON.stringify(st).slice(0, 300); return r; }
  const b = pick(st.btns);
  if (!b) { r.err = '没找到目标'; r.available = st.btns.map((x) => ({ t: x.text, a: x.aria, fp: x.fp.slice(0, 18) })); return r; }
  r.target = { text: b.text, aria: b.aria, fp: b.fp.slice(0, 24), rect: b.rect, cursor: b.cursor };
  if (b.cursor === 'not-allowed') { r.skipped = 'cursor=not-allowed（不可点）'; return r; }
  const before = await snap();
  const cx = b.rect[0] + b.rect[2] / 2, cy = b.rect[1] + b.rect[3] / 2;
  r.hit = await page.evaluate(([x, y]) => {
    const e = document.elementFromPoint(x, y); const btn = e && e.closest('button');
    return e ? { tag: e.tagName, btnAria: btn?.getAttribute('aria-label') || null,
      btnText: (btn?.innerText || '').trim().slice(0, 8) } : null;
  }, [cx, cy]);
  await page.mouse.click(cx, cy);
  await page.waitForTimeout(3200);
  await clearToasts(page);
  const after = await snap();
  const bs = new Set(before.map((o) => o.cls + '|' + o.rect.join(',')));
  r.added = after.filter((o) => !bs.has(o.cls + '|' + o.rect.join(',')))
    .sort((a, b) => (b.rect[2] * b.rect[3]) - (a.rect[2] * a.rect[3]));
  r.nAdded = r.added.length;
  r.top = r.added[0] || null;
  if (r.nAdded) { await shot(page, shotName); r.shot = shotName; }
  await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
  return r;
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await beginBatch(B, { note: '图片节点工具条逐枚实点 + 音频参考 + 文本节点面板' });

  const out = {};

  // ── ① 图片节点
  out.image = { start: await freshSelect('图片节点') };
  console.log('AX1 选中的节点类型:', JSON.stringify({ t: out.image.start.selectedType, ok: out.image.start.typeOk, note: out.image.start.note }));
  out.image.panel = await panelState();
  console.log('AX1 图片面板:', JSON.stringify(out.image.panel.panelRect));
  console.log('AX1 图片面板可点元素:');
  (out.image.panel.btns || []).forEach((b, i) =>
    console.log(`  [${i}] [${String(b.rect).padEnd(20)}] text=${(b.text || '-').padEnd(10)} aria=${(b.aria || '-').padEnd(10)} cursor=${b.cursor} fp=${b.fp.slice(0, 22)}`));

  out.image.clicks = [];
  // ⚠️ pick 收到的是 **panelState().btns 那个数组**，不是 panelState 对象本身。
  //    上一版我写成 `(st) => st.btns.find(...)` 然后按 `(st) => st.btns` 调用它 ——
  //    **第三次「我以为的 API」**：以为 pick 收整个对象，实际只收到数组。
  const byText = (t) => (arr) => arr.find((b) => b.text === t);
  const byAria = (a) => (arr) => arr.find((b) => b.aria === a);
  const byFp = (pfx) => (arr) => arr.find((b) => b.fp.startsWith(pfx));
  const plan = [
    ['参考', byText('参考'), 'M-158-图片-参考.png'],
    ['标记', byText('标记'), 'M-159-图片-标记.png'],
    ['风格', byText('风格'), 'M-160-图片-风格.png'],
    ['aria=预设', byAria('预设'), 'M-161-图片-预设.png'],
    ['无SVG 空按钮', byFp('nosvg'), 'M-162-图片-空按钮.png'],
    ['⤢(not-allowed?)', byFp('M8.3.3a1 1'), null],
  ];
  for (const [label, pick, shotName] of plan) {
    if (!shotName) {
      // ⤢ 也要验「点了会发生什么」，但不截图（not-allowed 时没有画面）
      const r0 = await clickOne(pick, label, null);
      out.image.clicks.push(r0);
      console.log(`  ${label} →`, JSON.stringify(r0).slice(0, 200));
      await freshSelect('图片节点');
      continue;
    }
    const r = await clickOne(pick, label, shotName);
    out.image.clicks.push(r);
    console.log(`  ${label} → 新增 ${r.nAdded} 个` + (r.top ? ` 最大 [${r.top.rect}] z=${r.top.z} ${r.top.cls}` : '') + (r.err ? ` ⚠ ${r.err}` : '') + (r.skipped ? ` (${r.skipped})` : ''));
    if (r.top) console.log('     ', r.top.text.slice(0, 200));
    if (r.err) console.log('      可用:', JSON.stringify(r.available).slice(0, 300));
    await freshSelect('图片节点');
  }

  // ── ② 音频的「参考」
  out.audio = { start: await freshSelect('音频节点') };
  out.audio.panel = await panelState();
  console.log('\nAX1 音频面板可点元素:', JSON.stringify((out.audio.panel.btns || []).map((b) => b.text || b.aria)));
  out.audio.click = await clickOne(byText('参考'), '音频-参考', 'M-163-音频-参考.png');
  console.log('  音频「参考」→ 新增', out.audio.click.nAdded, '个',
    out.audio.click.top ? `[${out.audio.click.top.rect}] ${out.audio.click.top.cls}` : '',
    out.audio.click.err || out.audio.click.skipped || '');
  if (out.audio.click.top) console.log('     ', out.audio.click.top.text.slice(0, 200));

  // ── ③ 文本节点的面板（只 dump，不点）
  await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  await page.mouse.click(80, 120); await page.waitForTimeout(1500);
  out.text = { start: await freshSelect('文本节点') };
  out.text.panel = await panelState();
  console.log('\nAX1 文本面板:', JSON.stringify(out.text.panel.panelRect || out.text.panel.err));
  console.log('AX1 文本面板全文:', (out.text.panel.panelText || '').slice(0, 200));
  console.log('AX1 文本面板可点元素:', JSON.stringify((out.text.panel.btns || []).map((b) => ({ t: b.text, a: b.aria }))));
  if (out.text.panel.panelRect) { await shot(page, 'M-164-文本节点-参数面板.png'); out.text.shot = 'M-164-文本节点-参数面板.png'; }

  await logStep(B, {
    id: 'AX1-image-toolbar-and-audio-text', title: '图片节点工具条逐枚实点 + 音频参考 + 文本节点面板',
    target: '图片面板有 **4 个无文字按钮**（其中一枚 `aria=预设`、一枚**连 SVG 都没有**）；'
      + '另验图片那枚 `⤢` 是不是真的 `not-allowed`。⚠️ 不点 文A 与提交箭头',
    evidence: out,
    visible_text: JSON.stringify({
      image: out.image.clicks.map((c) => ({ l: c.label, n: c.nAdded, top: c.top && { r: c.top.rect, c: c.top.cls, t: c.top.text.slice(0, 160) } })),
      audio: { l: out.audio.click.label, n: out.audio.click.nAdded, top: out.audio.click.top && out.audio.click.top.text.slice(0, 160) },
      text: out.text.panel && { rect: out.text.panel.panelRect, text: (out.text.panel.panelText || '').slice(0, 200) },
    }).slice(0, 3000),
    shot: out.text.shot || 'M-139-视频节点-参数面板.png',
  });
  console.log('\nAX1 完成');
} finally {
  await browser.close();
}
