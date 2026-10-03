// Batch DG-0：三个遗留，都不需要授权。
//
// 遗留 1：卡面那个数字**统计的是什么**（使用量？下载量？点赞？）。
//   已知：带 `w` 的是「万」；两个广场是同一个指标（漏斗图标 path 逐字相同）。
//   ⭐ 但**从来没读过它的容器和来源** —— 只读了「渲染出来的文字」。
//   本步往上游追：
//   ① 那个数字的**祖先链**（class / data-* / 任何语义属性）——
//      ⭐ 特别是有没有 `data-*` 或 `aria-label`，那通常直接写着字段名；
//   ② ⭐⭐ **页面的内嵌数据**（Next.js RSC payload / `__NEXT_DATA__` / 预取状态）
//      里**有没有对应字段名**。这是「这个数字叫什么」最直接的证据 ——
//      DOM 只能给我显示值，数据层能给我**字段名**。
//   ⚠️ 安全：只**读**不写；RSC payload 可能很大，只按关键词取上下文片段。
//
// 遗留 2：分类标签各有多少条内容。
//   广场是无限滚动 ⇒ 「数卡片」数不出总数。
//   ⭐ 但可以**比较规模**：切分类时读 `scrollHeight` 与「持续滚动到不再增长」的总高。
//   本步：对 4 个分类各滚到底，量最终 `scrollHeight`，比较相对大小。
//   ⚠️ 诚实预告：`scrollHeight` 只反映**已渲染部分**（§187），
//   所以这个数**不能当「总数」**，只能当「至少有多少」的下界。命名要说准。
//
// 遗留 3：`z-[180]` / `z-[305]` 两层的触发条件（已排除 12 种状态）。
//   办法：⭐ **不预设它们是干什么的**，改成**在若干已知操作前后各枚举一次
//   固定层**，看这两层在哪个动作前后出现/消失。
//   ⭐ 判别用「全量枚举 + 元素差集」，**不靠名字猜**。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = {};

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
await page.waitForTimeout(1500);
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2800);
for (let i = 0; i < 3; i += 1) {
  const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(600);
}
const pk = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
  if (!b) return null; const r = b.getBoundingClientRect();
  return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
});
if (pk) { await page.mouse.click(pk[0], pk[1]); await page.waitForTimeout(1200); }

async function openTab(名字) {
  await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
  await page.waitForTimeout(2000);
  await page.evaluate((n) => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith(n))?.click(), 名字);
  await page.waitForTimeout(3500);
}

// ---------- 全量固定层枚举（不预设 z 范围，只看"固定 + 有面积"的顶层）----------
const layers = () => page.evaluate(() => {
  const res = [];
  const walk = (e, depth) => {
    const s = getComputedStyle(e);
    const r = e.getBoundingClientRect();
    if (s.position === 'fixed' && r.width > 0 && r.height > 0) {
      res.push({
        z: s.zIndex, depth, tag: e.tagName.toLowerCase(),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
        class: (e.className || '').toString().slice(0, 80),
      });
    }
    for (const c of e.children) walk(c, depth + 1);
  };
  walk(document.body, 0);
  return res;
});

// =============== 0 画布基线 ===============
LOG('══════════ 0 画布基线：固定层枚举 ══════════');
out.基线 = await layers();
LOG(`固定层 ${out.基线.length} 个`);
for (const l of out.基线) LOG(`  z=${String(l.z).padStart(4)} <${l.tag}> ${JSON.stringify(l.rect)} 「${l.文字}」 ${l.class}`);
out.基线z = [...new Set(out.基线.map((l) => l.z))];
LOG(`基线出现的 z 值: ${JSON.stringify(out.基线z)}`);
LOG(`⭐ z=180 在基线里吗: ${out.基线z.includes('180') ? '有' : '没有'}；z=305 呢: ${out.基线z.includes('305') ? '有' : '没有'}`);

// =============== A 卡面数字的容器与来源 ===============
LOG('\n══════════ A 卡面数字：容器 + 数据层字段名 ══════════');
await openTab('风格库');
out.数字 = await page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  // 找出所有「文字像数字」的可见叶子
  const nums = [...document.querySelectorAll('body *')].filter((e) => {
    if (e.tagName === 'SCRIPT' || e.tagName === 'STYLE') return false;
    if (e.children.length) return false;
    if (!vis(e)) return false;
    const t = (e.innerText || '').replace(/\s+/g, '').trim();
    return /^\d+(\.\d+)?w?$/.test(t);
  });
  const 样本 = nums.slice(0, 6).map((e) => {
    const 链 = [];
    for (let p = e, i = 0; p && i < 7; p = p.parentElement, i += 1) {
      const r = p.getBoundingClientRect();
      const ds = {}; for (const a of p.attributes) if (a.name.startsWith('data-')) ds[a.name] = a.value;
      链.push({ tag: p.tagName.toLowerCase(), 文字: (p.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 30), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], aria: p.getAttribute('aria-label'), title: p.getAttribute('title'), data: ds, class: (p.className || '').toString().slice(0, 60) });
    }
    return { 数字: (e.innerText || '').trim(), 链 };
  });
  return { 数字元素数: nums.length, 全部数字: nums.map((e) => (e.innerText || '').trim()).slice(0, 40), 样本 };
});
LOG(`可见「纯数字」元素 ${out.数字.数字元素数} 个`);
LOG(`前 40 个: ${JSON.stringify(out.数字.全部数字)}`);
if (out.数字.样本.length) {
  LOG('\n⭐ 第一处数字的祖先链:');
  for (const c of out.数字.样本[0].链) LOG(`  <${c.tag}> ${JSON.stringify(c.rect)} aria=${c.aria} title=${c.title} data=${JSON.stringify(c.data)} 「${c.文字}」 ${c.class}`);
}

// ⭐⭐ 数据层：RSC payload / __NEXT_DATA__ 里找字段名
out.数据层 = await page.evaluate(() => {
  const 关键词 = ['downloadCount', 'useCount', 'usageCount', 'likeCount', 'favoriteCount', 'viewCount', 'clickCount', 'hotCount', 'sortCount', 'score', 'popularity', 'trend'];
  const 命中 = {};
  const texts = [];
  // ① __NEXT_DATA__
  const nd = document.getElementById('__NEXT_DATA__');
  if (nd) texts.push(['__NEXT_DATA__', nd.textContent || '']);
  // ② RSC 流（script 里的 push）
  for (const s of document.querySelectorAll('script')) {
    const t = s.textContent || '';
    if (t && t.length > 200) texts.push(['script', t]);
  }
  for (const [来源, t] of texts) {
    for (const k of 关键词) {
      if (t.includes(k)) {
        const i = t.indexOf(k);
        命中[k] = 命中[k] || [];
        if (命中[k].length < 3) 命中[k].push({ 来源, 片段: t.slice(Math.max(0, i - 60), i + 90).replace(/\s+/g, ' ') });
      }
    }
  }
  return { 扫过的文本源: texts.map(([a, b]) => `${a}(${b.length}字)`), 命中 };
});
LOG(`\n数据层文本源: ${JSON.stringify(out.数据层.扫过的文本源)}`);
LOG(`⭐ 关键词命中: ${JSON.stringify(Object.keys(out.数据层.命中))}`);
for (const [k, v] of Object.entries(out.数据层.命中)) {
  for (const h of v) LOG(`  ${k} @${h.来源}: …${h.片段}…`);
}
if (!Object.keys(out.数据层.命中).length) LOG('  ⛔ 一个都没命中');

// =============== B 分类规模（滚到底的最终高度 = 下界）===============
LOG('\n══════════ B 各分类滚到底的最终高度（下界）══════════');
out.分类 = [];
for (const 名 of ['推荐', '摄影写真', '电商营销', '动漫游戏', '风格插画', '平面设计']) {
  const ok = await page.evaluate((n) => {
    const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === n);
    if (!b) return false; b.click(); return true;
  }, 名);
  if (!ok) { LOG(`  ⛔ 找不到「${名}」`); continue; }
  await page.waitForTimeout(2500);
  // 反复滚到底，直到 scrollHeight 不再增长（最多 6 轮）
  let 末 = 0; let 轮 = 0; let 卡总数 = 0;
  for (let i = 0; i < 6; i += 1) {
    const h = await page.evaluate(() => {
      const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600);
      if (!v) return 0;
      v.scrollTop = v.scrollHeight;
      return v.scrollHeight;
    });
    await page.waitForTimeout(2200);
    轮 += 1;
    if (h === 末 && i > 0) break;
    末 = h;
  }
  卡总数 = await page.evaluate(() => document.querySelectorAll('button[aria-label="详情"]').length);
  out.分类.push({ 分类: 名, 最终scrollH: 末, 滚了轮数: 轮, DOM详情按钮总数: 卡总数 });
  LOG(`  【${名}】滚 ${轮} 轮，最终 scrollH=${末}，DOM 里详情按钮累计 ${卡总数}`);
}
const 最大 = Math.max(...out.分类.map((c) => c.最终scrollH));
LOG(`\n⭐ 相对大小（以最大者为 100）：${out.分类.map((c) => `${c.分类} ${Math.round((c.最终scrollH / 最大) * 100)}`).join(' / ')}`);
LOG(`⚠️ 这是**下界**（无限滚动只渲染一部分），不是内容总数`);

// =============== C z180 / z305 触发条件：逐动作差集 ===============
LOG('\n══════════ C z180 / z305：逐动作差集 ══════════');
const 步骤 = [
  { 名: '关掉广场(ESC)', fn: async () => { await page.keyboard.press('Escape'); await page.waitForTimeout(1500); } },
  { 名: '开节点下拉菜单', fn: async () => { await page.mouse.click(20, 400); await page.waitForTimeout(800); await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); }); await page.waitForTimeout(1500); } },
  { 名: '选中一个节点', fn: async () => { await page.keyboard.press('Escape'); await page.waitForTimeout(1200); await page.evaluate(() => { const n = document.querySelector('.react-flow__node[data-id="i-9nlG6HdjK2"]'); if (n) n.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: n.getBoundingClientRect().x + 40, clientY: n.getBoundingClientRect().y + 20 })); }); await page.waitForTimeout(2000); } },
  { 名: '点节点⤢(大编辑器)', fn: async () => { await page.evaluate(() => { const n = document.querySelector('.react-flow__node[data-id="i-9nlG6HdjK2"]'); if (!n) return; const b = [...n.querySelectorAll('button')].find((x) => { const r = x.getBoundingClientRect(); return Math.abs(r.width - 28) < 2 && r.y < n.getBoundingClientRect().y + 60; }); if (b) b.click(); }); await page.waitForTimeout(2000); } },
];
out.z轨迹 = [];
for (const s of 步骤) {
  try { await s.fn(); } catch (e) { LOG(`  ${s.名} 执行异常: ${String(e).slice(0, 80)}`); }
  const l = await layers();
  const zs = [...new Set(l.map((x) => x.z))];
  const 新 = zs.filter((z) => !out.基线z.includes(z));
  out.z轨迹.push({ 步骤: s.名, z值: zs, 相对基线新增: 新, 有180: zs.includes('180'), 有305: zs.includes('305') });
  LOG(`  ${s.名}: 固定层 ${l.length} 个，z 值 ${JSON.stringify(zs)}，新增 ${JSON.stringify(新)}，180=${zs.includes('180')} 305=${zs.includes('305')}`);
}
const 见180 = out.z轨迹.filter((x) => x.有180).map((x) => x.步骤);
const 见305 = out.z轨迹.filter((x) => x.有305).map((x) => x.步骤);
LOG(`\n⭐ 见过 z=180 的步骤: ${JSON.stringify(见180)}`);
LOG(`⭐ 见过 z=305 的步骤: ${JSON.stringify(见305)}`);

await writeFile(new URL('./batchDG0.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDG0.json ===');
await browser.close();
