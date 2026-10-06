/**
 * 批次 257：**换一条路去缩放 —— 走缩放菜单，而不是等取景程序给你那个落点。**
 *
 * 📌 背景：到这里为止，`0.08`（应用下限）与 `0.5`（封顶）都只是**「定位」这条路上**读到的数：
 *   把视口调得很窄时定位会给出 `0.08`（批次 248），定位到大画布上会给出 `0.5`（批次 245）。
 *   🔴 但**「定位」只是缩放的一种入口**。用户平时是点缩放菜单里的放大/缩小。
 *   ⇒ **那两个上下限到底住在哪儿，从没被问过**：
 *     · 若菜单按钮**自己也卡在 `0.08` / `0.5`** ⇒ 它们是**全局的缩放上下限**，
 *       「定位」只是恰好撞上了同一条限；
 *     · 若菜单能走到 `0.08` 以下 / `0.5` 以上 ⇒ 那两个地板**只属于取景程序**，
 *       跟缩放控件本身无关 —— **用户手动缩放时看不到它们**。
 *   两种可能，**对用户是两种不同的手册结论**。
 *
 * 📌 判据（先写死）：逐级读缩放，找到**平台期**（再点也不变的那一段）。
 *   记下「点了几次开始不变」与「不变在哪个值」—— **不预设它一定是 `0.08` / `0.5`**。
 *
 * 📌 顺带把菜单的 DOM 抄下来（`aria-label` / 文案 / `data-testid`），
 *   因为用户手册要写的就是这些**逐字标签**。
 *
 * 🔴 纪律：缩放**不改变画布内容**，也不产生任何扣费；不新建、不删除、不上传、
 *   不触发生成、不进扣费页、不点「保存到主体库」、不分享。
 *
 * 用法：node scripts/jimeng-b257.mjs      （读数落盘 /tmp/b257.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B257_OUT || '/tmp/b257.json';
const 宽 = 1280, 高 = 720;

const log = (...a) => console.log(a.join(' '));

const 读缩放 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return {
    scale: m ? Number(m[1]) : null,
    aria: z ? z.getAttribute('aria-label') : null,
    text: z ? (z.innerText || '').trim() : null,
    expanded: z ? z.getAttribute('aria-expanded') : null,
    禁用: z ? z.hasAttribute('disabled') || z.getAttribute('aria-disabled') === 'true' : null,
  };
});

// 📌 把菜单里能点的都列出来（不预设它们叫什么）
const 列菜单 = (p) => p.evaluate(() => {
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  const 面 = [];
  for (const e of document.querySelectorAll('button,[role="button"],[role="menuitem"],input,[data-testid*="zoom"],[data-testid*="Zoom"]')) {
    const b = e.getBoundingClientRect();
    if (b.width < 4 || b.height < 4) continue;
    if (z && (e === z || z.contains(e))) continue;
    const 靠近 = z ? Math.abs(b.x - (z.getBoundingClientRect().x + z.getBoundingClientRect().width / 2)) < 400 : false;
    if (!靠近) continue;
    面.push({
      tag: e.tagName.toLowerCase(),
      type: e.getAttribute('type'),
      aria: e.getAttribute('aria-label'),
      text: (e.innerText || e.getAttribute('value') || '').trim().replace(/\s+/g, ' ').slice(0, 24),
      testid: e.getAttribute('data-testid'),
      cls: (typeof e.className === 'string' ? e.className : '').slice(0, 60),
      x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2),
      disabled: e.hasAttribute('disabled') || e.getAttribute('aria-disabled') === 'true',
    });
  }
  return 面;
});

// 🔴 侦察发现：菜单项是 **`div`** 而不是 `button`，也没有 `aria-label`
//   ——逐字文案是「放大视图 ⌘ +」「缩小视图 ⌘ -」等 ⇒ **只能按文案定位**。
//   ⚠️ 定位**只在 `canvas-zoom-menu` 之内**找，绝不按全文档匹配（否则会误伤别的元素）。
const 菜单项 = {
  放大: '放大视图',
  缩小: '缩小视图',
  适配: '适配画布',
  选中: '缩放至选中项',
  至50: '缩放至50%',
  至100: '缩放至100%',
  至200: '缩放至200%',
};

const 打开菜单 = async (p) => {
  const 位 = await p.evaluate(() => {
    const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
    if (!z) return null;
    const b = z.getBoundingClientRect();
    return [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)];
  });
  if (!位) throw new Error('找不到缩放读数钮');
  await p.mouse.click(位[0], 位[1]);
  await p.waitForTimeout(1200);
};

const 点菜单项 = async (p, 键) => {
  // 📌 点之前**重新打开菜单**（点完菜单通常会收起）
  await 打开菜单(p);
  const 位 = await p.evaluate((词) => {
    const 面 = document.querySelector('[data-testid="canvas-zoom-menu"]');
    if (!面) return null;
    const e = Array.from(面.querySelectorAll('div,button,[role="menuitem"]'))
      .find((x) => (x.innerText || '').trim().startsWith(词));
    if (!e) return null;
    if (e.getAttribute('aria-disabled') === 'true') return { 禁用: true };
    const b = e.getBoundingClientRect();
    if (b.width < 4 || b.height < 4) return null;
    return [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)];
  }, 菜单项[键]);
  if (!位) return { 错: `菜单里没有「${菜单项[键]}」` };
  if (位.禁用) return { 禁用: true };
  await p.mouse.click(位[0], 位[1]);
  await p.waitForTimeout(450);
  return { 点位: 位 };
};

const out = { 轮次: 'b257', 视口: [宽, 高], 初始: null, 菜单: null, 向上: [], 向下: [] };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();
try {
  await p.setViewportSize({ width: 宽, height: 高 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(6500);

  out.初始 = await 读缩放(p);
  log('初始缩放 ' + JSON.stringify(out.初始));

  // 📌 打开缩放菜单
  const 钮位 = await p.evaluate(() => {
    const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
    if (!z) return null;
    const b = z.getBoundingClientRect();
    return [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)];
  });
  if (!钮位) throw new Error('找不到缩放读数钮');
  await p.mouse.click(钮位[0], 钮位[1]);
  await p.waitForTimeout(1800);
  out.开菜单后 = await 读缩放(p);
  out.菜单 = await 列菜单(p);
  log(`=== 缩放菜单里 ${out.菜单.length} 个可点控件 ===`);
  for (const m of out.菜单) {
    log(`  [${m.x},${m.y}] <${m.tag}> aria=${JSON.stringify(m.aria)} text=${JSON.stringify(m.text)}`
      + ` testid=${JSON.stringify(m.testid)} disabled=${m.disabled} cls=${JSON.stringify(m.cls)}`);
  }

  // 📌 向上（放大）逐级点，**找到平台期为止**
  const 走 = async (键, 数组) => {
    for (let i = 1; i <= 30; i++) {
      const r = await 点菜单项(p, 键);
      if (r.错) { 数组.push({ 次: i, 错: r.错 }); log(`  🔴 ${r.错}`); break; }
      if (r.禁用) { 数组.push({ 次: i, 禁用: true }); log(`  ⚠️ 第 ${i} 次：「${菜单项[键]}」已禁用`); break; }
      const s = await 读缩放(p);
      数组.push({ 次: i, scale: s.scale, aria: s.aria });
      log(`  ${键} 第 ${i} 次 → ${s.scale}（${s.aria}）`);
      if (数组.length >= 3 && 数组.slice(-3).every((x) => x.scale === 数组[数组.length - 3].scale)) {
        log(`  ⇒ ${键} 连续 3 次逐字不变 = ${s.scale}（平台期在第 ${i} 次）`);
        数组[数组.length - 1].平台期 = true;
        break;
      }
    }
  };
  log('=== 放大 ===');
  await 走('放大', out.向上);
  log('=== 缩小 ===');
  await 走('缩小', out.向下);

  // 📌 菜单里明摆着「缩放至50% / 100% / 200%」⇒ 顺手把三个预设档各点一次，
  //   看它们落在哪 —— **「菜单提供 200%」这件事本身就与「0.5 是全局封顶」冲突**。
  log('=== 预设档 ===');
  out.预设 = [];
  for (const 键 of ['至50', '至100', '至200', '适配']) {
    const r = await 点菜单项(p, 键);
    if (r.错) { out.预设.push({ 键, 错: r.错 }); log(`  🔴 ${r.错}`); continue; }
    if (r.禁用) { out.预设.push({ 键, 禁用: true }); log(`  ⚠️ 「${菜单项[键]}」已禁用`); continue; }
    await p.waitForTimeout(900);
    const s = await 读缩放(p);
    out.预设.push({ 键, 菜单文案: 菜单项[键], scale: s.scale, aria: s.aria });
    log(`  「${菜单项[键]}」→ ${s.scale}（${s.aria}）`);
  }

  out.平台 = {
    放大平台: (out.向上.filter((x) => x.平台期).map((x) => x.scale)[0]) ?? null,
    缩小平台: (out.向下.filter((x) => x.平台期).map((x) => x.scale)[0]) ?? null,
  };
  log('=== 汇总 ===');
  log(`放大方向平台期 ${out.平台.放大平台}；缩小方向平台期 ${out.平台.缩小平台}`);
  log(`初始 ${out.初始.scale} → 放大末 ${out.向上[out.向上.length - 1]?.scale} → 缩小末 ${out.向下[out.向下.length - 1]?.scale}`);
} catch (e) {
  out.错误 = e.message;
  log('🔴 ' + e.message);
} finally {
  try { await p.close(); } catch (e) { /* 忽略 */ }
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  log('写入 ' + OUT);
}
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);