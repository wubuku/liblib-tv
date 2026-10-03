// Batch CP-0：收 CI 留下的两个 📖 —— `z-[180]` 那个空层，和「跟随」横幅到底什么时候才显示。
//
// 两层的 class 几乎一样（`pointer-events-none fixed inset-0 … motion-safe:transition-opacity
// motion-safe:duration-200`，只差 z-index），像是**同一个组件的两种状态**：
//   z-[180]  [0,0,1440,810]  opacity 0  直接子元素 = 0
//   z-[305]  [633,0,174,34]  opacity 0  内含 `正在跟随 取消ESC 按 ESC 退出`
//
// ⭐ 本步的假设：**`z-[180]` 是画布「框选」时用的选区高亮层** ——
//    因为它铺满视口、平时全透明、一有交互就该亮起来。
// ⛔ 只做**不写盘**的交互：在空白处拖拽画选区、`Space`+拖、中键拖、抓手工具+拖。
//    **不拖节点**（那会改布局、写盘）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];

const boot = async (page) => {
  await open(page, URL_);
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2600);
  for (let i = 0; i < 3; i += 1) {
    const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
    if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(600);
  }
};
const killPromo = async (page) => {
  const b = await page.evaluate(() => {
    const t = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
    if (!t) return null; const r = t.getBoundingClientRect(); return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
  });
  if (!b) return false;
  await page.mouse.click(b[0], b[1]); await page.waitForTimeout(1200); return true;
};

// ⭐ 累计 opacity：沿祖先链连乘（CI 立下的规矩 —— opacity 不继承，只量自己会读出假的 1）
const layers = (page) => page.evaluate(() => {
  const 累计 = (el) => {
    let p = 1, a = el;
    while (a) { p *= parseFloat(getComputedStyle(a).opacity); a = a.parentElement; }
    return Math.round(p * 1000) / 1000;
  };
  const out = [];
  for (const e of document.body.children) {
    const s = getComputedStyle(e); const r = e.getBoundingClientRect();
    const cls = (e.className || '').toString();
    if (!/z-\[180\]|z-\[305\]/.test(cls)) continue;
    out.push({
      z: s.zIndex, 自己opacity: s.opacity, 累计opacity: 累计(e), pe: s.pointerEvents,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      子元素数: e.children.length, 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
      描边: getComputedStyle(e).outline, 背景: getComputedStyle(e).backgroundColor,
    });
  }
  return out;
});
// 全局搜有没有任何元素带「选区/框选」语义
const selectionHints = (page) => page.evaluate(() => {
  const 命中 = [];
  for (const e of document.querySelectorAll('body *')) {
    const c = (e.className || '').toString();
    const id = e.id || '';
    const da = e.getAttribute('data-*') || '';
    if (/selection|marquee|rubber|lasso|drag-box|select-box/i.test(`${c} ${id} ${da}`)) {
      const s = getComputedStyle(e); const r = e.getBoundingClientRect();
      命中.push({ tag: e.tagName.toLowerCase(), cls: c.slice(0, 70), z: s.zIndex, op: s.opacity, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
    }
  }
  return 命中.slice(0, 12);
});
// 画布上「没有任何节点」的空白点
const blankSpot = (page) => page.evaluate(() => {
  for (let y = 120; y < 740; y += 20) {
    for (let x = 60; x < 1380; x += 20) {
      const el = document.elementFromPoint(x, y);
      if (!el) continue;
      if (el.closest('.react-flow__node, .node-floating-ui, button, a, input, textarea')) continue;
      if (el.closest('.mantine-Drawer-root, .react-flow__pane, .react-flow__renderer')) return [x, y];
    }
  }
  return null;
});
const nodeRects = (page) => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}));
const viewBefore = (page) => page.evaluate(() => getComputedStyle(document.querySelector('.react-flow__viewport')).transform);

const out = { 动作: [] };
const { browser, page } = await launch();
await boot(page);
out.促销 = await killPromo(page);

const 记 = async (名) => { const l = await layers(page); out.动作.push({ 名, 层: l }); console.log(`  ${名.padEnd(26)} ${l.map((x) => `z${x.z} 累计${x.累计opacity} 子${x.子元素数} ${JSON.stringify(x.rect)}`).join(' | ')}`); };

console.log('=== 基线 ===');
await 记('开屏（未交互）');
out.选区语义命中 = await selectionHints(page);
console.log('  selection/marquee 类名命中：', JSON.stringify(out.选区语义命中));
const B = await blankSpot(page);
console.log('  空白点 =', JSON.stringify(B));
out.空白点 = B;

// ① 空白处左键拖拽（画选区）—— 重点假设
if (B) {
  const before = await nodeRects(page);
  const v0 = await viewBefore(page);
  await page.mouse.move(B[0], B[1]);
  await page.waitForTimeout(300);
  await page.mouse.down();
  await page.waitForTimeout(350);
  await 记('左键按下（还没动）');
  await page.mouse.move(B[0] + 180, B[1] + 120, { steps: 12 });
  await page.waitForTimeout(450);
  await 记('拖到 (180,120) 处');
  await page.mouse.up();
  await page.waitForTimeout(700);
  await 记('松手后');
  const after = await nodeRects(page);
  const v1 = await viewBefore(page);
  out.拖拽 = {
    节点有无移动: JSON.stringify(before) !== JSON.stringify(after),
    视口有无平移: v0 !== v1, 视口前: v0, 视口后: v1,
  };
  console.log(`  ⇒ 节点移动=${out.拖拽.节点有无移动} 视口平移=${out.拖拽.视口平移}`);
  if (out.拖拽.节点有无移动) console.log(`    ⚠️ 前：${JSON.stringify(before.slice(0, 3))}\n    ⚠️ 后：${JSON.stringify(after.slice(0, 3))}`);
}

// ② Space + 拖（平移）
{
  const b2 = await blankSpot(page);
  if (b2) {
    const v0 = await viewBefore(page);
    await page.keyboard.down('Space');
    await page.waitForTimeout(250);
    await page.mouse.move(b2[0], b2[1]);
    await page.mouse.down();
    await page.mouse.move(b2[0] + 150, b2[1] + 90, { steps: 10 });
    await page.waitForTimeout(400);
    await 记('Space+拖 途中');
    await page.mouse.up();
    await page.keyboard.up('Space');
    await page.waitForTimeout(600);
    const v1 = await viewBefore(page);
    out.Space拖 = { 视口平移: v0 !== v1 };
    await 记('Space+拖 松手后');
    console.log(`  ⇒ 视口平移=${out.Space拖.视口平移}`);
    await page.evaluate(() => document.body.focus());
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(2200);
  }
}

// ③ 中键拖
{
  const b3 = await blankSpot(page);
  if (b3) {
    const v0 = await viewBefore(page);
    await page.mouse.move(b3[0], b3[1]);
    await page.mouse.down({ button: 'middle' });
    await page.mouse.move(b3[0] + 120, b3[1] + 80, { steps: 10 });
    await page.waitForTimeout(400);
    await 记('中键拖 途中');
    await page.mouse.up({ button: 'middle' });
    await page.waitForTimeout(600);
    out.中键拖 = { 视口平移: (await viewBefore(page)) !== v0 };
    await page.evaluate(() => document.body.focus());
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(2200);
  }
}

// ④ 切到故事板视图，看跟随横幅亮不亮
{
  await 记('切故事板前');
  const sb = page.locator('button[aria-label="故事板"]').first();
  if (await sb.count()) {
    await sb.click({ timeout: 6000 }).catch(() => {});
    await page.waitForTimeout(2200);
    await 记('切到故事板');
    const wf = page.locator('button[aria-label="工作流"]').first();
    if (await wf.count()) { await wf.click({ timeout: 6000 }).catch(() => {}); await page.waitForTimeout(2000); await 记('切回工作流'); }
  } else console.log('  ⛔ 找不到 aria-label=故事板 的按钮');
}

// ⑤ 打开几个已知面板，看有没有能让它亮起来的
for (const [名, sel] of [['资产管理', 'text=资产管理'], ['TV Director 抽屉', '.mantine-Drawer-inner button[aria-label="打开"]']]) {
  const l = page.locator(sel).first();
  if (!(await l.count())) { console.log(`  ⛔ ${名} 没找到入口`); continue; }
  await l.click({ timeout: 6000 }).catch(() => {});
  await page.waitForTimeout(1800);
  await 记(`打开「${名}」后`);
}

// ⑥ 静置 60s，看它会不会自己亮
await page.mouse.move(720, 400);
console.log('\n  静置 60s …');
for (const t of [15, 30, 45, 60]) {
  await page.waitForTimeout(15000);
  const l = await layers(page);
  const hot = l.filter((x) => x.累计opacity > 0.001);
  console.log(`    ${t}s: 累计 opacity>0 的层 ${hot.length} 枚 ${JSON.stringify(hot.map((x) => [x.z, x.累计opacity]))}`);
  if (hot.length) { out.静置发亮 = { 秒: t, 层: hot }; break; }
}
await 记('静置 60s 后');

out.收尾节点 = await nodeRects(page);
console.log('\n收尾节点数 =', out.收尾节点.length, ' 与基线逐项一致 =', out.收尾节点.length === BASE.length && BASE.every((x) => out.收尾节点.some((n) => n.id === x)));
await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const ids = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.全新会话 = { 节点: ids, 与基线一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)), 层: await layers(p2) };
  console.log('全新会话 节点', ids.length, ' 一致 =', out.全新会话.与基线一致, ' 层 =', JSON.stringify(out.全新会话.层.map((x) => [x.z, x.累计opacity])));
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cp0-layers.json'), JSON.stringify(out, null, 2));
