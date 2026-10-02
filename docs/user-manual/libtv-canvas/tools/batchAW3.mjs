// Batch AW3 —— 用**正确的判据**把顶部工具条五枚逐枚点完。
//
// AW1 报「三枚全都没反应」是**判据 bug，不是产品行为**：
//   `diffPanels()` 实际**返回数组**（`after.filter(a => !seen.has(a.sig))`），
//   而我写的是 `d.added || []` → 恒为 undefined → 恒报 0。
//   AV2 里那个 `d.added || d.new || d` 的 fallback 恰好蒙对了，掩盖了这个误用。
//
//   教训：**「我以为的 API」和「我以为的清单」是同一族错误**（§15）。
//   调公共库之前先读实现，或者至少 `console.log` 一次看它长什么样。
//
// 判据沿用 AW2 那套：**无尺寸门槛的全量浮层快照 + 差集**。
// （`fingerprint()` 的 `width>120 && height>60` 门槛本身没问题 ——
//   特效广场那个模态框是 1440×810，够大；AW1 读不到纯粹是因为 diffPanels 用错了。）
//
// 已知：点「特效」弹的是**特效广场**（全屏 mantine-Modal-inner [0,0,1440,810] z=701），
// 和从「素材库」面板进入的是同一个模态框。这一轮把另外四枚也问出来。
//
// 安全边界不变：**只打开、不选择**。不点卡片就不会建节点、不消耗积分。
// 不点 文A / 提交箭头 / ⤢ / ⚙。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAW3';
const { browser, page } = await launch();

/** 全页可见浮层快照 —— **不设尺寸门槛**。 */
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
    out.push({ cls: (e.className || '').toString().slice(0, 55), pos: cs.position, z: cs.zIndex,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], text: txt.slice(0, 400) });
  }
  const seen = new Set();
  return out.filter((o) => { const k = o.cls + '|' + o.rect.join(','); if (seen.has(k)) return false; seen.add(k); return true; });
});

const panelState = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没有选中节点' };
  const c = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width > 400 && o.r.height > 100)
    .filter((o) => (o.e.innerText || '').includes('参考'))
    .sort((a, b) => (a.r.width * a.r.height) - (b.r.width * b.r.height))[0];
  if (!c) return { err: '没找到面板' };
  return { panelRect: [Math.round(c.r.x), Math.round(c.r.y), Math.round(c.r.width), Math.round(c.r.height)],
    descCount: c.e.querySelectorAll('*').length,
    btns: [...c.e.querySelectorAll('button,[role="button"]')].map((e) => {
      const q = e.getBoundingClientRect();
      return { text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10), rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] };
    }).filter((b) => b.rect[2] > 0) };
});

async function deselect() {
  await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  await page.mouse.click(80, 120); await page.waitForTimeout(1500);
}

async function dragToY(textPart, targetY) {
  const g = await page.evaluate((t) => {
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!(n.innerText || '').includes(t)) continue;
      const r = n.getBoundingClientRect();
      if (r.x < 5 || r.x + r.width > 1435 || r.y < 60 || r.y + r.height > 800) continue;
      for (const [fx, fy] of [[0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.3], [0.5, 0.7], [0.5, 0.2]]) {
        const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
        const on = document.elementFromPoint(cx, cy);
        if (on && n.contains(on) && !on.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
          return { cx: Math.round(cx), cy: Math.round(cy), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
        }
      }
    }
    return { err: '找不到可拖的「' + t + '」' };
  }, textPart);
  if (g.err) return g;
  const dy = Math.round(targetY - g.rect[1]);
  await page.mouse.move(g.cx, g.cy); await page.mouse.down();
  for (let i = 1; i <= 12; i += 1) { await page.mouse.move(g.cx, g.cy + (dy * i) / 12); await page.waitForTimeout(70); }
  await page.mouse.up(); await page.waitForTimeout(2000);
  return { grabbed: g, dy };
}

async function clickTool(label, shotName) {
  const r = { label };
  const st = await panelState();
  if (st.err) { r.err = st.err; return r; }
  const b = st.btns.find((x) => x.text === label);
  if (!b) { r.err = '面板里没有「' + label + '」'; r.available = st.btns.map((x) => x.text); return r; }
  r.rect = b.rect;
  r.panelBefore = st.panelRect;
  const before = await snap();
  const cx = b.rect[0] + b.rect[2] / 2, cy = b.rect[1] + b.rect[3] / 2;
  r.hit = await page.evaluate(([x, y]) => {
    const e = document.elementFromPoint(x, y);
    const btn = e && e.closest('button');
    return e ? { tag: e.tagName, btnText: (btn?.innerText || '').trim().slice(0, 8), cursor: btn ? getComputedStyle(btn).cursor : null } : null;
  }, [cx, cy]);
  await page.mouse.click(cx, cy);
  await page.waitForTimeout(3200);
  await clearToasts(page);

  const after = await snap();
  const bset = new Set(before.map((o) => o.cls + '|' + o.rect.join(',')));
  r.added = after.filter((o) => !bset.has(o.cls + '|' + o.rect.join(',')));
  const aset = new Set(after.map((o) => o.cls + '|' + o.rect.join(',')));
  r.removed = before.filter((o) => !aset.has(o.cls + '|' + o.rect.join(',')));
  // 挑最大的那个当「新浮层本体」
  r.top = r.added.sort((a, b) => (b.rect[2] * b.rect[3]) - (a.rect[2] * a.rect[3]))[0] || null;
  r.nAdded = r.added.length;
  const st2 = await panelState();
  r.panelAfter = st2.panelRect || st2.err;
  r.panelUnchanged = JSON.stringify(st2.panelRect) === JSON.stringify(st.panelRect);
  if (r.nAdded) { await shot(page, shotName); r.shot = shotName; }
  console.log(`  「${label}」→ 新增 ${r.nAdded} 个，最大：${r.top ? `[${r.top.rect}] z=${r.top.z} ${r.top.cls}` : '无'}`);
  if (r.top) console.log('     文本:', r.top.text.slice(0, 220));
  // 收场：Esc 关掉可能开着的浮层
  await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
  const st3 = await panelState();
  r.afterEscape = { panelRect: st3.panelRect || st3.err, descCount: st3.descCount };
  r.panelStillThere = !!(await panelState()).panelRect;
  return r;
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await beginBatch(B, { note: '工具条五枚逐枚实点（diffPanels 用错 API 之后改用无门槛全量快照差集）' });

  const out = {};
  out.deselected = (await deselect(), await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length));
  out.drag = await dragToY('视频节点', 150);
  const g = out.drag.grabbed;
  await page.mouse.click(g.cx, g.cy + Math.max(0, 150 - g.rect[1]));
  await page.waitForTimeout(4200);
  out.st = await panelState();
  console.log('AW3 面板:', JSON.stringify(out.st.panelRect), 'descCount:', out.st.descCount);

  out.clicks = [];
  for (const [label, shotName] of [['参考', 'M-152-工具条-参考.png'], ['标记', 'M-153-工具条-标记.png'],
    ['特效', 'M-154-工具条-特效.png'], ['角色库', 'M-155-工具条-角色库.png'], ['运镜', 'M-156-工具条-运镜.png']]) {
    console.log(`\n--- AW3 点「${label}」---`);
    const r = await clickTool(label, shotName);
    out.clicks.push(r);
    if (r.err) console.log('  ⚠', r.err);
  }

  await logStep(B, {
    id: 'AW3-toolbar-five-real-clicks', title: '顶部工具条五枚逐枚实点：各自打开什么',
    target: 'AW1 报「三枚都没反应」是**判据 bug**：`diffPanels()` 返回**数组**而不是 `{added}` 对象，'
      + '我写 `d.added` 恒为 undefined。**「我以为的 API」和「我以为的清单」是同一族错误**',
    evidence: out,
    visible_text: JSON.stringify(out.clicks.map((c) => ({ label: c.label, nAdded: c.nAdded, top: c.top && { rect: c.top.rect, cls: c.top.cls, text: c.top.text.slice(0, 180) } }))).slice(0, 3000),
    shot: out.clicks.find((c) => c.shot)?.shot || 'M-139-视频节点-参数面板.png',
  });
  console.log('\nAW3 完成');
} finally {
  await browser.close();
}
