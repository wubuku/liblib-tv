// Batch DB-5：给那枚无文字角标定名 —— hover 气泡 + 点击后果（隔离测）。
//
// DB-4 已把它从「模型徽标」里分离出来：30 张卡里 **24 张徽标、5 张角标、1 张空**。
// 角标读数：`24×24` <button>、class `flex size-6 items-center justify-center rounded-lg bg-[rgba(…`、
//   内含 1 个 svg、path 以 `M2 0a2 2 0 1 1 0 4 2 2 0 0 1 0-4m7 0a2 2…` 开头（三个闪烁的小圆点），
//   ⭐ **无文字、无 aria、无 title、无任何 data-***。
//
// 本步两问：
//   ① **hover 说不说话？** —— 手册读者只能靠气泡知道它是什么。
//   ② **点下去发生什么？** —— ⚠️⚠️ 安全顾虑：它左上角常驻、**不靠 hover 显形**，
//      万一点下去是「建节点」就会在画布上留垃圾。
//      ⇒ 铁律：**点之前先存基线**（画布节点数 + 全部 data-id 列表），
//      点完逐项比对，**只删本轮自己新增的**（id 不在基线 + m- 前缀 + 名字以「素材-」开头）。
//      广场是只读的，预期是「什么都不会发生」—— 但**预期不是读数**。
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
await page.waitForTimeout(3500);

// 定位第一枚角标（无文字、含 svg 的 24×24 button）
const target = await page.evaluate(() => {
  const D = [...document.querySelectorAll('button[aria-label="详情"]')];
  for (let i = 0; i < D.length; i += 1) {
    let card = null;
    for (let p = D[i].parentElement, j = 0; p && j < 8; p = p.parentElement, j += 1) {
      const r = p.getBoundingClientRect();
      if (r.width > 150 && r.height > 150) { card = p; break; }
    }
    if (!card) continue;
    const cr = card.getBoundingClientRect();
    const b = [...card.querySelectorAll('button')].find((x) => {
      const r = x.getBoundingClientRect();
      return r.x >= cr.x - 2 && r.x <= cr.x + 60 && r.y >= cr.y - 2 && r.y <= cr.y + 60
        && !(x.innerText || '').trim() && x.querySelectorAll('svg').length === 1;
    });
    if (!b) continue;
    const r = b.getBoundingClientRect();
    if (r.y > 810 - 20) continue; // 要在视口内
    return { 卡序: i, 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }
  return null;
});
LOG(`角标目标: ${JSON.stringify(target)}`);

if (target) {
  // ---------- ① hover 气泡 ----------
  LOG('\n══════════ ① hover 说不说话 ══════════');
  const before = await page.evaluate(() => [...document.querySelectorAll('[role="tooltip"],.mantine-Tooltip-tooltip,[class*="ooltip"]')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0; }).map((e) => (e.innerText || '').trim()));
  LOG(`hover 前已有 tooltip: ${JSON.stringify(before)}`);
  await page.mouse.move(target.中心[0], target.中心[1]);
  await page.waitForTimeout(1500);
  await page.mouse.move(target.中心[0] + 1, target.中心[1]);
  await page.waitForTimeout(1000);
  out.气泡 = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
    const t = [...document.querySelectorAll('body *')].filter((e) => e.tagName !== 'SCRIPT' && (e.getAttribute('role') === 'tooltip' || /tooltip/i.test(e.className || '')) && vis(e));
    return {
      tooltip元素: t.length,
      tooltip文字: t.map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean),
      tooltip位置: t.map((e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; }),
    };
  });
  LOG(`⭐ hover 后 tooltip 元素=${out.气泡.tooltip元素} 文字=${JSON.stringify(out.气泡.tooltip文字)} 位置=${JSON.stringify(out.气泡.tooltip位置)}`);
  await shot(page, 'DB-d-hover角标.png', { clip: { x: Math.max(0, target.rect[0] - 160), y: Math.max(0, target.rect[1] - 90), width: 420, height: 300 } });
  LOG('📸 DB-d');

  // ---------- ② 点击后果（隔离测）----------
  LOG('\n══════════ ② 点它会发生什么（先存基线）══════════');
  const base = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node[data-id]')].map((n) => ({ id: n.getAttribute('data-id'), 名: (n.innerText || '').split('\n')[0].trim().slice(0, 20) })));
  LOG(`基线: ${base.length} 个节点 → ${JSON.stringify(base.map((b) => b.id))}`);
  out.基线 = base;

  await page.mouse.move(20, 400);
  await page.waitForTimeout(400);
  await page.mouse.click(target.中心[0], target.中心[1]);
  await page.waitForTimeout(2500);

  out.点后 = await page.evaluate(() => {
    const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
    return {
      节点: [...document.querySelectorAll('.react-flow__node[data-id]')].map((n) => ({ id: n.getAttribute('data-id'), 名: (n.innerText || '').split('\n')[0].trim().slice(0, 20) })),
      广场还在: [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis).length,
      详情浮层: [...document.querySelectorAll('*')].filter((e) => e.children.length === 0 && vis(e) && /风格详情/.test(e.innerText || '')).length,
      顶部toast: [...document.querySelectorAll('body *')].filter((e) => e.tagName !== 'SCRIPT' && e.children.length === 0 && vis(e) && (e.innerText || '').trim().length < 40 && (e.innerText || '').trim().length > 2)
        .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter((t) => /成功|失败|不支持|请|暂|提示|新建|已/.test(t)).slice(0, 8),
      可见英文aria: [...document.querySelectorAll('[aria-label]')].filter(vis).map((e) => e.getAttribute('aria-label')).filter((a) => a && /^[a-z-]+$/.test(a)),
    };
  });
  const 新增 = out.点后.节点.filter((n) => !base.some((b) => b.id === n.id));
  const 消失 = base.filter((b) => !out.点后.节点.some((n) => n.id === b.id));
  LOG(`⭐ 点后节点数=${out.点后.节点.length} 新增=${JSON.stringify(新增)} 消失=${JSON.stringify(消失.map((x) => x.id))}`);
  LOG(`   广场还在=${out.点后.广场还在} 详情浮层=${out.点后['详情浮层']} 英文aria=${JSON.stringify(out.点后.可见英文aria)}`);
  LOG(`   可能的 toast: ${JSON.stringify(out.点后.顶部toast)}`);
  await shot(page, 'DB-e-点角标之后.png');
  LOG('📸 DB-e');

  // ⭐ 清理：只删本轮自己新增的
  if (新增.length) {
    for (const n of 新增) {
      const ok = !base.some((b) => b.id === n.id) && /^m-/.test(n.id) && /^素材-/.test(n.名);
      LOG(`   ${ok ? '✅ 符合清理条件' : '⛔ 不符合清理条件，不动'}：${n.id} 「${n.名}」`);
    }
  } else LOG('   ⭐ 没有新增节点 ⇒ 不需要清理');
}

await writeFile(new URL('./batchDB5.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDB5.json ===');
await browser.close();
