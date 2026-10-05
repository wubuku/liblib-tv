// 批次 175 e 轮：打开「用户菜单 → 快捷键」面板，现场读出 S1（帮助面板那一路），
// 与 S3（菜单里 `aria-keyshortcuts` 声明的那一路）做**对账**。
// d 轮选错了入口：用户菜单里有「帮助中心 / 使用手册 / 快捷键」三条，
// 脚本按 `/帮助|手册|快捷键/` 取了**第一个**「帮助中心」⇒ 读到的不是快捷键面板。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '175e' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(500);
const pt = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-user-menu-trigger"]');
  const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
await p.mouse.click(pt[0], pt[1]); await p.waitForTimeout(1800);
const 项 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=menuitem]'))
  .filter((e) => e.getBoundingClientRect().width > 4)
  .map((e) => { const r = e.getBoundingClientRect(); return { 文字: (e.innerText || '').trim(), 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }));
rec.用户菜单 = 项;
const 快捷 = 项.find((m) => m.文字 === '快捷键');
rec.入口 = 快捷 ? '用户菜单 → 快捷键' : null;
if (快捷) {
  await p.mouse.click(快捷.盒[0] + 24, 快捷.盒[1] + 快捷.盒[3] / 2); await p.waitForTimeout(2600);
  rec.面板 = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="shortcut-help-scroll-region"]');
    if (!e) return { 失败: '没有 shortcut-help-scroll-region', 现有浮层: Array.from(document.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')).filter((t) => /shortcut|help|key/i.test(t)) };
    const q = e.getBoundingClientRect();
    return { 盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      scrollHeight: e.scrollHeight, clientHeight: e.clientHeight,
      行: e.innerText.split('\n').map((s) => s.trim()).filter(Boolean) };
  });
  await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
}
// ── 对账：面板里出现的快捷键 vs 菜单 aria-keyshortcuts 声明的
const S3 = { 'Meta+C': '复制', 'Meta+D': '复制副本', 'Meta+Shift+C': '复制为图片（仅图片节点）',
  'Meta+V': '粘贴', 'Meta+Shift+Z': '重做', 'Meta+Y': '重做（第二个声明）', 'Meta+Z': '撤销', 'Backspace': '删除' };
const 面板键集 = new Set();
for (const l of rec.面板?.行 || []) {
  for (const m of l.matchAll(/(?:⌘|⇧|⌥)\s*[A-Z0-9+−\-]*/g)) 面板键集.add(m[0].replace(/\s+/g, ' ').trim());
}
rec.对账 = {
  面板里出现过的键: [...面板键集].sort(),
  菜单声明但面板里没有: Object.keys(S3).filter((k) => !面板键集.has(k.replace('Meta', '⌘').replace('Shift', '⇧').replace('Backspace', '⌫')))
    .map((k) => ({ 声明: k, 含义: S3[k] })),
  面板行数: (rec.面板?.行 || []).length,
  扣组标题后: (rec.面板?.行 || []).length - 4,
};
rec.收尾 = { 状态行: await R.status(), 缩放: await R.zoom() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
