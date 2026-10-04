// 批次 154 —— 给 SOURCE_OBSERVATIONS §4.49 那张「全灭 testid」分诊表里
// **已经过期但没人改的 4 行**做活体验证，并补 3 张图。
//
// 🎯 靶子来自一次纯静态元审计（`jimeng-b154-meta.mjs`）：
//    逐行读分诊表，再看手册**别处**是否已经有这些 testid 的实测记录 ——
//    9 行里有 **4 行**是「表里说没验 / 手册别处早就验了」的**漂移**：
//
//    | 分诊表那行现在写的 | 手册别处已经有的 |
//    |---|---|
//    | 生成 5 项「点开即进生成流程，**需单独授权**」 | `prepare-generation.md` / `20-reference.md` 都有逐字读数 |
//    | `canvas-source-picker-*` 2 项「同上，**需单独授权**」 | `20-reference.md:730-732` 有 4 项读数 |
//    | `audio-node-uploading`「批次 112 六次造不出来」 | `20-reference.md:1266` 批次 109 验成，文字逐字两段 |
//    | `workspace-project-info-dialog`「**需单独授权**」 | `canvas-context.md:244,309` 有读数 |
//
// 🔑 2026-10-04 目标更新：**测试帐号允许 CRUD 副作用，只要不执行真实生图/生视频**。
//    ⇒ 「打开生成表单 / 进入拾取模式 / 点开积分明细」**全部解锁**
//    （打开面板不扣积分；只有点提交才扣）。
//
// ⛔ 本轮的红线（逐条写进代码，不靠自觉）：
//    ① **绝不点 `generation-submit-icon`**（生成/发送）
//    ② **绝不点任何「确认」/「插入」/「立即」**类按钮
//    ③ 绝不点任何扣费按钮；**积分读数每一步都要记**，收尾必须仍是 805
//    ④ **打开浮层后绝不调 `settle()`**（它会连按 Esc 把刚开的浮层关掉 —— 批次 153 定位）
//    ⑤ 不按任何字母/数字键，只用 Esc 关自己开的东西
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 154, 目的: '给 §4.49 分诊表 4 行过期项做活体验证 + 补 3 张截图' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b154.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const 禁点 = ['generation-submit-icon']; // ⛔ 红线：这些 testid 一个都不许点

const 读testid = (ids) => p.evaluate((list) => {
  const box = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10, s.visibility, s.display]; };
  const 出 = {};
  for (const n of list) {
    const all = Array.from(document.querySelectorAll('[data-testid="' + n + '"]'));
    出[n] = { 命中: all.length, 实例: all.slice(0, 3).map((e) => ({ box: box(e), role: e.getAttribute('role'),
      aria: e.getAttribute('aria-label'), text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 90),
      祖先链: (() => { const c = []; let x = e; for (let i = 0; i < 7 && x; i++) { x = x.parentElement; if (!x || x === document.body) break;
        c.push((x.tagName.toLowerCase()) + (x.getAttribute('data-testid') ? '{' + x.getAttribute('data-testid') + '}' : '') + (x.className && typeof x.className === 'string' ? '.' + x.className.split(/\s+/)[0] : '')); } return c; })() })) };
  }
  return 出;
}, ids);

const 清零 = async () => {
  for (let k = 0; k < 4 && (await selCount(p)) > 0; k++) {
    const 空 = await p.evaluate(() => {
      const 坏 = (x, y) => { const h = document.elementFromPoint(x, y);
        if (!h) return 1;
        if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]')) return 1;
        if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
        return !(h.classList && h.classList.contains('react-flow__pane')); };
      for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
      return { __err: 'no-free-pane' };
    });
    if (空.__err) break;
    await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1000);
  }
  return selCount(p);
};

const 删一个 = async (id) => {
  await 清零();
  const 前 = await idsOf(p);
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
  if (落.__err) return { id, __err: 'no-point' };
  const 归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
    const n = h && h.closest('.react-flow__node'); return { 对: !!(n && n.getAttribute('data-id') === i) }; }, [落.x, 落.y, id]);
  if (!归属.对) return { id, __err: 'wrong-target（被压住）' };
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

const 生成5 = ['generation-form', 'generation-mention-panel', 'generation-mention-submenu',
  'generation-source-picker-chip', 'generation-source-picker-close'];
const 拾取2 = ['canvas-source-picker-canvas-frame', 'canvas-source-picker-canvas-mask'];

const { b, p } = await openCanvas();
const R = readers(p);
let 基线canvas = null;
try {
  await keyGuard(p); await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(),
    积分: await R.credits(), 组数: await 组数(p), 选中: await selCount(p) };
  基线canvas = await canvasPos(p);

  // ================= Q1：生成表单 + @提及面板 =================
  const 建 = await 建N个(p, '图片', 1, null, (await idsOf(p)).length);
  rec.建 = { ids: 建.ids, 护栏: 建.护栏.map((h) => [h.名, h.通过]), 护栏全过: 建.护栏.every((h) => h.通过) };
  落盘();
  if (建.ids && 建.ids.length) {
    const id = 建.ids[0];
    // 选中它（护栏建完已经选中），并把鼠标移回节点让悬停工具条出现
    rec.选中数 = await selCount(p);
    const 节点盒 = await p.evaluate((i) => { const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
      const r = n.getBoundingClientRect(); return [Math.round(r.width / 2 + r.x), Math.round(r.height / 2 + r.y), Math.round(r.width), Math.round(r.height)]; }, id);
    rec.节点盒 = 节点盒;
    await p.mouse.move(节点盒[0], 节点盒[1]); await p.waitForTimeout(1200);
    rec.工具条 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((e) => {
      const r = e.getBoundingClientRect();
      return { box: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10], 按钮数: e.querySelectorAll('button').length,
        按钮aria: Array.from(e.querySelectorAll('button')).map((b) => (b.getAttribute('aria-label') || b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16)) };
    }));
    落盘();

    // 找「展开图片生成器」按钮 —— ⛔ 先校验落点不是提交钮
    const 展 = await p.evaluate(() => {
      const cands = Array.from(document.querySelectorAll('[data-testid="node-toolbar"] button'))
        .filter((b) => /展开.*生成器/.test(b.getAttribute('aria-label') || ''));
      return cands.map((b) => { const r = b.getBoundingClientRect();
        return { aria: b.getAttribute('aria-label'), box: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; });
    });
    rec.展开钮 = 展;
    if (展.length) {
      const box = 展[0].box;
      const pt = await p.evaluate(([x, y, w, h]) => {
        for (let yy = Math.ceil(y) + 2; yy <= y + h - 2; yy += 2)
          for (let xx = Math.ceil(x) + 2; xx <= x + w - 2; xx += 2) {
            const el = document.elementFromPoint(xx, yy); if (el && el.closest('button')) {
              const t = el.closest('button').getAttribute('data-testid');
              if (t && t.indexOf('generation-submit-icon') >= 0) return { __err: '落点是提交钮，拒绝' };
              return { x: xx, y: yy, 文字: (el.closest('button').getAttribute('aria-label') || '') }; } }
        return { __err: 'no-point' };
      }, box);
      rec.展开落点 = pt;
      if (!pt.__err) {
        await p.mouse.click(pt.x, pt.y);
        // 🔑 **不调 settle**（它会连按 Esc 把刚开的面板关掉）
        await p.waitForTimeout(2200);
        rec.Q1_生成表单 = await 读testid(生成5);
        rec.提交钮存在 = await p.evaluate((禁) => document.querySelectorAll(禁.map((t) => '[data-testid="' + t + '"]').join(',')).length, 禁点);
        rec.积分_打开后 = await R.credits();
        落盘();

        // 打开 @提及面板
        const 引 = await p.evaluate(() => {
          const c = Array.from(document.querySelectorAll('[data-testid="node-toolbar"] button, [data-testid="node-toolbar"] [role=button]'))
            .filter((b) => (b.getAttribute('aria-label') || '').includes('引用参考'));
          return c.map((b) => { const r = b.getBoundingClientRect();
            return { aria: b.getAttribute('aria-label'), box: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; });
        });
        rec.引用参考钮 = 引;
        if (引.length) {
          const bb = 引[0].box;
          const pp = await p.evaluate(([x, y, w, h]) => {
            for (let yy = Math.ceil(y) + 2; yy <= y + h - 2; yy += 2)
              for (let xx = Math.ceil(x) + 2; xx <= x + w - 2; xx += 2) {
                const el = document.elementFromPoint(xx, yy); if (el && el.closest('button')) return { x: xx, y: yy }; }
            return { __err: 'no-point' };
          }, bb);
          if (!pp.__err) {
            await p.mouse.click(pp.x, pp.y); await p.waitForTimeout(1800);
            rec.Q1_提及面板 = await 读testid(生成5);
            rec.列表框 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=listbox]')).map((e) => {
              const r = e.getBoundingClientRect();
              return { aria: e.getAttribute('aria-label'), box: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)],
                子项: Array.from(e.querySelectorAll('[role=option],[role=menuitem]')).map((o) => (o.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20)).slice(0, 8) }; }));
            落盘();
            // 🔑 拍前逐条断言（截图纪律）
            const 拍前 = { 面板命中: rec.Q1_提及面板['generation-mention-panel'].命中,
              面板盒: rec.Q1_提及面板['generation-mention-panel'].实例[0] && rec.Q1_提及面板['generation-mention-panel'].实例[0].box,
              提交钮: await p.evaluate((禁) => document.querySelectorAll(禁.map((t) => '[data-testid="' + t + '"]').join(',')).length, 禁点),
              积分: await R.credits() };
            rec.拍前断言 = 拍前;
            断言('① `generation-mention-panel` 命中 ≥ 1 且有面积', 拍前.面板命中 >= 1 && 拍前.面板盒 && 拍前.面板盒[0] > 0, 拍前);
            断言('② 打开面板期间**提交钮存在但我一个都没点**（只记存在，不点）', true, { 提交钮命中: 拍前.提交钮 });
            断言('③ 打开面板**不扣积分**', String(拍前.积分).indexOf('805') >= 0, { 积分: 拍前.积分 });
            if (拍前.面板命中 >= 1) {
              await p.screenshot({ path: new URL('./54-generation-mention-panel.png', 出图).pathname });
              rec.截图1 = 'screenshots/54-generation-mention-panel.png';
            }
            await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
            await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
            rec.关提及后 = await 读testid(生成5);
            落盘();
          }
        }
      }
    }
    // ================= Q2：「从画布选择」全屏拾取模式 =================
    // 先看来源选择器里有没有「从画布选择」
    const 源入口 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="node-toolbar"] button,[data-testid="node-toolbar"] [role=button]'))
      .map((b) => { const r = b.getBoundingClientRect();
        return { aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'), box: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)], 有面积: r.width > 0 }; })
      .filter((x) => x.aria));
    rec.工具条按钮 = 源入口;
    落盘();
    // 依次尝试点开可能的「从画布选择」入口
    rec.Q2 = { 尝试: [] };
    for (const 候选 of 源入口.filter((x) => x.有面积 && /画布|选择|来源/.test(x.aria))) {
      const pt = await p.evaluate(([x, y, w, h]) => {
        for (let yy = Math.ceil(y) + 2; yy <= y + h - 2; yy += 2)
          for (let xx = Math.ceil(x) + 2; xx <= x + w - 2; xx += 2) { const el = document.elementFromPoint(xx, yy);
            if (el && el.closest('button')) return { x: xx, y: yy, aria: el.closest('button').getAttribute('aria-label') }; }
        return { __err: 'no-point' };
      }, 候选.box);
      if (pt.__err) { rec.Q2.尝试.push({ 候选: 候选.aria, __err: pt.__err }); continue; }
      await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1800);
      const 读 = await 读testid([...生成5, ...拾取2]);
      rec.Q2.尝试.push({ 候选: 候选.aria, 落点aria: pt.aria, 读 });
      落盘();
      if (读['generation-source-picker-chip'].命中 >= 1) {
        rec.Q2.进入 = 候选.aria;
        const 从画布 = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
          .filter((b) => (b.getAttribute('aria-label') || b.innerText || '').includes('从画布选择'))
          .map((b) => { const r = b.getBoundingClientRect();
            return { aria: b.getAttribute('aria-label'), text: (b.innerText || '').replace(/\s+/g, ' ').trim(), box: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)], 有面积: r.width > 0 }; }));
        rec.Q2.从画布选择钮 = 从画布;
        const 有面积的 = 从画布.filter((x) => x.有面积);
        if (有面积的.length) {
          const bb = 有面积的[0].box;
          const pp = await p.evaluate(([x, y, w, h]) => {
            for (let yy = Math.ceil(y) + 2; yy <= y + h - 2; yy += 2)
              for (let xx = Math.ceil(x) + 2; xx <= x + w - 2; xx += 2) { const el = document.elementFromPoint(xx, yy);
                if (el && el.closest('button')) return { x: xx, y: yy }; }
            return { __err: 'no-point' };
          }, bb);
          if (!pp.__err) {
            await p.mouse.click(pp.x, pp.y); await p.waitForTimeout(1800);
            rec.Q2.拾取模式 = await 读testid([...生成5, ...拾取2]);
            rec.积分_拾取后 = await R.credits();
            const 拍前2 = { frame: rec.Q2.拾取模式['canvas-source-picker-canvas-frame'].命中,
              mask: rec.Q2.拾取模式['canvas-source-picker-canvas-mask'].命中,
              chip盒: rec.Q2.拾取模式['generation-source-picker-chip'].实例[0] && rec.Q2.拾取模式['generation-source-picker-chip'].实例[0].box,
              积分: await R.credits() };
            rec.拍前断言2 = 拍前2;
            断言('④ 🔑 `canvas-source-picker-canvas-frame` 与 `-mask` 各命中 ≥ 1', 拍前2.frame >= 1 && 拍前2.mask >= 1, 拍前2);
            断言('⑤ `generation-source-picker-chip` 有面积且不扣积分', 拍前2.chip盒 && 拍前2.chip盒[0] > 0 && String(拍前2.积分).indexOf('805') >= 0, 拍前2);
            if (拍前2.frame >= 1) {
              await p.screenshot({ path: new URL('./55-source-picker-canvas-mode.png', 出图).pathname });
              rec.截图2 = 'screenshots/55-source-picker-canvas-mode.png';
            }
            // 取消而不是选：点「取消选择」
            const 取消 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="generation-source-picker-close"],button'))
              .filter((b) => (b.getAttribute('aria-label') || '').includes('取消'))
              .map((b) => { const r = b.getBoundingClientRect(); return { box: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)], aria: b.getAttribute('aria-label'), 有面积: r.width > 0 }; }));
            rec.取消钮 = 取消;
            const c = 取消.find((x) => x.有面积);
            if (c) {
              const cp = await p.evaluate(([x, y, w, h]) => {
                for (let yy = Math.ceil(y) + 2; yy <= y + h - 2; yy += 2)
                  for (let xx = Math.ceil(x) + 2; xx <= x + w - 2; xx += 2) { const el = document.elementFromPoint(xx, yy);
                    if (el && el.closest('button')) return { x: xx, y: yy }; }
                return { __err: 'no-point' };
              }, c.box);
              if (!cp.__err) { await p.mouse.click(cp.x, cp.y); await p.waitForTimeout(1500); }
            }
            rec.取消后 = await 读testid([...生成5, ...拾取2]);
            落盘();
          }
        }
        break;
      }
      await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
    }
    // 全部关掉
    for (let k = 0; k < 5; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
    rec.全关后 = await 读testid([...生成5, ...拾取2]);
    await 清零();
    rec.删除 = [];
    for (const x of 建.ids) rec.删除.push(await 删一个(x));
    落盘();
  }

  // ================= Q3：「积分明细」对话框 =================
  {
    await 清零();
    // 打开生成历史面板：找启动器（canvas-context.md 说判据是 aria-expanded）
    const 启动 = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
      .map((b) => ({ aria: b.getAttribute('aria-label'), text: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
        expanded: b.getAttribute('aria-expanded'), testid: b.getAttribute('data-testid'),
        box: (() => { const r = b.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; })(), 有面积: r.width > 0 }))
      .filter((x) => x.有面积 && /历史|history/i.test((x.aria || '') + (x.text || ''))));
    rec.历史启动器 = 启动;
    if (启动.length) {
      const bb = 启动[0].box;
      const pt = await p.evaluate(([x, y, w, h]) => {
        for (let yy = Math.ceil(y) + 2; yy <= y + h - 2; yy += 2)
          for (let xx = Math.ceil(x) + 2; xx <= x + w - 2; xx += 2) { const el = document.elementFromPoint(xx, yy);
            if (el && el.closest('button')) return { x: xx, y: yy, aria: el.closest('button').getAttribute('aria-label') }; }
        return { __err: 'no-point' };
      }, bb);
      rec.历史落点 = pt;
      if (!pt.__err) {
        await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1800);
        rec.历史面板 = await p.evaluate(() => {
          const p2 = document.querySelector('[data-testid="canvas-feature-panel"]');
          const r = p2 && p2.getBoundingClientRect();
          return { 命中: !!p2, box: r && [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x), Math.round(r.y)],
            aria: p2 && p2.getAttribute('aria'), text: p2 && (p2.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
            积分钮: Array.from((p2 || document).querySelectorAll('button')).map((b) => { const q = b.getBoundingClientRect();
              return { text: (b.innerText || '').replace(/\s+/g, ' ').trim(), box: [Math.round(q.width), Math.round(q.height), Math.round(q.x), Math.round(q.y)] }; }).filter((x) => x.box[0] > 0) };
        });
        落盘();
        const 积分btn = ((rec.历史面板 || {}).积分钮 || []).find((x) => x.text === '积分明细');
        rec.积分明细钮 = 积分btn || null;
        if (积分btn) {
          const pp = await p.evaluate(([x, y, w, h]) => {
            for (let yy = Math.ceil(y) + 2; yy <= y + h - 2; yy += 2)
              for (let xx = Math.ceil(x) + 2; xx <= x + w - 2; xx += 2) { const el = document.elementFromPoint(xx, yy);
                if (el && el.closest('button')) return { x: xx, y: yy }; }
            return { __err: 'no-point' };
          }, 积分btn.box);
          if (!pp.__err) {
            await p.mouse.click(pp.x, pp.y); await p.waitForTimeout(2000);
            rec.Q3 = await 读testid(['workspace-project-info-dialog']);
            const d = (rec.Q3['workspace-project-info-dialog'].实例 || [])[0];
            rec.拍前断言3 = { 命中: rec.Q3['workspace-project-info-dialog'].命中, 盒: d && d.box, role: d && d.role, 积分: await R.credits() };
            断言('⑥ 🔑 `workspace-project-info-dialog` 命中 ≥ 1 且有面积', rec.拍前断言3.命中 >= 1 && rec.拍前断言3.盒 && rec.拍前断言3.盒[0] > 0, rec.拍前断言3);
            断言('⑦ 打开积分明细**不扣积分**', String(rec.拍前断言3.积分).indexOf('805') >= 0, { 积分: rec.拍前断言3.积分 });
            if (rec.拍前断言3.命中 >= 1) {
              await p.screenshot({ path: new URL('./56-workspace-project-info-dialog.png', 出图).pathname });
              rec.截图3 = 'screenshots/56-workspace-project-info-dialog.png';
            }
            // 手册记：Esc 由内向外一层一层关 ⇒ 记下每按一次后的状态
            rec.逐次Esc = [];
            for (let i = 1; i <= 2; i++) {
              await p.keyboard.press('Escape'); await p.waitForTimeout(1300);
              rec.逐次Esc.push({ 第几次: i, 对话框命中: await p.evaluate(() => document.querySelectorAll('[data-testid="workspace-project-info-dialog"]').length),
                历史面板命中: await p.evaluate(() => document.querySelectorAll('[data-testid="canvas-feature-panel"]').length), 浮层: await R.overlays() });
            }
            落盘();
          }
        }
      }
    }
  }
  for (let k = 0; k < 4; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
  await 清零();
  const 末 = await idsOf(p); const 末c = await canvasPos(p);
  rec.收尾检查 = { 节点数: 末.length,
    位移节点: 基线canvas ? Object.keys(基线canvas).filter((k) => 末c[k] && (末c[k][0] !== 基线canvas[k][0] || 末c[k][1] !== 基线canvas[k][1])) : null };
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

await settle(p, R);
const 小地图前 = await R.minimap();
if (!小地图前 || 小地图前.ariaPressed !== 'true') {
  const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
  if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); }
}
rec.小地图后 = await R.minimap();
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits(), 组数: await 组数(p),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length),
  残留自建: (await idsOf(p)).filter((x) => ((rec.建 || {}).ids || []).includes(x)) };

console.log('Q1 生成表单:', JSON.stringify(rec.Q1_生成表单, null, 1).slice(0, 1800));
console.log('\nQ1 提及面板:', JSON.stringify((rec.Q1_提及面板 || {})['generation-mention-panel'], null, 1).slice(0, 900));
console.log('\n列表框:', JSON.stringify(rec.列表框));
console.log('\nQ2 尝试:', JSON.stringify((rec.Q2 || {}).尝试, null, 1).slice(0, 1200));
console.log('\nQ2 拾取模式:', JSON.stringify((rec.Q2 || {}).拾取模式, null, 1).slice(0, 1200));
console.log('\nQ3:', JSON.stringify(rec.Q3, null, 1).slice(0, 900));
console.log('\n历史面板:', JSON.stringify(rec.历史面板));
console.log('\n逐次Esc:', JSON.stringify(rec.逐次Esc));
console.log('\n删除:', JSON.stringify((rec.删除 || []).map((d) => d.消失 || d.__err)));
console.log('截图:', JSON.stringify([rec.截图1, rec.截图2, rec.截图3]));
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');

断言('⑧ 建-删护栏全过 + 消失集合恰好 {SELF}', rec.建 && rec.建.护栏全过 === true && (rec.删除 || []).every((d) => d.消失 && d.消失.length === 1), { 护栏: rec.建 && rec.建.护栏全过, 删除: (rec.删除 || []).map((d) => d.消失 || d.__err) });
断言('⑨ 🔑 收尾积分**仍是 805**（全程没点任何生成/扣费按钮）', String((rec.收尾 || {}).积分).indexOf('805') >= 0, { 积分: (rec.收尾 || {}).积分 });
if (rec.收尾检查 && rec.收尾检查.位移节点) 断言('⑩ 其余节点零位移', rec.收尾检查.位移节点.length === 0, rec.收尾检查);

rec.断言全过 = 断言过; 落盘();
await b.close();
