// 批次 79 · D：验一个**可证伪的预测**。
// b79a/b79b 的数字里有一组可疑的比例：
//   主体    旧记 310      实测 352   ⇒ 310/352   = 0.8807
//   时间线  旧记 1055×182 实测 1200×207 ⇒ 1055/1200 = 0.8792，182/207 = 0.8792
// ⇒ 两者共用同一个约 **0.88** 的除数。
// 预测：**如果在 88% 缩放下读屏上尺寸，就能逐字读出手册里的旧数字。**
// 做法：扫若干缩放档，把 5 个既有节点（只读）的**屏上**尺寸都记下来，
//      再反查「哪个档位能复现哪个旧数字」。
// 这同时也是对批次 78 那条规则的正面检验：除数必须当场读，不能靠记忆。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), sweep: [], legacy: {} };
const scaleOf = () => p.evaluate(() => { const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform); return m ? +(+m[1]).toFixed(6) : null; });
const labelOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const settle = async () => { for (let i = 0; i < 15; i++) { const a = await scaleOf(); await p.waitForTimeout(200); const c = await scaleOf();
  if (a === c) return { scale: c, label: await labelOf(), stable: true }; } return { scale: await scaleOf(), stable: false }; };
const setZoom = async (pct) => { await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const sl = 'input[data-testid=canvas-zoom-percent-input]';
  if (!(await p.$(sl))) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); return; }
  await p.fill(sl, String(pct)); await p.keyboard.press('Enter'); await p.waitForTimeout(1500); };
const readAll = () => p.evaluate((ids) => Object.fromEntries(ids.map((v) => {
  const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return [v, null];
  const r = n.getBoundingClientRect();
  return [v, { screen: [+r.width.toFixed(1), +r.height.toFixed(1)],
    title: (n.querySelector('[data-testid=flow-node-title]') || {}).innerText || (n.innerText || '').split('\n')[0] || '' }];
  // ⚠️ 自伤修正①：上一版少一个右括号（`Object.fromEntries(` 与 `p.evaluate(` 都等着闭合）。
  // ⚠️ 自伤修正②：即使补上括号仍在运行时抛 `ids is not defined` ——
  //    `readAll` 声明在模块层、`ids` 声明在 try 块内，闭包在调用时才解析。
  //    改成**全部提到模块作用域**，不再依赖块级作用域。
})), ids);   // 三个括号：map → fromEntries → evaluate；`ids` 是 evaluate 的第二个参数
// 观察名单提到模块层（全是基线/已登记的他人节点，**只读**，不创建、不删除）
const watch = Object.entries(BASE.nodes).map(([id, rec]) => ({ id, title: rec.title }));
const extAudio = Object.entries(BASE._external_nodes || {}).find(([, r]) => r.title === '音频 1');
if (extAudio) watch.push({ id: extAudio[0], title: '音频 1' });
const ids = watch.map((x) => x.id);
try {
  for (const pct of [88, 75, 70, 100, 60]) {
    await setZoom(pct);
    const z = await settle();
    if (!z.stable) { log('⚠️', pct + '%', '未稳定，跳过'); continue; }
    const r = await readAll();
    const row = { asked: pct, scale: z.scale, label: z.label, nodes: {} };
    for (const w of watch) { const v = r[w.id]; if (v) row.nodes[w.title] = v.screen; }
    out.sweep.push(row);
    log(`设 ${String(pct).padStart(3)}% → scale ${String(z.scale).padEnd(9)}`,
      watch.map((w) => `${w.title} ${JSON.stringify(r[w.id] ? r[w.id].screen : null)}`).join(' ｜ '));
  }
  // 反查：哪个旧数字能在哪个档位被复现
  const legacy = { '主体 310×310': 310, '时间线 1055': 1055, '时间线 182': 182, '音频 222': 222, '音频 240': 240, '导演台 281': 281, '视频/图片 569': 569, '文本 320': 320 };
  out.legacy = {};
  for (const [name, v] of Object.entries(legacy)) {
    const hit = out.sweep.filter((s) => Object.values(s.nodes).some((n) => n && (Math.abs(n[0] - v) <= 1.2 || Math.abs(n[1] - v) <= 1.2)))
      .map((s) => `${s.asked}%(${s.scale})`);
    out.legacy[name] = hit.length ? hit.join(' , ') : '任何档位都没复现';
  }
  log('反查', JSON.stringify(out.legacy, null, 1));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let t = 0; t < 3; t++) { const z = await labelOf(); if (z && z.includes('60%')) break; await setZoom(60); }
  const zf = await settle();
  out.final = { zoomLabel: await labelOf(), scale: zf.scale };
  log('归位', JSON.stringify(out.final));
  writeFileSync(new URL('./_tmp-b79d.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
