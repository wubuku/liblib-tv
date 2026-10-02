// Batch CI-3：横幅「在 DOM 里、有尺寸、opacity=1、visible，却画不出来」—— 差哪一层？
//
// CI-2 的硬读数（这一条是站得住的，因为采样器跑在所有页面脚本之前）：
//   · 元素在 **3925ms** 出现，此后 opacity 恒为 1、visibility 恒为 visible、宽恒为 64；
//   · 12 秒内**没有任何「不在」的记录**（采样器按状态去重，状态一变就会记一条）；
//   · 可 4108ms 拍下的裁图里，那个位置**是空的**。
//
// ⭐ 也就是说：不是 toast 淡出（那就该有 opacity 变 0 或元素被移除），
//    而是**有一个祖先把它整个藏起来了**。CI-0 只往上量了 4 层就停了 —— 差的就在 5 层以上。
//
// 本步三件事：
//   ① 量完整祖先链（到 <html> 为止），逐层算 **累计 opacity 乘积** 和 visibility 继承。
//   ② 算**绘制顺序**：把包含 (760,17) 的所有定位元素连同各自祖先的 z-index 排出来，
//      看谁压在上面 —— 顺便解释 M-323 当时为什么拍成了节点。
//   ③ 换状态再看它：故事板模式 / 工作流模式 / 收起 TV Director 抽屉之后，横幅画不画得出来。
//      （这三样都是**可逆的界面状态**，不写项目数据。）
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

// ── ① 完整祖先链：逐层算累计 opacity ─────────────────────────────
out.祖先链 = await page.evaluate(() => {
  const el = document.querySelector('[aria-label="退出跟随"]');
  if (!el) return { found: false };
  const rows = [];
  let acc = 1;
  for (let a = el; a; a = a.parentElement) {
    const cs = getComputedStyle(a);
    acc *= Number(cs.opacity);
    const r = a.getBoundingClientRect();
    rows.push({
      层: rows.length,
      tag: a.tagName.toLowerCase(),
      cls: (a.className || '').toString().slice(0, 78),
      opacity: cs.opacity,
      累计opacity: Math.round(acc * 1000) / 1000,
      visibility: cs.visibility,
      display: cs.display,
      position: cs.position,
      zIndex: cs.zIndex,
      overflow: cs.overflow,
      filter: cs.filter?.slice(0, 40) || 'none',
      backdropFilter: (cs.backdropFilter || cs.webkitBackdropFilter || 'none').slice(0, 40),
      transform: cs.transform === 'none' ? 'none' : cs.transform.slice(0, 40),
      clipPath: cs.clipPath === 'none' ? 'none' : cs.clipPath.slice(0, 40),
      尺寸: [Math.round(r.width), Math.round(r.height)],
    });
    if (a.tagName === 'HTML') break;
  }
  return { found: true, 总层数: rows.length, 层: rows };
});
console.log('════ 祖先链 ════');
for (const r of out.祖先链.层) {
  console.log(`  [${r.层}] ${r.tag}.${r.cls}`);
  console.log(`       opacity=${r.opacity} 累计=${r.累计opacity} vis=${r.visibility} disp=${r.display} pos=${r.position} z=${r.zIndex}`);
  console.log(`       overflow=${r.overflow} filter=${r.filter} backdrop=${r.backdropFilter} transform=${r.transform} clip=${r.clipPath} 尺寸=${JSON.stringify(r.尺寸)}`);
}

// ── ② 绘制顺序：谁压在 (760,17) 上面 ────────────────────────────
out.绘制顺序 = await page.evaluate(() => {
  const PX = 760, PY = 17;
  const rows = [];
  for (const a of document.querySelectorAll('*')) {
    const r = a.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    if (PX < r.x || PX > r.x + r.width || PY < r.y || PY > r.y + r.height) continue;
    const cs = getComputedStyle(a);
    if (cs.position === 'static' && cs.transform === 'none') continue;
    // 有效 z：自身 z-index 与祖先 z-index 逐层取最大（近似，只为排序看谁在上）
    let effZ = cs.zIndex === 'auto' ? 0 : Number(cs.zIndex);
    const chainZ = [effZ];
    for (let p = a.parentElement; p; p = p.parentElement) {
      const pz = getComputedStyle(p).zIndex;
      const v = pz === 'auto' ? 0 : Number(pz);
      chainZ.push(v);
      effZ = Math.max(effZ, v);
    }
    rows.push({
      tag: a.tagName.toLowerCase(),
      cls: (a.className || '').toString().slice(0, 52),
      pos: cs.position,
      z自身: cs.zIndex,
      有效z: effZ,
      opacity: cs.opacity,
      背景: cs.backgroundColor,
      尺寸: [Math.round(r.width), Math.round(r.height)],
      矩形: [Math.round(r.x), Math.round(r.y)],
    });
  }
  rows.sort((a, b) => b.有效z - a.有效z);
  return { 探测点: [PX, PY], 命中元素数: rows.length, 按z排序: rows.slice(0, 14) };
});
console.log('\n════ 绘制顺序（按有效 z 降序，前 14 个覆盖该点的元素）════');
for (const r of out.绘制顺序.按z排序) {
  console.log(`  z=${String(r.有效z).padStart(4)} (自身${r.pos}/z=${r.z自身}) op=${r.opacity} 背景=${r.背景} ${r.尺寸} @${r.矩形}  ${r.tag}.${r.cls}`);
}

// ── ③ 换状态看它画不画得出来 ────────────────────────────────────
const probe = () => page.evaluate(() => {
  const el = document.querySelector('[aria-label="退出跟随"]');
  if (!el) return { 有: false };
  let box = el;
  while (box.parentElement && !/border/.test(box.parentElement.className || '')) box = box.parentElement;
  let acc = 1;
  for (let a = box; a; a = a.parentElement) { acc *= Number(getComputedStyle(a).opacity); if (a.tagName === 'HTML') break; }
  const r = box.getBoundingClientRect();
  return {
    有: true, 累计opacity: Math.round(acc * 1000) / 1000,
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    抽屉在: !!document.querySelector('.mantine-Drawer-inner'),
    抽屉可见: [...document.querySelectorAll('.mantine-Drawer-inner')].some((d) => d.getBoundingClientRect().width > 0),
    模式: document.querySelector('[aria-label="故事板"]')?.getAttribute('aria-pressed') ?? null,
  };
});
const strip = async (tag) => {
  const st = await probe();
  const name = `M-326-${tag}.png`;
  if (st.有) await shot(page, name, { clip: { x: Math.max(0, st.rect[0] - 210), y: 0, width: 600, height: 100 } });
  console.log(`  ${tag}: ${JSON.stringify(st)}`);
  return st;
};

out.各状态 = {};
out.各状态.工作流抽屉开着 = await strip('工作流-抽屉开着');

await page.locator('[aria-label="故事板"]').first().click({ timeout: 8000 }).catch(() => {});
await page.waitForTimeout(2200);
out.各状态.故事板 = await strip('故事板模式');

await page.locator('[aria-label="工作流"]').first().click({ timeout: 8000 }).catch(() => {});
await page.waitForTimeout(2200);
out.各状态.回工作流 = await strip('回工作流');

// 收起 TV Director 抽屉（可逆的界面状态，不写项目数据）
await page.locator('.mantine-Drawer-inner').first().locator('button[aria-label="关闭"]').first().click({ timeout: 6000 }).catch((e) => console.log('收抽屉失败', e.message));
await page.waitForTimeout(1800);
out.各状态.抽屉收起 = await strip('抽屉收起');

await writeFile(resolve(HERE, '.evidence/ci3-paint-order.json'), JSON.stringify(out, null, 2));
console.log('\n（本步只读 + 只切视图/收抽屉，未点「取消」）');
await browser.close();
