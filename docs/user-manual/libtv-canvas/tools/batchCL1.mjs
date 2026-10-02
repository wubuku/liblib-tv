// Batch CL-1：补三件事。
//
// ⛔ 先认 CL-0 的一处自伤：③「找排序入口」用的判据是
//    「按钮里有 svg path 或文字含 ▾」⇒ **顶栏每一枚图标按钮都命中**，
//    候选里混进了 `画布 2` / `工作流` / `故事板` / `发布与分享` / `积分超市`，
//    我照着候选逐个点了一遍 —— **误点了「发布与分享」和「积分超市」**。
//    没有发布、没有充值（两枚都只是打开面板），**积分全程 `20 → 20`**，
//    但这仍然是自己制造的越界，记在这里，不当没发生过。
//    ⭐ 教训：**判据放宽到「页面上所有按钮」时，候选里必然混进不该点的东西**；
//    要么把范围锁死在**目标面板内部**，要么就只读不点。
//
// 本步：
//   ① 补上徽标那一枪的**落点验证**（`elementFromPoint`），把「点了没反应」
//      从「可能没点到」升级成「确实点到了、确实没反应」；
//   ② **只读**地清点广场面板内部的全部控件，回答「真正的排序入口到底有没有」；
//   ③ 测详情浮层里那枚 `使用`（盯积分；建了节点就按本轮新 `data-id` 删掉）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];

const { browser, page } = await launch();
const out = {};
await open(page, URL_);
await closePromos(page);
await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.reload({ waitUntil: 'domcontentloaded' });
await page.waitForTimeout(6000);
await closePromos(page);
await page.waitForTimeout(1500);
for (let i = 0; i < 3; i += 1) {
  const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(700);
}
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2600);
await page.locator('button[aria-label="工作流"]').first().click({ timeout: 8000 }).catch(() => {});   // 确认在工作流模式
await page.waitForTimeout(1500);

const snap = () => page.evaluate(() => ({
  节点id: [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')),
  积分: (() => { const t = (document.body.innerText || '').match(/\n(\d{1,4})\n/); return t ? Number(t[1]) : null; })(),
  广场: (document.body.innerText || '').includes('风格广场'),
  详情: (document.body.innerText || '').includes('风格详情'),
}));
out.基线 = await snap();
console.log('基线 = 节点', out.基线.节点id.length, ' 积分', out.基线.积分);

await page.locator('button[aria-label="素材库"]').first().click({ timeout: 8000 }).catch(() => {});
await page.waitForTimeout(2000);
const lb = page.locator('text=风格库').first();
if (await lb.count()) { await lb.click({ timeout: 8000 }).catch(() => {}); await page.waitForTimeout(2200); }

// ── ① 徽标落点验证 ─────────────────────────────────────────────
console.log('\n════ ① 模型徽标：落点验证 + 复点 ════');
out.徽标 = await page.evaluate(() => {
  const rows = [];
  for (const b of document.querySelectorAll('button[aria-label="详情"]')) {
    let card = b;
    for (let i = 0; i < 6 && card.parentElement; i += 1) { card = card.parentElement; const r = card.getBoundingClientRect(); if (r.width > 150 && r.width < 400 && r.height > 150) break; }
    rows.push(card);
  }
  for (const card of rows) {
    const badge = [...card.querySelectorAll('button')].find((x) => { const q = x.getBoundingClientRect(); return q.width > 0 && q.width <= 30 && !x.getAttribute('aria-label'); });
    if (!badge) continue;
    const r = badge.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const el = document.elementFromPoint(cx, cy);
    return {
      徽标文字: (badge.innerText || '').replace(/\s+/g, ' ').trim(),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      落点是不是徽标本身: el === badge || badge.contains(el),
      落点元素: el ? `${el.tagName.toLowerCase()}.${(el.className || '').toString().slice(0, 30)}` : null,
      cursor: getComputedStyle(badge).cursor,
      卡片文字: (card.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
    };
  }
  return null;
});
console.log('徽标 =', JSON.stringify(out.徽标));
if (out.徽标 && out.徽标.落点是不是徽标本身) {
  const b0 = await snap();
  await page.mouse.move(out.徽标.rect[0] + 12, out.徽标.rect[1] + 12);
  await page.waitForTimeout(900);
  await page.mouse.click(out.徽标.rect[0] + 12, out.徽标.rect[1] + 12);
  const seq = [];
  for (let i = 0; i < 6; i += 1) { await page.waitForTimeout(400); const s = await snap(); seq.push({ i: i + 1, 节点数: s.节点id.length, 新增: s.节点id.filter((x) => !b0.节点id.includes(x)), 积分: s.积分, 广场: s.广场, 详情: s.详情 }); }
  for (const r of seq) console.log(`  #${r.i} 节点=${r.节点数} 新增=${JSON.stringify(r.新增)} 积分=${r.积分} 广场=${r.广场} 详情=${r.详情}`);
  out.徽标复点 = seq;
}

// ── ② 只读清点广场面板内部的全部控件 ───────────────────────────
console.log('\n════ ② 广场面板内部控件（只读）════');
out.面板控件 = await page.evaluate(() => {
  // 面板根 = 含「风格广场」文字、且宽度 < 1000 的最近容器
  let panel = null;
  for (const e of document.querySelectorAll('div')) {
    const t = (e.innerText || '');
    if (t.includes('风格广场') && t.includes('仅看可商用') && e.getBoundingClientRect().width < 1000 && e.getBoundingClientRect().width > 200) { panel = e; break; }
  }
  if (!panel) return null;
  const pr = panel.getBoundingClientRect();
  const ctrls = [...panel.querySelectorAll('button,[role="button"],[role="checkbox"],[role="combobox"],input')].map((b) => {
    const r = b.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return null;
    return { tag: b.tagName.toLowerCase(), 文字: (b.innerText || b.getAttribute('placeholder') || '').replace(/\s+/g, ' ').trim().slice(0, 18), aria: b.getAttribute('aria-label'), role: b.getAttribute('role'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }).filter(Boolean);
  return { 面板rect: [Math.round(pr.x), Math.round(pr.y), Math.round(pr.width), Math.round(pr.height)], 控件数: ctrls.length, 控件: ctrls };
});
if (out.面板控件) {
  console.log('  面板 =', JSON.stringify(out.面板控件.面板rect), ' 控件数 =', out.面板控件.控件数);
  const 去重 = [];
  for (const c of out.面板控件.控件) { const k = `${c.文字}|${c.aria}|${c.role}`; if (!去重.some((x) => x.k === k)) 去重.push({ k, ...c }); }
  for (const c of 去重) console.log(`   ${c.tag} 「${c.文字}」 aria=${c.aria} role=${c.role} @${JSON.stringify(c.rect)}`);
  out.面板控件去重 = 去重.map(({ k, ...r }) => r);
} else console.log('  ⛔ 没定位到面板容器');

// ── ③ 详情浮层里的 `使用` ──────────────────────────────────────
console.log('\n════ ③ 详情浮层里的「使用」════');
const det = page.locator('button[aria-label="详情"]').first();
if (await det.count()) {
  await det.hover().catch(() => {});
  await page.waitForTimeout(700);
  await det.click({ timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(1600);
  out.详情面板 = await page.evaluate(() => {
    const p = [...document.querySelectorAll('*')].find((e) => (e.innerText || '').includes('风格详情') && (e.innerText || '').includes('首选推荐模型') && e.getBoundingClientRect().width > 200);
    if (!p) return null;
    const r = p.getBoundingClientRect();
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 全文: (p.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160), 按钮: [...p.querySelectorAll('button')].map((b) => { const q = b.getBoundingClientRect(); return { 文字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10), aria: b.getAttribute('aria-label'), rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; }).filter((x) => x.rect[2] > 0) };
  });
  console.log('  详情面板 =', JSON.stringify(out.详情面板, null, 1)?.slice(0, 900));

  const use = out.详情面板 && out.详情面板.按钮.find((b) => b.文字 === '使用');
  if (use) {
    const b0 = await snap();
    console.log(`  点「使用」前：节点 ${b0.节点id.length} 积分 ${b0.积分}`);
    await page.mouse.move(use.rect[0] + use.rect[2] / 2, use.rect[1] + use.rect[3] / 2);
    await page.waitForTimeout(700);
    await page.mouse.click(use.rect[0] + use.rect[2] / 2, use.rect[1] + use.rect[3] / 2);
    const seq = [];
    for (let i = 0; i < 8; i += 1) { await page.waitForTimeout(400); const s = await snap(); seq.push({ i: i + 1, 节点数: s.节点id.length, 新增: s.节点id.filter((x) => !b0.节点id.includes(x)), 积分: s.积分, 广场: s.广场, 详情: s.详情 }); }
    for (const r of seq) console.log(`  #${r.i} 节点=${r.节点数} 新增=${JSON.stringify(r.新增)} 积分=${r.积分} 广场=${r.广场} 详情=${r.详情}`);
    out.使用 = { 前: b0, 采样: seq, 新增: [...new Set(seq.flatMap((r) => r.新增))] };
    console.log('  「使用」结论 = 节点', b0.节点id.length, '→', seq.at(-1).节点数, ' 新增', JSON.stringify(out.使用.新增), ' 积分', b0.积分, '→', seq.at(-1).积分);
  } else console.log('  ⛔ 详情面板里没找到「使用」按钮');
} else console.log('  ⛔ 视口内没有详情按钮');

await writeFile(resolve(HERE, '.evidence/cl1-badge-sort-use.json'), JSON.stringify(out, null, 2));
console.log('\n（未发布、未充值、未提交生成）');
await browser.close();
