/**
 * 批次 204：销掉批次 203 §4.126.5 自己列下的三条「仍未测」。
 *
 * 203 的六步表只覆盖了「前置未点过 → 单击 → 单击 → 双击 → Esc」这一条路径，
 * 明确留下三条没测：
 *   ① 50% 档**未选中**时单击一次会怎样（选不选中 / 进不进编辑）
 *   ② 50% 档**未选中**时双击会怎样
 *   ③ 26% 档**双击**时，第一击的「展开」会不会吃掉双击的前一半
 *
 * 三条都用同一条纪律：每一步操作前先跑归属判据（立规 82），
 * 且每格都先断言「前置真的清干净了」才读数（立规 78）。
 *
 * ⚠️ 关键坑（203 c 轮踩过）：清空搜索框不能用 `nativeSet('')`，
 *    要用 `focus()` + `select()` + `Backspace`，否则 React 受控状态脱节、后续按键被丢弃。
 *
 * 全部只读：只做点击/双击，不新建/删除节点，不生成，不下载。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';
import { openCanvas, readers, settle, setZoom, endState, PORT } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b204a.json';
const T1 = 'node_5gftn3dnt1';   // 文本 3，canvas [560,319]，各档都在视口内
const BLANK = [1276, 716];       // 画布右下空白，清选中用

const 采样 = (p) => p.evaluate((tid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${tid}"]`);
  const db = n ? n.getAttribute('aria-describedby') : null;
  const host = db ? document.getElementById(db) : null;
  const cnt = (t) => document.querySelectorAll(`[data-testid="${t}"]`).length;
  const 编辑面 = Array.from(document.querySelectorAll('[contenteditable="true"],textarea')).filter((e) => e.offsetWidth > 0);
  return {
    宿主testid: host ? host.getAttribute('data-testid') : null,
    selected类: n ? n.classList.contains('selected') : null,
    选中集: document.querySelectorAll('.react-flow__node.selected').length,
    nodeToolbar: cnt('node-toolbar'),
    textEditorToolbar: cnt('text-editor-toolbar'),
    编辑面数: 编辑面.length,
    编辑面在节点内: 编辑面.length ? !!n.contains(编辑面[0]) : null,
  };
}, T1);

/** 立规 82：先证明这个点在目标节点里，再返回坐标。 */
const 点 = (p, id) => p.evaluate((tid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${tid}"]`);
  if (!n) return { 失败: '节点不在 DOM' };
  const r = n.getBoundingClientRect();
  for (let fy = 0.15; fy <= 0.9; fy += 0.15) for (let fx = 0.15; fx <= 0.9; fx += 0.15) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    const h = document.elementFromPoint(x, y);
    if (h && h.closest(`.react-flow__node[data-id="${tid}"]`)) return { x, y, 相对: [Math.round(fx * 100), Math.round(fy * 100)] };
  }
  return { 失败: '36 个候选点没有一个落在节点内（被别节点盖住）' };
}, id);

/** 清到「未选中」：点画布空白，并断言选中集归零。 */
const 清选中 = async (p) => {
  await p.mouse.click(BLANK[0], BLANK[1]);
  await p.waitForTimeout(1000);
  const n = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
  return { 清后选中数: n, 断言: { 判据: '点画布空白后选中集 = 0', 通过: n === 0 } };
};

const browser = await chromium.connectOverCDP({ endpointURL: `http://127.0.0.1:${PORT}` });
const ctx = browser.contexts()[0];
let p = ctx.pages().find((x) => /jimeng\.jianying\.com/.test(x.url())) || ctx.pages()[0];
const R = readers(p);

const out = { 轮次: 'b204a', 目标: T1, 三条未测: {} };
await openCanvas();
await settle(p, R);
out.基线 = { ids: await R.ids(), testids: await R.testids() };

/** 跑一格：清选中 → 断言 → 定位 → 执行动作 → 读。 */
const 跑格 = async (名, 缩放, 动作) => {
  const g = { 名, 缩放 };
  const z = await setZoom(p, 缩放);
  g.实测scale = z.实测scale;
  g.scale已追平 = z.scale已追平;
  g.清选中 = await 清选中(p);
  const 前 = await 采样(p);
  g.前置 = 前;
  if (!g.清选中.断言.通过) { g.无效臂 = '清选中失败'; out.三条未测[名] = g; return g; }
  const pt = await 点(p, T1);
  g.落点 = pt;
  if (pt.失败) { g.无效臂 = pt.失败; out.三条未测[名] = g; return g; }
  if (动作 === '单击') { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1400); }
  else { await p.mouse.dblclick(pt.x, pt.y); await p.waitForTimeout(1800); }
  g.动作后 = await 采样(p);
  console.error(`  ${名}（${缩放}% ${动作}）→ selected=${g.动作后.selected类} 选中集=${g.动作后.选中集} node-toolbar=${g.动作后.nodeToolbar} 编辑条=${g.动作后.textEditorToolbar} 编辑面=${g.动作后.编辑面数}`);
  out.三条未测[名] = g;
  return g;
};

// ① 50% 未选中 → 单击
await 跑格('①50%未选中单击', 50, '单击');
await p.keyboard.press('Escape'); await p.waitForTimeout(700);

// ② 50% 未选中 → 双击
await 跑格('②50%未选中双击', 50, '双击');
await p.keyboard.press('Escape'); await p.waitForTimeout(700);

// ③ 26% 未点过 → 双击（看第一击的「展开」会不会吃掉双击前一半）
await 跑格('③26%未点过双击', 26, '双击');
await p.keyboard.press('Escape'); await p.waitForTimeout(700);

// ④ 对照：26% 未点过 → 只单击一次（复现 203 的 ②，用来确认本轮 ③ 的前置与它同格）
await 跑格('④26%未点过单击对照', 26, '单击');
await p.keyboard.press('Escape'); await p.waitForTimeout(700);

const fin = await setZoom(p, 26);
out.收尾 = await endState(p, R, out.基线);
out.收尾.归位scale = fin.实测scale;
out.收尾.末尾选中 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
console.error(`写入 ${OUT}`);
console.log(JSON.stringify(Object.fromEntries(Object.entries(out.三条未测).map(([k, g]) => [k, {
  实测scale: g.实测scale, 清选中断言: g.清选中 && g.清选中.断言, 落点: g.落点,
  前置: g.前置 && { 宿主: g.前置.宿主testid, selected: g.前置.selected类, 选中集: g.前置.选中集 },
  动作后: g.动作后 && { 宿主: g.动作后.宿主testid, selected: g.动作后.selected类, 选中集: g.动作后.选中集, nodeTb: g.动作后.nodeToolbar, 编辑条: g.动作后.textEditorToolbar, 编辑面: g.动作后.编辑面数, 编辑面在节点内: g.动作后.编辑面在节点内 },
  无效臂: g.无效臂 || null,
}])), null, 1));
console.error(`末尾选中 ${out.收尾.末尾选中} ｜ ${out.收尾.状态行}`);
process.exit(0);
