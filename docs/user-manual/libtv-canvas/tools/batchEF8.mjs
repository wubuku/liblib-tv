// Batch EF-8：EF-7 顶排只剩「参考/标记」，「风格/替换」不见了 —— 大编辑器没打开。
//
// ⭐ 停止猜测，改成**先诊断再动作**：每一步都先读「现在是什么状态」，
//    读不到就停下来说明，而不是接着点。EF-1~EF-7 连续三轮栽在同一个地方：
//    **点节点 → 大编辑器是否真的打开了？没人验证过。**
//
// 本步只做一件事：点节点后，报告大编辑器到底开没开、开在哪、长什么样。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEF8.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };
const 目标ID = 'i-sODTbgLUm1';

/** ⭐ 大编辑器诊断：它到底是什么元素、在哪、里面有什么。 */
const 诊断大编辑器 = (page) => page.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!n) return { 错: '节点不在 DOM' };
  const nr = n.getBoundingClientRect();
  const 选中 = n.className.toString().includes('selected');

  // 找出所有同时含「风格」或「替换」文字、且尺寸够大的元素
  const 候选 = [];
  for (const e of document.querySelectorAll('div,section,aside')) {
    const txt = e.innerText || '';
    if (!/参考|标记|风格|替换|Lib Image/.test(txt)) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 250 || r.height < 150) continue;
    // 只要「最内层」的那个
    let 最内 = true;
    for (const c of e.children) {
      const cr = c.getBoundingClientRect();
      const ct = c.innerText || '';
      if (cr.width >= 250 && cr.height >= 150 && /参考|标记|风格|替换|Lib Image/.test(ct)) { 最内 = false; break; }
    }
    if (!最内) continue;
    候选.push({
      tag: e.tagName,
      cls: e.className.toString().slice(0, 80),
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      文本: txt.slice(0, 160).replace(/\n+/g, ' | '),
      按钮: [...e.querySelectorAll('button')].map(b => b.innerText.trim()).filter(Boolean).slice(0, 12),
    });
  }
  return { 节点选中: 选中, 节点box: [Math.round(nr.left), Math.round(nr.top), Math.round(nr.width), Math.round(nr.height)], 大编辑器候选: 候选 };
}, 目标ID);

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1200);
  await page.evaluate(() => { for (const b of document.querySelectorAll('button')) if ((b.innerText || '').trim() === '知道了') { b.click(); return; } });
  await page.waitForTimeout(600);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  // ── 诊断 A：点之前 ──
  const 前 = await 诊断大编辑器(page);
  结果.读数.点之前 = 前;
  记(`点之前：节点选中=${前.节点选中}，大编辑器候选 ${前.大编辑器候选.length} 个`);

  // ── 诊断 B：点节点**标题**而不是中心（大编辑器可能靠点标题触发）──
  const 标题点 = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) return null;
    // 节点卡上方的标题栏（带节点名的那个）
    const 标题 = [...n.querySelectorAll('*')].find(e => {
      const t = (e.innerText || '').trim();
      return /图片节点/.test(t) && e.children.length === 0;
    });
    if (标题) {
      const r = 标题.getBoundingClientRect();
      return { 用: '标题', 文本: 标题.innerText.trim(), box: [r.left + r.width / 2, r.top + r.height / 2] };
    }
    const r = n.getBoundingClientRect();
    return { 用: '中心', box: [r.left + r.width / 2, r.top + 20] };
  }, 目标ID);
  记(`点击位置：${JSON.stringify(标题点)}`);

  await page.mouse.click(标题点.box[0], 标题点.box[1]);
  await page.waitForTimeout(1600);

  // ── 诊断 C：点之后 ──
  const 后 = await 诊断大编辑器(page);
  结果.读数.点之后 = 后;
  记(`点之后：节点选中=${后.节点选中}，大编辑器候选 ${后.大编辑器候选.length} 个`);
  for (const c of 后.大编辑器候选) {
    console.log(`\n  候选 <${c.tag}> box=${JSON.stringify(c.box)}`);
    console.log(`    按钮: ${JSON.stringify(c.按钮)}`);
    console.log(`    文本: ${c.文本.slice(0, 130)}`);
  }
  落盘(结果);
  await page.screenshot({ path: '.evidence/batchEF8-点节点后的大编辑器诊断.png' });

  // ── 诊断 D：试双击 / 试点节点左上角的编辑区 ──
  if (!后.大编辑器候选.length) {
    记('没有大编辑器 → 试双击');
    await page.mouse.dblclick(标题点.box[0], 标题点.box[1]);
    await page.waitForTimeout(1800);
    const 双击后 = await 诊断大编辑器(page);
    结果.读数.双击后 = 双击后;
    记(`双击后：大编辑器候选 ${双击后.大编辑器候选.length} 个，节点选中=${双击后.节点选中}`);
    for (const c of 双击后.大编辑器候选) console.log('  按钮:', JSON.stringify(c.按钮));
    落盘(结果);
    await page.screenshot({ path: '.evidence/batchEF8-双击后.png' });
  }
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEF8.json ===');
}
