/**
 * 批次 236：**普查**画布上全部节点的 class，把批次 235 留下的缺口补上 ——
 * 「`kind = external`」与「带 `nopan` 修饰符」这两个因子，到底是不是 1:1 共变？
 *
 * 📌 批次 235 的诚实边界：测完 `导演台` 后只能说
 *   「`z-index` 已排除，而 `kind` 与 `nopan` 在现有数据里共变、分不开」。
 *   之所以分不开，是因为当时**只测了 5 个节点**——那是抽样，抽样**天然分不开共变因子**。
 *
 * 📌 本批换一种证据：**普查**（一次开页读全部 `76` 个节点，不是抽样）。
 *   普查能把话说得比抽样强得多：
 *     · 若 `nopan` 在全画布**只出现在 `导演台` 这一个节点**上，而 `导演台` 也是**唯一的 `external`**，
 *       那么在这张画布上两个因子是**完美 1:1** ⇒ 不是「我抽少了」，而是**这张画布上根本没有能分开它们的对象**；
 *     · 若还有别的节点也带 `nopan`（哪怕不是 `external`），那就**有现成的分离点**（立规 116 的判据三问之三）。
 *   ⇒ 无论哪种结果，都把批次 235 那句「分不开」从**「我还没查」**升级成**「查过了，原因是这个」**。
 *
 * 🔴 纪律：
 *   · **普查**必须报出总数，并与门 9 打印的节点数**对账**（对不上说明读漏了，结论作废）；
 *   · 纯只读：不点节点、不搜索、不新建、不删除；
 *   · 位置从 `transform` 读（`style.left` 是 `null` —— 批次 235 侦察已踩过这个坑）。
 *
 * ⛔ 纯只读探针。
 *
 * 用法：node scripts/jimeng-b236.mjs   （读数落盘 /tmp/b236.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b236.json';

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b236' };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();

try {
  await p.setViewportSize({ width: 1280, height: 720 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(6000);

  const 普查 = await p.evaluate(() => {
    const 全部 = Array.from(document.querySelectorAll('.react-flow__node'));
    const 拆 = (cls) => {
      const m = /react-flow__node-([a-z-]+)/.exec(cls || '');
      return m ? m[1] : '(无 kind 类)';
    };
    return 全部.map((n) => {
      const cs = getComputedStyle(n);
      const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
      return {
        id: n.getAttribute('data-id'),
        名: (n.innerText || '').split('\n')[0] || '',
        kind: 拆(n.className),
        有nopan: /\bnopan\b/.test(n.className || ''),
        类: n.className,
        尺寸: [cs.width, cs.height],
        z: n.style.zIndex,
        坐标: t ? [Number(t[1]), Number(t[2])] : null,
      };
    });
  });

  out.节点总数 = 普查.length;
  out.选中数 = await p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1] || null);
  out.状态行 = await p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
  out.节点 = 普查;

  // ---- 汇总：kind × nopan 的交叉表 ----
  const 表 = new Map();
  for (const n of 普查) {
    const k = `${n.kind} × ${n.有nopan ? '有nopan' : '无nopan'}`;
    表.set(k, (表.get(k) || 0) + 1);
  }
  out.交叉表 = [...表.entries()].map(([格, 数]) => ({ 格, 数 })).sort((a, z) => z.数 - a.数);
  out.有nopan的节点 = 普查.filter((n) => n.有nopan).map((n) => ({ id: n.id, 名: n.名, kind: n.kind, z: n.z }));

  log(`普查节点总数 ${out.节点总数}（状态行：${out.状态行}）`);
  log('kind × nopan 交叉表：');
  for (const r of out.交叉表) log(`   ${r.格}  →  ${r.数}`);
  log(`带 nopan 的节点共 ${out.有nopan的节点.length} 个：` + JSON.stringify(out.有nopan的节点));
  log(`kind 种类共 ${new Set(普查.map((n) => n.kind)).size} 种：` + JSON.stringify([...new Set(普查.map((n) => n.kind))]));
} catch (e) {
  out.错误 = e.message;
  log('🔴 ' + e.message);
} finally {
  try { await p.close(); } catch (e) { /* 忽略 */ }
}

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
await b.close();
