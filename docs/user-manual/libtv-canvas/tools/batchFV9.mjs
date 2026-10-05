// ⭐⭐⭐⭐⭐ Batch FV-9：节点标题 `{index}` 的决定性实验（现在有权限做状态变更了）
//
// 目标更新后明确允许：测试账号上做有副作用的 CRUD，⛔ 只要不跑真实生图/生视频。
// 于是 FV 一直卡着的决定性实验终于能做：**新建一个节点，看它拿到几号**。
//
// 已知：
//   文本1×2  图片2×2  视频3×2  音频1×2  智能剪辑4  导演台5  逐帧拉片(无数字)  脚本V2 1
//   ⇒ 数字不唯一 ⇒ H2「画布全局递增」已被 FV-3 实测排除
//   ⇒ H1「添加节点面板里的类型序号」：文本1 图片2 视频3 智能剪辑4 导演台5 全中，
//      但**音频实测 1**（按面板顺序该是 6/7）⇒ H1 也对不上
//   ⇒ 剩下 H3「复制节点沿用原 index」与 H4「index 来自别的计数源」
//
// 决定性做法（每一步都有自证字段，缺陷 488）：
//   ① 读添加节点面板的**真实顺序**（现在用 aria=添加节点 精确定位，不再靠尺寸猜）
//   ② 新建一个**文本节点**，读它的 index
//   ③ 再新建一个**图片节点**，读它的 index
//   ④ 两个新节点都从**资产管理抽屉的「⋯ → 删除」菜单**删掉（⛔ 绝不按 Delete/Backspace）
//   ⑤ 复原自证：节点集合与开跑前逐条一致
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFV9.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

const 节点快照 = () => page.evaluate(() => {
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
      数字: 标题 ? (标题.文.match(/(\d+)\s*$/) || [])[1] || '' : '' });
  }
  return out;
});

const 点aria = async (名) => {
  const t = await page.evaluate((n) => {
    const e = document.querySelector(`[aria-label="${n}"]`);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
      中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
  }, 名);
  if (!t) { 记(`  ⛔ 找不到 aria="${名}"`); return null; }
  // 落点自证
  const 落 = await page.evaluate(({ x, y }) => {
    const e = document.elementFromPoint(x, y);
    if (!e) return null;
    let p = e;
    while (p && p.getAttribute('aria-label') !== x) p = p.parentElement;
    return { 命中tag: e.tagName, 命中aria: e.getAttribute('aria-label'), 归属性: p ? p.getAttribute('aria-label') : null };
  }, { x: t.中心[0], y: t.中心[1], x2: t.中心[0] });
  记(`  点 \`${名}\` @${t.中心.join(',')} ${t.w}×${t.h}；落点 tag=${落?.命中tag} aria=${落?.命中aria} 祖先aria=${落?.归属性}`);
  await page.mouse.click(t.中心[0], t.中心[1]);
  await page.waitForTimeout(1300);
  return t;
};

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);
  await page.screenshot({ path: resolve(EVID, 'fv9-0-开跑前.png') });

  // ── 0 有没有残留的「整理画布」确认框
  const 待答 = await page.evaluate(() => [...document.querySelectorAll('*')]
    .some((e) => /是否保留此次整理结果/.test(e.innerText || '') && e.children.length === 0));
  记(`「是否保留此次整理结果」浮层：${待答 ? '⛔ 还在，本轮先回答它' : '不在'}`);
  if (待答) {
    const 对 = await page.evaluate(() => {
      const o = [];
      for (const e of document.querySelectorAll('button, [role="button"]')) {
        const t = (e.innerText || '').trim();
        if (t !== '还原' && t !== '保留') continue;
        const r = e.getBoundingClientRect();
        o.push({ 文字: t, 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], w: Math.round(r.width) });
      }
      return o;
    });
    记(`  找到 ${对.length} 个：${对.map((b) => `${b.文字}@${b.中心}`).join(' / ')}`);
    const 还原 = 对.find((b) => b.文字 === '还原');
    if (还原) { await page.mouse.click(还原.中心[0], 还原.中心[1]); await page.waitForTimeout(1500); 记('  已点「还原」'); }
  }

  // ── 1 基线
  const 前 = await 节点快照();
  R.读数.前 = 前;
  断言('开跑前 12 个节点', 前.length === 12, `实际 ${前.length} 个`);
  记('\n| 类型 | 标题 | 数字 |');
  记('|---|---|---|');
  前.forEach((n) => 记(`| ${n.类型} | \`${n.标题}\` | ${n.数字 || '—'} |`));
  const 前id = 前.map((n) => n.id).sort();

  // ── 2 打开添加节点面板，写真实顺序
  记('\n--- ① 打开添加节点面板 ---');
  await 点aria('添加节点');
  await page.screenshot({ path: resolve(EVID, 'fv9-1-添加节点面板.png') });
  const 面板 = await page.evaluate(() => {
    const out = [];
    for (const el of document.querySelectorAll('body *')) {
      const s = (el.innerText || '').trim();
      if (!s || s.length > 16) continue;
      if (!/^(文本|图片|视频|智能剪辑|导演台|逐帧拉片|音频|脚本|素材库)/.test(s)) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 40 || r.height < 12) continue;
      if (r.y > 780) continue;                          // ⛔ 排除画布上的同名节点（都在 y<780 之外/之内，要按容器筛）
      out.push({ 文字: s, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width) });
    }
    // 按 x 排序（面板是竖排，但 y 会有子行）
    const seen = new Set();
    const uniq = out.filter((o) => { if (seen.has(o.文字)) return false; seen.add(o.文字); return true; });
    return uniq.sort((a, b) => a.y - b.y || a.x - b.x);
  });
  R.读数.面板 = 面板;
  断言('面板真的开了', 面板.length >= 8, `读到 ${面板.length} 项：${面板.map((p) => p.文字).join(' / ')}`);

  // ── 3 建一个文本节点
  记('\n--- ② 建一个文本节点 ---');
  const 文本项 = 面板.find((p) => p.文字 === '文本' || p.文字.startsWith('文本'));
  if (!文本项) { 记('  ⛔ 面板里没有「文本」项，放弃建节点'); }
  else {
    const 落 = await page.evaluate(({ x, y }) => {
      const e = document.elementFromPoint(x, y);
      return e ? { tag: e.tagName, 文字: (e.innerText || '').trim().slice(0, 12) } : null;
    }, { x: 文本项.x + Math.min(20, 文本项.w / 2), y: 文本项.y + 10 });
    记(`  落点自证 @${文本项.x},${文本项.y} → ${落?.tag} 「${落?.文字}」`);
    断言('落点属主是面板项', !!落 && /文本/.test(落.文字 || ''), `命中「${落?.文字}」`);
    await page.mouse.click(文本项.x + Math.min(20, 文本项.w / 2), 文本项.y + 10);
    await page.waitForTimeout(2000);
    const 后 = await 节点快照();
    R.读数.建文本后 = 后;
    const 新 = 后.filter((n) => !前id.includes(n.id));
    断言('确实新建出节点', 新.length === 1, `新增 ${新.length} 个：${新.map((n) => `${n.类型}/${n.标题}`).join(', ')}`);
    if (新.length === 1) {
      记(`  ⭐⭐ 新建的文本节点标题是 \`${新[0].标题}\` ⇒ 已有两个是「文本节点 1」，它拿到 **${新[0].数字 || '（无数字）'}**`);
      R.读数.新建文本 = 新[0];
    }
    await page.screenshot({ path: resolve(EVID, 'fv9-2-新建文本节点之后.png') });
  }
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFV9.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
