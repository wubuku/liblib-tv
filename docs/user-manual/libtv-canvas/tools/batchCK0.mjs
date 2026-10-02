// Batch CK-0：⭐⭐⭐ 风格广场「点一下卡片本体」的后果 —— 特效广场已实测，风格广场一直空着。
//
// 手册现状（asset-library.md）：
//   · 特效广场点卡片 ⇒ 实测「立刻变成画布上一个节点」，`m-` 前缀，名字 `素材·特效·小蜜蜂运镜`，
//     并已原样删回；
//   · 风格广场点卡片 ⇒ **「不猜」**，正文写着没验。
//   · `⤢ 详情` 是只读浮层（已验），`收藏` 切收藏态（已验）—— 三者后果完全不同。
//
// 本步照抄特效广场那次的读法（节点数、抽屉行、时间序列采样、toast、落点），
// 并且**只删本轮自己造出来的那个节点**，收尾按 id 逐个复核。
//
// ⭐ 三条纪律：
//   ① 认人只用**本轮 diff 出来的新 `data-id`**，绝不按名字/位置/顺序；
//   ② 点卡片前先算出**独占点**，避开卡面上那两枚悬停才显形的按钮（`收藏` / `⤢ 详情`）
//      和左上角的模型徽标 —— 点到它们就不是「点卡片」了；
//   ③ 单点采样不足以定性（手册里已经吃过一次亏），所以点完**每 400ms 采一次、共 8 次**。
// ⛔ 不点生成、不派发任务、不动收藏态。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

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
// 抽屉开着会盖住，先收
{
  const d = page.locator('.mantine-Drawer-inner').first().locator('button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 6000 }).catch(() => {});
  await page.waitForTimeout(1500);
}

// ── 基线：节点 id 集合 ─────────────────────────────────────────
const nodeIds = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2600);
out.基线id = await nodeIds();
console.log('基线节点 =', JSON.stringify(out.基线id));

// ── 打开 素材库 → 风格库 ───────────────────────────────────────
console.log('\n════ 打开素材库 ════');
await page.locator('button[aria-label="素材库"]').first().click({ timeout: 8000 }).catch((e) => console.log('素材库按钮失败', e.message));
await page.waitForTimeout(2000);
out.素材库面板 = await page.evaluate(() => {
  const p = [...document.querySelectorAll('*')].find((e) => (e.innerText || '').includes('风格库') && (e.innerText || '').includes('特效库') && e.getBoundingClientRect().width < 900);
  return p ? { 文字: (p.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120), rect: (() => { const r = p.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() } : null;
});
console.log('素材库面板 =', JSON.stringify(out.素材库面板));
const lb = page.locator('text=风格库').first();
if (await lb.count()) { await lb.click({ timeout: 8000 }).catch(() => {}); await page.waitForTimeout(2200); }
out.标签行 = await page.evaluate(() => [...document.querySelectorAll('button,[role="button"]')].map((b) => ({ t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14), aria: b.getAttribute('aria-label') })).filter((x) => x.t || x.aria).slice(0, 24));
console.log('可见按钮 =', JSON.stringify(out.标签行));

// ── 读出前若干张卡：名字、作者、徽标，并找一张**确定的**卡 ──────
out.卡片 = await page.evaluate(() => {
  const rows = [];
  // 卡片根 = 含 `aria-label="详情"` 按钮的最近祖先容器
  for (const b of document.querySelectorAll('button[aria-label="详情"]')) {
    let card = b;
    for (let i = 0; i < 6 && card.parentElement; i += 1) {
      card = card.parentElement;
      const r = card.getBoundingClientRect();
      if (r.width > 150 && r.width < 400 && r.height > 150) break;
    }
    const r = card.getBoundingClientRect();
    const btns = [...card.querySelectorAll('button')].map((x) => { const q = x.getBoundingClientRect(); return { aria: x.getAttribute('aria-label'), 文字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10), rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; });
    rows.push({ 卡片文字: (card.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 按钮: btns });
  }
  return rows;
});
console.log(`\n════ 视口内卡片 ${out.卡片.length} 张 ════`);
for (const c of out.卡片.slice(0, 4)) console.log(`  ${JSON.stringify(c.rect)}  ${c.卡片文字}`);

if (!out.卡片.length) { console.log('视口内没有卡片 ⇒ 没测到'); await writeFile(resolve(HERE, '.evidence/ck0-style-card.json'), JSON.stringify(out, null, 2)); await browser.close(); process.exit(0); }

// 目标：第一张卡，但点一个**既不在任何按钮上、也不在徽标上**的位置（图片区中下部）
const c0 = out.卡片[0];
out.目标 = { 文字: c0.卡片文字, rect: c0.rect, 按钮: c0.按钮 };
const inBtn = (x, y) => c0.按钮.some((b) => x >= b.rect[0] - 4 && x <= b.rect[0] + b.rect[2] + 4 && y >= b.rect[1] - 4 && y <= b.rect[1] + b.rect[3] + 4);
let pt = null;
for (const fy of [0.45, 0.55, 0.35, 0.65, 0.25, 0.75]) {
  for (const fx of [0.5, 0.35, 0.65, 0.2, 0.8]) {
    const x = c0.rect[0] + c0.rect[2] * fx, y = c0.rect[1] + c0.rect[3] * fy;
    if (!inBtn(x, y)) { pt = [Math.round(x), Math.round(y)]; break; }
  }
  if (pt) break;
}
out.目标.点击点 = pt;
console.log('\n目标卡 =', JSON.stringify(c0.卡片文字), ' 点 =', JSON.stringify(pt));
if (!pt) { console.log('⛔ 找不到不压按钮的点 ⇒ 没测到'); await writeFile(resolve(HERE, '.evidence/ck0-style-card.json'), JSON.stringify(out, null, 2)); await browser.close(); process.exit(0); }

await page.mouse.move(pt[0], pt[1]);
await page.waitForTimeout(900);

// ── 点卡片本体，然后**时间序列采样** ────────────────────────────
console.log('\n════ 点卡片之后（每 400ms 采一次，共 8 次）════');
await page.mouse.click(pt[0], pt[1]);
out.采样 = [];
for (let i = 0; i < 8; i += 1) {
  await page.waitForTimeout(400);
  const s = await page.evaluate(() => ({
    节点id: [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')),
    广场还开着: (document.body.innerText || '').includes('风格广场'),
    toast: [...document.querySelectorAll('[class*="Toast"],[role="status"]')].map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24)).filter(Boolean).slice(0, 3),
    顶层浮层: [...document.querySelectorAll('[class*="Drawer"],[class*="Modal"],[class*="Popover"]')].filter((e) => e.getBoundingClientRect().width > 0).map((e) => (e.className || '').toString().slice(0, 28)),
  }));
  const 新增 = s.节点id.filter((x) => !out.基线id.includes(x));
  const 少了 = out.基线id.filter((x) => !s.节点id.includes(x));
  out.采样.push({ 次数: i + 1, 节点数: s.节点id.length, 新增, 少了, 广场还开着: s.广场还开着, toast: s.toast, 浮层: s.顶层浮层 });
  console.log(`  #${i + 1} 节点数=${s.节点id.length} 新增=${JSON.stringify(新增)} 少了=${JSON.stringify(少了)} 广场=${s.广场还开着} toast=${JSON.stringify(s.toast)}`);
}

out.新节点id = [...new Set(out.采样.flatMap((s) => s.新增))];
console.log('\n本轮新增的 id =', JSON.stringify(out.新节点id));

if (!out.新节点id.length) {
  console.log('⛔ 没有新增节点 ⇒ 「点风格卡片会加节点」不成立（阴性读数）');
} else {
  const NID = out.新节点id[0];
  out.新节点id_采用 = NID;
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2200);
  out.新节点读数 = await page.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!n) return { 在视口: false };
    const r = n.getBoundingClientRect();
    const t = n.querySelector('input');
    return { 在视口: true, class: (n.className || '').toString().slice(0, 60), 文字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60), 输入框值: t ? t.value : null, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }, NID);
  console.log('新节点 =', JSON.stringify(out.新节点读数));

  // 抽屉里的行名
  await page.locator('button[aria-label="资产管理"]').first().click({ timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(1800);
  out.抽屉共几节点 = await page.evaluate(() => {
    const m = (document.body.innerText || '').match(/共\s*(\d+)\s*节点/);
    return m ? Number(m[1]) : null;
  });
  out.抽屉行 = await page.evaluate(() => [...document.querySelectorAll('button')].map((b) => (b.innerText || '').replace(/\s+/g, ' ').trim()).filter((t) => t && t.includes('素材')).slice(0, 6));
  console.log('抽屉共几节点 =', out.抽屉共几节点, ' 含「素材」的行 =', JSON.stringify(out.抽屉行));

  // 复原读数：新节点拍一张（clip 只框它自己，先算好）
  if (out.新节点读数.在视口) {
    const r = out.新节点读数.rect;
    const clip = { x: Math.max(0, r[0] - 30), y: Math.max(0, r[1] - 30), width: r[2] + 60, height: r[3] + 60 };
    await page.mouse.click(20, 480);
    await page.waitForTimeout(900);
    await shot(page, 'M-331-风格卡片-点一下就进了画布.png', { clip });
    console.log('已拍 M-331');
  }
}

await writeFile(resolve(HERE, '.evidence/ck0-style-card.json'), JSON.stringify(out, null, 2));
console.log('\n（本步尚未删除新节点，下一步做）');
await browser.close();
