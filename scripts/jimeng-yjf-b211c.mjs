// 会话 mvs_fb62b78 · 批次 211 c 轮：**不用搜索**，用「归属判据 + 硬断言选中」直接测。
//
// 🔴 b 轮为什么作废：找不到目标 testid 时我写了 `|| all[0]` 兜底 ⇒ 两臂都点了**第一条**
//   （`node_tadm1nyykc`「音频 68」），却在**目标节点自己的子树**里读 ⊕ ⇒
//   读到 0/0，而全页是 1/1。**读数看着整齐、还过了「selected===1」断言，其实测错了对象。**
//   📌 立规 90（见 30-concepts）：**兜底分支会掩盖「目标不存在」**。
//     「点不到目标」必须写成无效臂，**绝不能退回「点第一个」** —— 后者会产出一份
//     格式完好、断言全过、但**对象是错的**读数，比直接失败危险得多。
//
// 本轮做法（全程**不搜索、不平移**）：
//  ① 停在 **26% 自适应档**（76 个节点全部在视口内，节点画布坐标已知可换算屏幕坐标）；
//  ② 点之前先跑**归属判据**：`document.elementFromPoint(中心)` 必须落在**目标节点子树内**
//     —— 立规 82（批次 203：42 个视口内节点里 18 个中心被别的节点盖住）。
//     归属不通过 ⇒ **换候选点，最多 24 个**；一个都不通过 ⇒ 该臂标无效臂。
//  ③ 点之后**硬断言 `selected===1` 且选中集里就是目标 id**（`26%` 档单击只展开不选中，
//     批次 203）⇒ 最多点 3 次，如实记录补点次数。
//  ④ 读 ⊕ 时同时读**本节点子树**与**全页**计数，两者不一致本身就是一条结论。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { idsOf, selCount } from './jimeng-b139-lib.mjs';

const 目标集 = [
  { 标题: 'b22-upload', 预期: '🔴 手册：带内容的图片节点只有 after' },
  { 标题: '视频 1', 预期: '✅ 手册矩阵：视频 before + after' },
  { 标题: '音频 68', 预期: '✅ 手册矩阵：音频 before + after（本轮新测）' },
  { 标题: '文本 1', 预期: '✅ 手册矩阵：文本只有 after' },
];
const OUT = 'scripts/_tmp-b211c.json';
const rec = { 批次: '211c', 测的量: 'flow-node-{target,source}-connection-menu-button 计数',
  作废的b轮: '兜底 `|| all[0]` 导致两臂都测了「音频 68」却读在目标节点上（立规 90）',
  目标集, 臂: {}, 无效臂: 0 };
const 落盘 = () => fs.writeFileSync(OUT, JSON.stringify(rec, null, 1));
let 全过 = true;
const 断言 = (名, ok, d) => { const v = !!ok; if (!v) 全过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(d).slice(0, 240))); return v; };

const { b, p } = await openCanvas();
const R = readers(p);
try {
  // 先把上一轮残留的选中清掉（b 轮收尾断言红了：selected 停在 1）
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  if (await selCount(p) > 0) {
    await p.mouse.click(30, 660); await p.waitForTimeout(800);   // 点空白处
  }
  rec.起点 = { 缩放: await R.zoom(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));
  断言('⓪ 清场后：76 节点 / 0 选中 / 积分 791', rec.起点.节点数 === 76 && rec.起点.选中 === 0, rec.起点);

  const 索引 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
    id: n.getAttribute('data-id'),
    标题: ((n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || '').trim(),
  })));

  for (const t of 目标集) {
    const hit = 索引.find((x) => x.标题 === t.标题);
    if (!hit) { rec.臂[t.标题] = { 无效: '画布上找不到该标题', 现有标题: 索引.slice(0, 10).map((x) => x.标题) };
      rec.无效臂++; 落盘(); continue; }
    try {
      // ② 归属判据：找一批「命中目标子树」的候选点
      const 候选 = await p.evaluate((nid) => {
        const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
        if (!n) return { 节点不在视口: true };
        const r = n.getBoundingClientRect();
        const pts = [];
        for (let fy = 0.15; fy <= 0.86; fy += 0.14) for (let fx = 0.15; fx <= 0.86; fx += 0.14) pts.push([fx, fy]);
        const 好 = [];
        for (const [fx, fy] of pts) {
          const x = r.x + r.width * fx, y = r.y + r.height * fy;
          if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
          const e = document.elementFromPoint(x, y);
          if (e && n.contains(e)) 好.push([Math.round(x), Math.round(y)]);
          if (好.length >= 24) break;
        }
        return { 屏上: [r.x, r.y, r.width, r.height].map(Math.round), 好点: 好, 候选总数: pts.length };
      }, hit.id);

      if (候选.节点不在视口) { rec.臂[t.标题] = { 无效: '节点不在 DOM/视口内', id: hit.id }; rec.无效臂++; 落盘(); continue; }
      if (!候选.好点.length) { rec.臂[t.标题] = { 无效: '24 个候选点没有一个归属本节点（被别的节点盖住）', id: hit.id, 候选 };
        rec.无效臂++; console.log(t.标题, '⛔ 无归属点', JSON.stringify(候选.屏上)); 落盘(); continue; }
      console.log(`\n[${t.标题}] 屏上 ${JSON.stringify(候选.屏上)}｜归属候选点 ${候选.好点.length} 个（试 ${候选.屏上}）`);

      // ③ 点到真的选中为止（26% 档单击只展开不选中 ⇒ 批次 203），逐次如实记录
      let 选中数 = 0, 选中集 = [], 用了点 = null, 补点次数 = 0;
      for (let k = 0; k < 3; k++) {
        await p.mouse.click(候选.好点[0][0], 候选.好点[0][1]);
        补点次数 = k + 1;
        await p.waitForTimeout(1500);
        选中数 = await selCount(p);
        选中集 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
        if (选中数 === 1 && 选中集[0] === hit.id) { 用了点 = 候选.好点[0]; break; }
      }
      const okSel = 断言(`${t.标题}：选中集恰好是它自己（selected===1 且 id 匹配）`,
        选中数 === 1 && 选中集[0] === hit.id, { 选中数, 选中集, 补点次数, 目标: hit.id });

      const 读 = await p.evaluate((nid) => {
        const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
        if (!n) return { 找不到节点: true };
        const q = (s) => Array.from(n.querySelectorAll(`[data-testid="${s}"]`));
        const 描 = (arr) => arr.map((e) => { const r = e.getBoundingClientRect();
          return { aria: e.getAttribute('aria-label'), 尺寸: [Math.round(r.width), Math.round(r.height)] }; });
        const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
        const 内 = (n.innerText || '').replace(/\s+/g, ' ');
        return {
          本节点before: 描(q('flow-node-target-connection-menu-button')),
          本节点after: 描(q('flow-node-source-connection-menu-button')),
          全页before: document.querySelectorAll('[data-testid="flow-node-target-connection-menu-button"]').length,
          全页after: document.querySelectorAll('[data-testid="flow-node-source-connection-menu-button"]').length,
          资源账: (内.match(/\d+ resource[s]?:[^A-Z]*/) || 内.match(/\d+ ready[^A-Z]*/) || [])[0] || null,
          有img: !!n.querySelector('img'), 有audio: !!n.querySelector('audio'), 有video: !!n.querySelector('video'),
          空态testid: Array.from(n.querySelectorAll('[data-testid$="-empty"]')).map((e) => e.getAttribute('data-testid')),
          媒体层: !!n.querySelector('[data-testid="flow-node-media-stroke"]'),
          测量时缩放: z ? z.getAttribute('aria-label') : null,
          内文: 内.slice(0, 140),
        };
      }, hit.id);

      rec.臂[t.标题] = { id: hit.id, 预期: t.预期, 屏上: 候选.屏上, 归属候选点数: 候选.好点.length,
        用了点, 补点次数, 选中数, 选中集, 硬断言选中过: okSel, 读 };
      console.log(`   预期 ${t.预期}`);
      console.log(`   本节点 before=${读.本节点before.length} after=${读.本节点after.length} ｜ 全页 before=${读.全页before} after=${读.全页after}`);
      console.log(`   before aria ${JSON.stringify(读.本节点before.map((x) => x.aria))}`);
      console.log(`   after  aria ${JSON.stringify(读.本节点after.map((x) => x.aria))}`);
      console.log(`   缩放 ${读.测量时缩放} ｜ 资源账 ${JSON.stringify(读.资源账)} ｜ img/audio/video ${读.有img}/${读.有audio}/${读.有video} ｜ 空态 ${JSON.stringify(读.空态testid)}`);
    } catch (e) { rec.臂[t.标题] = { 出错: e.message }; rec.无效臂++; console.log(t.标题, '🔴', e.message); }
    finally { 落盘(); }
  }
} finally {
  try {
    await p.keyboard.press('Escape'); await p.waitForTimeout(300);
    if (await selCount(p) > 0) { await p.mouse.click(30, 660); await p.waitForTimeout(800); }
  } catch (e) { rec.清场错 = e.message; }
  rec.收尾 = { 缩放: await R.zoom(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 积分: await R.credits(), 状态行: await R.status() };
  console.log('\n收尾', JSON.stringify(rec.收尾));
  断言('② 收尾：76 节点 / 0 选中 / 0 边 / 积分未变 / 缩放未动',
    rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.积分 === rec.起点.积分
    && rec.收尾.缩放 === rec.起点.缩放 && /0 edges/.test(rec.收尾.状态行 || ''), { 起点: rec.起点, 收尾: rec.收尾 });
  rec.断言全过 = 全过;
  落盘();
  await b.close();
}
