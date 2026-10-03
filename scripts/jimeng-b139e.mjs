// 批次 139 c 轮：把「296 是下限」这件事**验死**，并顺手解释手册 47% 那行读数。
//
// 🔑 b 轮四档：60/100/200 三档都满足 `工具条屏上宽 == 卡片canvas宽 × scale`，
//   **唯独 40% 不成立**：卡片屏上只有 `224`，工具条却读 `296` —— **工具条比卡片还宽 72px**。
//   而内层 `selection-context-toolbar` 四档**恒为 `296×40`**。
//   ⇒ 假设：外层宽 = `max(卡片canvas宽 × scale, 内层固有宽 296)`。
//
// 本轮把假设拆成可分辨的预测，再逐条验：
//   P1 下限值**逐字等于**内层 `selection-context-toolbar` 的屏上宽（本组应恒为 296）。
//   P2 存在**交叉点** `卡片canvas宽 × scale == 296` ⇒ `560 × 0.5286 = 296` ⇒
//      缩放 **50%** 应**恰好**等于 296（刚好在交叉点上），**45%** 应被下限接管（= 296），
//      **55%** 应脱离下限（> 296）。三档一起验，才能证明「是 max() 不是巧合」。
//   P3 内层宽度四档**恒定**（它是「内容撑出来的」，与卡片和缩放都无关）。
//
// ⚠️ 手册 47% 那行 `296×40` 很可能就是**同一个下限**（`560 × 0.47 = 263.2 < 296` ⇒ 取 296），
//   本轮顺带算一下，把「卡片宽度不同所致」这个归因查个底。
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 读组态全, 组数, idsOf, selCount } from './jimeng-b139-lib.mjs';
import fs from 'node:fs';

// 🔴 交叉点附近密集取档：45 / 50 / 55 / 53 / 52 四档，逼近 296/560 = 0.528571
const 档位 = [45, 50, 53, 55, 60];
const rec = { 轮: '139c', 档位 };
const { b, p } = await openCanvas();
const R = readers(p);
let 全过 = true;
const 断言 = (名, ok, 详情) => { (rec.断言 = rec.断言 || []).push({ 名, 通过: !!ok, 详情 }); if (!ok) 全过 = false; };

try {
  await keyGuard(p);
  await settle(p, R);
  const 组前 = await p.evaluate(() => {
    const 真身 = Array.from(document.querySelectorAll('.react-flow__node-group'))
      .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''));
    return { 真身数: 真身.length, canvas: 真身[0] ? { w: 真身[0].offsetWidth, h: 真身[0].offsetHeight } : null,
      选中数: 真身[0] ? 真身[0].classList.contains('selected') : false };
  });
  rec.组前 = 组前;
  断言('①起始恰好 1 个真身组卡片且选中', 组前.真身数 === 1 && 组前.选中数, 组前);

  rec.各档 = [];
  for (const pct of 档位) {
    // 🔴 无条件设缩放：不写任何跳过分支（批次 135 d 轮 / 137 a 轮各犯一次同一个 bug）
    const z = await setZoom(p, pct);
    const r = await 读组态全(p);
    const 卡片 = r.组 ? r.组.canvas宽 : null;
    const 内层 = r.inner ? r.inner.w : null;
    rec.各档.push({
      标称: pct, 追平: z.scale已追平, 实测scale: r.scale,
      卡片canvas宽: 卡片, 卡片屏上宽: r.组 && r.组.屏上.w,
      工具条屏上宽: r.外层 && r.外层.w, 工具条offset: r.外层 && r.外层.offsetWidth,
      内层屏上宽: 内层, 内层offset: r.inner && r.inner.offsetWidth,
      '预测max(卡片×scale, 内层)': (卡片 !== null && 内层 !== null) ? Math.max(卡片 * r.scale, 内层) : null,
      '实测算式': (卡片 !== null && r.scale) ? (卡片 * r.scale) : null,
      逐字: r.逐字, 按钮数: r.按钮 && r.按钮.length,
    });
  }

  rec.判定 = rec.各档.map((d) => ({
    标称: d.标称, scale: d.实测scale, '卡片×scale': d.实测算式, 内层: d.内层屏上宽,
    实测工具条: d.工具条屏上宽, max预测: d['预测max(卡片×scale, 内层)'],
    'max公式成立': d.工具条屏上宽 === d['预测max(卡片×scale, 内层)'],
    '纯乘法成立': d.工具条屏上宽 === d.实测算式,
  }));

  // P1：下限逐字等于内层宽
  rec.内层各档 = rec.各档.map((d) => d.内层屏上宽);
  rec.内层是否恒定 = new Set(rec.内层各档).size === 1;
  断言('P3 内层 selection-context-toolbar 五档恒定', rec.内层是否恒定, { 各档: rec.内层各档 });
  const 下限 = rec.内层各档[0];
  rec.下限 = 下限;
  rec.被下限接管的档 = rec.各档.filter((d) => d.实测算式 < 下限).map((d) => ({ 标称: d.标称, '卡片×scale': d.实测算式, 工具条: d.工具条屏上宽 }));
  断言('P1 存在被下限接管的档（卡片×scale < 内层宽）', rec.被下限接管的档.length > 0, { 下限, 被接管: rec.被下限接管的档 });
  // P1b：被接管的档，工具条**恰好等于**内层宽
  断言('P1b 被接管档的工具条逐字 == 内层宽', rec.被下限接管的档.every((d) => d.工具条 === 下限), { 下限, 被接管: rec.被下限接管的档 });
  // P2：max 公式五档全成立
  断言('P2 max(卡片canvas宽×scale, 内层固有宽) 五档全成立',
    rec.判定.every((d) => d['max公式成立']), rec.判定);
  // P2b：至少有一档「纯乘法成立」且至少一档「纯乘法不成立」⇒ 证明 max 不是恒等式
  const 纯乘 = rec.判定.filter((d) => d['纯乘法成立']).length;
  rec.纯乘法成立档数 = 纯乘;
  断言('P2b 既有纯乘法成立的档、也有不成立的档（否则 max 退化成恒等）',
    纯乘 > 0 && 纯乘 < rec.判定.length, { 纯乘, 总档: rec.判定.length, 判定: rec.判定 });

  // ---- 手册 47% 那行的算术复核
  rec.手册复核 = {
    手册行: '3 个文本节点 | 47% | 296×40',
    本组卡片canvas宽: rec.各档[0].卡片canvas宽,
    '560 × 0.47': Math.round(560 * 0.47 * 10) / 10,
    '若纯乘法应为': Math.round(560 * 0.47 * 10) / 10,
    '但实测/手册记的是': 296,
    '被下限接管?': 560 * 0.47 < 下限,
    '结论': '560 × 0.47 = 263.2 < 296 ⇒ 该行读数等于下限，不是「卡片宽度不同」造成的',
  };
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 600); }

try {
  const z = await setZoom(p, 60);
  rec.归位 = { zoom: await R.zoom(), 连读: await R.zoom(), 追平: z.scale已追平 };
  if ((await R.minimap()) && (await R.minimap()).ariaPressed !== 'true') {
    const mm = await p.evaluate(() => {
      const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); if (!e) return { __err: 'nf' };
      const r = e.getBoundingClientRect();
      for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
        for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
          const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y };
        }
      return { __err: 'np' };
    });
    if (!mm.__err) { await p.mouse.click(mm.x, mm.y); await p.waitForTimeout(1500); }
    rec.重开小地图 = mm;
  }
  rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p),
    选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom(), minimap: await R.minimap() };
} catch (e) { rec.收尾异常 = String(e && e.message).slice(0, 300); }

rec.断言全过 = 全过;
fs.writeFileSync(new URL('./_tmp-b139c.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify(rec.判定 || rec, null, 1));
console.log('手册复核', JSON.stringify(rec.手册复核, null, 1));
console.log('断言全过', 全过);
await b.close();
