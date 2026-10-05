// 批次 191 b2 轮：修掉 b 轮的选择器（`input[aria=…]` 应为 `input[aria-label=…]`）后重跑。
//
// 本轮要回答的唯一问题：**批次 190 记的「按 ⌘V 之后缩放会自己变」，变量到底是谁。**
//   候选 A：⌘V 本身            —— a 轮已当场证伪（⌘V 确实粘出节点 76→77，缩放 7 秒内 6 点逐字不变）
//   候选 B：点搜索结果行       —— 批次 188 f 轮撞见过「点结果行触发缩放动画」却当成干扰丢掉
//   候选 C：什么都不按也会漂   —— a 轮臂 3（7 秒静置）未见变化
//
// 🔑 每条臂都带**阳性守卫**；守卫不过 ⇒ 该臂标 `无效臂`，**不计入结论**（a 轮教训）。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b191b2.json';
const 记 = { 轮次: 'b191b2', 假设: '缩放变化来自「点搜索结果行」而非「按 ⌘V」', 臂: [], 附带发现: [], 收尾: null };
const save = () => fs.writeFileSync(OUT, JSON.stringify(记, null, 1));

const 读缩放 = (p) => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  const vp = document.querySelector('.react-flow__viewport');
  const t = (vp && vp.style.transform) || '';
  const ms = /scale\(([-\d.]+)\)/.exec(t);
  const mt = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(t);
  return { aria: e ? e.getAttribute('aria-label') : null,
    实测scale: ms ? Math.round(parseFloat(ms[1]) * 1000) / 1000 : null,
    平移: mt ? [Math.round(parseFloat(mt[1]) * 10) / 10, Math.round(parseFloat(mt[2]) * 10) / 10] : null };
});

async function 序列(p, 标签, 计划表 = [0, 300, 800, 2000, 4000]) {
  const 点 = []; const t0 = Date.now();
  for (const 计划 of 计划表) { const 等 = 计划 - (Date.now() - t0); if (等 > 0) await p.waitForTimeout(等);
    点.push({ ms: Date.now() - t0, ...(await 读缩放(p)) }); }
  const sc = 点.map((x) => x.实测scale);
  return { 标签, 点, 末态: 点[点.length - 1], scale取值集: [...new Set(sc)], scale是否收敛: new Set(sc).size === 1 };
}

const 归位 = async (p, pct = 26) => { const r = await setZoom(p, pct); await p.waitForTimeout(500); return r; };
const 输入框 = 'input[aria-label="搜索"]';

async function 开面板(p) {
  const btn = await p.evaluate(() => { const a = Array.from(document.querySelectorAll('BUTTON[data-testid="canvas-panel-launcher"]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
    if (!a) return null; const r = a.getBoundingClientRect();
    return { expanded: a.getAttribute('aria-expanded'), 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
  if (!btn) throw new Error('找不到搜索启动器');
  if (btn.expanded !== 'true') { await p.mouse.click(btn.中心[0], btn.中心[1]); await p.waitForTimeout(1200); }
  const 框值 = await p.evaluate((sel) => { const i = document.querySelector(sel); return i ? i.value : null; }, 输入框);
  const 框在 = await p.evaluate((sel) => { const i = document.querySelector(sel); if (!i) return null;
    const r = i.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 输入框);
  return { 启动器: btn, 框值, 框在 };
}

// 🔴 为什么不用 `p.fill`：这个输入框**通过全部可操作性检查**（visible / 非 disabled /
//   非 readonly / 命中测试返回它自己 / tabIndex=0），`page.fill` 却每次 30 秒超时。
//   c3 轮实测键盘路径（点一下 → ⌘A → type）**完全正常**。
//   剩下的最可能解释是「包围盒在抖」⇒ Playwright 的 stable 检查永远不满足；
//   下面 `采样包围盒` 就是去把这句话钉死或推翻的。
async function 采样包围盒(p, 帧数 = 24) {
  return p.evaluate((n) => {
    const i = document.querySelector('input[aria-label="搜索"]');
    if (!i) return null;
    const 采 = () => { const r = i.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map((v) => Math.round(v * 100) / 100); };
    return new Promise((res) => {
      const 序列 = []; let k = 0;
      const tick = () => { 序列.push({ 帧: k, 框: 采() }); if (++k < n) requestAnimationFrame(tick); else res(序列); };
      requestAnimationFrame(tick);
    });
  }, 帧数);
}

async function 搜(p, 词) {
  // 🔴 b2 轮第一版踩到：**改缩放会把搜索面板关掉**（与批次 134「任何缩放操作都会关掉小地图」同族）
  //   ⇒ 臂 A 里「先归位到 26% 再搜」之后，面板已经不在了，`搜` 直接抛「搜索框不在 DOM 里」。
  //   改成：取不到输入框就**重开面板**再取，并把「面板是否被缩放关掉」单独记一条。
  let 点 = await p.evaluate((sel) => { const i = document.querySelector(sel); if (!i) return null;
    const r = i.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 输入框);
  if (!点) { await 开面板(p); 点 = await p.evaluate((sel) => { const i = document.querySelector(sel); if (!i) return null;
    const r = i.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 输入框); }
  if (!点) throw new Error('搜索框不在 DOM 里（重开面板后仍取不到）');
  await p.mouse.click(点[0], 点[1]);
  await p.waitForTimeout(350);
  await p.keyboard.press('Meta+a');
  await p.keyboard.type(词);
  await p.waitForTimeout(1600);
  const 值 = await p.evaluate((sel) => { const i = document.querySelector(sel); return i ? i.value : null; }, 输入框);
  if (值 !== 词) throw new Error(`输入没生效：框里是 ${JSON.stringify(值)}，要求 ${JSON.stringify(词)}`);
  return p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]')).map((b) => {
    const r = b.getBoundingClientRect();
    return { id: (b.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), aria: b.getAttribute('aria-label'),
      中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }));
}

// ── 前置：把「输入框包围盒是否在抖」量出来（fill 超时的候选解释） ────────
const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
const 基线 = { ids: await R.ids(), credits: await R.credits() };
const P = await 开面板(p);
记.面板 = P;
{
  const 抖 = await 采样包围盒(p, 24);
  const 不同 = 抖 ? new Set(抖.map((x) => x.框.join(','))).size : 0;
  记.附带发现.push({ 项: '搜索框包围盒 24 帧内是否变化', 帧数: 抖 ? 抖.length : 0, 不同取值数: 不同,
    首帧: 抖 && 抖[0].框, 末帧: 抖 && 抖[抖.length - 1].框,
    结论: 不同 === 1 ? '24 帧内逐字不变 ⇒ 包围盒**不抖** ⇒ fill 超时不是 stable 造成的' : `24 帧内有 ${不同} 种取值 ⇒ 在抖` });
  console.log('包围盒 24 帧 =', 抖 ? 抖.length : 'null', '帧，不同取值', 不同);
}
console.log('面板框值 =', JSON.stringify(P.框值), '框在 =', JSON.stringify(P.框在));
save();

// ── 臂 A：对**三种不同类型**的节点各做一次「只点搜索结果行」 ──────────────
async function 臂A(词, 序) {
  await 归位(p, 26);
  const 结果 = await 搜(p, 词);
  if (!结果.length) { 记.臂.push({ 序, 词, 无效臂: true, 原因: '没有结果行', 结果数: 0 }); save(); return null; }
  const 目标 = 结果[0];
  const 前 = await 读缩放(p);
  await p.mouse.click(目标.中心[0], 目标.中心[1]);
  const 选中 = await R.selCount();
  const 状态行 = await R.status();
  const 焦点 = await p.evaluate(() => { const a = document.activeElement; return a ? a.tagName + '[' + (a.getAttribute('data-testid') || '') + ']' : null; });
  const 节点 = await p.evaluate((nid) => { const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
    return { 屏上: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10], aria: n.getAttribute('aria-label'),
      canvas: m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null }; }, 目标.id);
  const 序读 = await 序列(p, `臂A ${词}`);
  const 臂 = { 序, 词, 结果数: 结果.length, 目标: { id: 目标.id, aria: 目标.aria }, 前, 选中, 状态行, 焦点, 节点, 序列: 序读,
    阳性守卫: { 通过: 选中 === 1, 判据: `选中数 = ${选中}` }, 无效臂: 选中 !== 1,
    判定: { scale变化: 前.实测scale !== 序读.末态.实测scale, 旧: 前.实测scale, 新: 序读.末态.实测scale,
      平移变化: JSON.stringify(前.平移) !== JSON.stringify(序读.末态.平移), 旧平移: 前.平移, 新平移: 序读.末态.平移 } };
  记.臂.push(臂); save();
  console.log(`臂A(${词}) 结果${结果.length}行 守卫=${选中} scale ${前.实测scale}→${序读.末态.实测scale} 屏上=${JSON.stringify(节点 && 节点.屏上)}`);
  return 臂;
}
// ── 显式验一条：改缩放会不会关掉搜索面板（b2 轮第一版被它整轮打断） ──────
{
  await 开面板(p);
  const 前面板在 = await p.evaluate((sel) => !!document.querySelector(sel), 输入框);
  await 归位(p, 50);
  const 后面板在 = await p.evaluate((sel) => !!document.querySelector(sel), 输入框);
  记.附带发现.push({ 项: '改缩放会不会关掉搜索面板', 前面板在, 后面板在,
    结论: 前面板在 && !后面板在 ? '✅ 会被关掉（与批次 134「缩放关小地图」同族）' : (前面板在 ? '没被关掉' : '前面板就不在，结论不成立') });
  console.log('缩放关面板 =', 前面板在, '→', 后面板在);
  await 归位(p, 26);
  save();
}
await 臂A('视频', 'A1');
await 臂A('音频 1', 'A2');
await 臂A('时间线', 'A3');

// ── 臂 B：搜索选中 → 等动画结束 → 按 ⌘V → 再读（看 ⌘V 有没有第二次改动） ──
{
  const 结果 = await 搜(p, '视频');
  if (!结果.length) { 记.臂.push({ 序: 'B', 无效臂: true, 原因: '没有结果行' }); }
  else {
    const 目标 = 结果[0];
    await p.mouse.click(目标.中心[0], 目标.中心[1]);
    await p.waitForTimeout(4500);
    const 稳定值 = await 读缩放(p);
    const ids前 = await R.ids();
    const 焦点 = await p.evaluate(() => { const a = document.activeElement; return a ? a.tagName + '[' + (a.getAttribute('data-testid') || '') + ']' : null; });
    await p.keyboard.press('Meta+v');
    await p.waitForTimeout(300);
    const ids后 = await R.ids();
    const 序读 = await 序列(p, '臂B 稳定后按 ⌘V');
    记.臂.push({ 序: 'B', 动作: '搜索选中 → 等 4.5 秒 → 按 ⌘V', 目标: { id: 目标.id, aria: 目标.aria },
      稳定值, 焦点, 节点数: [ids前.length, ids后.length], 新增id: ids后.filter((x) => !ids前.includes(x)),
      阳性守卫: { 通过: ids后.length !== ids前.length, 判据: `节点数 ${ids前.length} → ${ids后.length}` },
      无效臂: ids后.length === ids前.length, 序列: 序读,
      判定: { scale变化: 稳定值.实测scale !== 序读.末态.实测scale, 旧: 稳定值.实测scale, 新: 序读.末态.实测scale,
        平移变化: JSON.stringify(稳定值.平移) !== JSON.stringify(序读.末态.平移) } });
    console.log(`臂B 守卫=${ids后.length !== ids前.length} 节点${ids前.length}→${ids后.length} scale ${稳定值.实测scale}→${序读.末态.实测scale}`);
    await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  }
  save();
}

// ── 臂 C：对照 · 不经搜索面板，直接点画布上的节点标题行 ──────────────────
{
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  await 归位(p, 26);
  const 命中 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const t = n.querySelector('[data-testid="flow-node-title"]'); if (!t) return null;
    const r = t.getBoundingClientRect();
    if (!(r.width > 3 && r.x > 80 && r.x + r.width < innerWidth - 340 && r.y > 100 && r.y + r.height < innerHeight - 100)) return null;
    return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'), 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
  }).filter(Boolean));
  if (!命中.length) 记.臂.push({ 序: 'C', 无效臂: true, 原因: '26% 下没有可点的标题行' });
  else {
    const 前 = await 读缩放(p);
    await p.mouse.click(命中[0].中心[0], 命中[0].中心[1]);
    const 选中 = await R.selCount();
    const 序读 = await 序列(p, '臂C 画布上直接点标题行');
    记.臂.push({ 序: 'C', 动作: '不经搜索面板，直接点画布上的节点标题行', 目标: { id: 命中[0].id, aria: 命中[0].aria }, 前,
      阳性守卫: { 通过: 选中 === 1, 判据: `选中数 = ${选中}` }, 无效臂: 选中 !== 1, 序列: 序读,
      判定: { scale变化: 前.实测scale !== 序读.末态.实测scale, 旧: 前.实测scale, 新: 序读.末态.实测scale } });
    console.log(`臂C 守卫=${选中} scale ${前.实测scale}→${序读.末态.实测scale}`);
  }
  save();
}

// ── 臂 D：搜索框的值会不会跨「开→关→再开」保留 ────────────────────────
{
  const 前值 = await p.evaluate((sel) => { const i = document.querySelector(sel); return i ? i.value : null; }, 输入框);
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  const 关后 = await p.evaluate((sel) => { const i = document.querySelector(sel); return { 在DOM: !!i, 值: i ? i.value : null }; }, 输入框);
  const 再开 = await 开面板(p);
  记.附带发现.push({ 项: '搜索框的值跨开合是否保留', 前值, 关后, 再开后: 再开.框值,
    保留: 再开.框值 === 前值, 注: '前值是批次 190 留在框里的哨兵 JIMENG-B190-SENTINEL' });
  console.log('臂D 搜索框保留值 =', 再开.框值, '（关后在DOM:', JSON.stringify(关后), '）');
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  save();
}

// ── 收尾 ────────────────────────────────────────────────────────────────
{
  const ids = await R.ids();
  const 新 = ids.filter((x) => !基线.ids.includes(x));
  const 清 = [];
  for (const id of 新) {
    const ok = await p.evaluate((nid) => { const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return { 删: false };
      const t = n.querySelector('[data-testid="flow-node-title"]') || n; const r = t.getBoundingClientRect();
      return { 删: true, aria: n.getAttribute('aria-label'), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }, id);
    if (!ok.删) { 清.push({ id, 失败: '找不到' }); continue; }
    await p.mouse.click(ok.点[0], ok.点[1]); await p.waitForTimeout(500);
    await p.mouse.click(ok.点[0], ok.点[1], { button: 'right' }); await p.waitForTimeout(900);
    const bb = await p.evaluateHandle(() => Array.from(document.querySelectorAll('[role=menuitem]')).find((x) => (x.innerText || '').trim().startsWith('删除')) || null);
    const el = bb.asElement();
    if (!el) { await p.keyboard.press('Escape'); 清.push({ id, 失败: '菜单无删除项' }); continue; }
    const box = await el.boundingBox();
    if (!box) { await p.keyboard.press('Escape'); 清.push({ id, 失败: '无包围盒' }); continue; }
    await p.mouse.click(box.x + box.width / 2, box.y + box.height / 2); await p.waitForTimeout(1300);
    清.push({ id, aria: ok.aria, 删了: true });
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  await 归位(p, 26);
  const ids2 = await R.ids();
  记.收尾 = { 清理: 清, 状态行: await R.status(), 选中: await R.selCount(), zoom: await R.zoom(), credits: await R.credits(),
    节点数: ids2.length, 基线节点数: 基线.ids.length,
    残留: ids2.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids2.includes(x)) };
  save();
  console.log('收尾 =', JSON.stringify(记.收尾));
}
await b.close();
console.log('写出', OUT);
