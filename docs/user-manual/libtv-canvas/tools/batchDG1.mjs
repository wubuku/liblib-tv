// Batch DG-1：修两处判据，把「卡面数字」这件事钉死。
//
// DG-0 的两个读数都**不能用**：
//
// ① 「数据层命中 `viewCount` / `hotCount`」
//    ⛔ 那两个片段的上下文是 **i18n 文案表**（「剧本生成预计耗时 1-3 分钟」
//    「ScriptV2 批量生视频仅支持…」），是**界面提示文案**，不是卡面数字的数据字段。
//    ⇒ **命中一个键名不等于命中了那个值**；必须证明它和卡面数字同源。
//    本步：⭐ 换一个更硬的办法 —— **在 RSC 数据里同时搜「键名」和「卡面上读到的那个具体数值」**，
//    看它们**是否出现在同一段 JSON 里**。同段才算证据。
//
// ② 「卡面数字的祖先链」
//    ⛔ 文档顺序第一个「纯数字」元素是**顶栏的「20」积分**，不是卡面数字。
//    ⇒ 找卡面数字必须**按几何**（在广场卡片区域内、且带漏斗图标）。
//
// ③ 顺带把 B 的读数也修了：6 个分类滚到底 scrollH 几乎一样（12622 / 12936）
//    ⇒ 「滚到底」其实**没滚到底**（无限滚动会继续加载），
//    所以这批数**只能当下界**，连相对大小都不能比。这条要如实写进正文。
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

await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(4000);

// ---------- A 按几何找「带漏斗图标的数字」 ----------
out.卡面数字 = await page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis);
  if (!modals.length) return { 找到: false };
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  // 漏斗图标 = 那个纸飞机 path；先把含该 path 的元素找出来当"锚"
  const 漏斗 = [...root.querySelectorAll('svg, path, div')].filter((e) => {
    const p = e.querySelector?.('path') || (e.tagName.toLowerCase() === 'path' ? e : null);
    return p && (p.getAttribute('d') || '').length > 10;
  });
  // ⭐ 逐张卡：在卡片内找「纯数字」叶子，且它左边 40px 内有一个 svg/path
  const 样本 = [];
  for (const D of root.querySelectorAll('button[aria-label="详情"]')) {
    let card = null;
    for (let p = D.parentElement, j = 0; p && j < 8; p = p.parentElement, j += 1) { const r = p.getBoundingClientRect(); if (r.width > 150 && r.height > 150) { card = p; break; } }
    if (!card) continue;
    const cr = card.getBoundingClientRect();
    if (cr.y < 0 || cr.y > 780) continue;
    for (const e of card.querySelectorAll('*')) {
      if (e.children.length) continue;
      if (!vis(e)) continue;
      const t = (e.innerText || '').replace(/\s+/g, '').trim();
      if (!/^\d+(\.\d+)?w?$/.test(t)) continue;
      const r = e.getBoundingClientRect();
      // ⭐ 左边 40px 内必须有 svg（漏斗）
      const hasIcon = [...card.querySelectorAll('svg, path')].some((s) => {
        const q = s.getBoundingClientRect();
        return q.x < r.x && q.x > r.x - 40 && Math.abs(q.y + q.height / 2 - (r.y + r.height / 2)) < 14;
      });
      if (!hasIcon) continue;
      const 链 = [];
      for (let p = e, i = 0; p && i < 6; p = p.parentElement, i += 1) {
        const q = p.getBoundingClientRect();
        const ds = {}; for (const a of p.attributes) if (a.name.startsWith('data-')) ds[a.name] = a.value;
        链.push({ tag: p.tagName.toLowerCase(), 文字: (p.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 30), rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)], aria: p.getAttribute('aria-label'), title: p.getAttribute('title'), data: ds, class: (p.className || '').toString().slice(0, 60) });
      }
      样本.push({ 数字: t, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 链 });
      break;
    }
  }
  return { 找到: true, 样本数: 样本.length, 数字列表: 样本.map((s) => s.数字), 样本: 样本.slice(0, 3) };
});
LOG(`带漏斗图标的数字 ${out.卡面数字.样本数} 个`);
LOG(`读到的值: ${JSON.stringify(out.卡面数字.数字列表)}`);
if (out.卡面数字.样本.length) {
  LOG('\n⭐ 完整祖先链（按几何取到的真·卡面数字）:');
  for (const c of out.卡面数字.样本[0].链) LOG(`  <${c.tag}> ${JSON.stringify(c.rect)} aria=${c.aria} title=${c.title} data=${JSON.stringify(c.data)} 「${c.文字}」 ${c.class}`);
  LOG(`\n⭐ 逐个 data-* 检查: ${JSON.stringify(out.卡面数字.样本[0].链.map((c) => c.data).filter((d) => Object.keys(d).length))}`);
}

// ---------- B 数据层：键名 + 具体数值 必须同段出现 ----------
out.数据层 = await page.evaluate((vals) => {
  const 候选键 = ['viewCount', 'hotCount', 'useCount', 'usageCount', 'downloadCount', 'likeCount', 'favoriteCount', 'clickCount', 'popularity', 'score', 'collectionCount', 'applyCount'];
  const 源 = [];
  const nd = document.getElementById('__NEXT_DATA__');
  if (nd) 源.push(['__NEXT_DATA__', nd.textContent || '']);
  for (const s of document.querySelectorAll('script')) { const t = s.textContent || ''; if (t && t.length > 500) 源.push(['script', t]); }
  const 结果 = [];
  for (const [来源, t] of 源) {
    for (const k of 候选键) {
      let i = t.indexOf(k);
      while (i !== -1) {
        // ⭐ 同一段（±1500 字符）里有没有我们读到的具体数值
        const 段 = t.slice(Math.max(0, i - 1500), i + 1500);
        const 命中的值 = vals.filter((v) => {
          const 裸 = v.replace(/w$/, '');
          return 段.includes(`"${v}"`) || 段.includes(`:${v}`) || 段.includes(`:${v},`) || 段.includes(v);
        });
        if (命中的值.length) {
          // 进一步：值与键的距离
          const v = 命中的值[0]; const 裸 = v.replace(/w$/, '');
          const vi = 段.search(new RegExp(`[:"]${裸.replace(/\./g, '\\.')}[",}]`));
          结果.push({ 来源, 键: k, 同段值: 命中的值, 键到值距离: vi === -1 ? null : vi, 片段: 段.slice(Math.max(0, i - 80), i + 120).replace(/\s+/g, ' ') });
        }
        i = t.indexOf(k, i + 1);
      }
    }
  }
  return { 源: 源.map(([a, b]) => `${a}(${b.length}字)`), 找到: 结果.length, 结果: 结果.slice(0, 8) };
}, out.卡面数字.数字列表 || []);
LOG(`\n数据层文本源: ${JSON.stringify(out.数据层.源)}`);
LOG(`⭐「键名与具体数值同段出现」的结果: ${out.数据层.找到} 条`);
for (const r of out.数据层.结果) LOG(`  键 ${r.键} 同段值 ${JSON.stringify(r.同段值)} 距离 ${r.键到值距离}\n     …${r.片段}…`);
if (!out.数据层.找到) LOG('  ⛔ 没有任何字段名和卡面数值同段 ⇒ 拿不到字段名，这条只能继续标未验');

// ---------- C 悬停那个数字：有没有气泡（复跑一次，带阳性对照）----------
LOG('\n══════════ C 悬停数字出不出气泡（带阳性对照）══════════');
if (out.卡面数字.样本.length) {
  const p = out.卡面数字.样本[0].rect;
  // 阳性对照：先悬停一张卡的模型徽标（已知会出气泡）
  const 徽标位 = await page.evaluate(() => {
    const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
    for (const D of document.querySelectorAll('button[aria-label="详情"]')) {
      let card = null;
      for (let q = D.parentElement, j = 0; q && j < 8; q = q.parentElement, j += 1) { const r = q.getBoundingClientRect(); if (r.width > 150 && r.height > 150) { card = q; break; } }
      if (!card) continue;
      const cr = card.getBoundingClientRect();
      if (cr.y < 0 || cr.y > 700) continue;
      for (const b of card.querySelectorAll('button')) {
        const r = b.getBoundingClientRect();
        if (Math.abs(r.x - (cr.x + 9)) <= 3 && Math.abs(r.y - (cr.y + 9)) <= 3 && (b.innerText || '').trim()) {
          return [Math.round(r.x + 12), Math.round(r.y + 12), (b.innerText || '').trim()];
        }
      }
    }
    return null;
  });
  const readTip = async (pt) => {
    await page.mouse.move(5, 400); await page.waitForTimeout(500);
    await page.mouse.move(pt[0], pt[1]); await page.waitForTimeout(1300);
    return page.evaluate(() => {
      const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
      const t = [...document.querySelectorAll('body *')].filter((e) => e.tagName !== 'SCRIPT' && e.tagName !== 'STYLE'
        && (e.getAttribute('role') === 'tooltip' || /tooltip/i.test(e.className || '')) && vis(e));
      return { 数: t.length, 文字: t.map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean) };
    });
  };
  if (徽标位) {
    const r1 = await readTip([徽标位[0], 徽标位[1]]);
    LOG(`⭐ 阳性对照 悬停模型徽标「${徽标位[2]}」→ tooltip ${r1.数} 个 ${JSON.stringify(r1.文字)}`);
    out.徽标气泡 = r1;
  } else LOG('  ⛔ 视口内找不到带文字的徽标卡 ⇒ 阳性对照不成立，本条结果不能用');
  const r2 = await readTip([p[0] + p[2] / 2, p[1] + p[3] / 2]);
  LOG(`⭐ 悬停卡面数字「${out.卡面数字.样本[0].数字}」→ tooltip ${r2.数} 个 ${JSON.stringify(r2.文字)}`);
  out.数字气泡 = r2;
  await shot(page, 'DG-a-悬停卡面数字.png', { clip: { x: Math.max(0, p[0] - 200), y: Math.max(0, p[1] - 80), width: 420, height: 260 } });
  LOG('📸 DG-a');
}

await writeFile(new URL('./batchDG1.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDG1.json ===');
await browser.close();
