// Batch DI-1：诊断「视口内 0 张卡」—— 先弄清楚是**回收**还是**判据错**。
//
// DI-0 的症状：每个分类滚完回到顶部，`collect()` 一张卡都收不到（视口内 0）。
// ⭐ 关键线索：6 个未收敛分类的 `最终scrollH` **全部等于 17016**（一模一样），
//   唯一收敛的「风格插画」是 4462。
//   ⇒ 强烈怀疑：**17016 是虚拟滚动的总高**（内容真实长度），
//     而 collect() 收不到卡是因为**窗口外的卡被虚拟滚动卸载了**。
//
// 三问：
//   ① 回到顶部后，DOM 里到底还有几张 `button[aria-label="详情"]`？它们的 rect 在哪？
//   ② 那个「整张卡」判据（宽 150~260 且 **高 > 245**）还成立吗？
//      —— DG-3 量到真卡是 191×302，但那是**旧一屏**；现在卡的尺寸可能变了。
//      ⭐ 把**所有候选祖先的尺寸**打出来，让判据自己显形。
//   ③ 滚到中段（不是顶也不是底）时，能不能收到卡？
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

// ---------- 诊断函数 ----------
const diag = (标签) => page.evaluate((tag) => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis);
  if (!modals.length) return { 标签: tag, 有广场: false };
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  const v = [...root.querySelectorAll('.mantine-ScrollArea-viewport')][0];
  const D = [...root.querySelectorAll('button[aria-label="详情"]')];
  // ⭐ 前 3 枚详情按钮的**每一层祖先尺寸**
  const 样本 = D.slice(0, 3).map((d) => {
    const 层 = [];
    for (let p = d, i = 0; p && i < 9; p = p.parentElement, i += 1) {
      const r = p.getBoundingClientRect();
      层.push({ i, tag: p.tagName.toLowerCase(), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 可见: vis(p), class: (p.className || '').toString().slice(0, 44) });
      if (r.width > 1400) break;
    }
    return 层;
  });
  return {
    标签: tag,
    scrollTop: v ? Math.round(v.scrollTop) : null,
    scrollH: v ? v.scrollHeight : null,
    clientH: v ? v.clientHeight : null,
    DOM里详情按钮: D.length,
    其中可见: D.filter(vis).length,
    可见按钮的y范围: D.filter(vis).map((d) => Math.round(d.getBoundingClientRect().y)).sort((a, b) => a - b).slice(0, 8),
    祖先样本: 样本,
  };
}, 标签);

out.顶部 = await diag('刚进分类（顶部）');
LOG('══════════ 顶部 ══════════');
LOG(`scrollTop=${out.顶部.scrollTop} scrollH=${out.顶部.scrollH} clientH=${out.顶部.clientH}`);
LOG(`DOM 里详情按钮 ${out.顶部.DOM里详情按钮} 枚，其中可见 ${out.顶部.其中可见} 枚`);
LOG(`可见按钮的 y: ${JSON.stringify(out.顶部.可见按钮的y范围)}`);
LOG('\n⭐ 前 3 枚详情按钮的祖先尺寸（看哪一层才是「整张卡」）:');
for (const [i, 层] of (out.顶部.祖先样本 || []).entries()) {
  LOG(`  按钮#${i}:`);
  for (const c of 层) LOG(`     [${c.i}] <${c.tag}> ${JSON.stringify(c.rect)} vis=${c.可见} ${c.class}`);
}

// 滚到中段
await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = Math.floor(v.scrollHeight / 2); });
await page.waitForTimeout(2800);
out.中段 = await diag('中段');
LOG('\n══════════ 中段 ══════════');
LOG(`scrollTop=${out.中段.scrollTop} scrollH=${out.中段.scrollH}`);
LOG(`DOM 里详情按钮 ${out.中段.DOM里详情按钮} 枚，其中可见 ${out.中段.其中可见} 枚`);
LOG(`可见按钮的 y: ${JSON.stringify(out.中段.可见按钮的y范围)}`);
LOG('\n祖先尺寸（按钮#0）:');
for (const c of (out.中段.祖先样本?.[0] || [])) LOG(`   [${c.i}] <${c.tag}> ${JSON.stringify(c.rect)} vis=${c.可见} ${c.class}`);

// 滚到底
await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = v.scrollHeight; });
await page.waitForTimeout(2800);
out.底部 = await diag('底部');
LOG('\n══════════ 底部 ══════════');
LOG(`scrollTop=${out.底部.scrollTop} scrollH=${out.底部.scrollH}`);
LOG(`DOM 里详情按钮 ${out.底部.DOM里详情按钮} 枚，其中可见 ${out.底部.其中可见} 枚`);
LOG(`可见按钮的 y: ${JSON.stringify(out.底部.可见按钮的y范围)}`);

await writeFile(new URL('./batchDI1.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDI1.json ===');
await browser.close();
