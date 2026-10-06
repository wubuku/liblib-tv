/**
 * 批次 256 · 侦察：画布上到底有哪几族节点、`导演台` / `主体` 的布局宽（`W`）是多少。
 *
 * 📌 背景：取景律（窄侧 `screen = w − 412`、族内地板 `100/W`、应用下限 `0.08`、封顶 `0.5`）
 *   已经跨 **4 个族**（text / timeline / image / audio）验过（批次 248/251/252），
 *   而画布工具栏上还有 **`主体`** 与 **`导演台`** 两个入口。
 *   🔴 **这两族一次都没测过窄侧** ⇒ 「`412` 律是通性」目前只成立于那 `4` 族，
 *   不能顺延到第 `5`、`6` 族。
 *
 * 📌 本步**只做两件事**：把全部 `76` 个节点按族分类列出；量出 `导演台`（及任何 `主体` 节点）
 *   的**布局宽 `offsetWidth`** —— 它就是律里的 `W`。
 *   🔴 `W` 是预测的输入，必须**先量出来**再写预测（立规 129：现象宽度要先算出来）。
 *
 * 📌 纪律：只读 DOM；一个控件都不点；不建不删不上传不生成不扣费不分享。
 *
 * 用法：node scripts/jimeng-b256-recon.mjs      （读数落盘 /tmp/b256-recon.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B256R_OUT || '/tmp/b256-recon.json';
const 宽 = 1280, 高 = 720;

const log = (...a) => console.log(a.join(' '));

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();
const out = { 轮次: 'b256-recon', 视口: [宽, 高], 族: {}, 节点: [], 重点: null };
try {
  await p.setViewportSize({ width: 宽, height: 高 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(6500);

  const 数据 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const cls = typeof n.className === 'string' ? n.className : '';
    // 📌 族名优先取 react-flow 的 kind 修饰符（node-text / node-image / …）
    const kind = (cls.match(/react-flow__node-([a-z]+)/) || [])[1] || '（无 kind 修饰符）';
    const r = n.getBoundingClientRect();
    return {
      id: n.getAttribute('data-id'),
      kind,
      cls: cls.slice(0, 120),
      testid: n.getAttribute('data-testid'),
      名: (n.innerText || '').trim().split('\n')[0] || null,
      布局宽: n.offsetWidth,
      布局高: n.offsetHeight,
      屏上宽: Math.round(r.width * 1000) / 1000,
      屏上高: Math.round(r.height * 1000) / 1000,
    };
  }));
  out.节点 = 数据;
  const 计 = {};
  for (const n of 数据) {
    (计[n.kind] = 计[n.kind] || []).push(n);
  }
  out.族 = Object.fromEntries(Object.entries(计).map(([k, v]) => [k, {
    个数: v.length,
    布局宽集合: [...new Set(v.map((x) => x.布局宽))].sort((a, c) => a - c),
    样例: v.slice(0, 3).map((x) => ({ 名: x.名, id: x.id, 布局宽: x.布局宽 })),
  }]));
  log('=== 按 kind 分族 ===');
  for (const [k, v] of Object.entries(out.族)) {
    log(`  ${k}: ${v.个数} 个，布局宽 ${JSON.stringify(v.布局宽)}`);
    for (const s of v.样例) log(`      ${s.名} (${s.id}) W=${s.布局宽}`);
  }

  // 📌 重点：导演台 与 任何名字里带「主体」的节点
  const 重点 = 数据.filter((n) => (n.名 || '').includes('导演台') || (n.名 || '').includes('主体'));
  out.重点 = 重点;
  log('=== 导演台 / 主体 ===');
  for (const n of 重点) {
    log(`  ${n.名} id=${n.id} kind=${n.kind} W=${n.布局宽} H=${n.布局高} testid=${JSON.stringify(n.testid)}`);
    log(`     class=${JSON.stringify(n.cls)}`);
  }
  if (!重点.length) log('  ⚠️ 没找到「导演台」或「主体」节点');
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