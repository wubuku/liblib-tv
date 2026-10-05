// 会话 mvs_fb62b78 · 批次 211 b 轮：在**同一个缩放**下测 before ⊕ / after ⊕，带阳性对照。
//
// 靶子（`connect-nodes.md:573`）：「带内容的图片节点只有 after ⊕」—— 批次 59/73 两次观测，
//   **机制未验证**。🔴 而 `20-reference.md:309` 记过一次教训：「两次都错在拿不同缩放的读数互比」。
//
// 本轮三个受控点：
//  ① **同一缩放**：先把画布缩放到 `100%`（全程同一个值，读数的那一刻再读一次缩放核对），
//     测完**复原回 26%**。⚠️ 不在同一缩放上比 before ⊕ 有没有，等于没比（批次 59/73 的老坑）。
//  ② **阳性对照**：`视频 1`（手册矩阵里 before + after 都有）同缩放同流程必须读到 before ⊕ = 1；
//     若对照臂也读到 0，说明是条件把入口整体压掉了，不是「图片带内容」的属性。
//  ③ **硬断言 `selected === 1`**：批次 203 实测 `26%` 档单击只展开变体、**不选中**（要点两下）；
//     批次 160 还记过「节点会互相压住，点之前先验那个坐标上是谁」。
//     ⇒ 读 ⊕ 之前必须先确认这个节点真的进了选中态，否则读到的是「没选中时本来就没有 ⊕」。
//
// 本轮**只做只读测量 + 改一次缩放（收尾复原）**，不新建/删除节点、不上传。
import fs from 'node:fs';
import { openCanvas, readers, setZoom } from './jimeng-b135-lib.mjs';
import { idsOf, selCount } from './jimeng-b139-lib.mjs';

const 目标集 = [
  { 名: 'b22-upload', 搜索词: 'b22', 预期: '🔴 只有 after（手册：带内容的图片节点没有 before）' },
  { 名: '视频 1', 搜索词: '视频', 预期: '✅ 阳性对照：before + after 都有' },
];
const OUT = 'scripts/_tmp-b211b.json';
const rec = { 批次: '211b', 目的: '同缩放下测 before/after ⊕，带阳性对照', 目标集, 臂: {}, 无效臂: 0 };
const 落盘 = () => fs.writeFileSync(OUT, JSON.stringify(rec, null, 1));
let 断言过 = true;
const 断言 = (名, ok, d) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(d).slice(0, 200))); return v; };

const { b, p } = await openCanvas();
const R = readers(p);
const 缩放原 = await R.zoom();
rec.起点 = { 缩放原, 节点数: (await idsOf(p)).length, 选中: await selCount(p), 积分: await R.credits(), 状态行: await R.status() };
console.log('起点', JSON.stringify(rec.起点));
rec.起点缩放原 = 缩放原;

try {
  断言('⓪ 护栏：76 节点 / 0 选中 / 积分 791', rec.起点.节点数 === 76 && rec.起点.选中 === 0, rec.起点);

  // ===== 固定缩放 =====
  await setZoom(p, 100);
  await p.waitForTimeout(1500);
  rec.测时缩放 = await R.zoom();
  断言('① 缩放已固定在 100%', /100/.test(rec.测时缩放 || ''), { 测时缩放: rec.测时缩放 });
  console.log('测时缩放', rec.测时缩放);

  // 建索引：标题 → node id
  const 索引 = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((n) => [
    ((n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || '').trim() || n.getAttribute('data-id'),
    n.getAttribute('data-id')])));

  for (const t of 目标集) {
    const id = 索引[t.名];
    if (!id) { rec.臂[t.名] = { 无效: '画布上找不到该标题的节点', 现有标题样本: Object.keys(索引).slice(0, 8) }; rec.无效臂++; 落盘(); continue; }
    try {
      // 用搜索取景把它弄到屏幕中央（批次 210 已验证的完整流程，不按 Esc）
      await p.keyboard.press('Escape'); await p.waitForTimeout(300);
      const 搜索钮 = await p.evaluate(() => {
        const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
          || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
        if (!e) return null; const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      });
      if (!搜索钮) { rec.臂[t.名] = { 无效: '找不到搜索钮' }; rec.无效臂++; 落盘(); continue; }
      await p.mouse.click(搜索钮[0], 搜索钮[1]); await p.waitForTimeout(1000);
      await p.evaluate(() => {
        const e = document.querySelector('input[aria-label*="搜索"],input[type="text"]');
        if (e) { Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(e, ''); e.dispatchEvent(new Event('input', { bubbles: true })); }
      });
      await p.keyboard.type(t.搜索词, { delay: 80 });
      await p.waitForTimeout(2200);
      // 🔴 第一版按 `innerText.includes('视频 1')` 找行 ⇒ 两臂都「搜索无结果」。
      //   改成**按 node id 精确匹配 testid**（`canvas-search-result-<id>`），
      //   顺带把「面板里到底有哪些行」记下来 —— 无效臂要留下原因，不能只留一个 continue。
      const 行 = await p.evaluate((nid) => {
        const all = Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'));
        const e = document.querySelector(`[data-testid="canvas-search-result-${nid}"]`) || all[0] || null;
        if (!e) return { 没有: true, 行数: all.length, 现有testid: all.slice(0, 8).map((x) => x.getAttribute('data-testid')) };
        const r = e.getBoundingClientRect();
        return { testid: e.getAttribute('data-testid'), 内文: (e.innerText || '').replace(/\s+/g, ' ').trim(),
          行数: all.length, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
      }, id);
      if (行.没有) { rec.臂[t.名] = { 无效: '搜索结果里没有这一行', 行 }; rec.无效臂++;
        console.log(t.名, '⛔ 无效臂，面板内容：', JSON.stringify(行).slice(0, 300)); 落盘(); continue; }
      console.log(`  取景行 ${行.testid}（面板共 ${行.行数} 行，内文「${行.内文}」）`);
      await p.mouse.click(行.点[0], 行.点[1]);
      await p.waitForTimeout(2200);

      // 硬断言：点它自己 → 必须真的选中
      const 点前 = await selCount(p);
      const 点位 = await p.evaluate((nid) => {
        const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
        if (!n) return null;
        const r = n.getBoundingClientRect();
        return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 屏上: [r.x, r.y, r.width, r.height].map(Math.round) };
      }, id);
      if (!点位) { rec.臂[t.名] = { 无效: '取景后画布上找不到该节点' }; rec.无效臂++; 落盘(); continue; }
      await p.mouse.click(点位.中心[0], 点位.中心[1]);
      await p.waitForTimeout(1600);
      let 选中数 = await selCount(p);
      // `26%` 档单击只展开变体不选中（批次 203）；若仍未选中，再点一次并**如实记录补点**
      let 补点次数 = 0;
      if (选中数 !== 1) {
        补点次数 = 1;
        await p.mouse.click(点位.中心[0], 点位.中心[1]);
        await p.waitForTimeout(1400);
        选中数 = await selCount(p);
      }
      const okSel = 断言(`${t.名}：真的选中了（selected===1）`, 选中数 === 1, { 点前, 选中数, 补点: 补点次数 });

      const 读 = await p.evaluate((nid) => {
        const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
        if (!n) return { 找不到节点: true };
        const q = (s) => Array.from(n.querySelectorAll(`[data-testid="${s}"]`));
        const 描 = (arr) => arr.map((e) => { const r = e.getBoundingClientRect(); return { aria: e.getAttribute('aria-label'), 尺寸: [Math.round(r.width), Math.round(r.height)] }; });
        const 全页before = document.querySelectorAll('[data-testid="flow-node-target-connection-menu-button"]').length;
        const 全页after = document.querySelectorAll('[data-testid="flow-node-source-connection-menu-button"]').length;
        const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
        return {
          本节点before: 描(q('flow-node-target-connection-menu-button')),
          本节点after: 描(q('flow-node-source-connection-menu-button')),
          全页before, 全页after,
          资源账: ((n.innerText || '').match(/[\d]+ resource[s]?:[^\n]*/) || [])[0] || ((n.innerText || '').match(/[\d]+\s*ready[^\n]*/) || [])[0] || null,
          有audio: !!n.querySelector('audio'), 有img: !!n.querySelector('img'),
          空态testid: Array.from(n.querySelectorAll('[data-testid$="-empty"]')).map((e) => e.getAttribute('data-testid')),
          测量时缩放: z ? z.getAttribute('aria-label') : null,
          内文: (n.innerText || '').replace(/\s+/g, ' ').slice(0, 120),
        };
      }, id);

      rec.臂[t.名] = { id, 预期: t.预期, 取景行: 行.testid, 点位, 点前, 选中数, 补点: 补点次数, 硬断言选中过: okSel, 读 };
      console.log(`\n[${t.名}] 预期 ${t.预期}`);
      console.log('   before ⊕ =', 读.本节点before.length, JSON.stringify(读.本节点before));
      console.log('   after  ⊕ =', 读.本节点after.length, JSON.stringify(读.本节点after));
      console.log('   全页 before/after =', 读.全页before, '/', 读.全页after, '｜ 缩放', 读.测量时缩放);
      console.log('   资源账', JSON.stringify(读.资源账), '｜ 空态', JSON.stringify(读.空态testid));
    } catch (e) { rec.臂[t.名] = { 出错: e.message }; rec.无效臂++; console.log(t.名, '🔴', e.message); }
    finally { 落盘(); }
  }
} finally {
  // ===== 收尾：把缩放复原回原值 =====
  try {
    await p.keyboard.press('Escape'); await p.waitForTimeout(300);
    await setZoom(p, parseInt(String(缩放原).match(/(\d+)%/)?.[1] || '26', 10));
    await p.waitForTimeout(1200);
  } catch (e) { rec.复原错 = e.message; }
  rec.收尾 = { 缩放: await R.zoom(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 积分: await R.credits(), 状态行: await R.status() };
  console.log('\n收尾', JSON.stringify(rec.收尾));
  断言('② 收尾：缩放复原 / 76 节点 / 0 选中 / 积分未变',
    rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.缩放 === 缩放原 && rec.收尾.积分 === rec.起点.积分,
    { 复原到: 缩放原, 收尾: rec.收尾 });
  rec.断言全过 = 断言过;
  落盘();
  await b.close();
}
