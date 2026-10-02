// 批次 101 · c20 轮：只做「删自建节点」这一件事。
//
// c19 的收尾脚本被自己的落点判据拦下了（`vanished: []`，节点还在，**零伤害**）——
// 这已经和 c2 那次是同一类错误的**第二次**：
//   · c2：按钮里有 SVG 图标 ⇒ `elementFromPoint` 返回 `<path>`，我却要求它**必须**是 `BUTTON`
//   · c19：菜单项里有 SPAN ⇒ `elementFromPoint` 返回 `SPAN`，我却要求它**必须**带 `role=menuitem`
// ⇒ **落点判据的正路只有一条**：命中元素是否落在**目标元素内部**（`el === target || target.contains(el)`），
//   外加「属于 SELF 节点」这一条归属检查。**永远不要要求命中元素本身就是目标。**
//
// 📌 顺带记一条手册用得上的读数：**带媒体的视频节点**，右键菜单 `200×332`、**8 项**：
//   复制 / 复制副本 / 粘贴 / 保存到主体库 / 下载 / 重做（禁用）/ 撤销 / 删除
//   与批次 97（音频，空态）与批次 98（主体）的「7 项基础 + 按类型插入额外项」口径一致；
//   **「下载」在这里是可用态**（空节点时它是禁用的）。
//   ⚠️ 「删除」项的文案是 **`删除 ⌫`**，即菜单**标注了 ⌫ 快捷键**；
//      而批次 95 实测 **`Delete` 键无效**。二者矛盾，本轮不重测按键，记为待核。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_fxhrsbbfrz' };
const SELF = out.selfId;

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const selN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });
const toolAria = () => p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return t ? t.getAttribute('aria-label') : null; });

// 护栏 ①
out.idsBefore = await allIds();
const before = new Set(out.idsBefore);
log('删前 id 数：', out.idsBefore.length, '｜含 SELF？', before.has(SELF));
if (!before.has(SELF)) { log('SELF 不在画布上 ⇒ 无需删除'); out.alreadyGone = true; }
else {
  // 确保「已选中且不是编辑态」
  for (let k = 0; k < 2; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); }
  const cur = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return { gone: true };
    const s = n.querySelector('[data-testid="video-flow-node-surface"]').getBoundingClientRect();
    const x = Math.round(s.x + s.width / 2), y = Math.round(s.y + s.height * 0.2);
    const el = document.elementFromPoint(x, y);
    return { selected: n.classList.contains('selected'), point: [x, y], insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)) }; }, SELF);
  log('Esc 后：', JSON.stringify(cur));
  if (!cur.selected && cur.insideSelf) {
    await p.mouse.move(cur.point[0], cur.point[1]); await p.waitForTimeout(400);
    await p.mouse.click(cur.point[0], cur.point[1]); await p.waitForTimeout(1200);
    log('点选后 selected =', await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); return n.classList.contains('selected'); }, SELF));
  }
  // 右键：move → move → down → 停 260ms → up
  const rc = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const s = n.querySelector('[data-testid="video-flow-node-surface"]').getBoundingClientRect();
    return [Math.round(s.x + s.width / 2), Math.round(s.y + s.height * 0.2)]; }, SELF);
  await p.mouse.move(rc[0], rc[1]); await p.waitForTimeout(300);
  await p.mouse.move(rc[0], rc[1]); await p.waitForTimeout(200);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1100);

  const del = await p.evaluate(() => {
    for (const m of document.querySelectorAll('[role=menu]')) for (const it of m.querySelectorAll('[role=menuitem]')) {
      const t = (it.innerText || '').trim();
      if (t.startsWith('删除')) { const r = it.getBoundingClientRect();
        return { point: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], txt: t,
          disabled: it.getAttribute('aria-disabled') === 'true',
          itemRect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }; } }
    return null; });
  log('删除项：', JSON.stringify(del));

  if (!del || del.disabled) log('🔴 无可点的「删除」⇒ 不删');
  else {
    // ✅ 修正后的落点判据：命中元素必须**落在目标 menuitem 内部**
    const land = await p.evaluate(([x, y]) => {
      let target = null;
      for (const m of document.querySelectorAll('[role=menu]')) for (const it of m.querySelectorAll('[role=menuitem]')) {
        if ((it.innerText || '').trim().startsWith('删除')) target = it; }
      if (!target) return { noTarget: true };
      const el = document.elementFromPoint(x, y);
      return { hitTag: el ? el.tagName : null, hitRole: el ? el.getAttribute('role') : null,
        hitText: el ? (el.textContent || '').trim().slice(0, 20) : null,
        insideTarget: !!(el && (el === target || target.contains(el))),
        targetText: (target.innerText || '').trim().slice(0, 20) };
    }, del.point);
    log('落点校验（修正后）：', JSON.stringify(land));
    if (land.insideTarget) {
      await p.mouse.move(del.point[0], del.point[1]); await p.waitForTimeout(400);
      await p.mouse.click(del.point[0], del.point[1]);
      await p.waitForTimeout(2000);
      out.clicked = true;
    } else { log('  🔴 仍不对 ⇒ 不点'); out.clicked = false; }
  }
}

await p.waitForTimeout(1200);
// 护栏 ③
out.idsAfter = await allIds();
const after = new Set(out.idsAfter);
out.vanished = out.idsBefore.filter((id) => !after.has(id));
out.appeared = out.idsAfter.filter((id) => !before.has(id));
out.guardOk = out.vanished.length === 1 && out.vanished[0] === SELF;
log('护栏：删前', out.idsBefore.length, '→ 删后', out.idsAfter.length,
    '｜消失：', JSON.stringify(out.vanished), '｜新增：', JSON.stringify(out.appeared));
log('  ⇒ 消失的**恰好只有 SELF**？', out.guardOk ? '✅' : '🔴');

out.end = { nodes: await nodeN(), sel: await selN(), scale: await scaleNow(), tool: await toolAria(), hasSelf: after.has(SELF) };
log('终态：', JSON.stringify(out.end));
out.clean = out.end.sel === '0' && out.end.scale === 0.6 && out.end.tool === '选择工具' && !out.end.hasSelf;
log('收尾干净？', out.clean ? '✅' : '🔴');
writeFileSync(new URL('./_tmp-b101z2.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
