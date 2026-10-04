// 批次 153 · b 轮 —— a 轮「资产库模态九层全部读到 0 个」，先查清是**没点着**还是**点了没反应**。
//
// a 轮的实况：
//   · 左栏「资产库」按钮**确实存在**（`BUTTON 40×40@16,501`），`可点落点` 也**确实找到了落点**
//     （否则 `rec.资产库` 会是 `{__err:…}`，而它进了九层读取分支）；
//   · 点击后 2.6 秒读 `[role=dialog]` 数 = **0**，九个 `canvas-asset-library-*` **一个都不在 DOM 里**；
//   · 同一次会话里左栏其余 7 个按钮（文本/图片/视频/音频/时间线/主体/导演台）都能读到。
//
// ⇒ 三种可能，本轮逐个排除：
//   甲 **点着的是别的东西**（落点虽在按钮盒内，但 `elementFromPoint` 命中的是它的伪元素/子元素，
//       或悬停后布局变了、落点已过期）⇒ 每次点击前**重新取一次落点并回读归属**。
//   乙 **需要更久**（资产库要拉远端列表，首帧慢）⇒ 点击后**按 1s 步长轮询到 20 秒**，
//       逐个时点记 `[role=dialog]` 数与九个 testid 的存在数，看是「慢」还是「根本没有」。
//   丙 **入口换了**（按钮点了但走的是别的流程）⇒ 点击后把**新增的所有 testid / dialog / overlay**
//       整份倒出来，与 a 轮起点的 testid 全集做差集。
//
// ⚠️ 仍然零风险：不选文件、不点「确认」、不碰任何生成/扣费按钮、不输入一个字。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 153, 轮次: 'b', 目的: '查清「资产库模态没打开」是没点着 / 要更久 / 还是入口变了' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b153b.json', import.meta.url), JSON.stringify(rec, null, 1));

/** 全页 testid 全集 + dialog / overlay 计数 —— 用来做差集。 */
const 快照 = () => p.evaluate(() => ({
  testid: Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')),
  dialog: document.querySelectorAll('[role=dialog]').length,
  alertdialog: document.querySelectorAll('[role=alertdialog]').length,
  浮层: document.querySelectorAll('[role=menu],[role=listbox],[data-radix-popper-content-wrapper],[data-state=open]').length,
  资产库testid: Array.from(document.querySelectorAll('[data-testid^="canvas-asset-library"]')).map((e) => e.getAttribute('data-testid')),
  body末: (document.body.innerText || '').replace(/\s+/g, ' ').trim().slice(-260),
}));

const { b, p } = await openCanvas();
const R = readers(p);
let 基线canvas = null;
try {
  await keyGuard(p); await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(),
    积分: await R.credits(), 组数: await 组数(p), 选中: await selCount(p) };
  基线canvas = await canvasPos(p);

  rec.起点快照 = await 快照();
  const 起点集 = new Set(rec.起点快照.testid);
  rec.起点testid数 = 起点集.size;

  // ---- 甲：每次点击前重新取落点 + 回读归属 ----
  const 试点 = async (sel, tag) => {
    const 记 = { 标签: tag, 选择器: sel, 轮次: [] };
    for (let i = 0; i < 3; i++) {
      const pt = await 可点落点(p, sel, 3, 3);
      if (pt.__err) { 记.轮次.push({ 第几次: i + 1, __err: pt.__err }); break; }
      const 归属 = await p.evaluate(([x, y, s]) => {
        const h = document.elementFromPoint(x, y);
        const btn = h && h.closest('[aria-label]');
        return { tag: h && h.tagName, class: h && (h.className || '').slice(0, 50),
          aria: h && h.getAttribute('aria-label'), 最近aria: btn && btn.getAttribute('aria-label'),
          是否按钮: !!(h && (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button')),
          是button本身: !!(h && h.matches(s)) };
      }, [pt.x, pt.y, sel]);
      // 悬停 → 等布局稳定 → **重新**取落点
      await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(700);
      const pt2 = await 可点落点(p, sel, 3, 3);
      const 落 = pt2.__err ? pt : pt2;
      const 归属2 = pt2.__err ? { __err: '重取落点失败，用第一次的' }
        : await p.evaluate(([x, y, s]) => { const h = document.elementFromPoint(x, y);
            return { tag: h && h.tagName, aria: h && h.getAttribute('aria-label'), 是button本身: !!(h && h.matches(s)) }; }, [pt2.x, pt2.y, sel]);
      记.轮次.push({ 第几次: i + 1, 点: [pt.x, pt.y], 归属, 悬停后点: [落.x, 落.y], 悬停后归属: 归属2 });
      await p.mouse.click(落.x, 落.y); await p.waitForTimeout(1200);
      // ---- 乙：轮询到 20 秒 ----
      const 轨 = [];
      for (let s = 0; s <= 10; s++) {
        const q = await p.evaluate(([x, y]) => {
          const h = document.elementFromPoint(x, y);
          return { dialog: document.querySelectorAll('[role=dialog]').length,
            资产库testid数: document.querySelectorAll('[data-testid^="canvas-asset-library"]').length,
            该点现在命中: h && h.getAttribute('aria-label'), 秒: 0, tag: h && h.tagName };
        }, [落.x, 落.y]);
        q.秒 = s;
        轨.push(q);
        if (q.dialog > 0 || q.资产库testid数 > 0) break;
        await p.waitForTimeout(1000);
      }
      记.轮次[记.轮次.length - 1].轮询 = 轨;
      const 末 = await 快照();
      记.轮次[记.轮次.length - 1].快照 = { dialog: 末.dialog, 资产库testid: 末.资产库testid, 浮层: 末.浮层, body末: 末.body末 };
      记.轮次[记.轮次.length - 1].新增testid = [...new Set(末.testid)].filter((x) => !起点集.has(x));
      落盘();
      await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
      await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
    }
    return 记;
  };

  rec.试左栏资产库 = await 试点('[aria-label="资产库"]', '左栏资产库');
  落盘();
  rec.试左栏上传 = await 试点('[aria-label="上传"]', '左栏上传');

  const 末 = await idsOf(p); const 末c = await canvasPos(p);
  rec.收尾检查 = { 节点数: 末.length,
    位移节点: 基线canvas ? Object.keys(基线canvas).filter((k) => 末c[k] && (末c[k][0] !== 基线canvas[k][0] || 末c[k][1] !== 基线canvas[k][1])) : null };
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
const 小地图前 = await R.minimap();
if (!小地图前 || 小地图前.ariaPressed !== 'true') {
  const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
  if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); }
}
rec.小地图后 = await R.minimap();
await settle(p, R);
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits(), 组数: await 组数(p),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };

console.log('起点 testid 数:', rec.起点testid数, '| 起点 dialog:', (rec.起点快照 || {}).dialog, '| 起点资产库testid:', JSON.stringify((rec.起点快照 || {}).资产库testid));
for (const t of ['试左栏资产库', '试左栏上传']) {
  console.log('\n=== ' + t + ' ===');
  for (const r of ((rec[t] || {}).轮次 || [])) {
    console.log(' 第' + r.第几次 + '次点击 点=' + JSON.stringify(r.点) + ' 命中' + JSON.stringify(r.归属) + ' | 悬停后命中' + JSON.stringify(r.悬停后归属));
    if (r.轮询) console.log('   轮询：' + (r.轮询 || []).map((q) => q.秒 + 's:d' + q.dialog + '/t' + q.资产库testid数 + '@' + q.该点现在命中).join(' | '));
    if (r.快照) console.log('   末快照 dialog=' + r.快照.dialog + ' 资产库testid=' + JSON.stringify(r.快照.资产库testid) + ' 浮层=' + r.快照.浮层);
    if (r.新增testid) console.log('   🔴 新增 testid: ' + JSON.stringify(r.新增testid));
    console.log('   body 末 200 字: ' + (r.快照 ? r.快照.body末 : ''));
  }
}
console.log('\n收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');

const 有dialog = ['试左栏资产库', '试左栏上传'].some((t) => ((rec[t] || {}).轮次 || []).some((r) => (r.快照 || {}).dialog > 0));
const 有新增 = ['试左栏资产库', '试左栏上传'].some((t) => ((rec[t] || {}).轮次 || []).some((r) => (r.新增testid || []).length));
rec.结论 = { 有dialog, 有新增testid: 有新增 };
断言('① 每次点击的落点归属都能回读，且悬停后归属不变成别的东西', ['试左栏资产库', '试左栏上传'].every((t) => ((rec[t] || {}).轮次 || []).every((r) => r.归属 && (r.悬停后归属 === undefined || r.悬停后归属.__err || r.悬停后归属.aria === r.归属.aria))), ['试左栏资产库', '试左栏上传'].map((t) => ((rec[t] || {}).轮次 || []).map((r) => [r.归属 && r.归属.aria, r.悬停后归属 && r.悬停后归属.aria])));
断言('② 轮询满 20 秒后仍**没有**对话框出现（本批复现「点了没反应」）', !有dialog, { 有dialog });
断言('③ 点击后新增的 testid 全集（若非空则说明入口换了）', true, { 新增: ['试左栏资产库', '试左栏上传'].flatMap((t) => ((rec[t] || {}).轮次 || []).flatMap((r) => r.新增testid || [])) });
if (rec.收尾检查 && rec.收尾检查.位移节点) 断言('④ 其余节点零位移', rec.收尾检查.位移节点.length === 0, rec.收尾检查);

rec.断言全过 = 断言过; 落盘();
await b.close();
