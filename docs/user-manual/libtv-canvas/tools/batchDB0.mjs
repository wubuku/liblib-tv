// Batch DB-0：收两个不需要授权就能验的遗留。
//
// 遗留 1：广场那层 `close`（40×40，与 minimize 同一排）点下去会怎样？
//   CZ 已经坐实 minimize 是「缩成小窗 + 还能 maximize 还原」。
//   ⭐ 同一排的 close **至今没点过** —— 而「关掉整个风格库」是影响很大的动作，
//   要么它会关、要么它有二次确认、要么它什么都不做。**三种结果对读者意义完全不同。**
//   ⚠️ 顾虑：点它可能**把广场整个关掉**。但广场本来就是只读面板、
//   重开一次的成本就是点两下，**不写盘、不扣积分** ⇒ 可以放心点。
//   ⭐ 必须做**前后对照**：点之前先量「广场在不在 + 画布节点数」，
//   点之后再量同一组 —— 只看「关没关」会漏掉「关掉的同时画布也变了」。
//
// 遗留 2：广场卡面那枚 114×27「新功能：支持真人」标记挂在哪个按钮上？
//   PROGRESS 记着它在视频节点顶部工具排上也出现过一枚**逐字相同**的。
//   ⭐⭐ 按本会话铁律：**不能靠文字认身份**（同名同符号≠同一功能）。
//   治法：把该标记的**祖先链整条打出来**（含 rect / class / data-*），
//   看它**物理上挂在谁里面** —— 祖先链是结构事实，不受文案撞车影响。
//   顺带读它的兄弟节点，确认它是不是某个按钮的**子元素**（那就是「按钮上的角标」）。
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

// ---------------- 打开风格广场 ----------------
async function openPlaza() {
  await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
  await page.waitForTimeout(1800);
  await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
  await page.waitForTimeout(3000);
}
await openPlaza();

const snap = () => page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const 广场容器 = [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis).map((e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; });
  const dr = document.querySelector('.mantine-Drawer-inner');
  return {
    画布节点数: document.querySelectorAll('.react-flow__node[data-id]').length,
    广场容器,
    广场详情按钮: [...document.querySelectorAll('button[aria-label="详情"]')].filter(vis).length,
    收藏星: [...document.querySelectorAll('button[aria-label="收藏"],button[aria-label="取消收藏"]')].filter(vis).length,
    资产抽屉在: vis(dr),
    minimize: [...document.querySelectorAll('button[aria-label="minimize"]')].filter(vis).length,
    maximize: [...document.querySelectorAll('button[aria-label="maximize"]')].filter(vis).length,
    close: [...document.querySelectorAll('button[aria-label="close"]')].filter(vis).length,
    可见英文aria: [...document.querySelectorAll('[aria-label]')].filter(vis).map((e) => e.getAttribute('aria-label')).filter((a) => a && /^[a-z-]+$/.test(a)),
  };
});

// =============== 1：「新功能：支持真人」标记的归属 ===============
LOG('══════════ 1：「新功能：支持真人」标记归属 ══════════');
// ⭐ 阳性对照：广场到底开没开、卡片在不在。
// 没有这一步，「标记命中 0」和「广场没加载出来」读数一模一样。
out.对照 = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const 详情 = [...document.querySelectorAll('button[aria-label="详情"]')].filter(vis);
  return {
    广场容器数: [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis).length,
    广场容器rect: [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis).map((e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; }),
    可见详情按钮: 详情.length,
    scrollH: [...document.querySelectorAll('.mantine-ScrollArea-viewport')].filter(vis).map((e) => e.scrollHeight),
    // ⭐ 阳性对照的靶子：页面上**应该**能读到的文字
    对照文字: [...document.querySelectorAll('body *')].filter((e) => e.children.length === 0 && vis(e))
      .map((e) => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim())
      .filter((t) => t && t.length <= 24).slice(0, 60),
    含真人的任何文字: [...document.querySelectorAll('body *')].filter((e) => (e.textContent || '').includes('真人'))
      .map((e) => ({ tag: e.tagName.toLowerCase(), 文字: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 30), 可见: vis(e) })).slice(0, 12),
    含新功能的任何文字: [...document.querySelectorAll('body *')].filter((e) => (e.textContent || '').includes('新功能'))
      .map((e) => ({ tag: e.tagName.toLowerCase(), 文字: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 30), 可见: vis(e) })).slice(0, 12),
  };
});
LOG(`广场容器数=${out.对照.广场容器数} rect=${JSON.stringify(out.对照.广场容器rect)} 可见详情按钮=${out.对照.可见详情按钮} scrollH=${JSON.stringify(out.对照.scrollH)}`);
LOG(`含「真人」的元素: ${JSON.stringify(out.对照.含真人的任何文字, null, 1)}`);
LOG(`含「新功能」的元素: ${JSON.stringify(out.对照.含新功能的任何文字, null, 1)}`);
LOG(`对照文字(前40): ${JSON.stringify(out.对照.对照文字.slice(0, 40))}`);

// ⭐ 匹配放宽：原写法要求「叶子节点且文字逐字相等」，
// 一旦标记被包在 span 里、或前后带空格/图标，就永远命中 0。
out.标记 = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const hits = [];
  for (const e of document.querySelectorAll('body *')) {
    const t = (e.textContent || '').replace(/\s+/g, ' ').trim();
    if (t !== '新功能：支持真人') continue;
    // ⭐ 跳过祖先（textContent 会让外层也命中），只留「自己那一层」：
    // 判据 = 没有任何子元素也含这段文字
    const 有子含 = [...e.children].some((c) => (c.textContent || '').includes('支持真人'));
    if (有子含) continue;
    const r = e.getBoundingClientRect();
    const 链 = [];
    for (let p = e, i = 0; p && i < 9; p = p.parentElement, i += 1) {
      const b = p.getBoundingClientRect();
      const s = getComputedStyle(p);
      const ds = {};
      for (const a of p.attributes) if (a.name.startsWith('data-')) ds[a.name] = a.value;
      链.push({
        tag: p.tagName.toLowerCase(),
        文字: (p.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40),
        rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
        可见: vis(p),
        aria: p.getAttribute('aria-label'),
        pos: s.position, z: s.zIndex, overflow: s.overflow,
        data: ds,
        class: (p.className || '').toString().slice(0, 70),
      });
    }
    let btn = null;
    for (let p = e; p; p = p.parentElement) { if (p.tagName === 'BUTTON') { btn = p; break; } }
    hits.push({
      自身rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      自身可见: vis(e),
      祖先链: 链,
      最近button祖先: btn ? (() => { const b = btn.getBoundingClientRect(); return { 文字: (btn.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40), aria: btn.getAttribute('aria-label'), rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] }; })() : null,
      兄弟: e.parentElement ? [...e.parentElement.children].filter((c) => c !== e).map((c) => (c.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24)).filter(Boolean) : [],
    });
  }
  return { 命中数: hits.length, hits };
});
LOG(`命中数: ${out.标记.命中数}`);
for (const h of out.标记.hits ?? []) {
  LOG(`\n--- 一处命中 @${JSON.stringify(h.自身rect)} 可见=${h.自身可见}`);
  LOG(`  最近 button 祖先: ${h.最近button祖先 ? `「${h.最近button祖先.文字}」 aria=${h.最近button祖先.aria} @${JSON.stringify(h.最近button祖先.rect)}` : '⛔ 没有 button 祖先 ⇒ 不是角标，是独立标签'}`);
  LOG(`  兄弟元素文字: ${JSON.stringify(h.兄弟)}`);
  LOG(`  祖先链:`);
  for (const c of h.祖先链) LOG(`    <${c.tag}> ${JSON.stringify(c.rect)} vis=${c.可见} pos=${c.pos} z=${c.z} aria=${c.aria} data=${JSON.stringify(c.data)} 「${c.文字}」`);
}

// =============== 2：点 close 会怎样 ===============
LOG('\n══════════ 2：广场 close 点下去 ══════════');
out.close前 = await snap();
LOG(`点之前: ${JSON.stringify(out.close前, null, 1)}`);

const closeRect = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const b = [...document.querySelectorAll('button[aria-label="close"]')].find(vis);
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
});
LOG(`close 按钮 @${JSON.stringify(closeRect)}`);
if (closeRect) {
  await page.mouse.click(closeRect[0] + closeRect[2] / 2, closeRect[1] + closeRect[3] / 2);
  await page.waitForTimeout(2000);
  out.close后 = await snap();
  LOG(`\n⭐ 点之后: ${JSON.stringify(out.close后, null, 1)}`);
  LOG(`\n⭐ 差异:`);
  for (const k of Object.keys(out.close前)) {
    const a = JSON.stringify(out.close前[k]); const b = JSON.stringify(out.close后?.[k]);
    LOG(`   ${k}: ${a} → ${b} ${a === b ? '' : '  ⭐ 变了'}`);
  }
  // ⭐ 二次确认？
  out.close后可见文字 = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
    return [...document.querySelectorAll('body *')].filter((e) => e.children.length === 0 && vis(e))
      .map((e) => (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim())
      .filter((t) => t && t.length <= 20).slice(0, 40);
  });
  LOG(`\n点之后视口内可见文字(前40): ${JSON.stringify(out.close后可见文字)}`);
  await shot(page, 'DB-a-点广场close之后.png');
  LOG('📸 DB-a');
}

await writeFile(new URL('./batchDB0.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n已写 tools/batchDB0.json');
await browser.close();
