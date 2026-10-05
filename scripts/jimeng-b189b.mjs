// 批次 189 b 轮：**`min(2, 1/缩放)` 是不是页面上的一条通用规则** —— 而不只是 ⊕ 的怪癖。
//
// a 轮普查（扫过 2400–2534 个元素/态）的结果：
//   带**独立 `scale` 属性 ≠ 1** 的元素有 **171–229 个**，落在四个 testid 家族上：
//     ① `flow-node-*-connection-menu-button`（⊕）  offsetWidth 36，scale 读 `2`
//     ② `flow-node-title`                            offsetWidth 56，scale 读 `2`
//     ③ `flow-node-selected-tag`                     offsetWidth 24，scale 读 `2`
//     ④ （无 testid）`absolute -inset-1 visible`       offsetWidth 32，scale 读 **1.88838 / 1.92308**（小数！）
//   而「只有 transform 缩放 ≠ 1」的只有 **1–3 个**（viewport 本体、node-feature-chrome-host、canvas-feature-sidecar）。
//
// 🔴 家族 ①②③ 的 `scale` 读数**恒为 `2`，与缩放无关**；而它们的屏上尺寸却随缩放变
//   （`flow-node-title`：50% 档屏上 55.55、100% 档 111.09、22% 档 24.44、26% 档 28.88）
//   ⇒ 与 ⊕ **完全同形**：`屏上 = offsetWidth × min(2, 1/缩放) × 缩放` = `min(2·offsetWidth·缩放, offsetWidth)`。
// 家族 ④ 的 scale 是**小数且逐档不同**，规则可能不一样 ⇒ 单独读，不硬套。
//
// 本轮：对同一批节点，在 **6 档缩放**下逐个家族验公式，并给家族 ④ 找它自己的规律。
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '189b', 目标: '逐档验 scale=min(2,1/s) 是否通用' };
await settle(p, R);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
rec.起点 = { 节点数: 基线.ids.length, 积分: await R.credits(), 缩放: await R.zoom() };

// 选中带内容的图片节点（搜索面板，188b/188f 验证过）
const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
  if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
if (!开) throw new Error('没有搜索按钮');
await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
  if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
if (!输入) { await p.keyboard.press('Escape'); throw new Error('搜索面板没打开'); }
await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
await p.fill('[data-testid="canvas-search-panel"] input', 'b22-upload'); await p.waitForTimeout(1500);
const 命中结果 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
  .map((e) => { const r = e.getBoundingClientRect(); return { 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; })
  .filter((x) => x.文字.includes('b22-upload')));
if (!命中结果.length) { await p.keyboard.press('Escape'); throw new Error('搜索无命中'); }
await p.mouse.click(命中结果[0].点[0], 命中结果[0].点[1]); await p.waitForTimeout(1800);
rec.选中 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
if (rec.选中.length !== 1) throw new Error('选中集不干净');

// 逐元素读：把「带独立 scale ≠ 1」的元素按 testid 家族归组
const 读家族 = () => p.evaluate(() => {
  const 视口 = document.querySelector('.react-flow__viewport');
  const ms = 视口 ? /scale\(([-\d.]+)\)/.exec(视口.style.transform || '') : null;
  const s = ms ? parseFloat(ms[1]) : null;
  const 数 = (v) => { if (v === null || v === undefined) return null; const t = String(v).trim();
    if (t === '' || t === 'none') return null; const n = parseFloat(t); return Number.isFinite(n) ? n : null; };
  const 组 = {};
  for (const e of Array.from(document.querySelectorAll('*'))) {
    let cs; try { cs = getComputedStyle(e); } catch { continue; }
    const sc = 数(cs.scale); if (sc === null || Math.abs(sc - 1) <= 0.001) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 0.5) continue;   // 看不见的不进统计
    const key = e.getAttribute('data-testid') || ('(无testid)' + String(e.className || '').split(' ').slice(0, 3).join(' '));
    (组[key] = 组[key] || []).push({ scale: sc, offsetW: e.offsetWidth, offsetH: e.offsetHeight,
      屏上w: Math.round(r.width * 100) / 100, 屏上h: Math.round(r.height * 100) / 100,
      逐字: (e.innerText || '').trim().slice(0, 20) });
  }
  const 出 = {};
  for (const k of Object.keys(组)) {
    const v = 组[k];
    // 只留「有代表性」的：取前 3 个不同 (offsetW, 屏上w) 组合
    const 签 = new Set(v.map((x) => `${x.offsetW}|${x.屏上w}`));
    出[k] = { 实例数: v.length, 不同签名数: 签.size,
      样本: Array.from(签).slice(0, 4).map((t) => { const [ow, sw] = t.split('|').map(Number);
        const one = v.find((x) => x.offsetW === ow && x.屏上w === sw);
        return { offsetW: ow, 屏上w: sw, offsetH: one.offsetH, 屏上h: one.屏上h, scale: one.scale, 逐字: one.逐字 }; }) };
  }
  return { scale: s, 缩放aria: (document.querySelector('[data-testid="canvas-zoom-percent"]') || {}).ariaLabel || null,
    选中数: document.querySelectorAll('.react-flow__node.selected').length, 家族: 出 };
});

const 档位 = [22, 26, 40, 50, 60, 100, 150, 200, 26];
rec.各档 = [];
for (const pct of 档位) {
  const z = await setZoom(p, pct);
  await p.mouse.move(1250, 706); await p.waitForTimeout(850);
  const d = await 读家族();
  rec.各档.push({ 档: pct, 回读: z.回读, 已追平: z.scale已追平, ...d });
}

// —— 判定：逐家族逐档对照 min(2·offsetW·s, offsetW)
rec.公式对照 = [];
for (const st of rec.各档) {
  for (const k of Object.keys(st.家族)) {
    for (const smp of st.家族[k].样本) {
      const 预测通用 = Math.min(2 * smp.offsetW * st.scale, smp.offsetW);
      const 预测朴素 = smp.offsetW * st.scale;
      rec.公式对照.push({ 家族: k, 档: st.档, scale: st.scale, offsetW: smp.offsetW, 屏上: smp.屏上w,
        scale属性: smp.scale, 预测min2式: Math.round(预测通用 * 100) / 100, 预测朴素式: Math.round(预测朴素 * 100) / 100,
        符合min2式: Math.abs(smp.屏上w - 预测通用) <= Math.max(0.6, smp.offsetW * 0.02),
        符合朴素式: Math.abs(smp.屏上w - 预测朴素) <= 0.6, 逐字: smp.逐字 });
    }
  }
}
const 按家族 = {};
for (const r of rec.公式对照) {
  (按家族[r.家族] = 按家族[r.家族] || { 总数: 0, 合min2: 0, 合朴素: 0, 档: [] });
  按家族[r.家族].总数++;
  if (r.符合min2式) { 按家族[r.家族].合min2++; 按家族[r.家族].档.push(r.档); }
  if (r.符合朴素式) 按家族[r.家族].合朴素++;
}
for (const k of Object.keys(按家族)) 按家族[k].全档合min2 = 按家族[k].合min2 === 按家族[k].总数;
rec.判定 = { 按家族,
  家族清单: Object.keys(按家族),
  全都符合min2式: Object.keys(按家族).every((k) => 按家族[k].全档合min2),
  非空守卫: { 档数: rec.各档.length, 对照行数: rec.公式对照.length, 家族数: Object.keys(按家族).length,
    每档都选中: rec.各档.every((x) => x.选中数 === 1), scale与aria一致: rec.各档.every((x) => Math.abs(x.scale - x.档 / 100) <= 0.005) } };

await p.keyboard.press('Escape'); await p.waitForTimeout(700);
rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();
