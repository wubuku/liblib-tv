// Batch BB1 —— 先验自己写进正文的那条建议，再把各节点的下拉选项清点成清单。
//
// 上一批在正文里写了这句建议：
//   「先把参数条最左边那枚模型下拉换成 Lib Image / General image Pro /
//     General image V2 之一，再回来看哪些变亮了。」
// ⚠️ **这句话是我推出来的，没验过。**
//    悬停提示只说了「仅支持 XX 模型」，**没说换成 XX 之后就一定能点**。
//    手册里写一条自己没验过的操作建议，用户照做发现没用，就是手册在坑人。
//    → 这轮第一件事就是**把它验掉**：换模型 → 看预设是否变亮 → **换回来**。
//
// 换模型是**节点参数**，不是账户数据，改回去即可复原。
// ⚠️ 但仍要记下原值，验完逐字确认复原了。
//
// 第二件事：**各节点模型/规格下拉的选项清单**（纯只读：打开 → 读 → Esc）。
//   此前手册只写了当前选中值，没写过「还能选什么」——
//   规格串那节写着「有上下箭头可切换，未逐个试」，这轮能补多少补多少。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBB1';
const { browser, page } = await launch();

const TOOLBAR_TOP = 735;

async function hoverTooltip(cx, cy, waitMs = 900) {
  await page.mouse.move(cx, cy);
  await page.waitForTimeout(waitMs);
  return page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip-tooltip"],[role="tooltip"]')]
    .filter((e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; })
    .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean));
}
const NOISE = /^(按 ESC 退出|新功能：.+)$/;
const clean = (l) => l.filter((t) => !NOISE.test(t));

async function hoverVerified(pg, rect) {
  const x = Math.round(rect[0] + rect[2] / 2), y = Math.round(rect[1] + rect[3] / 2);
  const owner = await pg.evaluate(([px, py]) => {
    const e = document.elementFromPoint(px, py);
    if (!e) return { kind: 'nothing' };
    const b = e.closest('button,[role="button"]');
    return b ? { kind: 'button', text: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18), aria: b.getAttribute('aria-label') }
      : { kind: 'not-button', tag: e.tagName };
  }, [x, y]);
  if (y > TOOLBAR_TOP || owner.kind !== 'button') {
    return { skipped: `落点 (${x},${y}) ${y > TOOLBAR_TOP ? '压在底栏工具条上' : owner.kind}`, owner };
  }
  return { point: [x, y], owner, tip: clean(await hoverTooltip(x, y)) };
}

const listNodes = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  const t = (n.innerText || '').replace(/\s+/g, ' ').trim();
  return { id: n.getAttribute('data-id') || '?',
    prefix: (n.getAttribute('data-id') || '?').split('-')[0],
    cls: ((/react-flow__node-([a-zA-Z]+)/.exec(n.className || '') || [])[1] || '?'),
    name: (/^[^\s]+(?:\s+\d+)?/.exec(t) || [''])[0].slice(0, 14),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
}));

async function exclusivePoint(pg, nodeId) {
  return pg.evaluate((id) => {
    const t = [...document.querySelectorAll('.react-flow__node')].find((n) => n.getAttribute('data-id') === id);
    if (!t) return { err: 'no node' };
    const r = t.getBoundingClientRect();
    for (let fy = 0.2; fy <= 0.8; fy += 0.15) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === t) return { x, y };
    }
    return { err: 'no exclusive point' };
  }, nodeId);
}

/** 按 `data-id` 前缀选节点 —— 不用 class（智能剪辑也是 node-video）。 */
async function selectByPrefix(pg, prefix, nameKeyword) {
  await pg.keyboard.press('Escape'); await pg.waitForTimeout(700);
  await pg.mouse.click(80, 120); await pg.waitForTimeout(900);
  await fitView(pg); await pg.waitForTimeout(1700);
  for (const cand of (await listNodes()).filter((n) => n.prefix === prefix
    && (!nameKeyword || n.name.includes(nameKeyword)))) {
    const pt = await exclusivePoint(pg, cand.id);
    if (pt.err) { console.log(`  ${cand.id} → ${pt.err}`); continue; }
    await pg.mouse.click(pt.x, pt.y);
    await pg.waitForTimeout(3600);
    const sel = await pg.evaluate((id) => {
      const n = document.querySelector('.react-flow__node.selected');
      return n && n.getAttribute('data-id') === id
        ? { ok: true, id, name: ((n.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] || '').slice(0, 12) }
        : { ok: false, got: n ? n.getAttribute('data-id') : null };
    }, cand.id);
    console.log(`  ${cand.id} 点(${pt.x},${pt.y}) → ${JSON.stringify(sel)}`);
    if (sel.ok) return sel;
    await pg.keyboard.press('Escape'); await pg.waitForTimeout(800);
  }
  return { err: `没选中前缀 ${prefix}` };
}

async function readBars() {
  return page.evaluate(() => {
    const n = document.querySelector('.react-flow__node.selected');
    if (!n) return { err: '没选中节点' };
    const panels = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
      .filter((o) => o.r.width >= 480 && o.r.height >= 100)
      .filter((o) => o.e.querySelectorAll('button,[role="button"]').length >= 3);
    if (!panels.length) return { err: '没找到参数面板' };
    const p = panels.sort((a, b) => (b.r.width * b.r.height) - (a.r.width * a.r.height))[0];
    const fp = (x) => { const s = x.querySelector('svg'); if (!s) return 'nosvg';
      const d = [...s.querySelectorAll('path')].map((z) => z.getAttribute('d') || '').filter(Boolean);
      return d.length ? d.sort((a, b) => b.length - a.length)[0].slice(0, 30) : 'svgonly'; };
    const all = [...p.e.querySelectorAll('button,[role="button"]')].map((x) => { const q = x.getBoundingClientRect();
      return { text: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), aria: x.getAttribute('aria-label'),
        fp: fp(x), disabled: x.disabled === true,
        rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; })
      .filter((b) => b.rect[2] > 0);
    const maxY = Math.max(...all.map((b) => b.rect[1] + b.rect[3]));
    const minY = Math.min(...all.map((b) => b.rect[1]));
    return { panelRect: [Math.round(p.r.x), Math.round(p.r.y), Math.round(p.r.width), Math.round(p.r.height)],
      panelText: (p.e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
      bottomBar: all.filter((b) => maxY - (b.rect[1] + b.rect[3]) <= 8),
      topToolBar: all.filter((b) => b.rect[1] - minY <= 4) };
  });
}

/** 打开参数条上第 idx 枚按钮（假设它是个下拉），读出全部选项，然后 Esc 关掉。 */
async function readDropdown(pg, idx, label) {
  const bar = await readBars();
  if (bar.err) return { err: bar.err };
  const btn = bar.bottomBar[idx];
  if (!btn) return { err: `参数条没有第 ${idx} 枚` };
  const hv = await hoverVerified(pg, btn.rect);
  if (hv.skipped) return { err: `按钮被遮挡：${hv.skipped}`, btn };
  const before = bar.bottomBar.map((b) => b.text);
  await pg.mouse.click(hv.point[0], hv.point[1]);
  await pg.waitForTimeout(2200);
  const opened = await pg.evaluate(() => {
    const cands = [...document.querySelectorAll('[role="listbox"],[role="menu"],.mantine-Select-dropdown,[class*="Popover-dropdown"],[class*="Combobox-dropdown"],[class*="Select-dropdown"]')]
      .filter((e) => { const r = e.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; });
    const pick = cands.sort((a, b) => b.getBoundingClientRect().width * b.getBoundingClientRect().height
      - a.getBoundingClientRect().width * a.getBoundingClientRect().height)[0];
    if (!pick) return { err: '没找到下拉容器' };
    const r = pick.getBoundingClientRect();
    const opts = [...pick.querySelectorAll('[role="option"],[role="menuitem"],li,button,[class*="Select-option"]')]
      .filter((o) => { const q = o.getBoundingClientRect(); return q.width > 0 && q.height > 0; })
      .map((o) => ({ text: (o.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
        ariaSelected: o.getAttribute('aria-selected'), dataSelected: o.getAttribute('data-selected'),
        selected: o.getAttribute('aria-selected') === 'true' || o.getAttribute('data-selected') === 'true',
        disabled: o.getAttribute('aria-disabled') === 'true' || o.disabled === true,
        cursor: getComputedStyle(o).cursor }));
    const seen = new Set();
    return { cls: (pick.className || '').toString().slice(0, 60),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      role: pick.getAttribute('role'), text: (pick.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 500),
      opts: opts.filter((o) => { const k = o.text; if (seen.has(k)) return false; seen.add(k); return true; }) };
  });
  await pg.keyboard.press('Escape'); await pg.waitForTimeout(1200);
  const barAfter = await readBars();
  const after = barAfter.bottomBar ? barAfter.bottomBar.map((b) => b.text) : null;
  return { label, btnText: btn.text, hoverTip: hv.tip, dropdown: opened,
    barUnchanged: after ? JSON.stringify(before) === JSON.stringify(after) : '读不到参数条' };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2000);
  await beginBatch(B, { note: '验证正文里「换模型预设就变亮」这条建议 + 各节点模型/规格下拉选项只读清单' });

  const out = {};

  // ═══ A：验证「换模型 → 预设变亮」
  console.log('--- BB1 A 验证「换模型后预设变亮」 ---');
  const imgSel = await selectByPrefix(page, 'i', '图片节点');
  console.log('选中图片节点:', JSON.stringify(imgSel));
  out.modelSwap = { sel: imgSel };
  if (imgSel.err) { console.log('  ⚠', imgSel.err); }
  else {
    const bar0 = await readBars();
    const modelBtn = bar0.bottomBar[0];
    console.log(`  当前模型按钮: "${modelBtn.text}" [${modelBtn.rect}]`);
    const ORIGINAL = modelBtn.text;
    out.modelSwap.original = ORIGINAL;

    // 预设 15 条当前的 cursor
    const presetState = () => page.evaluate(() => {
      const n = document.querySelector('.react-flow__node.selected');
      if (!n) return { err: '没选中' };
      const pre = [...n.querySelectorAll('button,[role="button"]')].find((b) => b.getAttribute('aria-label') === '预设');
      if (!pre) return { err: '面板里没有预设按钮' };
      const r = pre.getBoundingClientRect();
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    });
    const ps0 = await presetState();
    await page.mouse.click(ps0.rect[0] + ps0.rect[2] / 2, ps0.rect[1] + ps0.rect[3] / 2);
    await page.waitForTimeout(2400); await clearToasts(page);
    const countCursors = () => page.evaluate(() => {
      const items = [...document.querySelectorAll('button')].filter((e) => {
        const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
        return t.length > 3 && t.length < 40 && e.querySelector('svg')
          && /调度故事板|故事板|宫格|推演|质感|光影|全景|九宫格|三视图|设定图|画面推演/.test(t); });
      const seen = new Set(); const rows = [];
      for (const e of items) { const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
        const name = t.split(' ')[0]; if (seen.has(name)) continue; seen.add(name);
        rows.push({ name, cursor: getComputedStyle(e).cursor, disabled: e.disabled === true,
          aria: e.getAttribute('aria-disabled') }); }
      return rows.sort((a, b) => a.name.localeCompare(b.name));
    });
    const c0 = await countCursors();
    console.log(`  换模型前：${c0.length} 条，cursor=pointer 的 ${c0.filter((x) => x.cursor === 'pointer').length} 条`);
    out.modelSwap.before = c0;
    await page.keyboard.press('Escape'); await page.waitForTimeout(1400);

    // 打开模型下拉，读选项
    const md = await readDropdown(page, 0, '图片节点·模型');
    console.log('\n  模型下拉:', JSON.stringify(md.dropdown || md).slice(0, 1400));
    out.modelDropdown = md;

    // 只在明确列出的支持模型里挑一个换（不点「付费/需升级」的那些）
    const opts = (md.dropdown && md.dropdown.opts) || [];
    const target = opts.find((o) => /^Lib Image\b/i.test(o.text) && !/2\.5|Pro|Fast/.test(o.text))
      || opts.find((o) => /General image Pro/i.test(o.text));
    console.log('  支持模型候选:', JSON.stringify(opts.filter((o) => /Lib Image|General image/i.test(o.text))));
    out.modelSwap.target = target || null;
    if (!target) {
      console.log('  ⚠ 下拉里没有 Lib Image / General image Pro，跳过换模型');
    } else {
      // 重新点开下拉并选中它
      const bar1 = await readBars();
      const mb = bar1.bottomBar[0];
      const hv = await hoverVerified(page, mb.rect);
      await page.mouse.click(hv.point[0], hv.point[1]);
      await page.waitForTimeout(2000);
      const optPt = await page.evaluate((t) => {
        const hit = [...document.querySelectorAll('[role="option"],li,button')].filter((e) => {
          const q = e.getBoundingClientRect();
          return q.width > 0 && q.height > 0 && (e.innerText || '').replace(/\s+/g, ' ').trim().startsWith(t); });
        if (!hit.length) return { err: '下拉里找不到以 ' + t + ' 开头的选项',
          sample: [...document.querySelectorAll('[role="option"]')].slice(0, 3).map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30)) };
        // 命中最长的那个 —— 「Lib Image」会同时匹配到 Lib Image 2.5 Pro / 2.5 Fast / 60s
        hit.sort((a, b) => (b.innerText || '').length - (a.innerText || '').length);
        const o = hit[hit.length - 1];
        const r = o.getBoundingClientRect();
        return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
          text: (o.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40), n: hit.length }; }, target.text);
      console.log('  选中目标选项:', JSON.stringify(optPt));
      if (!optPt.err) {
        await page.mouse.click(optPt.x, optPt.y);
        await page.waitForTimeout(3600); await clearToasts(page);
        const bar2 = await readBars();
        const nowModel = bar2.bottomBar[0].text;
        console.log(`  换完模型: "${ORIGINAL}" → "${nowModel}"`);
        out.modelSwap.newModel = nowModel;

        const ps1 = await presetState();
        if (!ps1.err) {
          await page.mouse.click(ps1.rect[0] + ps1.rect[2] / 2, ps1.rect[1] + ps1.rect[3] / 2);
          await page.waitForTimeout(2400); await clearToasts(page);
          const c1 = await countCursors();
          console.log(`  换模型后：${c1.length} 条，cursor=pointer 的 ${c1.filter((x) => x.cursor === 'pointer').length} 条`);
          c1.forEach((x) => console.log(`    ${x.cursor === 'pointer' ? '✅ 可点' : '⛔ 灰  '} ${x.name}`));
          out.modelSwap.after = c1;
          out.modelSwap.becameClickable = c1.filter((x) => x.cursor === 'pointer').map((x) => x.name);
          await shot(page, 'M-174-换模型后预设.png');
          out.shot = 'M-174-换模型后预设.png';
          await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
        }
        // ✅ 换回原模型
        const bar3 = await readBars();
        const mb3 = bar3.bottomBar[0];
        const hv3 = await hoverVerified(page, mb3.rect);
        await page.mouse.click(hv3.point[0], hv3.point[1]);
        await page.waitForTimeout(2000);
        const backPt = await page.evaluate((t) => {
          const hit = [...document.querySelectorAll('[role="option"],li,button')].filter((e) => {
            const q = e.getBoundingClientRect();
            return q.width > 0 && q.height > 0 && (e.innerText || '').replace(/\s+/g, ' ').trim().startsWith(t); });
          if (!hit.length) return { err: '下拉里找不到以 ' + t + ' 开头的选项' };
          const o = hit[0];
          const r = o.getBoundingClientRect();
          return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
            text: (o.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) }; }, ORIGINAL.trim());
        if (!backPt.err) {
          await page.mouse.click(backPt.x, backPt.y);
          await page.waitForTimeout(3400); await clearToasts(page);
          const back = (await readBars()).bottomBar[0].text;
          out.modelSwap.restored = back;
          console.log(`  ✅ 还原模型: "${back}"（原值 "${ORIGINAL.trim()}"）${back.trim() === ORIGINAL.trim() ? ' — 一致' : ' — ⚠ 不一致'}`);
        } else console.log('  ⚠ 还原失败:', backPt.err, '当前下拉里没有原值');
      }
    }
  }

  // ═══ B：各节点模型/规格下拉的选项清单（只读）
  console.log('\n--- BB1 B 下拉选项清单 ---');
  out.dropdowns = {};
  for (const [prefix, kw, label, idxs] of [
    ['i', '图片节点', '图片节点', [0, 1]],
    ['v', '视频节点', '视频节点', [0, 1, 2]],
    ['a', '音频节点', '音频节点', [0, 1]],
    ['t', '文本节点', '文本节点', [0]],
    ['v', '智能剪辑', '智能剪辑', [0, 1]],
  ]) {
    const sel = await selectByPrefix(page, prefix, kw);
    if (sel.err) { console.log(`${label}: ${sel.err}`); out.dropdowns[label] = { err: sel.err }; continue; }
    const bar = await readBars();
    console.log(`\n${label} 参数条 ${bar.bottomBar.length} 枚:`, JSON.stringify(bar.bottomBar.map((b) => b.text)));
    out.dropdowns[label] = { sel, barTexts: bar.bottomBar.map((b) => b.text), items: [] };
    for (const idx of idxs) {
      const d = await readDropdown(page, idx, `${label}·第${idx + 1}枚`);
      const o = (d.dropdown && d.dropdown.opts) || [];
      console.log(`  第${idx + 1}枚 "${d.btnText || ''}" → ${d.dropdown ? (d.dropdown.err || (o.length + ' 个选项: ' + o.map((x) => x.text + (x.selected ? '(当前)' : '') + (x.disabled ? '(禁用)' : '')).join(' | '))) : d.error}`);
      out.dropdowns[label].items.push(d);
    }
  }

  await logStep(B, {
    id: 'BB1-model-dropdown-and-verify', title: '验证「换模型预设就变亮」+ 各节点下拉选项清单',
    target: '上一批正文写了「把模型换成 Lib Image / General image Pro 之一，预设就会变亮」—— '
      + '**那是我推出来的，没验过**。这轮换模型 → 数 15 条的 cursor → **换回原值**。'
      + '模型/规格下拉一律**打开→读→Esc**，只读不改。',
    evidence: out,
    visible_text: JSON.stringify({ swap: out.modelSwap, dropdowns: out.dropdowns }).slice(0, 3500),
    shot: out.shot,
  });
  console.log('\nBB1 完成');
} finally {
  await browser.close();
}
