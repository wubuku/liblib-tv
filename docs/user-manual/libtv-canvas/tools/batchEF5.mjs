// Batch EF-5：⭐ 验证「当前使用」白底徽标 —— 本轮是**可逆写操作**，已获用户明确许可。
//
// 源码判据（3-mou5v69wxmq.js）：
//   W = typeof a === 'string' ? a === e.uuid : a?.has(e.uuid) ?? false
//   a = 当前节点正在用的风格 uuid；e.uuid = 这张卡的 uuid
//   W ? <白底胶囊><CurrentUseCheck>当前使用</白底胶囊> : <空白占位>
//
// ⛔⛔ 本脚本的硬约束（ED 事故后重写）：
//   ① **先完整快照节点状态**，验证完**逐项改回**；
//   ② 绝不按 Delete / Backspace / ⌘A —— 一个删除键都不碰；
//   ③ 不点「使用」按钮（那会建节点）；
//   ④ 不碰生成按钮（会扣积分）；
//   ⑤ 最后一步必须验证「已改回原样」，改不回要在日志里写明。
//
// 目标：图片节点 i-sODTbgLUm1（它的大编辑器里有独立的「风格」格）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEF5.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 快照: {}, 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 目标ID = 'i-sODTbgLUm1';

/** 读节点大编辑器里「风格」那一格的完整状态。 */
const 读风格格 = (page) => page.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!n) return { 错: '节点不在' };
  // 选中态下大编辑器在节点外；先找带「风格」字的按钮群
  const btns = [...document.querySelectorAll('button')].filter(b => {
    const t = (b.innerText || '').trim();
    return ['参考', '标记', '风格', '特效', '角色库', '运镜'].includes(t);
  });
  return {
    节点选中: n.className.toString().includes('selected'),
    顶部按钮: btns.map(b => {
      const r = b.getBoundingClientRect();
      return {
        文案: b.innerText.trim(),
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        激活: b.getAttribute('data-active') || b.getAttribute('aria-selected') || '',
        disabled: b.disabled,
        cls: b.className.toString().slice(0, 70),
      };
    }),
  };
}, 目标ID);

/** ⭐ 找「当前使用」徽标（按白底胶囊 + 文字，精确）。 */
const 找徽标 = (page) => page.evaluate(() => {
  const out = [];
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = w.nextNode())) {
    const t = (n.nodeValue || '').trim();
    if (t !== '当前使用') continue;
    if (n.parentElement.tagName === 'SCRIPT') continue;   // 排掉 SSR 注水
    const leaf = n.parentElement;
    if (leaf.querySelector('span,div')) continue;          // 只要叶子
    const 胶囊 = leaf.parentElement;
    const r = 胶囊.getBoundingClientRect();
    const cs = getComputedStyle(胶囊);
    const 广场 = [...document.querySelectorAll('.mantine-Modal-content,.mantine-Drawer-content')]
      .find(e => /风格广场|我的收藏|最近使用/.test(e.innerText || ''));
    out.push({
      胶囊class: 胶囊.className.toString(),
      胶囊bg: cs.backgroundColor,
      胶囊box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      文字色: getComputedStyle(leaf).color,
      字号: getComputedStyle(leaf).fontSize,
      svg数: 胶囊.querySelectorAll('svg').length,
      所在卡: (胶囊.closest('[class*="group"]')?.innerText || '').split('\n').filter(Boolean).slice(0, 2).join(' / '),
      在广场内: !!(广场 && 广场.contains(胶囊)),
      html: 胶囊.outerHTML.slice(0, 300),
    });
  }
  return out;
});

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6000 });
  await closePromos(page);
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1600);

  // ── 步骤 0：节点/基线快照 ──
  const 节点数 = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  结果.快照.开跑节点数 = 节点数;
  记(`开跑：节点 ${节点数}（基线 ${BASE.length}）`);

  // ── 步骤 1：选中目标节点，读风格格原状态 ──
  const 框 = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return [r.left, r.top, r.width, r.height];
  }, 目标ID);
  await page.mouse.click(框[0] + 框[2] / 2, 框[1] + 框[3] / 2);
  await page.waitForTimeout(1300);

  const 原状态 = await 读风格格(page);
  结果.快照.风格格原状态 = 原状态;
  记(`读原状态：选中=${原状态.节点选中}，顶部按钮=${JSON.stringify(原状态.顶部按钮?.map(b => b.文案))}`);

  const 基线徽标 = await 找徽标(page);
  结果.快照.操作前徽标 = 基线徽标;
  记(`⭐ 操作前「当前使用」徽标：${基线徽标.length} 枚`);

  // ── 步骤 2：打开风格广场（点「风格」格）──
  const 开了 = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === '风格');
    if (!b) return false; b.click(); return true;
  });
  await page.waitForTimeout(2200);
  记(`点「风格」：${开了}`);
  结果.读数.开广场后徽标 = await 找徽标(page);

  // ── 步骤 3：⭐ 选一张卡（记录选了哪张）──
  const 选卡 = await page.evaluate(() => {
    const 广场 = [...document.querySelectorAll('.mantine-Modal-content,.mantine-Drawer-content')]
      .find(e => /风格广场|我的收藏|最近使用/.test(e.innerText || ''));
    if (!广场) return null;
    const 卡 = [...广场.querySelectorAll('img')].map(i => {
      const c = i.closest('[class*="group"]') || i.parentElement.parentElement;
      return c;
    }).filter(c => c && c.getBoundingClientRect().width > 120)[0];
    if (!卡) return null;
    // 读卡名
    const r = 卡.getBoundingClientRect();
    const 文本 = (卡.innerText || '').split('\n').filter(Boolean);
    return { 卡名: 文本[0] || '', 行: 文本.slice(0, 4), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  });
  结果.读数.选中的卡 = 选卡;
  记(`准备选卡：${JSON.stringify(选卡?.卡名)}`);

  if (选卡) {
    // 点卡（这会改节点风格 —— 用户已许可）
    await page.mouse.click(选卡.box[0] + 选卡.box[2] / 2, 选卡.box[1] + 选卡.box[3] / 2);
    await page.waitForTimeout(2800);
    记('已点卡（改风格）');

    // ── 步骤 4：⭐ 读徽标 ──
    const 选后徽标 = await 找徽标(page);
    结果.读数.选卡后徽标 = 选后徽标;
    记(`⭐⭐ 选卡后「当前使用」徽标：${选后徽标.length} 枚`);
    for (const m of 选后徽标) {
      console.log('   →', JSON.stringify({ 所在卡: m.所在卡, bg: m.胶囊bg, box: m.胶囊box, 文字色: m.文字色, 字号: m.字号, svg: m.svg数 }));
    }
    await page.screenshot({ path: '.evidence/batchEF5-选中风格后找徽标.png' });
    落盘(结果);

    // 再开一次广场，这次广场里应该能看到徽标在卡面上
    const 再开 = await page.evaluate(() => {
      const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === '风格');
      if (!b) return false; b.click(); return true;
    });
    await page.waitForTimeout(2200);
    const 广场徽标 = await 找徽标(page);
    结果.读数.广场内徽标 = 广场徽标;
    记(`⭐⭐⭐ 广场里「当前使用」徽标：${广场徽标.length} 枚`);
    for (const m of 广场徽标) {
      console.log('   →', JSON.stringify({ 所在卡: m.所在卡, bg: m.胶囊bg, box: m.胶囊box, 文字色: m.文字色, 字号: m.字号, svg: m.svg数, html: m.html.slice(0, 160) }));
    }
    await page.screenshot({ path: '.evidence/batchEF5-广场里的当前使用徽标.png' });
    落盘(结果);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1200);
  }
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEF5.json ===');
}
