// 批次 139 b 轮：**单自变量四档缩放** —— 锁定同一个组，只改缩放。
//
// 🔑 假设：组工具条屏上宽 = 组卡片 canvas 宽 × scale。
//   a 轮首档已验：60% 时卡片 canvas 560、工具条屏上 336，`560 × 0.6 = 336` 逐字相等。
//   并且它**不是**多选工具条那套公式 `(包围盒 canvas 宽 + 80) × scale` ——
//   `(560+80) × 0.6 = 384 ≠ 336` ⇒ **组工具条没有那个 +80**。
//
// 📌 本轮只改缩放，**组、选中态、节点位置全部不动**。
//   纪律：每次换档前现算前置（组仍选中、缩放已追平），每一档读数都记「实测 scale」。
//   ⚠️ 缩放归位纪律（批次 131/134/137）：任何缩放操作都会关掉小地图 ⇒ 收尾要重开。
//   ⚠️ 批次 137 教训：`if (pct !== 60) await setZoom(...)` 会**把回程 60% 档也跳过**
//      （批次 135 d 轮同一个 bug，第二次犯）⇒ 本轮**无条件**每档都调 setZoom，不写任何跳过。
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 读组态全, 组数, idsOf, selCount } from './jimeng-b139-lib.mjs';
import fs from 'node:fs';

const 档位 = [40, 60, 100, 200];
const rec = { 轮: '139b', 档位 };
const { b, p } = await openCanvas();
const R = readers(p);
let 全过 = true;
const 断言 = (名, ok, 详情) => { (rec.断言 = rec.断言 || []).push({ 名, 通过: !!ok, 详情 }); if (!ok) 全过 = false; };

try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p),
    zoom: await R.zoom(), 选中数: await selCount(p) };
  // 🔴 护栏：a 轮留下的组必须**恰好 1 个**且处于选中态，否则「锁定同一个组」不成立。
  const 组前 = await p.evaluate(() => {
    const gs = Array.from(document.querySelectorAll('.react-flow__node-group'));
    const 真身 = gs.filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''));
    return { 总数: gs.length, 真身数: 真身.length, 选中数: gs.filter((g) => g.classList.contains('selected')).length,
      id: 真身[0] ? 真身[0].getAttribute('data-id') : null,
      canvas: 真身[0] ? { w: 真身[0].offsetWidth, h: 真身[0].offsetHeight } : null };
  });
  rec.组前 = 组前;
  断言('①起始恰好 1 个真身组卡片', 组前.真身数 === 1, 组前);
  断言('②组处于选中态（否则工具条不在）', 组前.选中数 > 0, 组前);

  rec.四档 = [];
  for (const pct of 档位) {
    // 🔴 无条件设缩放：不写 `if (pct !== 60)` 之类的跳过（批次 135 d 轮 / 137 a 轮各犯一次）
    const z = await setZoom(p, pct);
    const r = await 读组态全(p);
    const 档 = { 标称: pct, setZoom: z, ...r };
    // 每档现算：这一档量到的「卡片 canvas 宽」和「工具条屏上宽」
    档.算 = r.组 && r.外层 ? {
      卡片canvas宽: r.组.canvas宽,
      卡片屏上宽: r.组.屏上.w,
      工具条屏上宽: r.外层.w,
      工具条offsetWidth: r.外层.offsetWidth,
      实测scale: r.scale,
      '卡片×scale': r.组.canvas宽 * (r.scale || 0),
      '多选公式(卡片+80)×scale': (r.组.canvas宽 + 80) * (r.scale || 0),
    } : null;
    rec.四档.push(档);
    断言(`③${pct}% 实测 scale 已追平`, z.scale已追平 === true, { setZoom: z, 实测: r.scale });
  }

  // ---- 公式判定（用读数算，不预设）
  rec.判定 = rec.四档.map((d) => ({
    标称: d.标称, 实测scale: d.scale, 卡片canvas宽: d.算 && d.算.卡片canvas宽,
    工具条屏上宽: d.算 && d.算.工具条屏上宽, 卡片屏上宽: d.算 && d.算.卡片屏上宽,
    '工具条==卡片×scale': d.算 ? d.算.工具条屏上宽 === d.算.卡片canvas宽 * d.scale : null,
    '工具条==卡片屏上宽': d.算 ? d.算.工具条屏上宽 === d.算.卡片屏上宽 : null,
  }));
  rec.公式成立档数 = rec.判定.filter((x) => x['工具条==卡片×scale']).length;
  断言('④「工具条屏上宽 == 卡片canvas宽 × scale」四档全成立', rec.公式成立档数 === 4, rec.判定);
  // 反向：是不是恒定（那才叫「不随缩放」）
  rec.工具条是否恒定 = new Set(rec.四档.map((d) => d.算 && d.算.工具条屏上宽)).size === 1;
  断言('⑤工具条宽度**不是**恒定（否则前一条的成立只是巧合）', rec.工具条是否恒定 === false,
    { 各档屏上宽: rec.四档.map((d) => d.算 && d.算.工具条屏上宽) });
  // 反向：组卡片 canvas 宽在四档里应**恒定**（它是节点的 style.width）
  const 卡片恒定 = new Set(rec.四档.map((d) => d.算 && d.算.卡片canvas宽)).size === 1;
  rec.卡片canvas宽是否恒定 = 卡片恒定;
  断言('⑥组卡片 canvas 宽四档恒定（证明自变量真的只有缩放）', 卡片恒定,
    { 各档: rec.四档.map((d) => d.算 && d.算.卡片canvas宽) });
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 600); }

// ---- 收尾：缩放归 60% + 重开小地图
try {
  const z = await setZoom(p, 60);
  rec.归位 = { setZoom: z, zoom: await R.zoom(), 归位后连读: await R.zoom() };
  if ((await R.minimap()) && (await R.minimap()).ariaPressed !== 'true') {
    const mm = await p.evaluate(() => {
      const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]');
      if (!e) return { __err: 'not-found' };
      const r = e.getBoundingClientRect();
      for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
        for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
          const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y };
        }
      return { __err: 'no-point' };
    });
    rec.重开小地图 = mm;
    if (!mm.__err) { await p.mouse.click(mm.x, mm.y); await p.waitForTimeout(1500); }
  }
  rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p),
    选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom(), minimap: await R.minimap() };
} catch (e) { rec.收尾异常 = String(e && e.message).slice(0, 300); }

rec.断言全过 = 全过;
fs.writeFileSync(new URL('./_tmp-b139b.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify(rec.判定 || rec, null, 1));
console.log('断言全过', 全过);
await b.close();
