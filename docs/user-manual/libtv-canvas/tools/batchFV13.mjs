// ⭐⭐⭐⭐⭐ Batch FV-13：把主画布修回 12 个（删 3 个多余文本 + 补回 1 个音频）
//
// 事故账（必须写清楚，这是 FV-11 造成的）：
//   FV-11 依次点了三个「⋯」，其中一次「删除」点到了**别的行** ——
//   脚本自报「菜单里没找到删除」，但画布 15 → 13，**实际删掉了一个音频节点**。
//   ⭐ ⇒ 缺陷 490：**报告与实测不符时，以画布实测为准**，
//      而且「没找到就跳过」不是安全动作 —— 它把错误静默吞了。
//
// 现在画布 13 个：audio×1、text×4、image×2、video×2、clip×1、director×1、
//                script-v2×1、shot-breakdown×1
// 目标 12 个：audio×2、text×2、其余不变
//
// ⛔ 手段约束（用户已明确授权有副作用的 CRUD）：
//   删除走资产管理抽屉的「⋯ → 删除」菜单，⛔ 绝不按 Delete / Backspace；
//   ⛔ 每次删完都**重新读画布**，发现删错行立刻停手（不再盲点下一个）。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [], 已删: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFV13.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

// FV-3 基线（12 个）：这两组是**原有**节点，别的都是本轮多出来的
const 原有文本 = new Set(['t-UtVx3lZmrV', 't-WqqxbeJ4TG']);

const 快照 = () => page.evaluate(() => {
  const out = [];
  for (const el of document.querySelectorAll('.react-flow__node')) {
    const cls = [...el.classList].find((c) => c.startsWith('react-flow__node-')) || '';
    const b = el.getBoundingClientRect();
    let 标题 = null;
    for (const t of el.querySelectorAll('*')) {
      if (t.children.length) continue;
      const s = (t.textContent || '').trim();
      if (!s || s.length > 24) continue;
      const r = t.getBoundingClientRect();
      if (r.top < b.top + 44 && (!标题 || r.top < 标题.top)) 标题 = { 文: s, top: r.top };
    }
    out.push({ id: (el.getAttribute('data-id') || '').trim(),
      类型: cls.replace('react-flow__node-', ''), 标题: 标题 ? 标题.文 : '' });
  }
  return out;
});

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);

  let 前 = await 快照();
  R.读数.开跑前 = 前;
  记(`开跑前 ${前.length} 个，其中音频 ${前.filter((n) => n.类型 === 'audio').length} 个、文本 ${前.filter((n) => n.类型 === 'text').length} 个`);

  // 多余的文本节点 = 所有文本 id 减去原有的两个
  const 多余文本 = 前.filter((n) => n.类型 === 'text' && !原有文本.has(n.id));
  记(`要删的文本节点：${多余文本.map((n) => `${n.id}(\`${n.标题}\`)`).join(' / ') || '（无）'}`);
  断言('恰好 3 个多余文本节点', 多余文本.length === 3, `${多余文本.length} 个`);

  // 打开资产管理抽屉
  const 开 = await page.evaluate(() => {
    for (const e of document.querySelectorAll('button, [role="button"], div, span')) {
      if (e.children.length) continue;
      if ((e.innerText || '').trim() !== '资产管理') continue;
      const r = e.getBoundingClientRect();
      if (r.width < 10) continue;
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    }
    return null;
  });
  记(`点「资产管理」@${开}`);
  await page.mouse.click(开[0], 开[1]);
  await page.waitForTimeout(1500);

  // ⭐ 读抽屉里的每一行：往上找包含「节点名」的最内层容器
  const 读行 = () => page.evaluate(() => {
    const out = [];
    for (const e of document.querySelectorAll('[aria-label="更多操作"]')) {
      const r = e.getBoundingClientRect();
      if (r.width < 8) continue;
      // 往上爬最多 6 层，取第一个 innerText 短且非空的
      let 行文 = '', 节点 = null;
      let p = e;
      for (let i = 0; i < 6 && p; i++) {
        p = p.parentElement;
        if (!p) break;
        const t = (p.innerText || '').trim();
        if (t && t.length <= 20) { 行文 = t.split('\n')[0]; break; }
      }
      // 行内第一个「节点名」样式文字
      out.push({ 行文, 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], y: Math.round(r.y) });
    }
    return out.sort((a, b) => a.y - b.y);
  });
  const 行 = await 读行();
  R.读数.抽屉行 = 行;
  记(`\n抽屉 ${行.length} 行：`);
  行.forEach((r, i) => 记(`   ${i + 1}. 「${r.行文}」 @y=${r.y}`));
  await page.screenshot({ path: resolve(EVID, 'fv13-1-抽屉行.png') });

  // 逐个删：每次删完重读画布，删错立刻停
  for (const 目标 of 多余文本) {
    const 当前 = await 读行();
    const 命中 = 当前.find((r) => r.行文 === 目标.标题 && !R.已删.includes(目标.id));
    if (!命中) { 记(`\n⛔ 抽屉里找不到标题为「${目标.标题}」的行，跳过 ${目标.id}`); continue; }
    记(`\n删 ${目标.id}（标题「${目标.标题}」）：点该行「⋯」@y=${命中.y}`);
    await page.mouse.click(命中.中心[0], 命中.中心[1]);
    await page.waitForTimeout(900);
    const 菜单 = await page.evaluate(() => {
      const o = [];
      for (const e of document.querySelectorAll('*')) {
        if (e.children.length) continue;
        if ((e.innerText || '').trim() !== '删除') continue;
        const r = e.getBoundingClientRect();
        if (r.width < 20 || r.height < 10) continue;
        o.push([Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]);
      }
      return o;
    });
    if (!菜单.length) { 记('  ⛔ 菜单里没有「删除」，Esc 关掉'); await page.keyboard.press('Escape'); await page.waitForTimeout(500); continue; }
    await page.mouse.click(菜单[0][0], 菜单[0][1]);
    await page.waitForTimeout(1500);
    const 后 = await 快照();
    const 音频数 = 后.filter((n) => n.类型 === 'audio').length;
    记(`  删后：${后.length} 个（音频 ${音频数}、文本 ${后.filter((n) => n.类型 === 'text').length}）`);
    R.已删.push(目标.id);
    if (音频数 !== 2) {
      断言('没有误删音频', false, `音频变成 ${音频数} 个 —— ⛔ 立刻停手，不再盲点下一个`);
      break;
    }
    断言(`删掉 ${目标.id}`, !后.some((n) => n.id === 目标.id), 后.some((n) => n.id === 目标.id) ? '还在' : '已消失');
    前 = 后;
  }
  await page.screenshot({ path: resolve(EVID, 'fv13-2-删完之后.png') });
  const 末 = await 快照();
  R.读数.末 = 末;
  记(`\n末态 ${末.length} 个：${末.map((n) => `${n.类型}:${n.标题}`).join(' / ')}`);
  断言('文本回到 2 个', 末.filter((n) => n.类型 === 'text').length === 2, `${末.filter((n) => n.类型 === 'text').length} 个`);
  断言('音频仍是 1 个（待补）', 末.filter((n) => n.类型 === 'audio').length === 1, 'FV-11 误删的那个还没补回');
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFV13.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
