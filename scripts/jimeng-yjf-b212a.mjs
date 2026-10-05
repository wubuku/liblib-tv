// 会话 mvs_fb62b78 · 批次 212 a 轮：结清「**选中之后描述会不会改**」这条未取证。
//
// 靶子（`20-reference.md` 描述宿主那一节）：
//   「⚠️ 但「选中之后它会不会改」**本批没测到**：4 种类型里 **3 种点不中**
//     （脚本算出的「标题落点」和「节点落点」是**同一个坐标**，实际只试了一个点），
//      唯一选中的图片节点那条描述**本来就是空的**。
//     ⇒ 如实记为**未取证**，不写成「选中后描述不变」。」
//
// 🔴 上一轮失败的原因**不是**点不中，是**只试了一个点** —— 而那个点算错了。
//   本轮直接用批次 211c 验证过的办法（同一套代码路径）：
//   ① 归属判据：`elementFromPoint` 必须落在目标节点子树内（候选点 ≤24，一次不行换下一个）；
//   ② 点完**硬断言** `selected === 1` 且选中集里就是目标 id（`26%` 档单击只展开不选中）；
//   ③ 断言不过就写成**无效臂**并记原因，**绝不用兜底点别的节点**（立规 90）。
//
// 本轮只读：不改任何东西，不新建/删除节点。选中是允许的副作用，收尾清回 0。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { idsOf, selCount } from './jimeng-b139-lib.mjs';

const 目标集 = ['文本 1', '时间线 1', '音频 68', 'b22-upload', '视频 1', '导演台'];
const OUT = 'scripts/_tmp-b212a.json';
const rec = { 批次: '212a', 靶子: '20-reference.md「选中之后描述会不会改」未取证',
  读的是什么: '节点 aria-describedby 指向的那个宿主的 innerText（未选中 vs 选中）',
  目标集, 臂: {}, 无效臂: 0 };
const 落盘 = () => fs.writeFileSync(OUT, JSON.stringify(rec, null, 1));
let 全过 = true;
const 断言 = (名, ok, d) => { const v = !!ok; if (!v) 全过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(d).slice(0, 240))); return v; };

/** 读一个节点的「描述宿主 + 描述逐字」。`nid` 传 null 表示「这个类型没有节点」。 */
const 读描述 = (nid) => p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!n) return { 节点不在: true };
  const ids = (n.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean);
  const 宿主 = ids.map((x) => document.getElementById(x)).filter(Boolean);
  const r = n.getBoundingClientRect();
  return {
    节点屏上: [r.x, r.y, r.width, r.height].map(Math.round),
    描述id列表: ids,
    宿主数: 宿主.length,
    宿主逐个: 宿主.map((h) => {
      const q = h.getBoundingClientRect();
      return { tag: h.tagName, testid: h.getAttribute('data-testid'),
        是节点根: h === n, 是节点子树内: n.contains(h),
        面积: [Math.round(q.width), Math.round(q.height)],
        innerText: (h.innerText || '').replace(/\s+/g, ' ').trim(),
        textContent: (h.textContent || '').replace(/\s+/g, ' ').trim() };
    }),
    节点自身innerText: (n.innerText || '').replace(/\s+/g, ' ').trim(),
    选中态: n.classList.contains('selected'),
  };
}, nid);

const { b, p } = await openCanvas();
const R = readers(p);
try {
  rec.起点 = { 缩放: await R.zoom(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 积分: await R.credits(), 浮层: await R.overlays() };
  console.log('起点', JSON.stringify(rec.起点));
  断言('⓪ 76 节点 / 0 选中 / 浮层 0', rec.起点.节点数 === 76 && rec.起点.选中 === 0, rec.起点);

  const 索引 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
    id: n.getAttribute('data-id'), 标题: ((n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || '').trim() })));
  rec.索引样本 = 索引.slice(0, 6);

  for (const 标题 of 目标集) {
    const hit = 索引.find((x) => x.标题 === 标题);
    if (!hit) { rec.臂[标题] = { 无效: '画布上找不到该标题', 现有标题: Array.from(new Set(索引.map((x) => x.标题))).slice(0, 10) };
      rec.无效臂++; console.log(标题, '⛔ 找不到节点'); 落盘(); continue; }
    try {
      // —— 未选中态 ——
      const 前 = await 读描述(hit.id);

      // —— 归属判据拿候选点 ——
      const 候选 = await p.evaluate((nid) => {
        const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return [];
        const r = n.getBoundingClientRect(); const 好 = [];
        for (let fy = 0.15; fy <= 0.86; fy += 0.14) for (let fx = 0.15; fx <= 0.86; fx += 0.14) {
          const x = r.x + r.width * fx, y = r.y + r.height * fy;
          if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
          const e = document.elementFromPoint(x, y);
          if (e && n.contains(e)) { 好.push([Math.round(x), Math.round(y)]); if (好.length >= 24) break; }
        }
        return 好;
      }, hit.id);
      if (!候选.length) { rec.臂[标题] = { 无效: '无归属候选点（被别的节点盖住）', id: hit.id, 前 }; rec.无效臂++;
        console.log(标题, '⛔ 无归属点'); 落盘(); continue; }

      // —— 点到选中为止（如实记补点次数）——
      let 选中集 = [], 补点 = 0;
      for (let k = 0; k < 3; k++) {
        await p.mouse.click(候选[0][0], 候选[0][1]); 补点 = k + 1; await p.waitForTimeout(1500);
        选中集 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
        if (选中集.length === 1 && 选中集[0] === hit.id) break;
      }
      const 选中了 = 选中集.length === 1 && 选中集[0] === hit.id;
      断言(`${标题}：真的选中了`, 选中了, { 选中集, 补点, 目标: hit.id });

      // —— 选中态 ——
      const 后 = 选中了 ? await 读描述(hit.id) : null;

      // 逐字比较：到底改没改
      const 逐字前 = 前.宿主逐个?.map((h) => h.innerText) || [];
      const 逐字后 = 后?.宿主逐个?.map((h) => h.innerText) || [];
      rec.臂[标题] = {
        id: hit.id, 前, 后, 补点, 选中了, 无效: 选中了 ? null : `点了 ${补点} 次仍没选中（选中集 ${JSON.stringify(选中集)}）`,
        对比: {
          宿主数一致: 前.宿主数 === 后?.宿主数,
          逐字前, 逐字后,
          变了: JSON.stringify(逐字前) !== JSON.stringify(逐字后),
          末句前: 逐字前.map((s) => (s || '').slice(-14)),
          末句后: 逐字后.map((s) => (s || '').slice(-14)),
        },
      };
      if (!选中了) rec.无效臂++;
      console.log(`\n[${标题}] ${前.宿主数} 个描述宿主 ｜ 宿主是节点根? ${前.宿主逐个?.map((h) => h.是节点根)}`);
      console.log('   未选中 逐字：', JSON.stringify(逐字前));
      console.log('   选中后 逐字：', JSON.stringify(逐字后), '｜ 变了?', rec.臂[标题].对比.变了);
      console.log('   末句 前→后：', JSON.stringify(rec.臂[标题].对比.末句前), '→', JSON.stringify(rec.臂[标题].对比.末句后));
    } catch (e) { rec.臂[标题] = { 出错: e.message }; rec.无效臂++; console.log(标题, '🔴', e.message); }
    finally {
      // 每臂结束都把选中态清掉，免得下一臂在「上一个还选中」的状态下开跑
      try { await p.keyboard.press('Escape'); await p.waitForTimeout(300);
        if (await selCount(p) > 0) { await p.mouse.click(30, 660); await p.waitForTimeout(700); } } catch {}
      落盘();
    }
  }
} finally {
  try {
    await p.keyboard.press('Escape'); await p.waitForTimeout(300);
    if (await selCount(p) > 0) { await p.mouse.click(30, 660); await p.waitForTimeout(700); }
  } catch (e) { rec.清场错 = e.message; }
  rec.收尾 = { 缩放: await R.zoom(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(), 积分: await R.credits(), 状态行: await R.status() };
  console.log('\n收尾', JSON.stringify(rec.收尾));
  断言('② 收尾：76 节点 / 0 选中 / 0 边 / 浮层 0 / 积分未变 / 缩放未动',
    rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0
    && rec.收尾.积分 === rec.起点.积分 && rec.收尾.缩放 === rec.起点.缩放 && /0 edges/.test(rec.收尾.状态行 || ''),
    { 起点: rec.起点, 收尾: rec.收尾 });
  rec.断言全过 = 全过;
  rec.无效臂 = Object.values(rec.臂).filter((x) => x && x.无效).length;
  console.log('无效臂：', rec.无效臂, '/', 目标集.length);
  落盘();
  await b.close();
}
