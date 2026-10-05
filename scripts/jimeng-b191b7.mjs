// 批次 191 b7 轮：b6 把「上界是节点尺寸的函数」**推翻了** —— 同为 canvas 320×320 的三个节点，
//   音频 1/2/3 → 1.125（三者逐字相同）｜ 文本 3 → 1.5625 ｜ 导演台 → 1.75
// ⇒ 上界**与尺寸无关**；而 3 个音频逐字相同、又与文本/导演台各不相同
//   ⇒ 最可能是**按节点类型给的预设取景缩放**。
//
// 🔑 b7 就是判这一条：把每一类里能取到的多个节点各测一遍。
//   · 同类型逐字相同 ⇒ 「按类型给预设」成立，机制结清。
//   · 同类型内部还有差异 ⇒ 连「按类型」都不成立，只能记「随节点而异、机制未隔离」。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b191b7.json';
const 记 = { 轮次: 'b191b7', 问题: '取景缩放是不是「按节点类型给的预设」', 读数: [] };
const save = () => fs.writeFileSync(OUT, JSON.stringify(记, null, 1));

const 读缩放 = (p) => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  const vp = document.querySelector('.react-flow__viewport');
  const t = (vp && vp.style.transform) || '';
  return { aria: e ? e.getAttribute('aria-label') : null, 原始transform: t,
    实测scale: (function () { const m = /scale\(([-\d.]+)\)/.exec(t); return m ? Math.round(parseFloat(m[1]) * 1000000) / 1000000 : null; })() };
});
const 输入框 = 'input[aria-label="搜索"]';
async function 开面板(p) {
  const btn = await p.evaluate(() => { const a = Array.from(document.querySelectorAll('BUTTON[data-testid="canvas-panel-launcher"]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '搜索'); if (!a) return null;
    const r = a.getBoundingClientRect(); return { expanded: a.getAttribute('aria-expanded'), 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
  if (btn && btn.expanded !== 'true') { await p.mouse.click(btn.中心[0], btn.中心[1]); await p.waitForTimeout(1100); }
}
async function 取结果(p, 词) {
  let 点 = await p.evaluate((sel) => { const i = document.querySelector(sel); if (!i) return null;
    const r = i.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 输入框);
  if (!点) { await 开面板(p); 点 = await p.evaluate((sel) => { const i = document.querySelector(sel); if (!i) return null;
    const r = i.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 输入框); }
  if (!点) return [];
  await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(300);
  await p.keyboard.press('Meta+a'); await p.keyboard.type(词); await p.waitForTimeout(1500);
  return p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]')).map((b) => {
    const r = b.getBoundingClientRect();
    return { id: (b.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), aria: b.getAttribute('aria-label'),
      中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }));
}

const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
const 基线 = { ids: await R.ids(), credits: await R.credits() };

// 每一类取**多个**：音频取 4 个（翻页换行）、文本取 3 个、时间线取 2 个、视频/图片/其他各 1 个
const 计划 = [['音频', 4], ['文本', 3], ['时间线', 2], ['视频', 1], ['图片', 1], ['导演台', 1]];
for (const [词, 取几条] of 计划) {
  for (let i = 0; i < 取几条; i++) {
    await setZoom(p, 200); await p.waitForTimeout(550);
    await p.keyboard.press('Escape'); await p.waitForTimeout(350);
    const 前 = await 读缩放(p);
    const 行 = await 取结果(p, 词);
    if (!行.length) { 记.读数.push({ 词, 第几条: i + 1, 无效: true, 原因: '没有结果行' }); save(); break; }
    const 目标 = 行[i % 行.length];      // 换一条：同一次搜索里点不同的结果行
    await p.mouse.click(目标.中心[0], 目标.中心[1]);
    const 选中 = await R.selCount();
    await p.waitForTimeout(2000);
    const 末 = await 读缩放(p);
    const 节点 = await p.evaluate(([nid, z]) => { const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
      const r = n.getBoundingClientRect(); const s = z || 1;
      return { 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        canvas尺寸: [Math.round(r.width / s), Math.round(r.height / s)],
        完整在视口内: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight }; }, [目标.id, 末.实测scale]);
    记.读数.push({ 词, 第几条: i + 1, 目标id: 目标.id, 目标aria: 目标.aria, 前: 前.实测scale, 选中, 无效: 选中 !== 1,
      取景: 末.实测scale, transform: 末.原始transform, 节点 });
    console.log(`搜「${词}」第${i + 1}条 (${目标.aria}) 200% → ${末.实测scale}  canvas尺寸 ${JSON.stringify(节点 && 节点.canvas尺寸)}`);
    await p.keyboard.press('Escape'); await p.waitForTimeout(350);
    save();
  }
}
const 有效 = 记.读数.filter((x) => !x.无效);
const 按类 = {};
for (const r of 有效) { (按类[r.词] = 按类[r.词] || []).push({ aria: r.目标aria, 取景: r.取景 }); }
记.小结 = { 按类, 每类是否逐字相同: Object.fromEntries(Object.entries(按类).map(([k, v]) => [k, new Set(v.map((x) => x.取景)).size === 1])),
  全在视口内: 有效.every((x) => x.节点 && x.节点.完整在视口内) };
console.log('小结 =', JSON.stringify(记.小结, null, 1));
const ids = await R.ids();
记.收尾 = { 状态行: await R.status(), credits: await R.credits(), 节点数: ids.length,
  残留: ids.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids.includes(x)) };
await setZoom(p, 26); await p.waitForTimeout(500);
记.收尾.zoom = await R.zoom();
save();
console.log('收尾 =', JSON.stringify(记.收尾));
await b.close();
