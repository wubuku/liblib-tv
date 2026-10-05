// 批次 189 a 轮：**全画布普查独立 CSS `scale` / `zoom` 属性。**
//
// 背景（批次 188 g 轮）：⊕ 按钮的屏上尺寸是 `min(72×缩放, 36)`，
// 机制是它身上一个**独立 CSS `scale` 属性 = `min(2, 1/缩放)`** ——
// 而这个 `scale` **不出现在 `getComputedStyle(el).transform` 里**。
// 我 188 f 轮只读 transform，整层漏掉，绕了半天。
//
// 🔴 立规 59 由此而立，但它只钉住了 ⊕ 一个元素。**手册里还有多少尺寸读数可能栽在同一个盲区？**
// 本轮做一次全量普查：把页面上**每一个**元素的 computed `scale` / `zoom` 读出来，
// 找出 `scale ≠ 1` 或 `zoom ≠ 1` 的那些，看它们是谁、量级多少、有没有出现在手册里。
//
// ⚠️ 阳性对照必须先做：普查前先在一个已知元素（⊕）上确认本扫描器**能抓到**它，
// 否则「只找到 0 个」是扫描器坏了，不是页面干净（立规：下「不存在」结论前先证明扫描器抓得到）。
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '189a', 目标: '普查独立 CSS scale / zoom 属性' };
await settle(p, R);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
rec.起点 = { 节点数: 基线.ids.length, 积分: await R.credits(), 缩放: await R.zoom() };

/**
 * 全量扫描：找出 computed scale ≠ 1 或 zoom ≠ 1 的元素。
 * 同时把 transform 的缩放分量一起读，便于判断「是 transform 在缩放，还是独立 scale 在缩放」。
 * @param {string} 态 标签
 * @param {boolean} 是否带上 transform 矩阵（带矩阵的读法慢，只在必要时开）
 */
const 普查 = (态, 详细) => p.evaluate(({ 态, 详细 }) => {
  const 视口 = document.querySelector('.react-flow__viewport');
  const ms = 视口 ? /scale\(([-\d.]+)\)/.exec(视口.style.transform || '') : null;
  const 画布缩放 = ms ? parseFloat(ms[1]) : null;
  const 数 = (v) => { if (v === null || v === undefined) return null; const t = String(v).trim();
    if (t === '' || t === 'none') return null; const n = parseFloat(t); return Number.isFinite(n) ? n : null; };
  const 全部 = Array.from(document.querySelectorAll('*'));
  const 命中 = []; let 扫过 = 0; let 读错 = 0;
  for (const e of 全部) {
    扫过++;
    let cs; try { cs = getComputedStyle(e); } catch { 读错++; continue; }
    const sc = 数(cs.scale); const zm = 数(cs.zoom);
    // transform 里的缩放分量
    let tsc = null;
    if (详细) { const m = /matrix\(([-\d.eE+]+),\s*[-\d.eE+]+,\s*[-\d.eE+]+,\s*([-\d.eE+]+)/.exec(cs.transform || '');
      tsc = m ? parseFloat(m[2]) : null; }
    const 独立缩放 = (sc !== null && Math.abs(sc - 1) > 0.001) || (zm !== null && Math.abs(zm - 1) > 0.001);
    const 变换缩放 = tsc !== null && Math.abs(tsc - 1) > 0.001;
    if (!独立缩放 && !(详细 && 变换缩放)) continue;
    const r = e.getBoundingClientRect();
    命中.push({
      tag: e.tagName, testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
      cls: String(e.className || '').split(' ').slice(0, 3).join(' '),
      独立scale: cs.scale, 独立zoom: cs.zoom, transform: cs.transform, transform缩放分量: tsc,
      offsetWidth: e.offsetWidth, offsetHeight: e.offsetHeight,
      屏上: { w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100 },
      在viewport内: !!e.closest('.react-flow__viewport'),
      在renderer内: !!e.closest('.react-flow__renderer'),
      祖先testid: (() => { const c = []; for (let n = e.parentElement; n && n !== document.body && c.length < 4; n = n.parentElement) { const t = n.getAttribute && n.getAttribute('data-testid'); if (t) c.push(t); } return c; })(),
    });
  }
  // 按「独立 scale/zoom ≠ 1」与「只有 transform ≠ 1」分成两组
  const 独立的 = 命中.filter((x) => (x.独立scale !== null && Math.abs(parseFloat(x.独立scale) - 1) > 0.001)
    || (x.独立zoom !== null && Math.abs(parseFloat(x.独立zoom) - 1) > 0.001));
  const 只变换的 = 命中.filter((x) => !独立的.includes(x));
  return { 态, 画布缩放, 缩放aria: (document.querySelector('[data-testid="canvas-zoom-percent"]') || {}).ariaLabel || null,
    选中数: document.querySelectorAll('.react-flow__node.selected').length,
    扫过元素数: 扫过, 读样式失败: 读错,
    独立scale或zoom命中: 独立的.length, 只有transform命中: 只变换的.length,
    独立命中清单: 独立的.slice(0, 40), 只变换清单: 只变换的.slice(0, 40) };
}, { 态, 详细 });

// —— 阳性对照：先选中一个带内容的图片节点，⊕ 一定在「独立命中」里
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
  .map((e) => { const r = e.getBoundingClientRect(); return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; })
  .filter((x) => x.文字.includes('b22-upload')));
if (!命中结果.length) { await p.keyboard.press('Escape'); throw new Error('搜索无命中'); }
await p.mouse.click(命中结果[0].点[0], 命中结果[0].点[1]); await p.waitForTimeout(1600);
rec.选中 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
await p.keyboard.press('Escape'); await p.waitForTimeout(500);

rec.各态 = [];
// ① 单选节点、26%（阳性对照所在状态）
await p.mouse.move(1250, 706); await p.waitForTimeout(600);
rec.各态.push(await 普查('单选节点@26%', true));
// ② 同状态、换 100%：看 scale 公式是否随之变化
await setZoom(p, 100); await p.mouse.move(1250, 706); await p.waitForTimeout(800);
rec.各态.push(await 普查('单选节点@100%', true));
// ③ 22%：再取一个低缩放点
await setZoom(p, 22); await p.mouse.move(1250, 706); await p.waitForTimeout(800);
rec.各态.push(await 普查('单选节点@22%', true));
// ④ 取消选中、26%：静息态
await setZoom(p, 26); await p.keyboard.press('Escape'); await p.waitForTimeout(900);
rec.各态.push(await 普查('静息@26%', true));

// —— 判定
rec.判定 = {
  阳性对照: (() => { const a = rec.各态[0];
    const 加号 = a.独立命中清单.find((x) => /connection-menu-button/.test(x.testid || ''));
    return { 单选态独立命中数: a.独立scale或zoom命中, 抓到加号: !!加号,
      加号读数: 加号 ? { testid: 加号.testid, 独立scale: 加号.独立scale, 独立zoom: 加号.独立zoom, transform: 加号.transform, offsetWidth: 加号.offsetWidth, 屏上: 加号.屏上 } : null }; })(),
  各态独立命中数: rec.各态.map((x) => ({ 态: x.态, 缩放: x.画布缩放, 独立: x.独立scale或zoom命中, 只变换: x.只有transform命中, 扫过: x.扫过元素数, 读样式失败: x.读样式失败 })),
  独立命中的testid种类: (() => { const s = new Set(); for (const x of rec.各态) for (const h of x.独立命中清单) s.add(h.testid || ('(无testid) ' + h.cls.slice(0, 40))); return Array.from(s); })(),
  非空守卫: { 态数: rec.各态.length, 每态都扫过足够元素: rec.各态.every((x) => x.扫过元素数 > 1000), 阳性对照通过: rec.各态[0].独立命中清单.some((h) => /connection-menu-button/.test(h.testid || '')) },
};

await p.keyboard.press('Escape'); await p.waitForTimeout(700);
rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();
