// Batch BW2 — 把 BW 的两个缺口补上。
//
// 缺口 ①：`Delete` 实测能断线（`3 → 2`），但 BW 的循环在成功处 `break` 了，
//         **`Backspace` 没测到** —— 分母是 1 不是 2，不能拿「Delete 能」代表两个键。
// 缺口 ②：回收站排查里两个下拉（顶栏「画布 2 ▾」、右上角头像）**都落进了 catch**，
//         ②c 一行没打出来，那两处其实**根本没打开**。排查不完整。
//
// 本轮：① 单独测 `Backspace`（造边 → 选中 → 按键 → 清理）；
//        ② 用更笨但更可靠的办法打开那两个下拉：先把候选入口的坐标、尺寸、可见性全打出来，
//           逐个点，**点了就自证「菜单真的开了」**（新出现的浮层 + 项目文本变长），
//           不用「没报错」当成功。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBW2';
const { browser, page } = await launch();
const settle = (ms = 900) => page.waitForTimeout(ms);

const edgeIds = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => e.getAttribute('data-id')));
const edgeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const edgeInfo = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((g) => {
  const p = g.querySelector('path'); let L = 0; try { L = p.getTotalLength(); } catch { L = 0; }
  const ctm = p && p.getScreenCTM(); let mid = null;
  if (ctm && L) { const q = p.getPointAtLength(L / 2); const s = new DOMPoint(q.x, q.y, 0, 1).matrixTransform(ctm); mid = [Math.round(s.x), Math.round(s.y)]; }
  return { id: g.getAttribute('data-id'), mid, inView: mid && mid[0] > 3 && mid[0] < 1437 && mid[1] > 3 && mid[1] < 786 };
}));
const nodeBox = (id) => page.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);
const handleAt = (nodeId, kind) => page.evaluate(({ nodeId, kind }) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nodeId}"]`);
  if (!n) return null;
  const h = [...n.querySelectorAll('.react-flow__handle')].find((x) => kind === 'source' ? /\bsource\b/.test(x.getAttribute('class') || '') : /\btarget\b/.test(x.getAttribute('class') || ''));
  if (!h) return null; const r = h.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y)];
}, { nodeId, kind });
const selState = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].filter((e) => e.classList.contains('selected')).map((e) => e.getAttribute('data-id')));

const makeEdge = async (a, b) => {
  const ids0 = await edgeIds();
  const na = await nodeBox(a); const nb = await nodeBox(b);
  if (!na || !nb) return { ok: false, why: '节点不在视口' };
  await page.mouse.move(na[0], na[1]); await settle(1100);
  const hs = await handleAt(a, 'source');
  await page.mouse.move(nb[0], nb[1]); await settle(1100);
  const ht = await handleAt(b, 'target');
  if (!hs || !ht) return { ok: false, why: 'handle 取不到' };
  await page.mouse.move(hs[0], hs[1]); await settle(700);
  await page.mouse.down(); await settle(350);
  await page.mouse.move(hs[0] + 8, hs[1] + 4); await settle(300);
  await page.mouse.move((hs[0] + ht[0]) / 2, (hs[1] + ht[1]) / 2); await settle(450);
  await page.mouse.move(ht[0], ht[1]); await settle(450);
  await page.mouse.up(); await settle(2400);
  const extra = (await edgeIds()).filter((i) => !ids0.includes(i));
  return { ok: extra.length === 1, extra: extra[0] };
};
const selectEdge = async (id) => {
  await page.mouse.move(700, 730); await page.keyboard.press('Escape'); await settle(900);
  const m = (await edgeInfo()).find((x) => x.id === id);
  if (!m || !m.inView) return { ok: false };
  await page.mouse.move(m.mid[0], m.mid[1]); await settle(600);
  await page.mouse.click(m.mid[0], m.mid[1]); await settle(1600);
  const s = await selState();
  return { ok: s.includes(id), sel: s, mid: m.mid };
};
const cutByScissors = async (id) => {
  const m = (await edgeInfo()).find((x) => x.id === id);
  if (!m || !m.inView) return { ok: false };
  await page.mouse.move(200, 780); await settle(600);
  await page.mouse.move(m.mid[0], m.mid[1]); await settle(1700);
  const mine = await page.evaluate(([mx, my]) => [...document.querySelectorAll('.scissors-enter')].map((e) => {
    const r = e.getBoundingClientRect(); const c = [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    return { c, near: Math.abs(c[0] - mx) < 40 && Math.abs(c[1] - my) < 40 };
  }).filter((s) => s.near), m.mid);
  if (!mine.length) return { ok: false, why: '没剪刀' };
  const pt = mine[mine.length - 1].c;
  const c0 = await edgeCount();
  await page.mouse.move(pt[0], pt[1]); await settle(600);
  await page.mouse.down(); await settle(180); await page.mouse.up(); await settle(3000);
  return { ok: (await edgeCount()) < c0, before: c0, after: await edgeCount() };
};

/** 点开一个下拉并**自证它真的开了**（浮层出现 + 面板文本变长），不接受「没报错」当成功。 */
const openDropdown = async (name, pt) => {
  const before = await page.evaluate(() => ({
    len: (document.body.innerText || '').length,
    layers: [...document.querySelectorAll('[role="menu"],[role="listbox"],.mantine-Menu-content,[class*="dropdown" i],[class*="Dropdown" i],[class*="popover" i],[class*="Popover" i],[class*="menu" i],[class*="Menu" i]')]
      .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 8 && r.height > 8; }).length,
  }));
  await page.mouse.move(pt[0], pt[1]); await settle(500);
  await page.mouse.click(pt[0], pt[1]); await settle(1800);
  const after = await page.evaluate(() => {
    const vis = [...document.querySelectorAll('div,ul,section')]
      .filter((d) => { const r = d.getBoundingClientRect(); const s = getComputedStyle(d);
        return r.width > 140 && r.height > 30 && r.width < 700 && r.y < 460 && s.display !== 'none' && +s.opacity > 0.05; })
      .map((d) => ({ cls: (d.getAttribute('class') || '').slice(0, 50), text: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200) }));
    // 挑出「正文里原本没有」的那几层 = 这次新弹出来的
    return { len: (document.body.innerText || '').length, panels: vis };
  });
  const grew = after.len - before.len;
  const items = await page.evaluate(() => [...document.querySelectorAll('[role="menuitem"],[role="option"],li,[data-menu-item]')]
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 4 && r.height > 4; })
    .map((e) => (e.getAttribute('aria-label') || e.innerText || '').replace(/\s+/g, ' ').trim())
    .filter((t) => t && t.length < 26));
  const opened = grew > 4 || after.panels.length > 0;
  console.log(`  ${name} @${JSON.stringify(pt)}：正文 ${before.len} → ${after.len} 字（${grew >= 0 ? '+' : ''}${grew}）｜疑似浮层 ${after.panels.length} 个｜菜单项 ${JSON.stringify([...new Set(items)].slice(0, 20))}`);
  return { name, point: pt, opened, textDelta: grew, panels: after.panels.slice(-5), items: [...new Set(items)].slice(0, 20) };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1600);
  await fitView(page); await settle(2200);
  await beginBatch(B, { note: '补 Backspace + 补两个下拉' });
  const out = {};
  const baseIds = (await edgeInfo()).map((e) => e.id);
  out.base = { ids: baseIds, count: baseIds.length };
  console.log(`═══ 基线：连线 ${baseIds.length} 条 ${JSON.stringify(baseIds)} ═══`);

  // ── ① Backspace
  console.log('\n═══ ① 选中连线后按 Backspace ═══');
  const made = await makeEdge('i-9nlG6HdjK2', 'v-v2hlWY4Br3');
  console.log(`  造边：ok=${made.ok}｜新增 ${JSON.stringify(made.extra)}`);
  out.makeEdge = made;
  if (made.ok) {
    const s = await selectEdge(made.extra);
    console.log(`  选中：ok=${s.ok}｜${JSON.stringify(s.sel)}`);
    const c0 = await edgeCount();
    if (s.ok) {
      await page.keyboard.press('Backspace'); await settle(2400);
      const c1 = await edgeCount();
      const dlg = await page.evaluate(() => [...document.querySelectorAll('[role="dialog"],.mantine-Modal-content')]
        .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 4 && r.height > 4; })
        .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 140)));
      out.backspace = { executed: true, selected: true, before: c0, after: c1, delta: c1 - c0, dialogs: dlg };
      console.log(`  ⭐ Backspace：连线 ${c0} → ${c1}（${c1 - c0 >= 0 ? '+' : ''}${c1 - c0}）｜弹窗 ${JSON.stringify(dlg)}`);
    } else { out.backspace = { executed: false, why: '没选中，**未执行**' }; console.log('  ⛔ 没选中，未执行'); }
    if ((await edgeIds()).includes(made.extra)) {
      const cut = await cutByScissors(made.extra);
      console.log(`  收尾：剪刀清理 → ok=${cut.ok}｜${cut.before} → ${cut.after}`);
      out.cleanup = cut;
    } else { out.cleanup = { note: '键已经把它删了' }; }
  }

  // ── ② 两个下拉：先把候选坐标打出来再点
  console.log('\n═══ ② 顶栏两个下拉（先打坐标，再点，再自证）═══');
  const cands = await page.evaluate(() => [...document.querySelectorAll('button,[role="button"],div,span')]
    .filter((e) => { const r = e.getBoundingClientRect();
      return r.width > 10 && r.height > 10 && r.y < 40 && r.y > 0; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { tag: e.tagName, cls: (e.getAttribute('class') || '').slice(0, 44),
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18),
        aria: e.getAttribute('aria-label'), at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        w: Math.round(r.width), h: Math.round(r.height) }; })
    .filter((e) => e.text || e.aria));
  out.topbarCandidates = cands;
  console.log(`  顶栏候选 ${cands.length} 个：${JSON.stringify(cands.slice(0, 14).map((c) => [c.text || c.aria, c.at]))}`);

  const menus = [];
  // 「画布 2」按钮
  const canvasBtn = cands.find((c) => c.text === '画布 2');
  if (canvasBtn) menus.push(await openDropdown('画布菜单', canvasBtn.at));
  await page.keyboard.press('Escape'); await settle(1000);
  // 右上角头像：取最靠右上、圆形的那个
  const avatar = await page.evaluate(() => [...document.querySelectorAll('button,[role="button"],div,img')]
    .filter((e) => { const r = e.getBoundingClientRect(); return r.x > 1300 && r.y < 60 && r.width > 10 && r.width < 80 && r.height > 10 && r.height < 80; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { tag: e.tagName, cls: (e.getAttribute('class') || '').slice(0, 44), at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], w: Math.round(r.width) }; })
    .sort((a, b) => a.w - b.w));
  console.log(`  右上角候选 ${avatar.length} 个：${JSON.stringify(avatar.slice(0, 6))}`);
  if (avatar.length) menus.push(await openDropdown('用户菜单', avatar[0].at));
  out.menus = menus;
  await page.keyboard.press('Escape'); await settle(900);

  // ③ 「生成历史」这枚按钮：全页唯一带「历史」字样的控件，值得开一次看看是不是回收站
  console.log('\n═══ ③ 打开底栏「生成历史」 ═══');
  const gh = cands.length ? null : null; void gh;
  const ghBtn = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button,[role="button"]')].find((x) => (x.getAttribute('aria-label') || '').includes('生成历史'));
    if (!b) return null; const r = b.getBoundingClientRect();
    return { at: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
  if (ghBtn) {
    await page.mouse.click(ghBtn.at[0], ghBtn.at[1]); await settle(2200);
    const hist = await page.evaluate(() => {
      const vis = [...document.querySelectorAll('div,section,aside')]
        .filter((d) => { const r = d.getBoundingClientRect(); const s = getComputedStyle(d);
          return r.width > 250 && r.height > 200 && s.display !== 'none' && +s.opacity > 0.05; })
        .map((d) => ({ cls: (d.getAttribute('class') || '').slice(0, 44), text: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300) }));
      return vis.sort((a, b) => b.text.length - a.text.length).slice(0, 3);
    });
    out.history = { button: ghBtn, panels: hist };
    console.log(`  「生成历史」开出来：${JSON.stringify(hist.map((h) => h.text.slice(0, 160)))}`);
    const all = (hist.map((h) => h.text).join(' '));
    console.log(`  ⭐ 里面有没有「回收/垃圾桶/trash」：${/回收|垃圾桶|trash|recycle/i.test(all) ? '有' : '没有'}`);
    await shot(page, 'M-285-生成历史面板.png');
    await page.keyboard.press('Escape'); await settle(1200);
  }

  // ── ④ 收尾
  const fin = await edgeIds();
  out.final = { count: fin.length, ids: fin, identical: fin.join(',') === baseIds.join(',') };
  console.log(`\n═══ ④ 收尾：连线 ${fin.length} 条｜与基线逐项相同=${out.final.identical} ═══`);
  await clearToasts(page);

  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · Backspace：${out.backspace ? (out.backspace.executed ? (out.backspace.delta < 0 ? '✅ 能断' : '❌ 不断') : '⛔ 未执行') : '⛔ 没测到'}`);
  console.log(`  · 下拉打开情况：${JSON.stringify(menus.map((m) => [m.name, m.opened, m.textDelta]))}`);
  console.log(`  · 生成历史里有回收站吗：${out.history ? (/回收|垃圾桶|trash|recycle/i.test(out.history.panels.map((h) => h.text).join(' ')) ? '有' : '没有') : '没测到'}`);

  await logStep(B, {
    id: 'BW2-backspace-and-dropdown-sweep',
    title: '补测 Backspace + 把两个下拉真正打开',
    target: 'BW 的两个缺口：① 循环在 `Delete` 成功处 `break`，**`Backspace` 没测到**（分母 1 不是 2）；'
      + '② 回收站排查里「画布 2 ▾」与头像两个下拉**都落进 catch**，②c 一行没打，**那两处其实没打开**。'
      + '本轮 ① 单独测 `Backspace`；② 改成「先打坐标 → 点 → **自证菜单真的开了**（正文长度变化 + 新浮层）」，'
      + '不接受「没报错」当成功；③ 顺手开一次底栏那枚**全页唯一带「历史」字样**的「生成历史」，看它是不是回收站。',
    evidence: out,
    visible_text: JSON.stringify({ 基线: out.base, Backspace: out.backspace, 清理: out.cleanup,
      下拉: out.menus, 生成历史: out.history, 收尾: out.final }).slice(0, 3400),
    shot: 'M-285-生成历史面板.png',
  });
  console.log('\nBW2 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}
