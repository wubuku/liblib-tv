/**
 * 批次 262：用**建一个、量一个、撤一个**的方式，补两条用户面「推断 / 未复现」条目。
 *
 * 📌 要补的两条（都在 `20-reference.md`，都是用户会照着用的）：
 *   ① **`:89`** 「视频（空）| 新建默认 **`569×320` canvas**（16:9 横版）；
 *      📌 **方向随素材比例**，画布上那个「视频 1」是 **`320×569`（9:16 竖版）**」
 *      🔴 **而画布上那个 `视频 1` 现在是空的**（批次 258 实测 `媒体元素 = 0 个`），
 *      却仍是竖版 ⇒ 「方向随素材比例」这条**对空节点无法复验**，两边对不上。
 *   ② **`:168`** 「主体 | **`352×352`** | `310` ≈ `88%` 屏上（**属推断**，本轮画布无主体节点可复现）」
 *
 * 📌 **判据**：把**新建的空**节点量出来。
 *   · 空视频节点若真是 **`568.875×320` 横版** ⇒ 「方向随素材比例」成立，
 *     而竖版的 `视频 1` **必然曾经有过素材**（方向被保留了下来）；
 *   · 若空视频节点直接就是竖版 ⇒ 那条「随素材比例」要订正。
 *   **两种可能都指向可执行的动作，两种都算成功。**
 *
 * 📌 **可逆性是硬要求**（`prepare-generation.md:466` 已有先例：新建→量→删→回到 `76`）：
 *   建完立刻 **`⌘Z` 撤回**，并**逐条核对**节点数与位置都回到基线。
 *   ⚠️ **绝不点生成面板里的任何东西**（生成 = 扣费）；只点左侧工具条的入口。
 *
 * 🔴 纪律：只新建与撤回；**不触发任何生成**、不进扣费页、不点「保存到主体库」、不分享、
 *   不上传、不删除既有节点。
 *
 * 用法：node scripts/jimeng-b262.mjs      （读数落盘 /tmp/b262.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B262_OUT || '/tmp/b262.json';
const 宽 = 1280, 高 = 720;

const log = (...a) => console.log(a.join(' '));

/** 📌 节点快照：id → [kind, x, y, 屏上宽]；用来核对「回到基线」 */
const 快照 = () => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const s = m ? Number(m[1]) : null;
  const 全部 = Array.from(document.querySelectorAll('.react-flow__node'));
  const 表 = {};
  for (const n of 全部) {
    const cls = typeof n.className === 'string' ? n.className : '';
    const kind = (cls.match(/react-flow__node-([a-z]+)/) || [])[1] || '无';
    const r = n.getBoundingClientRect();
    const id = n.getAttribute('data-id');
    表[id] = {
      kind,
      名: (n.innerText || '').trim().split('\n')[0] || null,
      aria: n.getAttribute('aria-label'),
      x: Math.round(parseFloat(n.style.transform.match(/translate\(([-\d.]+)px/)?.[1] || '0') * 100) / 100,
      y: Math.round(parseFloat(n.style.transform.match(/translate\([-\d.]+px,\s*([-\d.]+)px/)?.[1] || '0') * 100) / 100,
      css宽: s ? Math.round((r.width / s) * 10000) / 10000 : null,
      css高: s ? Math.round((r.height / s) * 10000) / 10000 : null,
      屏上宽: Math.round(r.width * 100) / 100,
      媒体元素: n.querySelectorAll('img,video,canvas,svg image').length,
    };
  }
  return { scale: s, 个数: 全部.length, 表 };
};

const 找工具条项 = (p, 名) => p.evaluate((nm) => {
  const b = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => (x.getAttribute('aria-label') || '') === nm);
  if (!b) return null;
  const r = b.getBoundingClientRect();
  if (r.width < 4 || r.height < 4) return null;
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, 名);

// 📌 可只跑其中一项：`node scripts/jimeng-b262.mjs 主体`
const 只跑 = process.argv[2] || null;
const 全部项 = [{ 键: '视频', 名: '视频' }, { 键: '主体', 名: '主体' }];
const 项表 = 只跑 ? 全部项.filter((x) => x.键 === 只跑) : 全部项;
if (!项表.length) throw new Error(`没有名为「${只跑}」的试验项`);
const out = { 轮次: 'b262', 视口: [宽, 高], 只跑: 只跑 || '全部', 基线: null, 试验: [] };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();
try {
  await p.setViewportSize({ width: 宽, height: 高 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(7000);

  const 基线 = await p.evaluate(快照);
  out.基线 = { 个数: 基线.个数, scale: 基线.scale };
  log(`基线：${基线.个数} 个节点，scale=${基线.scale}`);
  if (基线.个数 !== 76) log(`⚠️ 基线不是 76（是 ${基线.个数}），记下来但不阻塞 —— 以本批读到的基线为准`);

  // 🔴 每次只试一个入口，量完立刻 ⌘Z 撤回并核对
  for (const 项 of 项表) {
    const 记 = { 项: 项.键 };
    try {
      const 位 = await 找工具条项(p, 项.名);
      if (!位) throw new Error(`工具条里找不到「${项.名}」`);
      记.点位 = 位;
      await p.mouse.click(位[0], 位[1]);
      await p.waitForTimeout(3200);

      const 建后 = await p.evaluate(快照);
      记.建后个数 = 建后.个数;
      记.scale = 建后.scale;
      const 新增 = Object.keys(建后.表).filter((k) => !基线.表[k]);
      记.新增节点 = 新增;
      log(`【${项.键}】建后 ${建后.个数} 个节点（基线 ${基线.个数}），新增 id：${JSON.stringify(新增)}`);
      if (新增.length) {
        记.读数 = 新增.map((id) => 建后.表[id]);
        for (const r of 记.读数) {
          log(`   ${r.名}（${r.kind}）canvas ${r.css宽} × ${r.css高}｜屏上 ${r.屏上宽}｜媒体元素 ${r.媒体元素}`);
          log(`      aria=${JSON.stringify(r.aria)}｜画布坐标 (${r.x}, ${r.y})`);
        }
      } else {
        log(`   ⚠️ 没有新增节点：点了「${项.名}」但画布节点数没变`);
      }
      // 📌 顺手看一眼有没有弹出生成面板（只读，不点）
      记.生成面板 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid]'))
        .map((e) => e.getAttribute('data-testid'))
        .filter((t) => /generat|panel/i.test(t || ''))
        .filter((t, i, a) => a.indexOf(t) === i).slice(0, 20));
      log(`   生成/面板类 testid：${JSON.stringify(记.生成面板)}`);
    } catch (e) {
      记.错误 = e.message;
      log(`🔴 ${项.键} ${e.message}`);
    }

    // 🔴 **撤回**：`⌘Z`。先按一次，核对节点数是否回到基线
    await p.keyboard.press('Meta+z');
    await p.waitForTimeout(2500);
    const 撤后 = await p.evaluate(快照);
    记.撤后个数 = 撤后.个数;
    const 仍多 = Object.keys(撤后.表).filter((k) => !基线.表[k]);
    记.撤回后仍多 = 仍多;
    // 📌 位置比对：基线里每个节点的位置有没有被改动
    const 位置变了 = [];
    for (const k of Object.keys(基线.表)) {
      if (!撤后.表[k]) { 位置变了.push(`${k} 消失`); continue; }
      const a = 基线.表[k], c = 撤后.表[k];
      if (a.x !== c.x || a.y !== c.y) 位置变了.push(`${k} (${a.x},${a.y})→(${c.x},${c.y})`);
    }
    记.位置变化 = 位置变了;
    log(`   ⌘Z 后：${撤后.个数} 个节点（基线 ${基线.个数}）｜仍多 ${JSON.stringify(仍多)}｜位置变化 ${JSON.stringify(位置变了)}`);
    out.试验.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));

    // 🔴 若撤回没把节点数带回来，**再撤一次**并如实记录
    if (撤后.个数 > 基线.个数) {
      await p.keyboard.press('Meta+z');
      await p.waitForTimeout(2500);
      const 再撤 = await p.evaluate(快照);
      记.二次撤回个数 = 再撤.个数;
      log(`   ⚠️ 二次 ⌘Z 后：${再撤.个数} 个节点`);
    }
    await p.waitForTimeout(800);
  }

  const 末 = await p.evaluate(快照);
  out.末态个数 = 末.个数;
  out.回到基线 = 末.个数 === 基线.个数;
  log('=== 末态 ===');
  log(`${末.个数} 个节点（基线 ${基线.个数}）⇒ ${out.回到基线 ? '✅ 已回到基线' : '🔴 未回到基线'}`);
} catch (e) {
  out.错误 = e.message;
  log('🔴 ' + e.message);
} finally {
  try { await p.close(); } catch (e) { /* 忽略 */ }
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  log('写入 ' + OUT);
}
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);