// 批次 203 d 轮：修掉「清空输入框」的正确姿势，拿到**编辑态**在无头下的读数。
//
// 🔴 前面两轮卡住的**真根因**（与「点错行」无关）：
//   我一直用 `nativeSet(value='')` + `dispatchEvent('input')` 清空搜索框。
//   实测三种清空方式（同一次会话、同一个输入框，逐字读回）：
//     ① nativeSet+input  → 值 = `""` ✅，但随后 `keyboard.type('文本')` **打不进去**（值仍 `""`）
//     ② 逐字 Backspace 12 次 → 值 = `"频"`（删过头），随后 type **进去了** ⇒ `"频文本"`
//     ③ select+Backspace → 值 = `""` ✅，随后 type **又打不进去**
//   ⇒ **`nativeSet` 会让 React 受控状态与 DOM 值脱节**，后续按键被丢弃。
//   ⇒ **正确姿势：`focus()` → `select()` → 连按 `Backspace` 删空**（别去设 value）。
//
// 📌 为什么前面的批次没踩到：批次 195/198/200 **每档都新开页签** ⇒ 输入框初始就是空的，
//    那句「清空」是多余动作，`keyboard.type` 直接能进去 ⇒ **那些读数没问题**（它们搜「音频」
//    确实搜到了音频结果）。**只有「复用同一页签连续多次搜索」才会踩坑。**
//
// 本轮：修正清空 → 搜「文本」→ **精确定位**（无 fallback）→ 50% 双击进编辑态 → 与有头逐条比对。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const TARGET = 'node_5gftn3dnt1';
const TARGET_TID = 'canvas-search-result-node_5gftn3dnt1';
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b203d', 目标: TARGET, 修的根因: 'nativeSet 清空会让 React 受控状态脱节，后续按键被丢弃' };

await settle(p, R);
await setZoom(p, 50);

// 🔴 正确的清空：focus → select → 连按 Backspace
const 打开并搜索 = async (词) => {
  const 钮 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
    || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
    if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!钮) return { 中止: '找不到搜索钮' };
  await p.mouse.click(钮[0], 钮[1]); await p.waitForTimeout(1500);
  // 清空
  await p.evaluate(() => { const e = document.querySelector('input[aria-label="搜索"]'); if (e) { e.focus(); e.select(); } });
  for (let i = 0; i < 14; i++) await p.keyboard.press('Backspace');
  await p.waitForTimeout(500);
  const 清空后 = await p.evaluate(() => { const e = document.querySelector('input[aria-label="搜索"]'); return e ? e.value : null; });
  // 输入
  await p.keyboard.type(词, { delay: 80 });
  await p.waitForTimeout(2200);
  const r = await p.evaluate((tid) => ({ 值: document.querySelector('input[aria-label="搜索"]')?.value,
    总条数: document.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length,
    全部: Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).slice(0, 12).map((e) => e.getAttribute('data-testid')),
    命中目标: !!document.querySelector(`[data-testid="${tid}"]`) }), TARGET_TID);
  return { 清空后, ...r };
};

out.搜文本 = await 打开并搜索('文本');
log('搜「文本」：清空后=', JSON.stringify(out.搜文本.清空后), '| 现在值=', JSON.stringify(out.搜文本.值),
  '| 总条数=', out.搜文本.总条数, '| 命中目标=', out.搜文本.命中目标);
if (out.搜文本.全部) log('   结果逐条：', JSON.stringify(out.搜文本.全部, null, 1));

const 位 = await p.evaluate((tid) => { const e = document.querySelector(`[data-testid="${tid}"]`); if (!e) return { 找到: false };
  const r = e.getBoundingClientRect(); return { 找到: true, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }, TARGET_TID);

if (!位.找到) { out.无效臂 = '结果面板里没有目标行（无 fallback 兜底）'; log('🔴 无效臂：', out.无效臂); }
else {
  await p.mouse.click(位.点[0], 位.点[1]); await p.waitForTimeout(3000);
  out.定位后 = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { 找不到: true };
    const r = n.getBoundingClientRect();
    return { 选中: n.classList.contains('selected'), 屏上: [r.x, r.y, r.width, r.height].map(Math.round),
      在视口内: r.x > 10 && r.right < innerWidth - 10 && r.y > 60 && r.bottom < innerHeight - 10,
      正文中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height * 0.55)] }; }, TARGET);
  log('定位后：', JSON.stringify(out.定位后));
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);

  if (out.定位后.在视口内) {
    const [cx, cy] = out.定位后.正文中心;
    await p.mouse.dblclick(cx, cy); await p.waitForTimeout(2400);
    out.编辑态 = await p.evaluate(() => {
      const g = (sel) => { const e = document.querySelector(sel); if (!e) return null;
        const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map((z) => Math.round(z * 100) / 100); };
      return { 编辑面数: document.querySelectorAll('.tiptap.ProseMirror').length,
        节点内contenteditable: document.querySelectorAll('.react-flow__node [contenteditable]').length,
        nodeToolbar: document.querySelectorAll('[data-testid="node-toolbar"]').length,
        textEditorToolbar: document.querySelectorAll('[data-testid="text-editor-toolbar"]').length,
        编辑态工具条屏上: g('[data-testid="text-editor-toolbar"]'), 编辑面屏上: g('.tiptap.ProseMirror'),
        选中态工具条屏上: g('[data-testid="node-toolbar"]'),
        焦点: (() => { const a = document.activeElement; return a ? a.tagName : null; })(),
        编辑面在节点内: (() => { const e = document.querySelector('.tiptap.ProseMirror'); return e ? !!e.closest('.react-flow__node') : null; })() };
    });
    out.编辑态.断言 = { 判据: '编辑面数 = 1', 通过: out.编辑态.编辑面数 === 1 };
    log('编辑态：', JSON.stringify(out.编辑态), '→', out.编辑态.断言.通过 ? '✅' : '🔴 无效臂');
    if (out.编辑态.断言.通过) {
      out.比对 = [
        { 项: '编辑面数', 有头批次194: 1, 无头: out.编辑态.编辑面数 },
        { 项: '节点内contenteditable', 有头批次194: 0, 无头: out.编辑态.节点内contenteditable },
        { 项: '编辑面在节点内', 有头批次194: false, 无头: out.编辑态.编辑面在节点内 },
        { 项: '焦点', 有头批次194: 'DIV', 无头: out.编辑态.焦点 },
        { 项: 'text-editor-toolbar 实例数', 有头批次194: 1, 无头: out.编辑态.textEditorToolbar },
        { 项: 'node-toolbar 实例数（编辑态）', 有头批次194: 0, 无头: out.编辑态.nodeToolbar },
      ].map((r) => ({ ...r, 一致: String(r.有头批次194) === String(r.无头) }));
      log('与有头逐条比对：');
      for (const r of out.比对) log(`   ${r.一致 ? '✅' : '🔴'} ${r.项}：有头 ${r.有头批次194} / 无头 ${r.无头}`);
    }
    await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  } else out.跳过 = '定位后不在视口内';
}
await p.keyboard.press('Escape'); await p.waitForTimeout(900);

fs.writeFileSync('/tmp/b203d.json', JSON.stringify(out, null, 1));
await p.evaluate(() => { const ns = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  for (let x = 40; x < innerWidth - 340; x += 40) for (let y = 100; y < innerHeight - 120; y += 40) {
    const h = document.elementFromPoint(x, y);
    if (h && h.classList && h.classList.contains('react-flow__pane') && !ns.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return { x, y }; }
  return null; }).then((s) => { if (s) return p.mouse.click(s.x, s.y); });
await p.waitForTimeout(900);
await setZoom(p, 26);
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();
