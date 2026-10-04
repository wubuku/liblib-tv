// Batch EU-4：同一会话内把「隐藏节点连线」的开/关两态**用枚举判据**读齐。
//
//   EU-2 留下的疑问：点过之后 `[aria-label="隐藏节点连线"]` 查不到了。
//     但 EU-2 的判据是**按名字查** ⇒ 「查不到」只等于「这个名字没有」，
//     分不出「改名」还是「删属性」。§289 记的是「改成 `显示节点连线`」—— 未证实。
//   EU-3 的教训：它改用枚举了，可我的「找开态」判据是 `svg数>=2 || /显示/.test(aria)`，
//     而这枚开关**开态恰好也不满足**（EU-2 读到的就是 svg/aria 都拿不到）⇒ 又漏。
//     ⛔ 正确做法：**不预设「开态长什么样」**，而是**点一次、枚举、再点一次、枚举**。
//
//   独立第四种读数：这次把选择器修对 —— 读 `path.react-flow__edge-path` 的
//   `stroke` / `stroke-opacity` / `getTotalLength()`，而不是 `<svg>` 容器。
//   （EU-3 抓的是 svg 容器，读出来的「描边: none」毫无意义。）
//
// ⛔ 只点这一枚纯视图开关，收尾在同一会话内复原。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEU4.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

/** 枚举底栏整排按钮 —— **不预设开态长什么样**，只如实列出 */
const 枚举底栏 = (page) => page.evaluate(() => {
  const 出 = [];
  for (const e of document.querySelectorAll('button,[aria-label],[role="button"]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 14 || r.height < 14) continue;
    if (r.bottom < 750 || r.top > 800) continue;
    if (r.right > 260 || r.left < 160) continue;          // 只取「隐藏节点连线 / 网格吸附」这两枚所在的段
    if (e.querySelector('button,[role="button"]')) continue;
    const cs = getComputedStyle(e);
    const svgs = [...e.querySelectorAll('svg')];
    出.push({
      tag: e.tagName, 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12),
      aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
      子数: e.children.length, svg数: svgs.length,
      svg路径: svgs.map(s => { const p = s.querySelector('path'); return p ? p.getAttribute('d').slice(0, 50) : '(无 path)'; }),
      背景: cs.backgroundColor, 边框: cs.borderColor, 边框宽: cs.borderTopWidth, 不透明: cs.opacity,
      cls: String(e.className).slice(0, 130),
    });
  }
  出.sort((a, b) => a.box[0] - b.box[0]);
  return 出;
});

/** ⭐ 独立第四种读数：真的把连线的描边读出来（这次选对元素） */
const 数连线 = (page) => page.evaluate(() => {
  const sel = ['path.react-flow__edge-path', '.react-flow__edge path', 'g.react-flow__edge path'];
  let 元素 = null, 用哪 = null;
  for (const s of sel) { const n = document.querySelectorAll(s); if (n.length) { 元素 = [...n]; 用哪 = s; break; } }
  if (!元素) return { 找到: false, 各选择器命中: sel.map(s => [s, document.querySelectorAll(s).length]) };
  return {
    找到: true, 用哪, 共: 元素.length,
    明细: 元素.slice(0, 4).map(p => {
      const r = p.getBoundingClientRect(); const cs = getComputedStyle(p);
      let 长 = null; try { 长 = Math.round(p.getTotalLength()); } catch (e) { 长 = null; }
      return { 尺寸: [Math.round(r.width), Math.round(r.height)], 路径长: 长, 描边: cs.stroke, 描边宽: cs.strokeWidth, 描边不透明: cs.strokeOpacity, 不透明: cs.opacity, 可见性: cs.visibility, 显示: cs.display, d: (p.getAttribute('d') || '').slice(0, 40) };
    }),
  };
});

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 7000 });
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === '知道了'); if (b) b.click(); });
  await page.waitForTimeout(800);
  await page.evaluate(() => {
    const 条 = [...document.querySelectorAll('div')].filter(d => /开启浏览器通知/.test(d.innerText || ''));
    if (条.length) { 条.sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width); const btn = [...条[条.length - 1].querySelectorAll('button')].find(b => (b.innerText || '').trim() === ''); if (btn) btn.click(); }
  });
  await page.waitForTimeout(700);
  await page.evaluate(() => { for (const b of document.querySelectorAll('button')) if (b.getAttribute('aria-label') === '关闭' && b.getBoundingClientRect().width < 40) { b.click(); return; } });
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3500);
  记(`开局坐标偏差：${JSON.stringify(await 核对坐标(page))}`);

  const 全 = {};
  const 打印 = (名, 栏, 连) => {
    记(`\n　　【${名}】`);
    for (const b of 栏) {
      记(`　　<${b.tag}> 「${b.文字}」 aria=${JSON.stringify(b.aria)} title=${JSON.stringify(b.title)} box=${JSON.stringify(b.box)} 子数=${b.子数} svg数=${b.svg数} 背景=${b.背景} 边框宽=${b.边框宽}`);
      for (const p of b.svg路径) 记(`　　　　└ path ${p}`);
    }
    记(`　　⭐ 连线（独立读数）：${JSON.stringify(连)}`);
  };

  // ① 关态（初始）
  记('\n════ ① 初始态 ════');
  const 栏0 = await 枚举底栏(page);
  const 连0 = await 数连线(page);
  打印('初始', 栏0, 连0);
  await page.screenshot({ path: EVID + 'eu4-连线-关态.png' });

  // ② 点「隐藏节点连线」
  const 目标 = 栏0.find(b => b.aria === '隐藏节点连线');
  if (!目标) throw new Error('找不到 隐藏节点连线');
  记(`\n════ ② 点它 ════\n　　目标 box=${JSON.stringify(目标.box)} 中心 ${JSON.stringify(目标.中心)}`);
  const 验 = await page.evaluate((c) => { const e = document.elementFromPoint(c[0], c[1]); return e ? `${e.tagName}.${String(e.className).slice(0, 30)}` : null; }, 目标.中心);
  记(`　　elementFromPoint 自证 ${JSON.stringify(验)}`);
  await page.mouse.click(目标.中心[0], 目标.中心[1]);
  await page.waitForTimeout(2000);
  const 栏1 = await 枚举底栏(page);
  const 连1 = await 数连线(page);
  打印('点后', 栏1, 连1);
  await page.screenshot({ path: EVID + 'eu4-连线-开态.png' });

  // ③ 再点一次复原
  记('\n════ ③ 再点一次（复原）════');
  const 再目标 = 栏1.find(b => b.box[0] >= 目标.box[0] - 4 && b.box[0] <= 目标.box[0] + 4);
  if (!再目标) throw new Error('复原时找不到同一枚');
  记(`　　同一位置 box=${JSON.stringify(再目标.box)}，当前 aria=${JSON.stringify(再目标.aria)}，先点它复原`);
  await page.mouse.click(再目标.中心[0], 再目标.中心[1]);
  await page.waitForTimeout(2000);
  const 栏2 = await 枚举底栏(page);
  const 连2 = await 数连线(page);
  打印('复原后', 栏2, 连2);
  await page.screenshot({ path: EVID + 'eu4-连线-复原.png' });

  const 同 = JSON.stringify(栏0.map(b => [b.aria, b.svg数, b.背景])) === JSON.stringify(栏2.map(b => [b.aria, b.svg数, b.背景]));
  记(`\n⭐⭐ 复原回归：底栏读数与初始${同 ? '**逐字相同 ✅**' : '**不一致 ⛔**'}`);
  记(`⭐⭐ 连线读数：初始 ${JSON.stringify(连0.明细)} → 复原 ${JSON.stringify(连2.明细)}`);

  全.关态 = { 栏: 栏0, 连线: 连0 };
  全.开态 = { 栏: 栏1, 连线: 连1 };
  全.复原 = { 栏: 栏2, 连线: 连2, 与初始一致: 同 };
  结果.读数.全 = 全;
  记('\n✅ 完成（只点这一枚纯视图开关，已复原）');
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  try {
    记('⏳ ⌘0 复位 + 静置 15s…');
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(15000);
    const 现 = await 读全部坐标(page);
    const 真动 = Object.keys(坐标).filter(id => 现[id] && (Math.abs(现[id][0] - 坐标[id][0]) > 1.5 || Math.abs(现[id][1] - 坐标[id][1]) > 1.5));
    记(`⭐ 真的被移动：${真动.length} 个 ${JSON.stringify(真动)}`);
  } catch (e) { console.error(e); }
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEU4.json ===');
}
