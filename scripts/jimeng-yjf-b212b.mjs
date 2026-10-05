// 会话 mvs_fb62b78 · 批次 212 b 轮：补齐 a 轮没跑完的臂，并**复现** a 轮那两个真发现。
//
// a 轮发生了什么（如实记）：
//  ① 🔴 **共享画布漂了**：跑 a 轮时是 **79 节点 / 积分 813**（a 轮基线断言因此判红，
//     这是**对的** —— 别把「76」当常数）。另有会话新建了 3 个节点。
//     ⇒ 本轮**不把 76 当基线、不删任何东西、不碰别人的节点**，只如实记录当前值。
//  ② 浏览器**没死**，是**页签被别的会话关掉了**（`Target page … has been closed`，
//     而 9444 一直在、browserId 没变）⇒ 📌 **keepalive 只守进程，不守页签**。
//  ③ a 轮两个真发现需要复现：
//     · 时间线 1：`… 0 clips. Not selected.` → `… Selected.`
//     · 音频 68：🔴 **不止末句变** —— 前半句也从
//       「No resources. Current preview: 暂无音频.」变成
//       「No resources: 0 ready, 0 processing, 0 failed.」
//  ④ a 轮 `视频 1` / `导演台` 两臂在页签被关后没跑完；`文本 1` 无归属点。
//
// 本轮：**每次取页签都重新找**（页签会被别的会话关掉，不能只在开头拿一次），
// 并把**收尾断言也包在 try 里** —— a 轮就是在 `finally` 里读页面而崩掉的，
// 崩在那里等于**收尾校验根本没跑**（立规：收尾清单是可交付物的一部分，不是可选步骤）。
import fs from 'node:fs';
import { readers } from './jimeng-b135-lib.mjs';
import { idsOf, selCount } from './jimeng-b139-lib.mjs';

const 目标集 = [
  { 标题: '音频 68', 目的: '复现「前半句也变」那个发现' },
  { 标题: '时间线 1', 目的: '复现「只有末句变」' },
  { 标题: '视频 1', 目的: 'a 轮未跑完' },
  { 标题: '导演台', 目的: 'a 轮未跑完' },
  { 标题: '文本 1', 目的: 'a 轮无归属点；这轮用更细的网格' },
];
const OUT = 'scripts/_tmp-b212b.json';
const rec = { 批次: '212b', a轮出了什么问题: '共享画布漂到 79 节点/813 积分；页签被别的会话关掉；finally 里读页面导致收尾断言没跑',
  目标集, 臂: {} };
const 落盘 = () => fs.writeFileSync(OUT, JSON.stringify(rec, null, 1));

const { chromium } = await import('playwright');
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

/** 🔴 每一次用页签之前都重新找一遍 —— 页签会被别的会话关掉。 */
async function 取页签() {
  let pg = ctx.pages().find((x) => x.url().includes('ai-canvas'));
  if (pg && !pg.isClosed()) return pg;
  await new Promise((r) => setTimeout(r, 2000));
  pg = ctx.pages().find((x) => x.url().includes('ai-canvas'));
  if (!pg) throw new Error('共享画布页签不在（可能正被别人关/开）');
  return pg;
}
let R = null;
const 安全 = async (fn, 名) => { try { return await fn(); } catch (e) { rec[名 || '错'] = String(e.message || e).slice(0, 200); return null; } };

const 读描述 = (p, nid) => p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!n) return { 节点不在: true };
  const ids = (n.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean);
  const 宿主 = ids.map((x) => document.getElementById(x)).filter(Boolean);
  return {
    描述id列表: ids, 宿主数: 宿主.length,
    宿主逐个: 宿主.map((h) => { const q = h.getBoundingClientRect();
      return { tag: h.tagName, testid: h.getAttribute('data-testid'), 是节点根: h === n,
        面积: [Math.round(q.width), Math.round(q.height)],
        innerText: (h.innerText || '').replace(/\s+/g, ' ').trim() }; }),
    选中态: n.classList.contains('selected'),
  };
}, nid);

// 更细的归属网格：a 轮步长 0.14 对文本节点不够
const 候选点 = (p, nid) => p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return [];
  const r = n.getBoundingClientRect(); const 好 = [];
  for (let fy = 0.08; fy <= 0.94; fy += 0.06) for (let fx = 0.08; fx <= 0.94; fx += 0.06) {
    const x = r.x + r.width * fx, y = r.y + r.height * fy;
    if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
    const e = document.elementFromPoint(x, y);
    if (e && n.contains(e)) { 好.push([Math.round(x), Math.round(y)]); if (好.length >= 40) break; }
  }
  return 好;
}, nid);

try {
  let p = await 取页签();
  R = readers(p);
  rec.起点 = await 安全(async () => ({ 缩放: await R.zoom(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 积分: await R.credits(), 浮层: await R.overlays() }), '起点错');
  console.log('起点', JSON.stringify(rec.起点));

  const 索引 = await 安全(async () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
    id: n.getAttribute('data-id'), 标题: ((n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || '').trim() }))), '索引错');
  if (!索引) throw new Error('读不到节点索引');

  for (const t of 目标集) {
    const hit = 索引.find((x) => x.标题 === t.标题);
    if (!hit) { rec.臂[t.标题] = { 无效: '画布上找不到该标题', 目的: t.目的,
      现有标题: Array.from(new Set(索引.map((x) => x.标题))).slice(0, 12) }; console.log(t.标题, '⛔ 找不到'); 落盘(); continue; }
    try {
      p = await 取页签(); R = readers(p);
      const 前 = await 安全(async () => 读描述(p, hit.id), '前错');
      const 候选 = await 安全(async () => 候选点(p, hit.id), '候选错');
      if (!候选 || !候选.length) { rec.臂[t.标题] = { 无效: '仍无归属候选点', 目的: t.目的, id: hit.id, 前 }; console.log(t.标题, '⛔ 无归属点'); 落盘(); continue; }

      let 选中集 = [], 补点 = 0;
      for (let k = 0; k < 3; k++) {
        if (p.isClosed()) { p = await 取页签(); R = readers(p); }
        await p.mouse.click(候选[0][0], 候选[0][1]); 补点 = k + 1; await p.waitForTimeout(1500);
        选中集 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
        if (选中集.length === 1 && 选中集[0] === hit.id) break;
      }
      const 选中了 = 选中集.length === 1 && 选中集[0] === hit.id;
      const 后 = 选中了 ? await 安全(async () => 读描述(p, hit.id), '后错') : null;

      const 前字 = 前?.宿主逐个?.map((h) => h.innerText) || [];
      const 后字 = 后?.宿主逐个?.map((h) => h.innerText) || [];
      rec.臂[t.标题] = {
        目的: t.目的, id: hit.id, 补点, 选中了, 候选点数: 候选.length,
        无效: 选中了 ? null : `点了 ${补点} 次仍未选中（${JSON.stringify(选中集)}）`,
        宿主是节点根: 前?.宿主逐个?.map((h) => h.是节点根),
        逐字前: 前字, 逐字后: 后字,
        变了: JSON.stringify(前字) !== JSON.stringify(后字),
      };
      console.log(`\n[${t.标题}] ${t.目的} ｜ 候选点 ${候选.length} 个 ｜ 补点 ${补点} ｜ 选中了 ${选中了}`);
      console.log('   前：', JSON.stringify(前字));
      console.log('   后：', JSON.stringify(后字), '｜ 变了?', rec.臂[t.标题].变了);
    } catch (e) { rec.臂[t.标题] = { 出错: String(e.message || e).slice(0, 200), 目的: t.目的 }; console.log(t.标题, '🔴', e.message); }
    finally {
      // 每臂清场（清不掉就记下来，不硬来）
      try {
        if (!p.isClosed()) { await p.keyboard.press('Escape'); await p.waitForTimeout(300);
          if (await selCount(p) > 0) { await p.mouse.click(30, 660); await p.waitForTimeout(600); } }
      } catch (e) { rec.清场错 = String(e.message || e).slice(0, 160); }
      落盘();
    }
  }

  // —— 收尾：整段包在 try 里，绝不让它把脚本带崩（a 轮就是死在这）——
  rec.收尾 = await 安全(async () => {
    p = await 取页签(); R = readers(p);
    return { 缩放: await R.zoom(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(), 积分: await R.credits(), 状态行: await R.status() };
  }, '收尾错');
  console.log('\n收尾', JSON.stringify(rec.收尾));
  if (rec.收尾) {
    console.log(rec.收尾.节点数 === rec.起点.节点数 && rec.收尾.选中 === 0 && /0 edges/.test(rec.收尾.状态行 || '')
      ? '  ✅ 收尾：节点数未变 / 0 选中 / 0 边'
      : '  ❌ 收尾对不上');
  } else console.log('  🔴 收尾读不到（页签又被关了）—— 如实记为未校验，不假装通过');
  rec.有效臂 = Object.values(rec.臂).filter((x) => x && x.选中了).length;
  rec.无效臂 = Object.values(rec.臂).filter((x) => x && (x.无效 || x.出错)).length;
  console.log('有效臂', rec.有效臂, '｜ 无效臂', rec.无效臂, '｜ 共', 目标集.length);
} finally {
  落盘();
  try { await b.close(); } catch {}
}
