// Batch BW — 两件事：① 把「选中连线按删除键」这条 📖 真正测掉；
//                  ② 把画布级回收站从 ⛔「找不到」变成「查过了，没有」。
//
// ① 之所以现在才敢测：BV4 已经能让点击点**自证**（沿 path 采样 + elementFromPoint 反查），
//    BV9 又验证了「拖 source → target 能造出线」，BV10–BV13 验证了「点剪刀能断线」。
//    也就是**造线、选中、剪断、复原**四步全都各自验过了，才轮到测删除键。
//    对象是自造边，最坏情况就是它没了 —— 画布正好回到基线。
//
// ② ⛔ 挂了很久的「画布级回收站找不到」。本轮不再找，而是**穷举候选位置逐个记读数**：
//    顶栏画布菜单 / 用户菜单 / 资产抽屉全部页签 / 底栏全部按钮 / 全页文本 / 接口路径。
//    找得到就记下入口；找不到就把「⛔ 找不到」改写成「已查过 N 处，确实没有」——
//    后者对用户更有用：他们不用再找了。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBW';
const { browser, page } = await launch();
const settle = (ms = 900) => page.waitForTimeout(ms);

const edgeIds = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((e) => e.getAttribute('data-id')));
const edgeCount = () => page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
const edgeInfo = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__edge')].map((g) => {
  const p = g.querySelector('path'); let L = 0; try { L = p.getTotalLength(); } catch { L = 0; }
  const ctm = p && p.getScreenCTM(); let mid = null;
  if (ctm && L) { const q = p.getPointAtLength(L / 2); const s = new DOMPoint(q.x, q.y, 0, 1).matrixTransform(ctm); mid = [Math.round(s.x), Math.round(s.y)]; }
  return { id: g.getAttribute('data-id'), aria: g.getAttribute('aria-label'), mid,
    inView: mid && mid[0] > 3 && mid[0] < 1437 && mid[1] > 3 && mid[1] < 786 };
}));
const nodeBox = (id) => page.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, id);
const handleAt = (nodeId, kind) => page.evaluate(({ nodeId, kind }) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nodeId}"]`);
  if (!n) return null;
  const h = [...n.querySelectorAll('.react-flow__handle')].find((x) => kind === 'source' ? /\bsource\b/.test(x.getAttribute('class') || '') : /\btarget\b/.test(x.getAttribute('class') || ''));
  if (!h) return null; const r = h.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y)];
}, { nodeId, kind });
const selState = () => page.evaluate(() => ({
  edges: [...document.querySelectorAll('.react-flow__edge')].filter((e) => e.classList.contains('selected')).map((e) => e.getAttribute('data-id')),
  nodes: [...document.querySelectorAll('.react-flow__node')].filter((e) => e.classList.contains('selected')).map((e) => e.getAttribute('data-id')) }));
const dialogs = () => page.evaluate(() => [...document.querySelectorAll('[role="dialog"],.mantine-Modal-content')]
  .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 4 && r.height > 4; })
  .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160)));

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
  const preview = await page.evaluate(() => document.querySelectorAll('.react-flow__connection, .react-flow__connectionline').length);
  await page.mouse.move(ht[0], ht[1]); await settle(450);
  await page.mouse.up(); await settle(2400);
  const extra = (await edgeIds()).filter((i) => !ids0.includes(i));
  return { ok: extra.length === 1, preview, extra: extra[0] };
};
const selectEdge = async (id) => {
  await page.mouse.move(700, 730); await page.keyboard.press('Escape'); await settle(900);
  const m = (await edgeInfo()).find((x) => x.id === id);
  if (!m || !m.inView) return { ok: false, why: '中点不在视口内' };
  await page.mouse.move(m.mid[0], m.mid[1]); await settle(600);
  await page.mouse.click(m.mid[0], m.mid[1]); await settle(1600);
  const s = await selState();
  return { ok: s.edges.includes(id), mid: m.mid, sel: s };
};
const cutByScissors = async (id) => {
  const m = (await edgeInfo()).find((x) => x.id === id);
  if (!m || !m.inView) return { ok: false, why: '中点不在视口内' };
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
  return { ok: (await edgeCount()) < c0, point: pt, before: c0, after: await edgeCount() };
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await settle(1600);
  await fitView(page); await settle(2200);
  await beginBatch(B, { note: '删除键断线（自造边）+ 回收站穷举排查' });
  const out = {};
  const baseIds = (await edgeInfo()).map((e) => e.id);
  out.base = { ids: baseIds, count: baseIds.length };
  console.log(`═══ 基线：连线 ${baseIds.length} 条 ${JSON.stringify(baseIds)} ═══`);

  // ═══ ① 选中连线 → Delete / Backspace
  console.log('\n═══ ① 选中连线后按删除键 ═══');
  const made = await makeEdge('i-9nlG6HdjK2', 'v-v2hlWY4Br3');
  console.log(`  造边：ok=${made.ok}｜预览线 ${made.preview}｜新增 ${JSON.stringify(made.extra)}`);
  out.makeEdge = made;
  const keys = [];
  if (made.ok) {
    for (const k of ['Delete', 'Backspace']) {
      const s = await selectEdge(made.extra);
      const c0 = await edgeCount();
      console.log(`  选中（读数自证：选中 ${s.ok}｜${JSON.stringify(s.sel || s.why)}）→ 按 ${k}`);
      if (!s.ok) { keys.push({ key: k, executed: false, why: '没选中，**未执行**', sel: s.sel }); continue; }
      await page.keyboard.press(k); await settle(2400);
      const c1 = await edgeCount();
      const dlg = await dialogs();
      keys.push({ key: k, executed: true, selected: true, before: c0, after: c1, delta: c1 - c0, dialogs: dlg });
      console.log(`     连线 ${c0} → ${c1}（${c1 - c0 >= 0 ? '+' : ''}${c1 - c0}）｜弹窗 ${JSON.stringify(dlg)}`);
      if (c1 < c0) { await shot(page, 'M-284-选中连线按删除键之后.png'); break; }
      await page.keyboard.press('Escape'); await settle(700);
    }
    out.keys = keys;
    // 收尾：自造边还在就用剪刀清掉
    if ((await edgeIds()).includes(made.extra)) {
      const cut = await cutByScissors(made.extra);
      console.log(`  收尾：剪刀清理 ${made.extra} → ok=${cut.ok}｜${cut.before} → ${cut.after}`);
      out.cleanup = cut;
    } else { out.cleanup = { note: '删除键已经把它删掉了，用不着清理' }; }
  }
  out.deleteKeys = keys;
  const tested = keys.filter((k) => k.executed);
  const cutIt = tested.filter((k) => k.delta < 0);
  console.log(`  ⭐ 结论：${tested.length === 0 ? '⛔ 没测到（分母 0）' : `${cutIt.length}/${tested.length} 个键真的断了线`}`);

  // ═══ ② 回收站：穷举候选位置
  console.log('\n═══ ② 画布级回收站：穷举排查 ═══');
  const sweep = { text: null, buttons: null, menus: [], drawer: [], api: null };

  // ②a 全页文本
  sweep.text = await page.evaluate(() => {
    const t = (document.body.innerText || '').replace(/\s+/g, ' ');
    const words = ['回收', '垃圾桶', '废纸', '历史', '还原', 'trash', 'recycle', 'bin'];
    return { found: words.filter((w) => t.toLowerCase().includes(w.toLowerCase())),
      sample: t.slice(0, 200) };
  });
  console.log(`  ②a 全页文本里出现的相关词：${JSON.stringify(sweep.text.found)}`);

  // ②b 顶栏 / 底栏 全部按钮点名
  sweep.buttons = await page.evaluate(() => [...document.querySelectorAll('button,[role="button"],[aria-label]')]
    .map((b) => { const r = b.getBoundingClientRect();
      return { tag: b.tagName, label: b.getAttribute('aria-label') || b.getAttribute('title') || (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16),
        rect: [Math.round(r.x), Math.round(r.y)], w: Math.round(r.width) }; })
    .filter((b) => b.w > 0 && b.label));
  console.log(`  ②b 带名字的控件共 ${sweep.buttons.length} 个`);
  console.log(`     名字：${JSON.stringify([...new Set(sweep.buttons.map((b) => b.label))].slice(0, 60))}`);

  // ②c 顶栏两个下拉：画布菜单 + 用户菜单
  for (const [label, sel] of [['画布菜单', null], ['用户菜单', null]]) {
    const b = page.getByText(/^画布 2$/).first();
    void sel; void b; void label;
  }
  const openMenu = async (getter, name) => {
    try {
      const target = await getter();
      if (!target) { sweep.menus.push({ name, ok: false, why: '入口没找到' }); return; }
      await target.click({ timeout: 3000 }); await settle(1600);
      const txt = await page.evaluate(() => {
        const vis = [...document.querySelectorAll('div,ul,section')]
          .filter((d) => { const r = d.getBoundingClientRect(); const s = getComputedStyle(d);
            return r.width > 120 && r.height > 40 && r.y < 400 && s.display !== 'none' && +s.opacity > 0.05; })
          .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim())
          .filter((t) => t && t.length < 300);
        return [...new Set(txt0 => txt0, txt)].slice(-4);
      });
      const items = await page.evaluate(() => [...document.querySelectorAll('[role="menuitem"],[role="option"],li,button')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 4 && r.height > 4 && r.y < 420; })
        .map((e) => (e.getAttribute('aria-label') || e.innerText || '').replace(/\s+/g, ' ').trim())
        .filter((t) => t && t.length < 24));
      sweep.menus.push({ name, ok: true, text: txt, items: [...new Set(items)].slice(0, 30) });
      console.log(`  ②c ${name}：${JSON.stringify([...new Set(items)].slice(0, 30))}`);
      await page.keyboard.press('Escape'); await settle(900);
    } catch (e) { sweep.menus.push({ name, ok: false, why: e.message.slice(0, 60) }); }
  };
  await openMenu(async () => page.getByText(/^画布 2$/).first(), '画布菜单');
  await openMenu(async () => page.locator('[class*="avatar" i], img[alt*="头像" i]').first(), '用户菜单');

  // ②d 资产抽屉的全部页签
  const drawer = [];
  for (const preferX of [0, 700]) {
    const mgr = page.locator('[aria-label="资产管理"]');
    const cnt = await mgr.count();
    for (let i = 0; i < cnt; i += 1) {
      const el = mgr.nth(i);
      const bb = await el.boundingBox();
      if (!bb) continue;
      if (preferX === 0 && bb.x > 400) continue;
      if (preferX === 700 && bb.x < 400) continue;
      await el.click({ timeout: 3000 }).catch(() => {});
      await settle(1800);
      const tabs = await page.evaluate(() => [...document.querySelectorAll('[role="tab"],button,div')]
        .filter((e) => { const r = e.getBoundingClientRect(); const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
          return t && t.length < 12 && r.x < 400 && r.width > 20 && r.width < 200 && r.height > 12 && r.height < 60; })
        .map((e) => ({ t: e.innerText.replace(/\s+/g, ' ').trim(), r: [Math.round(e.getBoundingClientRect().x), Math.round(e.getBoundingClientRect().y)] })));
      const uniq = []; const seen = new Set();
      for (const t of tabs) { if (!seen.has(t.t + t.r[1])) { seen.add(t.t + t.r[1]); uniq.push(t); } }
      drawer.push({ at: [Math.round(bb.x), Math.round(bb.y)], tabs: uniq.slice(0, 14) });
      console.log(`  ②d 抽屉（x=${Math.round(bb.x)}）里的短标签：${JSON.stringify(uniq.slice(0, 14).map((t) => t.t))}`);
      await page.keyboard.press('Escape'); await settle(1000);
      break;
    }
  }
  sweep.drawer = drawer;

  // ②e 接口路径里有没有 trash/recycle/bin
  sweep.api = await page.evaluate(() => (performance.getEntriesByType('resource') || [])
    .map((r) => r.name).filter((n) => /trash|recycle|bin|history|undo/i.test(n))
    .map((n) => n.replace(/^https?:\/\/[^/]+/, '').slice(0, 90)));
  console.log(`  ②e 资源路径里带 trash/recycle/bin/history/undo 的：${JSON.stringify(sweep.api)}`);

  out.sweep = sweep;
  const hitText = sweep.text.found.filter((w) => ['回收', '垃圾桶', 'trash', 'recycle'].includes(w));
  console.log(`\n═══ 本轮结论 ═══`);
  console.log(`  · 删除键断线：${tested.length === 0 ? '⛔ 没测到' : (cutIt.length ? `✅ ${cutIt.map((k) => k.key).join('/')} 能` : '❌ 都不能')}`);
  console.log(`  · 回收站线索：文本命中 ${JSON.stringify(hitText)}｜菜单 ${sweep.menus.length} 个已查｜资源路径 ${sweep.api.length} 条`);

  // ═══ ③ 收尾
  const fin = await edgeIds();
  out.final = { count: fin.length, ids: fin, identical: fin.join(',') === baseIds.join(',') };
  console.log(`\n═══ ③ 收尾：连线 ${fin.length} 条｜与基线逐项相同=${out.final.identical} ═══`);
  await clearToasts(page);

  await logStep(B, {
    id: 'BW-delete-key-and-trash-sweep',
    title: '删除键断线（这次分母不为 0）＋ 回收站穷举排查',
    target: '① 手册此前写「`Delete` / `Backspace` 没用」，但那条读数**不成立** —— '
      + 'BV3 根本没点到线上（点坐标恒为 `(0,0)`），BV4 选中了却没按键。'
      + '本轮用**自证点击点**先选中（读数自证 `selectedEdges` 含目标 id）再按键，'
      + '并给每条试验加 `executed` 字段：**没选中就报「未执行」，不报「无反应」**。'
      + '⛔ 造线、选中、剪断、复原四步都已各自验过，才轮到测删除键；对象是自造边。'
      + '② 把画布级回收站从 ⛔「找不到」变成穷举排查：全页文本 / 带名控件 / 顶栏两个下拉 / 资产抽屉页签 / 资源路径。',
    evidence: out,
    visible_text: JSON.stringify({ 基线: out.base, 造边: out.makeEdge, 删除键: out.keys,
      收尾清理: out.cleanup, 排查: out.sweep, 收尾: out.final }).slice(0, 3400),
  });
  console.log('\nBW 完成');
} catch (e) {
  console.log('⛔ 中止：' + e.message + '\n' + (e.stack || '').split('\n').slice(0, 5).join('\n'));
} finally {
  await browser.close();
}
