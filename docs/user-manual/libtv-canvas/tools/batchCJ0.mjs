// Batch CJ-0：`⤢` 把参数卡片收起之后，**到底哪几条路能把它叫回来**。
//
// CG 批坐实了 `⤢` 是「收起/展开整张参数卡片」，收起用不回来、
// 24 秒不自动恢复、鼠标移开移回都不恢复，只坐实了「刷新能恢复」。
// ⇒ 对用户来说这条是**死的**：收起了就只能刷新。
//
// 本步要把「恢复路径」穷举出来，**每条都用元素差集判**（不看照片 —— CG 就是栽在
// 「眼睛看的是另一个同名节点」上）。候选按「代价从小到大」排：
//   ① 重新点一下节点本体        ② 点节点标题      ③ 双击节点
//   ④ 切到故事板再切回工作流    ⑤ `⌘0` 适合屏幕   ⑥ 刷新页面（已知可行，作阳性对照）
//
// ⭐ 判据（吸取 CG 教训）：
//   - 只认**本轮自己折的那个 `data-id`**，绝不按位置/顺序/名字认；
//   - 硬前置：折之前先断言目标节点**在视口内且处于选中态**（`.react-flow__node`
//     只渲染视口内节点，折的可能是屏幕外那个）；
//   - 每条路之后都量**该节点自己的后代可见元素数** + 参数卡容器尺寸，
//     收起态和展开态的数字必须能区分（先量基线确认有分辨力，再开跑）。
//
// ⛔ 折卡片不扣积分、不落盘（CG 已验），本轮仍不碰生成、不碰「取消」。
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

// ── 认节点：按 data-id 锁定，列出候选供我挑一个参数卡最全的 ──────
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2600);

const list = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), 选中: n.classList.contains('selected'), 文字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}));
console.log('════ 视口内节点 ════');
for (const n of list) console.log(`  ${n.id.padEnd(18)} ${n.选中 ? '[选中]' : '       '} ${JSON.stringify(n.rect)}  ${n.文字}`);
out.节点清单 = list;

// 目标：画面左上、离原点最近的视频节点（CG 折过的那类）
const target = list.find((n) => n.id === 'v-v2hlWY4Br3') || list.find((n) => n.文字.startsWith('视频节点'));
if (!target) { console.log('没挑到目标节点，输出只能是「没测到」'); await browser.close(); process.exit(0); }
const TID = target.id;
console.log(`\n本轮目标节点 = ${TID}（${target.文字}）`);

// ── 量节点自身状态的函数：元素差集 + 参数卡尺寸 ──────────────────
const state = () => page.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!n) return { 在: false };
  const vis = [...n.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const card = [...n.querySelectorAll('*')].map((e) => e.getBoundingClientRect())
    .filter((r) => r.width > 200 && r.height > 80)
    .sort((a, b) => (b.width * b.height) - (a.width * a.height))[0];
  const r = n.getBoundingClientRect();
  return {
    在: true, 选中: n.classList.contains('selected'),
    可见后代数: vis.length,
    节点尺寸: [Math.round(r.width), Math.round(r.height)],
    最大浮层: card ? [Math.round(card.width), Math.round(card.height)] : null,
    有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'),
    有生成按钮: vis.filter((e) => e.tagName === 'BUTTON').length,
    文字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
  };
}, TID);

// 硬前置：必须先选中，且参数卡是展开态（CG 教训：折叠态没有选中态也无妨，但要看清）
const box = await page.locator(`.react-flow__node[data-id="${TID}"]`).boundingBox();
await page.mouse.click(box.x + box.width / 2, box.y + box.height - 12);
await page.waitForTimeout(1400);
out.基线_选中后 = await state();
console.log('\n基线（选中后）=', JSON.stringify(out.基线_选中后));
if (!out.基线_选中后.在) { console.log('目标节点不在，输出只能是「没测到」'); await browser.close(); process.exit(0); }

// ── 找到那枚 `⤢` 并折起来 ───────────────────────────────────────
const foldInfo = await page.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  const btn = n.querySelector('button[class*="absolute"][class*="right-2"][class*="top-2"]') ||
    [...n.querySelectorAll('button')].find((b) => b.className.toString().includes('size-7') && b.className.toString().includes('absolute'));
  if (!btn) return { 找到: false, 节点里所有button: [...n.querySelectorAll('button')].map((b) => b.className.toString().slice(0, 46)) };
  const r = btn.getBoundingClientRect();
  return { 找到: true, cls: btn.className.toString(), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}, TID);
console.log('⤢ =', JSON.stringify(foldInfo));
if (!foldInfo.找到) { console.log('没找到 ⤢，输出只能是「没测到」'); await browser.close(); process.exit(0); }

await page.mouse.click(foldInfo.rect[0] + 14, foldInfo.rect[1] + 14);
await page.waitForTimeout(1500);
out.折叠后 = await state();
console.log('折叠后 =', JSON.stringify(out.折叠后));

// ⭐ 先确认判据有分辨力：折叠态与展开态必须读得出差别，否则后面全是空转
const 可分辨 = out.基线_选中后.可见后代数 !== out.折叠后.可见后代数;
console.log(`判据分辨力 = ${可分辨}（展开 ${out.基线_选中后.可见后代数} vs 折叠 ${out.折叠后.可见后代数}）`);
if (!可分辨) { console.log('判据无分辨力，本步结论只能是「没测到」'); await browser.close(); process.exit(0); }

// ── 逐条试恢复路径 ───────────────────────────────────────────────
const 恢复 = async (name, act) => {
  const before = await state();
  await act();
  await page.waitForTimeout(1600);
  const after = await state();
  const 恢复了吗 = after.在 && after.可见后代数 > before.可见后代数;
  console.log(`  ${恢复了吗 ? '✅' : '⛔'} ${name.padEnd(22)} ${before.可见后代数} → ${after.可见后代数}  最大浮层=${JSON.stringify(after.最大浮层)}`);
  return { 路径: name, 恢复了: 恢复了吗, 前: before, 后: after };
};

out.恢复路径 = [];
out.恢复路径.push(await 恢复('① 重新点一下节点', async () => {
  const b = await page.locator(`.react-flow__node[data-id="${TID}"]`).boundingBox();
  await page.mouse.click(b.x + b.width / 2, b.y + b.height - 12);
}));

out.恢复路径.push(await 恢复('② 点节点标题', async () => {
  const t = await page.locator(`.react-flow__node[data-id="${TID}"] >> text=视频节点 3`).first().boundingBox().catch(() => null);
  const b = await page.locator(`.react-flow__node[data-id="${TID}"]`).boundingBox();
  await page.mouse.click(t ? t.x + 8 : b.x + 40, t ? t.y + 8 : b.y + 8);
}));

out.恢复路径.push(await 恢复('③ 双击节点', async () => {
  const b = await page.locator(`.react-flow__node[data-id="${TID}"]`).boundingBox();
  await page.mouse.dblclick(b.x + b.width / 2, b.y + b.height - 12);
}));

out.恢复路径.push(await 恢复('④ 切故事板再切回', async () => {
  await page.locator('[aria-label="故事板"]').first().click({ timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(1800);
  await page.locator('[aria-label="工作流"]').first().click({ timeout: 8000 }).catch(() => {});
}));

out.恢复路径.push(await 恢复('⑤ ⌘0 适合屏幕', async () => {
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
}));

out.恢复路径.push(await 恢复('⑥ 刷新页面（阳性对照）', async () => {
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6500);
  await closePromos(page);
  await page.waitForTimeout(1500);
}));

// ── 收尾复原：不折了就算复原成功，但要用**独立读数**确认 ─────────
out.收尾 = await state();
console.log('\n收尾状态 =', JSON.stringify(out.收尾));
const 全部展开 = !out.恢复路径.some((r) => r.恢复了) ? null : out.收尾.可见后代数;
console.log('是否有路径能恢复 =', out.恢复路径.some((r) => r.恢复了));
if (out.收尾.在 && out.收尾.有提示词框) console.log('✅ 收尾：参数卡在（已复原）');
else console.log('⚠️ 收尾：参数卡不在，需要下一轮处理');

await writeFile(resolve(HERE, '.evidence/cj0-fold-recovery.json'), JSON.stringify(out, null, 2));
console.log('\n（本步不扣积分、不落盘、未点生成）');
await browser.close();
