// Batch EM-3b：先验「中键拖到底有没有弄坏画布」。
//   EM-3 的守卫报了 4 个节点偏差，但打印出来的记录里 **`现` 字段是空的**
//   —— 说明 `读全部坐标` 根本没读到它们。
//   ⭐ React Flow **只渲染视口内的节点**，中键拖成功平移后，
//      被推出视口的节点压根不在 DOM 里 ⇒ 守卫把「没渲染」误判成了「坐标变了」。
// 本脚本 ⌘0 复位后重读，区分「真被移动」和「没渲染」两种情况。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEM3b.json';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

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

  const 未复位 = await 读全部坐标(page);
  记(`⌘0 之前：DOM 里有 ${Object.keys(未复位).length} 个节点`);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3500);
  const 现 = await 读全部坐标(page);
  记(`⌘0 之后：DOM 里有 ${Object.keys(现).length} 个节点`);

  const 表 = BASE.map(id => {
    const 缺 = !(id in 现);
    const 差 = 现[id] ? [+(现[id][0] - 坐标[id][0]).toFixed(2), +(现[id][1] - 坐标[id][1]).toFixed(2)] : null;
    return { id, 未渲染: 缺, 现: 现[id] || null, 标准: 坐标[id], 差 };
  });
  记('\n逐节点：');
  for (const t of 表) 记(`　${t.id} ${t.未渲染 ? '⛔未渲染' : `现=${JSON.stringify(t.现)} 差=${JSON.stringify(t.差)} ${Math.abs(t.差[0]) <= 1.5 && Math.abs(t.差[1]) <= 1.5 ? '✅' : '❌ 真的动了'}`}`);
  const 真的动 = 表.filter(t => !t.未渲染 && (Math.abs(t.差[0]) > 1.5 || Math.abs(t.差[1]) > 1.5));
  记(`\n⭐ 结论：未渲染 ${表.filter(t => t.未渲染).length} 个；**真的被移动 ${真的动.length} 个** ${JSON.stringify(真的动.map(t => t.id))}`);
  记(`⭐ 核对坐标原样返回：${JSON.stringify(await 核对坐标(page))}`);
  结果.读数.表 = 表;
  结果.读数.真的动 = 真的动;
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEM3b.json ===');
}
