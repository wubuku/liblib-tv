// 批次 154-c —— 真点击取证（修掉 154 主脚本的三个自身 bug）
//
// 🔴 修掉的三个自身 bug（**全部是 154 主脚本自己的，不是产品的**）：
//   ① 点扫描解构顺序错：盒格式 `[w,h,x,y]` 却按 `[x,y,w,h]` 解 ⇒「点展开按钮」实际点了
//      (52,42) 的**画布标题**。修法：🔑 **点扫描一律在页面内现取现算，只把 `{x,y}` 两个
//      标量带回 Node 侧**，跨边界的永远是具名标量对象，不再有数组解构。
//   ② `有面积: r.width > 0` 里 `r` 只在 IIFE 内可见 ⇒ `ReferenceError: r is not defined`，
//      Q3 整段没跑。修法：先算盒再用盒派生。
//   ③ 收尾 `JSON.stringify(undefined).slice` 崩。修法：`?? '无'`。
//
// 🔑 154-b（纯只读）已经拿到的地面真相，本轮直接当前提用，不再重复验证：
//   · 建图片节点**之前** `node-toolbar` 实例数 = **0**；
//   · 建完并选中**不必点任何按钮**，`generation-form` 已命中 1、`680×208`、7 个按钮；
//   · 「展开图片生成器」是 40×40 的**折叠钮**，批次 147 已在音频族定案「点了没有任何可见变化」；
//   · 把鼠标移出画布后工具条**不消失**、选中仍为 1 ⇒ 是**选中常驻**不是悬停出现。
//
// 🎯 本轮三问：
//   Q1 点「引用参考」→ `generation-mention-panel` / `-submenu` / listbox
//   Q2 点「添加参考」→ 来源选择器 → 「从画布选择」→ `canvas-source-picker-canvas-frame` / `-mask`
//   Q3 顶栏「生成历史」→ 标题行「积分明细」→ `workspace-project-info-dialog`
//
// ⛔ 红线（写进代码，不靠自觉）：
//   ① 绝不点 `data-testid` 含 `submit` 的元素；绝不点 aria 逐字为 `生成` 的按钮
//   ② 绝不点 aria/文案含「确认」「插入」「立即」「提交」的按钮 —— 找点函数里硬拦
//   ③ 积分每一步都记，收尾必须仍是 805
//   ④ **打开浮层后绝不调 `settle()`**（它会连按 Esc 把刚开的浮层关掉）
//   ⑤ 不按任何字母/数字键；只用 Esc 关自己开的东西
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '154c', 目的: '真点击：@提及面板 / 画布拾取模式 / 积分明细对话框 + 3 张截图' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b154c.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const 禁词 = ['提交', '确认', '插入', '立即', '生成'];

// 🔑 找点 = 页面内现取现算；只回 {x, y} 标量 + 归属证据
const 找点 = (pred) => p.evaluate((pd) => {
  const cands = Array.from(document.querySelectorAll('button,[role=button]')).filter((b) => {
    const a = b.getAttribute('aria-label') || ''; const t = b.getAttribute('data-testid') || '';
    const inBar = !!b.closest('[data-testid="node-toolbar"]');
    if (pd.ariaIncludes && a.indexOf(pd.ariaIncludes) < 0) return false;
    if (pd.ariaRegex && !new RegExp(pd.ariaRegex).test(a)) return false;
    if (pd.字面等于 && a !== pd.字面等于) return false;
    if (pd.testidIncludes && t.indexOf(pd.testidIncludes) < 0) return false;
    if (pd.在工具条内 === true && !inBar) return false;
    if (pd.在工具条内 === false && inBar) return false;
    if (pd.必须非空文字 && !(b.innerText || '').replace(/\s+/g, '').trim()) return false;
    if (pd.排除testid && pd.排除testid.some((x) => t.indexOf(x) >= 0)) return false;
    // ⛔ 红线硬拦
    if (/submit/i.test(t)) return false;
    if (pd.禁词 && pd.禁词.some((w) => a.indexOf(w) >= 0)) return false;
    return true;
  });
  const out = [];
  for (const b of cands) {
    const r = b.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    const cx = Math.round(r.x + r.width / 2); const cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy);
    const btn = h && h.closest('button,[role=button]');
    out.push({ x: cx, y: cy, 宽: Math.round(r.width), 高: Math.round(r.height), 左: Math.round(r.x), 上: Math.round(r.y),
      aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'),
      逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 26),
      中心是自己: btn === b,
      中心是谁: btn ? (btn.getAttribute('aria-label') || btn.getAttribute('data-testid') || btn.tagName.toLowerCase()) : null });
  }
  return { 候选数: cands.length, 点: out };
}, { ...pred, 禁词 });

const 读testid = (ids) => p.evaluate((list) => {
  const 出 = {};
  for (const n of list) {
    const all = Array.from(document.querySelectorAll('[data-testid="' + n + '"]'));
    出[n] = { 命中: all.length, 实例: all.slice(0, 2).map((e) => { const r = e.getBoundingClientRect();
      return { 盒: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10],
        role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
        逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 100),
        祖先链: (() => { const c = []; let n = e; for (let i = 0; i < 7 && n; i++) { n = n.parentElement; if (!n || n === document.body) break;
          c.push(n.tagName.toLowerCase() + (n.getAttribute('data-testid') ? '{' + n.getAttribute('data-testid') + '}' : '') + (typeof n.className === 'string' && n.className ? '.' + n.className.split(/\s+/)[0] : '')); } return c; })() }; }) };
  }
  return 出;
}, ids);

const 清零 = async () => {
  for (let k = 0; k < 4 && (await selCount(p)) > 0; k++) {
    const 空 = await p.evaluate(() => { const 坏 = (x, y) => { const h = document.elementFromPoint(x, y); if (!h) return 1;
      if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]')) return 1;
      if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
      return !(h.classList && h.classList.contains('react-flow__pane')); };
      for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
      return { __err: 'no-free-pane' }; });
    if (空.__err) break; await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1000);
  }
  return selCount(p);
};

const 关一个 = async (id) => {
  await 清零();
  const 前 = await idsOf(p);
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
  if (落.__err) return { id, __err: 'no-point' };
  const 归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
    const n = h && h.closest('.react-flow__node'); return { 对: !!(n && n.getAttribute('data-id') === i) }; }, [落.x, 落.y, id]);
  if (!归属.对) return { id, __err: 'wrong-target' };
  await p.mouse.click(落.x, 落.y, { button: 'right' }); await p.waitForTimeout(1800);
  const del = await p.evaluate(() => {
    const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
      .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
    if (!els.length) return { __err: 'no-delete-item' };
    const e = els[0]; const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
      for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
        const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() }; }
    return { __err: 'no-point' };
  });
  if (del.__err) return { id, __err: del.__err };
  await p.mouse.click(del.x, del.y); await p.waitForTimeout(2500); await settle(p, R);
  const 后 = await idsOf(p);
  return { id, 消失: 前.filter((x) => !后.includes(x)), 删除项逐字: del.逐字 };
};

const 五项 = ['generation-form', 'generation-mention-panel', 'generation-mention-submenu',
  'generation-source-picker-chip', 'generation-source-picker-close'];
const 拾取2 = ['canvas-source-picker-canvas-frame', 'canvas-source-picker-canvas-mask'];

const { b, p } = await openCanvas();
const R = readers(p);
let 基线canvas = null;
try {
  await keyGuard(p); await settle(p, R);
  await setZoom(p, 60); await p.waitForTimeout(1200);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(),
    实测scale: await p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); return e ? e.style.transform : null; }),
    积分: await R.credits(), 组数: await 组数(p), 选中: await selCount(p) };
  基线canvas = await canvasPos(p);

  // ================= Q1 + Q2：都在这个新节点上做 =================
  const 建 = await 建N个(p, '图片', 1, null, (await idsOf(p)).length);
  rec.建 = { ids: 建.ids, 护栏: 建.护栏, 护栏全过: 建.护栏.every((h) => h.通过) };
  落盘();
  if (建.ids && 建.ids.length) {
    const id = 建.ids[0];
    rec.选中数 = await selCount(p);
    const 节点盒 = await p.evaluate((i) => { const n = document.querySelector('.react-flow__node[data-id="' + i + '"]'); const r = n.getBoundingClientRect();
      return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }, id);
    await p.mouse.move(节点盒.cx, 节点盒.cy); await p.waitForTimeout(1400);
    rec.默认态五项 = await 读testid(五项);

    // ---------- Q1：「引用参考」→ @提及面板 ----------
    // 面板内那个是 32×32，提示词内那个是 24×24；先点 32×32（不在提示词 combobox 内的那个）
    rec.Q1_候选 = await 找点({ ariaIncludes: '引用参考', 在工具条内: true });
    const 大 = (rec.Q1_候选.点 || []).filter((z) => z.宽 * z.高 >= 32 * 32);
    const 选点 = 大[0] || (rec.Q1_候选.点 || [])[0];
    rec.Q1_用的点 = 选点 || null;
    if (选点 && 选点.中心是自己) {
      await p.mouse.click(选点.x, 选点.y);
      await p.waitForTimeout(2000); // 🔑 不调 settle
      rec.Q1_提及 = await 读testid(五项);
      rec.列表框 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=listbox]')).map((e) => {
        const r = e.getBoundingClientRect();
        return { aria: e.getAttribute('aria-label'), 盒: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)],
          子项: Array.from(e.querySelectorAll('[role=option],[role=menuitem]')).map((o) => (o.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18)).slice(0, 10),
          子项数: e.querySelectorAll('[role=option],[role=menuitem]').length }; }));
      rec.积分_提及后 = await R.credits();
      const 拍前 = { 面板命中: rec.Q1_提及['generation-mention-panel'].命中,
        面板盒: (rec.Q1_提及['generation-mention-panel'].实例[0] || {}).盒,
        面板祖先: (rec.Q1_提及['generation-mention-panel'].实例[0] || {}).祖先链,
        提交钮: await p.evaluate(() => document.querySelectorAll('[data-testid*="submit"]').length),
        积分: await R.credits() };
      rec.拍前断言1 = 拍前;
      断言('① 🔑 `generation-mention-panel` 命中 ≥ 1 且有面积', 拍前.面板命中 >= 1 && !!拍前.面板盒 && 拍前.面板盒[0] > 0, 拍前);
      断言('② 打开提及面板期间**页面上没有任何 submit 元素被我点过**（只记存在）', true, { 页面submit元素数: 拍前.提交钮 });
      断言('③ 打开提及面板**不扣积分**（仍 805）', String(拍前.积分).indexOf('805') >= 0, { 积分: 拍前.积分 });
      if (拍前.面板命中 >= 1) {
        await p.screenshot({ path: new URL('./54-generation-mention-panel.png', 出图).pathname });
        rec.截图1 = 'screenshots/54-generation-mention-panel.png';
      }
      await p.keyboard.press('Escape'); await p.waitForTimeout(1400);
      rec.Q1_Esc一次后 = await 读testid(五项);
      await p.keyboard.press('Escape'); await p.waitForTimeout(1400);
      rec.Q1_Esc两次后 = await 读testid(五项);
      落盘();
    }

    // ---------- Q2：「添加参考」→ 来源选择器 → 「从画布选择」 ----------
    rec.Q2_候选 = await 找点({ ariaIncludes: '添加参考', 在工具条内: true });
    const 添 = (rec.Q2_候选.点 || [])[0];
    rec.Q2_用的点 = 添 || null;
    if (添 && 添.中心是自己) {
      await p.mouse.click(添.x, 添.y); await p.waitForTimeout(2000);
      rec.Q2_打开后 = await 读testid([...五项, ...拾取2]);
      rec.Q2_可见按钮 = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
        .map((b) => { const r = b.getBoundingClientRect(); return { aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'),
          逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), w: Math.round(r.width), h: Math.round(r.height) }; })
        .filter((z) => z.w > 0 && z.h > 0 && z.aria).slice(0, 60));
      落盘();
      // 来源选择器里找「从画布选择」
      rec.Q2_从画布 = await 找点({ ariaIncludes: '从画布选择' });
      const 从 = (rec.Q2_从画布.点 || [])[0];
      rec.Q2_从画布用的点 = 从 || null;
      if (从 && 从.中心是自己) {
        await p.mouse.click(从.x, 从.y); await p.waitForTimeout(2200);
        rec.Q2_拾取 = await 读testid([...五项, ...拾取2]);
        const f = rec.Q2_拾取['canvas-source-picker-canvas-frame'];
        const m = rec.Q2_拾取['canvas-source-picker-canvas-mask'];
        const c = rec.Q2_拾取['generation-source-picker-chip'];
        const 拍前2 = { frame: f.命中, frame盒: (f.实例[0] || {}).盒, mask: m.命中, mask盒: (m.实例[0] || {}).盒,
          chip: c.命中, chip盒: (c.实例[0] || {}).盒, chip逐字: (c.实例[0] || {}).逐字, 积分: await R.credits() };
        rec.拍前断言2 = 拍前2;
        断言('④ 🔑 `canvas-source-picker-canvas-frame` 与 `-mask` 各命中 ≥ 1', 拍前2.frame >= 1 && 拍前2.mask >= 1, 拍前2);
        断言('⑤ `generation-source-picker-chip` 命中 ≥ 1 且有面积，且不扣积分', 拍前2.chip >= 1 && !!拍前2.chip盒 && 拍前2.chip盒[0] > 0 && String(拍前2.积分).indexOf('805') >= 0, 拍前2);
        if (拍前2.frame >= 1) {
          await p.screenshot({ path: new URL('./55-source-picker-canvas-mode.png', 出图).pathname });
          rec.截图2 = 'screenshots/55-source-picker-canvas-mode.png';
        }
        // 取消而不是选
        rec.Q2_取消候选 = await 找点({ 排除testid: ['submit'] });
        const 取 = (rec.Q2_取消候选.点 || []).filter((z) => /取消/.test(z.aria || ''));
        rec.Q2_取消用的点 = 取[0] || null;
        if (取[0] && 取[0].中心是自己) { await p.mouse.click(取[0].x, 取[0].y); await p.waitForTimeout(1600); }
        rec.Q2_取消后 = await 读testid([...五项, ...拾取2]);
        落盘();
      }
    }
    for (let k = 0; k < 5; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
    rec.全关后 = await 读testid([...五项, ...拾取2]);
    rec.删除 = [];
    for (const x of 建.ids) rec.删除.push(await 关一个(x));
    落盘();
  }

  // ================= Q3：生成历史面板 → 积分明细 =================
  {
    await 清零();
    // 🔴 修 bug ②：先算盒，再用盒派生「有面积」，不要引用 IIFE 里的 r
    rec.历史启动器 = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]')).map((b) => {
      const r = b.getBoundingClientRect();
      return { aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'),
        逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
        expanded: b.getAttribute('aria-expanded'),
        cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), 宽: Math.round(r.width), 高: Math.round(r.height) };
    }).filter((z) => z.宽 > 0 && z.高 > 0 && /历史|history/i.test((z.aria || '') + (z.逐字 || ''))));
    const 启 = (rec.历史启动器 || [])[0];
    if (启) {
      const ok = await p.evaluate((c) => { const h = document.elementFromPoint(c.cx, c.cy); const b = h && h.closest('button,[role=button]');
        return { 中心是自己: b === document.querySelector('button[aria-label="' + (c.aria || '') + '"]') || (b && (b.getAttribute('aria-label') || '') === (c.aria || '')) }; }, 启);
      rec.历史落点校验 = ok;
      if (ok.中心是自己) {
        await p.mouse.click(启.cx, 启.cy); await p.waitForTimeout(2000);
        rec.历史面板 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-feature-panel"]');
          const r = e && e.getBoundingClientRect();
          return { 命中: !!e, 盒: r && [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)],
            aria: e && e.getAttribute('aria'), 逐字: e && (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 140),
            按钮: e ? Array.from(e.querySelectorAll('button,[role=tab]')).map((b) => { const q = b.getBoundingClientRect();
              return { 逐字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12), aria: b.getAttribute('aria-label'),
                selected: b.getAttribute('aria-selected'), 宽: Math.round(q.width), 高: Math.round(q.height),
                cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) }; }).filter((z) => z.宽 > 0) : [] }; });
        落盘();
        const 积 = (rec.历史面板.按钮 || []).find((z) => z.逐字 === '积分明细');
        rec.积分明细钮 = 积 || null;
        if (积) {
          const ok2 = await p.evaluate((c) => { const h = document.elementFromPoint(c.cx, c.cy); const b = h && h.closest('button,[role=button]');
            return { 中心是自己: !!(b && (b.innerText || '').replace(/\s+/g, '').trim() === '积分明细'), 命中逐字: b ? (b.innerText || '').replace(/\s+/g, ' ').trim() : null }; }, 积);
          rec.积分落点校验 = ok2;
          if (ok2.中心是自己) {
            await p.mouse.click(积.cx, 积.cy); await p.waitForTimeout(2200);
            rec.Q3 = await 读testid(['workspace-project-info-dialog']);
            const d = (rec.Q3['workspace-project-info-dialog'].实例 || [])[0];
            const 拍前3 = { 命中: rec.Q3['workspace-project-info-dialog'].命中, 盒: d && d.盒, role: d && d.role,
              aria: d && d.aria, 逐字: d && d.逐字, 祖先链: d && d.祖先链, 积分: await R.credits() };
            rec.拍前断言3 = 拍前3;
            断言('⑥ 🔑 `workspace-project-info-dialog` 命中 ≥ 1 且有面积', 拍前3.命中 >= 1 && !!拍前3.盒 && 拍前3.盒[0] > 0, 拍前3);
            断言('⑦ 打开积分明细**不扣积分**（仍 805）', String(拍前3.积分).indexOf('805') >= 0, { 积分: 拍前3.积分 });
            if (拍前3.命中 >= 1) {
              await p.screenshot({ path: new URL('./56-workspace-project-info-dialog.png', 出图).pathname });
              rec.截图3 = 'screenshots/56-workspace-project-info-dialog.png';
            }
            rec.逐次Esc = [];
            for (let i = 1; i <= 3; i++) {
              await p.keyboard.press('Escape'); await p.waitForTimeout(1400);
              rec.逐次Esc.push({ 第几次: i,
                对话框: await p.evaluate(() => document.querySelectorAll('[data-testid="workspace-project-info-dialog"]').length),
                历史面板: await p.evaluate(() => document.querySelectorAll('[data-testid="canvas-feature-panel"]').length),
                浮层: await R.overlays() });
            }
            落盘();
          }
        }
      }
    }
  }
  for (let k = 0; k < 4; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
  await 清零();
  await setZoom(p, 60); await p.waitForTimeout(1400);
  const 末 = await idsOf(p); const 末c = await canvasPos(p);
  rec.收尾检查 = { 节点数: 末.length,
    位移节点: 基线canvas ? Object.keys(基线canvas).filter((k) => 末c[k] && (末c[k][0] !== 基线canvas[k][0] || 末c[k][1] !== 基线canvas[k][1])) : null };
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

await settle(p, R);
const mm = await R.minimap();
if (!mm || mm.ariaPressed !== 'true') { const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3); if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); } }
rec.小地图 = await R.minimap();
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), 积分: await R.credits(), 组数: await 组数(p),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length),
  残留自建: (await idsOf(p)).filter((x) => ((rec.建 || {}).ids || []).includes(x)) };
落盘();

console.log('起点', JSON.stringify(rec.起点));
console.log('\n默认态五项命中', JSON.stringify(Object.fromEntries(Object.entries(rec.默认态五项 || {}).map(([k, v]) => [k, v.命中]))));
console.log('\nQ1 候选', JSON.stringify(rec.Q1_候选));
console.log('Q1 用的点', JSON.stringify(rec.Q1_用的点));
console.log('Q1 提及面板', JSON.stringify((rec.Q1_提及 || {})['generation-mention-panel'], null, 1));
console.log('Q1 submenu', JSON.stringify((rec.Q1_提及 || {})['generation-mention-submenu']));
console.log('列表框', JSON.stringify(rec.列表框));
console.log('Esc一次后 mention-panel 命中', ((rec.Q1_Esc一次后 || {})['generation-mention-panel'] || {}).命中);
console.log('Esc两次后 mention-panel 命中', ((rec.Q1_Esc两次后 || {})['generation-mention-panel'] || {}).命中);
console.log('\nQ2 候选', JSON.stringify(rec.Q2_候选));
console.log('Q2 打开后拾取2命中', JSON.stringify(Object.fromEntries(Object.entries(rec.Q2_打开后 || {}).filter(([k]) => k.indexOf('canvas-source') === 0).map(([k, v]) => [k, v.命中]))));
console.log('Q2 可见按钮(前40)', JSON.stringify((rec.Q2_可见按钮 || []).slice(0, 40)));
console.log('Q2 从画布选择', JSON.stringify(rec.Q2_从画布));
console.log('Q2 拾取', JSON.stringify((rec.Q2_拾取 || {})['canvas-source-picker-canvas-frame'], null, 1), JSON.stringify((rec.Q2_拾取 || {})['canvas-source-picker-canvas-mask']));
console.log('Q2 chip', JSON.stringify((rec.Q2_拾取 || {})['generation-source-picker-chip'], null, 1));
console.log('Q2 取消后 frame/mask 命中', ((rec.Q2_取消后 || {})['canvas-source-picker-canvas-frame'] || {}).命中, ((rec.Q2_取消后 || {})['canvas-source-picker-canvas-mask'] || {}).命中);
console.log('\nQ3 历史启动器', JSON.stringify(rec.历史启动器));
console.log('Q3 历史面板', JSON.stringify(rec.历史面板));
console.log('Q3 积分明细钮', JSON.stringify(rec.积分明细钮));
console.log('Q3 dialog', JSON.stringify(rec.Q3, null, 1));
console.log('逐次Esc', JSON.stringify(rec.逐次Esc));
console.log('\n删除', JSON.stringify((rec.删除 || []).map((d) => d.消失 || d.__err)));
console.log('收尾检查', JSON.stringify(rec.收尾检查));
console.log('收尾', JSON.stringify(rec.收尾), '| 小地图', JSON.stringify(rec.小地图), '| 异常', rec.异常 || '无');
console.log('截图', JSON.stringify([rec.截图1, rec.截图2, rec.截图3]));

断言('⑧ 建-删护栏全过 + 消失集合恰好 {SELF}', rec.建 && rec.建.护栏全过 === true && (rec.删除 || []).length > 0 && (rec.删除 || []).every((d) => d.消失 && d.消失.length === 1), { 护栏: rec.建 && rec.建.护栏全过, 删除: (rec.删除 || []).map((d) => d.消失 || d.__err) });
断言('⑨ 🔑 收尾积分**仍是 805**（全程没点任何生成/确认/扣费按钮）', String((rec.收尾 || {}).积分).indexOf('805') >= 0, { 积分: (rec.收尾 || {}).积分 });
if (rec.收尾检查 && rec.收尾检查.位移节点) 断言('⑩ 其余节点零位移', rec.收尾检查.位移节点.length === 0, rec.收尾检查);
rec.断言全过 = 断言过; 落盘();
await b.close();
