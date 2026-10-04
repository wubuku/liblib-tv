// Batch EI-3：组操作条到底出不出来 —— 换**框选**（拖一个选框）再试。
//
// EI-1/EI-2 用「点一个 + Shift 点第二个」建立了 2 个 selected 节点，
// 但组操作条一个字都没渲染。源码的渲染条件里还有 `!l$ && !nG && !aF && !aG`
// 四个门槛（`l$`/`nG` 的定义追不到，放弃源码层）。
//
// ⭐ 换正规入口：**在空白处拖一个选框**（框选是多选的正规方式），
//    框住 2 个图片节点，再读工具条。
//
// ⛔ 拖空��是纯选择手势，**不改任何节点位置**；读完点空白取消。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEI3.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1200);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  const 位置 = await page.evaluate(() => {
    const out = {};
    for (const id of ['i-9nlG6HdjK2', 'i-sODTbgLUm1']) {
      const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      const r = el.getBoundingClientRect();
      out[id] = [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
    }
    return out;
  });
  记(`两个图片节点位置：${JSON.stringify(位置)}`);

  // ⭐ 拖一个选框把两个都框进去
  const a = 位置['i-9nlG6HdjK2'], b = 位置['i-sODTbgLUm1'];
  const x1 = Math.min(a[0], b[0]) - 20, y1 = Math.min(a[1], b[1]) - 10;
  const x2 = Math.max(a[0] + a[2], b[0] + b[2]) + 20, y2 = Math.max(a[1] + a[3], b[1] + b[3]) + 20;
  await page.mouse.move(x1, y1);
  await page.mouse.down();
  await page.mouse.move((x1 + x2) / 2, (y1 + y2) / 2, { steps: 12 });
  await page.mouse.move(x2, y2, { steps: 12 });
  await page.waitForTimeout(400);
  await page.mouse.up();
  await page.waitForTimeout(1600);

  const 选中 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  结果.读数.框选后 = 选中;
  记(`框选后选中的节点：${JSON.stringify(选中)}`);

  // ⭐ 读组操作条
  const 条 = await page.evaluate(() => {
    const 文本 = [];
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = w.nextNode())) {
      const t = (n.nodeValue || '').trim();
      if (!t || t.length > 10) continue;
      if (/转分镜组|解组|整组执行|批量下载|添加到工具箱|排列|成组|Group/.test(t)) {
        const p = n.parentElement;
        const r = p.getBoundingClientRect();
        if (r.width === 0) continue;
        文本.push({ 文本: t, tag: p.tagName, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
      }
    }
    return 文本;
  });
  结果.读数.操作条文字 = 条;
  记(`命中组操作条文字 ${条.length} 个：${JSON.stringify(条.map(t => t.文本))}`);

  // ⭐ 全页所有短文字按钮（阳性对照，证明多选态下确实有按钮浮层）
  const 浮层 = await page.evaluate(() => {
    const out = [];
    for (const b of document.querySelectorAll('button')) {
      const r = b.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      const t = (b.innerText || '').trim();
      // 只看不在节点卡里的（画布层浮层）
      if (b.closest('.react-flow__node')) continue;
      out.push({ 文字: t.slice(0, 12), disabled: b.disabled, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], cls: b.className.toString().slice(0, 50) });
    }
    return out;
  });
  结果.读数.画布层按钮 = 浮层;
  记(`画布层（非节点内）按钮 ${浮层.length} 个`);
  for (const b of 浮层.slice(0, 20)) console.log(`   「${b.文字}」 disabled=${b.disabled} box=${JSON.stringify(b.box)}`);

  await page.screenshot({ path: 'tools/.evidence/ei3-框选后的画面.png' });
  落盘(结果);
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI3.json ===');
}
