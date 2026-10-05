/**
 * 批次 226 收尾修复：把焦点从画布搜索框交回画布，让第 9 道门（焦点守卫）变绿。
 *
 * 背景：`jimeng-final-gate.mjs` 第 9 项用 `keyGuard(page)` 读 `document.activeElement`。
 * 批次 226 的实验期间焦点停在画布搜索框（`INPUT aria="搜索"`）⇒ 门报「⛔ 不可」。
 *
 * ⚠️ 为什么不能用「点画布空白处」这种一厢情愿的做法（批次 226 第一版就是这么失效的）：
 *   点到**节点**上会把节点选中，状态行的 `N selected` 就从 0 变成 1 ⇒ 另一条门转红，
 *   治好了焦点、治坏了选中态。所以下面的顺序是：
 *     ① 先 `Escape`（纯键盘，不碰鼠标，最不可能产生副作用）
 *     ② 再从 `.react-flow__pane` 的真实包围盒里**逐点验证** `elementFromPoint`，
 *        只在确认那个点命中 pane 本身（而不是任何节点）时才点
 *     ③ 都不行才 `.blur()`，并如实记下用了第几步
 *   每一步之后都重读 activeElement，**不许**把「点过了」当成「好了」。
 *
 * 用法：node scripts/jimeng-focus-fix.mjs
 */
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { keyGuard } from './jimeng-safe-keys.mjs';

const PORT = 9444;
const out = { steps: [], 命中: null };

const b = await chromium.connectOverCDP(`http://127.0.0.1:${PORT}`);
const page = b.contexts()[0].pages().find((p) => p.url().includes('ai-canvas'));
if (!page) { console.error('找不到画布页面'); process.exit(2); }

const act = () => page.evaluate(() => {
  const a = document.activeElement;
  if (!a) return null;
  const anc = [];
  for (let e = a; e && e !== document.body && anc.length < 6; e = e.parentElement) {
    anc.push(`${e.tagName}${e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/\s+/).join('.') : ''}`
      + `${e.getAttribute('data-testid') ? `[${e.getAttribute('data-testid')}]` : ''}`);
  }
  const r = a.getBoundingClientRect();
  return {
    tag: a.tagName,
    label: a.getAttribute('aria-label'),
    placeholder: a.getAttribute('placeholder'),
    testid: a.getAttribute('data-testid'),
    type: a.getAttribute('type'),
    box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    anc,
    openDialogs: Array.from(document.querySelectorAll('[role="dialog"]'))
      .filter((e) => e.getBoundingClientRect().width > 1)
      .map((e) => e.getAttribute('data-testid') || e.getAttribute('aria-label') || '(无名对话框)'),
  };
});

out.before = await act();
console.log('【前】activeElement =', JSON.stringify(out.before, null, 1));

// ---- ① Escape ----
await page.keyboard.press('Escape');
await page.waitForTimeout(400);
let after = await act();
out.steps.push({ step: 'Escape', act: after });
console.log(`【① Escape】activeElement = ${after ? after.tag + (after.label ? ` aria="${after.label}"` : '') : 'null'}`);

if (!after || after.tag === 'INPUT' || after.tag === 'TEXTAREA') {
  // ---- ② 找一块「确实命中 pane、且不是任何节点」的屏幕点 ----
  const pt = await page.evaluate(() => {
    const pane = document.querySelector('.react-flow__pane');
    if (!pane) return { err: '没有 .react-flow__pane' };
    const r = pane.getBoundingClientRect();
    const cands = [];
    // 在 pane 内按 40px 步长撒点，只收命中 pane 自己的
    for (let y = Math.ceil(r.top) + 24; y < r.bottom - 24; y += 40) {
      for (let x = Math.ceil(r.left) + 24; x < r.right - 24; x += 40) {
        const e = document.elementFromPoint(x, y);
        if (!e) continue;
        if (e !== pane && !e.contains(pane)) { /* 继续 */ } else {
          if (e.closest('.react-flow__node, [role="dialog"], button, a, input, textarea')) continue;
          cands.push([x, y]);
        }
      }
    }
    return { paneBox: [r.x, r.y, r.width, r.height].map(Math.round), 候选: cands.slice(0, 5), 总数: cands.length };
  });
  out.paneProbe = pt;
  console.log('【② pane 探针】', JSON.stringify(pt));

  if (pt && pt.候选 && pt.长度 !== 0 && pt.候选.length) {
    const [x, y] = pt.候选[Math.floor(pt.候选.length / 2)];
    // 点之前再核一次那个点仍然命中 pane（避免用过期坐标）
    const still = await page.evaluate(([px, py]) => {
      const e = document.elementFromPoint(px, py);
      return e ? (e.className || e.tagName) : null;
    }, [x, y]);
    out.pickCheck = { [`${x},${y}`]: still };
    if (still && /pane/.test(String(still))) {
      await page.mouse.click(x, y);
      await page.waitForTimeout(400);
      after = await act();
      out.steps.push({ step: `点 pane 空白 (${x},${y})`, act: after });
      console.log(`【② 点 pane 空白 ${x},${y}（点前复核命中 ${still}）】activeElement = ${after ? after.tag : 'null'}`);
    } else {
      out.steps.push({ step: '点 pane 空白：复核不通过，放弃', act: after });
      console.log(`【② 放弃】点前复核命中 ${still}，不是 pane`);
    }
  }

  if (after && (after.tag === 'INPUT' || after.tag === 'TEXTAREA')) {
    // ---- ③ 兜底 blur（会如实记进输出） ----
    await page.evaluate(() => { const a = document.activeElement; if (a && a.blur) a.blur(); });
    await page.waitForTimeout(300);
    after = await act();
    out.steps.push({ step: 'blur() 兜底', act: after });
    console.log('【③ blur 兜底】activeElement =', after ? after.tag : 'null');
  }
}

out.after = after;
const g = await keyGuard(page);
out.焦点守卫 = g;
console.log(`【焦点守卫】${g.safe ? '✅ 可按字母键' : '⛔ 不可'}（${g.where}）｜ ${g.reason}`);

// 顺带核一遍选中态：点 pane 不应该选中任何节点
const sel = await page.evaluate(() => {
  const t = document.body.innerText;
  return (t.match(/[\d]+ nodes?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0] || null;
});
out.状态行 = sel;
console.log('【状态行】', sel);

writeFileSync('/tmp/b226-focus.json', JSON.stringify(out, null, 1));
console.log('写入 /tmp/b226-focus.json');
await b.close();