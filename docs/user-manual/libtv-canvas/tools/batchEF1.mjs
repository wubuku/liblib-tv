// Batch EF-1：⭐ 验证「当前使用」白底徽标在画布节点卡面上的真实读数。
//
// 源码查清（3-mou5v69wxmq.js）：
//   ① 卡面下拉里的勾： e.modelKey === t  → 这一行的模型 == 当前模型
//   ② ⭐ 卡面左下角**常驻白底徽标**：
//        W = typeof a === 'string' ? a === e.uuid : a?.has(e.uuid) ?? false
//        W ? <白底胶囊><CurrentUseCheck 图标>当前使用</白底胶囊> : <空白占位>
//      a = 当前节点正在用的风格 uuid；e.uuid = 这张卡的 uuid
//      ⇒ W = 「这张卡就是这个节点当前在用的风格」
//
// DT 批只验证了 ①（广场悬停看不到），结论是可信阴性。
// ⭐ 本批验 ②：在**画布节点的风格下拉**里，找这枚白底徽标。
//
// ⛔ 安全约束：纯只读。**不点任何会创建/删除/生成的东西**；
//    只「点开下拉 → 读 → 按 ESC 关掉」。不点菜单里的具体模型（那会改节点模型）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEF1.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 读数: {} };

const 读节点 = (page) => page.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const W = window.innerWidth, H = window.innerHeight;
  return {
    缩放: vp ? getComputedStyle(vp).transform : null,
    节点: [...document.querySelectorAll('.react-flow__node')].map(n => {
      const r = n.getBoundingClientRect();
      return {
        id: n.getAttribute('data-id'),
        cls: n.className.toString().split(' ').filter(c => c.startsWith('react-flow__node-')).join(','),
        标题: (n.querySelector('input,textarea')?.value) || (n.innerText || '').split('\n')[0] || '',
        rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        在视口内: r.right > 0 && r.bottom > 0 && r.left < W && r.top < H,
      };
    }),
  };
});

/** ⭐ 全文搜「当前使用」出现在哪、连同它的祖先 class 和精确盒模型。 */
const 找当前使用 = (page) => page.evaluate(() => {
  const 命中 = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  let n;
  while ((n = walker.nextNode())) {
    if (!/当前使用/.test(n.nodeValue || '')) continue;
    if (seen.has(n.parentElement)) continue;
    seen.add(n.parentElement);
    // 往上找那个「白底胶囊」
    let el = n.parentElement, capsule = null;
    for (let i = 0; i < 5 && el; i++, el = el.parentElement) {
      const cs = getComputedStyle(el);
      if (cs.backgroundColor && cs.backgroundColor !== 'rgba(0, 0, 0, 0)') { capsule = el; break; }
    }
    const tgt = capsule || n.parentElement;
    const r = tgt.getBoundingClientRect();
    const cs = getComputedStyle(tgt);
    命中.push({
      文本: n.nodeValue.trim(),
      节点id: tgt.closest('.react-flow__node')?.getAttribute('data-id') || null,
      tag: tgt.tagName,
      className: tgt.className.toString().slice(0, 90),
      背景: cs.backgroundColor, 文字色: cs.color,
      字号: cs.fontSize,
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      可见: r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.opacity !== '0',
      html: tgt.outerHTML.slice(0, 400),
    });
  }
  return 命中;
});

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6000 });
  await closePromos(page);
  await page.waitForTimeout(1000);
  // ⭐ 每轮先复位视图（ED 批教训 §107.4）
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1600);

  const 前 = await 读节点(page);
  结果.读数.节点 = 前;
  console.log('节点数:', 前.节点.length, '（基线', BASE.length, '）| 缩放:', 前.缩放);
  console.log('  id:', 前.节点.map(n => n.id).join(' '));
  const 缺 = BASE.filter(x => !前.节点.some(n => n.id === x));
  console.log('  与基线比对 —— 缺失:', 缺.length ? 缺 : '无 ✅');
  落盘(结果);

  // 基线读数：页面上有没有「当前使用」
  const 基线徽标 = await 找当前使用(page);
  结果.读数.基线徽标 = 基线徽标;
  console.log('\n═══ 未点任何东西时，「当前使用」出现次数:', 基线徽标.length);
  for (const h of 基线徽标) console.log('  ', h.节点id, h.box, h.背景, h.文字色, '可见=' + h.可见);
  落盘(结果);

  // ⭐ 逐个点开「风格」下拉（大编辑器里那枚「风格」按钮）
  // 先找一个图片/视频节点（手册记着它们才有「风格」入口）
  for (const n of 前.节点) {
    if (!n.在视口内) continue;
    if (!/node-image|node-video\b|node-video-clip/.test(n.cls)) continue;

    const cx = n.rect[0] + n.rect[2] / 2;
    const cy = n.rect[1] + n.rect[3] / 2;
    console.log(`\n──── 试节点 ${n.id}（${n.cls}）────`);
    await page.mouse.click(cx, cy);
    await page.waitForTimeout(1200);

    // 找「风格」按钮
    const 开 = await page.evaluate(() => {
      const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === '风格');
      if (!b) return false;
      b.click(); return true;
    });
    console.log('  点「风格」:', 开);
    await page.waitForTimeout(1500);

    const 弹层 = await page.evaluate(() => {
      const cands = [...document.querySelectorAll('.mantine-Modal-content, .mantine-Drawer-content, [class*="Popover"]')]
        .filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
      return cands.map(c => ({
        cls: c.className.toString().slice(0, 60),
        box: (() => { const r = c.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })(),
        文本: c.innerText.slice(0, 260),
      }));
    });
    console.log('  弹出的层:', JSON.stringify(弹层.map(x => x.box)));
    结果.读数['弹层_' + n.id] = 弹层;
    落盘(结果);

    // ⭐ 在弹层里找「当前使用」
    const 徽标 = await 找当前使用(page);
    console.log('  ⭐ 弹层里「当前使用」:', 徽标.length ? JSON.stringify(徽标.map(h => ({ 节点: h.节点id, box: h.box, 背景: h.背景, 可见: h.可见 }))) : '0 个');
    结果.读数['徽标_' + n.id] = 徽标;
    落盘(结果);

    if (弹层.length) await page.screenshot({ path: `.evidence/batchEF1-${n.id}-风格弹层.png` });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(900);
  }
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEF1.json ===');
}
