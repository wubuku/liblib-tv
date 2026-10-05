// ⭐⭐⭐⭐⭐ Batch FV-16：把主画布补回 12 个基线（补 1 音频 + 1 文本）
//
// 现状（FV-15 末态实测 10 个）：audio×1 text×1 image×2 video×2 clip×1 director×1
//                             script-v2×1 shot-breakdown×1
// 目标 12 个：补 1 个音频 + 1 个文本。
//
// ⭐⭐⭐ 本轮最重要的一条，是 FV-15 暴露的**新缺陷 492**：
//   FV-15 的目标数组写的是 `text: 2`，而**基线其实是 text×1** ——
//   FV-3 实测的 12 个里文本只有 2 个，但 FV-9/FV-11 建节点时又各自多建了，
//   中间 FV-13 误删过一轮 ⇒ 「基线数字」在一轮轮增删之后已经漂了。
//   ⇒ **基线必须写成「节点 id 清单」，不能写成「各类型应有几个」**。
//   FV-3 记下来的原始 id 只有文本节点那两个，
//   音频节点 FV-3 没记 id（只记了标题）⇒ 本轮按「类型+标题」补。
//
// ⛔ 建节点不消耗积分（FQ-6 实测）。⛔ 一次只建一个，建完立即重读。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFV16.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
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
      类型: cls.replace('react-flow__node-', ''), 标题: 标题 ? 标题.文 : '' });
  }
  return out;
});

const 等稳定 = async (标签) => {
  let 上次 = -1, 稳 = 0;
  for (let i = 0; i < 25; i++) {
    const n = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    if (n === 上次) { 稳++; if (稳 >= 3) { 记(`  ${标签}：稳定在 ${n}`); return n; } }
    else { 稳 = 0; }
    上次 = n;
    await page.waitForTimeout(1200);
  }
  return 上次;
};

const 建一个 = async (词) => {
  const 加 = await page.evaluate(() => {
    const e = document.querySelector('[aria-label="添加节点"]');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  if (!加) { 记('  ⛔ 找不到「添加节点」'); return null; }
  await page.mouse.click(加[0], 加[1]);
  await page.waitForTimeout(1400);
  const p = await page.evaluate((w) => {
    const 候选 = [...document.querySelectorAll('div')].filter((d) => {
      const t = (d.innerText || '');
      return /智能剪辑/.test(t) && /逐帧拉片/.test(t) && new RegExp(w).test(t) && !/视频节点/.test(t) && !/图片节点/.test(t);
    });
    候选.sort((a, b) => a.getBoundingClientRect().height - b.getBoundingClientRect().height);
    const box = 候选[0];
    if (!box) return { 错: '面板容器没找到' };
    for (const el of box.querySelectorAll('*')) {
      if ((el.innerText || '').trim() !== w) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 30 || r.height < 10) continue;
      return { x: Math.round(r.x + Math.min(30, r.width / 2)), y: Math.round(r.y + r.height / 2) };
    }
    return { 错: `面板里没有「${w}」` };
  }, 词);
  if (p.错) { 记(`  ⛔ ${p.错}`); await page.keyboard.press('Escape'); await page.waitForTimeout(500); return null; }
  const 落 = await page.evaluate(({ x, y }) => {
    const e = document.elementFromPoint(x, y);
    return e ? (e.innerText || '').trim() : null;
  }, { x: p.x, y: p.y });
  断言(`落点属主是「${词}」`, 落 === 词, `命中「${落}」`);
  await page.mouse.click(p.x, p.y);
  await page.waitForTimeout(2200);
  return true;
};

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6000);
  await closePromos(page);
  await page.waitForTimeout(3000);
  await 等稳定('开跑前');

  let 前 = await 快照();
  R.读数.前 = 前;
  const 计 = (s, t) => s.filter((n) => n.类型 === t).length;
  记(`开跑前 ${前.length} 个：${前.map((n) => `${n.类型}:${n.标题}`).join(' / ')}`);

  // 目标（FV-3 的 12 个基线）
  const 目标 = { audio: 2, text: 2, image: 2, video: 2, 'video-clip': 1, 'director-console-3d': 1, 'script-v2': 1, 'shot-breakdown': 1 };
  for (const [类型, 要几个] of [['audio', 2], ['text', 2]]) {
    const 缺 = 目标[类型] - 计(前, 类型);
    记(`\n${类型}：目标 ${目标[类型]}，现有 ${计(前, 类型)}，缺 ${缺}`);
    for (let i = 0; i < 缺; i++) {
      const 词 = 类型 === 'audio' ? '音频' : '文本';
      记(`  建第 ${i + 1} 个「${词}」`);
      await 建一个(词);
      const 后 = await 快照();
      const 新 = 后.filter((n) => !前.some((o) => o.id === n.id));
      记(`  建后 ${后.length} 个，新增：${新.map((n) => `${n.id} ${n.类型}\`${n.标题}\``).join(' / ') || '（无）'}`);
      断言('只新增 1 个', 新.length === 1, `新增 ${新.length} 个`);
      if (新.length !== 1) break;
      前 = 后;
    }
  }

  await page.waitForTimeout(2500);
  const 末 = await 快照();
  R.读数.末 = 末;
  await page.screenshot({ path: resolve(EVID, 'fv16-1-末态.png') });
  记(`\n末态 ${末.length} 个：`);
  末.forEach((n) => 记(`   ${n.id}  ${n.类型}  \`${n.标题}\``));
  for (const [t, v] of Object.entries(目标)) 断言(`${t} = ${v}`, 计(末, t) === v, `${计(末, t)} 个`);
  断言('总数 12', 末.length === 12, `${末.length} 个`);
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFV16.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
