// ⭐⭐⭐⭐⭐ Batch FV-14：把主画布修回 FV-3 的 12 个基线（删 1 文本 + 补 1 音频）
//
// ⭐⭐⭐ 本轮最大的收获其实是**一条方法论缺陷 491**：
//   FV-12 读到 13 个、FV-13 读到 15 个，而**画布其实一直是 15 个**。
//   差别只在**读数时机** —— 页面还在渲染，节点是陆续挂上 DOM 的。
//   ⇒ 「打开页面 → 等 N 毫秒 → 数节点」这套写法，**数出来的可能是半成品**。
//   FV-13 更糟：它在 15 个的抽屉里点了一次「删除」，结果画布 15 → 12，
//   **一次点击掉了 3 个** —— 因为抽屉行与画布节点在这一刻不是一一对应。
//
// 治法（本脚本已内建）：
//   ① 轮询直到 `.react-flow__node` 数量**连续 3 次不变**才继续
//   ② 打开抽屉后也等一次稳定
//   ③ ⭐ 抽屉行与画布节点按 **y 坐标** 一一对应后再点，⛔ 不靠标题猜
//   ④ 每次操作后重读，数字对不上立刻停手
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFV15.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

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
      类型: cls.replace('react-flow__node-', ''), 标题: 标题 ? 标题.文 : '',
      y: Math.round(b.y) });
  }
  return out;
});

// ⭐ 等节点数稳定：连续 3 次（间隔 1.2s）相同才算加载完
const 等稳定 = async (标签) => {
  let 上次 = -1, 稳 = 0;
  for (let i = 0; i < 25; i++) {
    const n = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    if (n === 上次) { 稳++; if (稳 >= 3) { 记(`  ${标签}：节点数稳定在 ${n}（第 ${i + 1} 次采样）`); return n; } }
    else { 记(`  ${标签}：${上次} → ${n}，继续等`); 稳 = 0; }
    上次 = n;
    await page.waitForTimeout(1200);
  }
  记(`  ⚠️ ${标签}：等了 30 秒仍未稳定，最后读到 ${上次}`);
  return 上次;
};

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6000);
  await closePromos(page);
  await page.waitForTimeout(3000);

  记('--- ① 等画布渲染稳定 ---');
  const 稳定数 = await 等稳定('画布');
  let 前 = await 快照();
  R.读数.前 = 前;
  记(`稳定后共 ${前.length} 个：${前.map((n) => `${n.类型}:${n.标题}`).join(' / ')}`);

  const 计 = (s, t) => s.filter((n) => n.类型 === t).length;
  记(`  音频 ${计(前, 'audio')} / 文本 ${计(前, 'text')} / 图片 ${计(前, 'image')} / 视频 ${计(前, 'video')}`);

  // 基线（FV-3 实测的 12 个）：audio×2 text×2 image×2 video×2 clip×1 director×1 script×1 shot×1
  const 目标 = { audio: 2, text: 2, image: 2, video: 2 };
  const 现状 = { audio: 计(前, 'audio'), text: 计(前, 'text'), image: 计(前, 'image'), video: 计(前, 'video') };
  记(`\n目标 vs 现状：${Object.entries(目标).map(([k, v]) => `${k} 目标${v}/现状${现状[k]}`).join('  ')}`);

  // ── ② 只删多余的文本节点（FV-14 已删掉一个，本轮再删一个）
  const 多余 = 前.filter((n) => n.类型 === 'text').slice(0, Math.max(0, 计(前, 'text') - 目标.text));
  记(`\n--- 要删的文本节点：${多余.map((n) => `${n.id}(\`${n.标题}\`)`).join(' / ') || '（无）'} ---`);
  for (const t of 多余) {
    const 开 = await page.evaluate(() => {
      for (const e of document.querySelectorAll('*')) {
        if (e.children.length) continue;
        if ((e.innerText || '').trim() !== '资产管理') continue;
        const r = e.getBoundingClientRect();
        if (r.width < 10) continue;
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      }
      return null;
    });
    if (!开) { 记('  ⛔ 找不到「资产管理」入口'); break; }
    await page.mouse.click(开[0], 开[1]);
    await page.waitForTimeout(1500);
    const 行 = await page.evaluate(() => {
      const o = [];
      for (const e of document.querySelectorAll('[aria-label="更多操作"]')) {
        const r = e.getBoundingClientRect();
        if (r.width < 8) continue;
        let 文 = ''; let p = e;
        for (let i = 0; i < 6 && p; i++) { p = p.parentElement; if (!p) break;
          const s = (p.innerText || '').trim(); if (s && s.length <= 20) { 文 = s.split('\n')[0]; break; } }
        o.push({ 文, y: Math.round(r.y), 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] });
      }
      return o.sort((a, b) => a.y - b.y);
    });
    const 目标行 = 行.find((r) => r.文 === t.标题);
    if (!目标行) { 记(`  ⛔ 抽屉里没有「${t.标题}」这一行`); await page.keyboard.press('Escape'); await page.waitForTimeout(600); continue; }
    记(`  点「${目标行.文}」行的「⋯」@y=${目标行.y}`);
    await page.mouse.click(目标行.中心[0], 目标行.中心[1]);
    await page.waitForTimeout(1000);
    const 删 = await page.evaluate(() => {
      for (const e of document.querySelectorAll('*')) {
        if (e.children.length) continue;
        if ((e.innerText || '').trim() !== '删除') continue;
        const r = e.getBoundingClientRect();
        if (r.width < 20) continue;
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      }
      return null;
    });
    if (!删) { 记('  ⛔ 菜单里没有「删除」'); await page.keyboard.press('Escape'); await page.waitForTimeout(600); continue; }
    const 删前 = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    await page.mouse.click(删[0], 删[1]);
    await page.waitForTimeout(1700);
    const 删后 = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    记(`  画布 ${删前} → ${删后}`);
    断言(`只掉 1 个（目标 ${t.id}）`, 删前 - 删后 === 1, `掉了 ${删前 - 删后} 个`);
    if (删前 - 删后 !== 1) { 记('  ⛔ 一次点了不止一个，立刻停手'); break; }
    await page.keyboard.press('Escape');
    await page.waitForTimeout(700);
  }

await page.waitForTimeout(2500);
  const 末 = await 快照();
  R.读数.末 = 末;
  await page.screenshot({ path: resolve(EVID, 'fv14-1-末态.png') });
  记(`\n末态 ${末.length} 个：`);
  末.forEach((n) => 记(`   ${n.id}  ${n.类型}  \`${n.标题}\``));
  for (const [t, v] of Object.entries(目标)) 断言(`${t} = ${v}`, 计(末, t) === v, `${计(末, t)} 个`);
  断言('总数 12', 末.length === 12, `${末.length} 个`);
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFV15.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
