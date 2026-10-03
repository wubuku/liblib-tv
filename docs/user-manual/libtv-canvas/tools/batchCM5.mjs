// Batch CM-5：CM-4 推翻了「⤢ 收起参数卡片」。现在盘清楚 ⤢ 打开的那个**大编辑器模态框**。
//
// CM-4 决定性读数：
//   点 ⤢ 之后，body 下**新出现**两枚固定层（展开态枚举里没有它们，阳性对照自带）：
//     z=600  `z-(--z-overlay) fixed inset-0 bg-black/50`              ← 压暗遮罩
//     z=601  `fixed left-1/2 top-1/2 z-[calc(var(--z-overlay)+1)]`   ← 居中对话框 [320,105,800×600]
//   关掉它 = 点遮罩；点框内关不掉。
//
// 本步：
//   ① 模态框的**完整控件清单**（只读，不点提交）—— 手册里可能压根没写过这个编辑器
//   ② ESC 能不能关？（最自然的关闭方式）
//   ③ 有没有标题栏 / 关闭按钮
//   ④ 音频节点的 ⤢ 是不是也弹模态
//   ⑤ 刷新页面后节点**还是不是选中态** —— 用来审 CJ 的「⛔ 刷新不管用」
//   ⑥ 老实拍一张模态态的图
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

const read = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { 在: false };
  const vis = [...n.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const fold = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
  const r = n.getBoundingClientRect();
  return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'), 折叠钮: fold ? [Math.round(fold.getBoundingClientRect().x), Math.round(fold.getBoundingClientRect().y)] : null, 节点rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}, id);

const layers = (page) => page.evaluate(() => [...document.body.children].map((e) => {
  const s = getComputedStyle(e); const r = e.getBoundingClientRect();
  return { tag: e.tagName.toLowerCase(), cls: (e.className || '').toString().slice(0, 72), z: s.zIndex, op: s.opacity, pe: s.pointerEvents, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 子元素数: e.children.length, 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) };
}));

const dialogState = (page) => page.evaluate(() => {
  const dlg = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  const ov = [...document.body.children].find((e) => (e.className || '').toString().includes('z-(--z-overlay)'));
  if (!dlg) return { 模态: false, 遮罩: !!ov };
  const r = dlg.getBoundingClientRect();
  return { 模态: true, 遮罩: !!ov, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 全文: (dlg.innerText || '').replace(/\s+/g, ' ').trim() };
});

// ⭐ 模态框内的完整控件清单 —— 只读，一个都不点
const controls = (page) => page.evaluate(() => {
  const dlg = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!dlg) return null;
  const box = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
  const path = (e) => { const p = e.querySelector('svg path'); return p ? (p.getAttribute('d') || '').slice(0, 26) : null; };
  const btns = [...dlg.querySelectorAll('button')].map((b) => ({ 类: (b.className || '').toString().slice(0, 40), 文字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), aria: b.getAttribute('aria-label'), 图标: path(b), rect: box(b), 禁用: b.disabled }));
  const areas = [...dlg.querySelectorAll('textarea,[contenteditable="true"],input')].map((t) => ({ tag: t.tagName.toLowerCase(), 占位: t.getAttribute('placeholder') || t.getAttribute('data-placeholder') || '', rect: box(t) }));
  return { 按钮数: btns.length, 按钮: btns, 输入区: areas };
});

const out = {};
const { browser, page } = await launch();
await boot(page);

// —— ① 视频节点：模态清单 + ESC + 截图 ——
const VID = 'v-oZNpH99MtM';
let sel = await read(page, VID);
console.log('视频节点 初始 =', JSON.stringify(sel));
// 选中
{
  const pts = await page.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    const q = n.getBoundingClientRect(); const a = [];
    for (const fy of [0.25, 0.4, 0.55, 0.7, 0.85]) for (const fx of [0.1, 0.25, 0.5, 0.75, 0.9]) {
      const x = q.x + q.width * fx, y = q.y + q.height * fy;
      const el = document.elementFromPoint(x, y);
      if (el && el.closest('.react-flow__node') === n && !el.closest('button,a')) a.push([Math.round(x), Math.round(y)]);
    }
    return a;
  }, VID);
  for (const p of pts) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1400); sel = await read(page, VID); if (sel.选中 && sel.折叠钮) break; }
}
console.log('视频节点 选中后 =', JSON.stringify(sel));
out.点前层 = await layers(page);

await page.mouse.click(sel.折叠钮[0] + 14, sel.折叠钮[1] + 14);
await page.waitForTimeout(1800);
out.点后层 = await layers(page);
out.点后 = await read(page, VID);
out.模态 = await dialogState(page);
console.log('点 ⤢ 后 =', JSON.stringify(out.点后), ' 模态 =', JSON.stringify(out.模态).slice(0, 160));
out.清单 = await controls(page);
console.log(`模态里 ${out.清单?.按钮数} 枚按钮 / ${out.清单?.输入区.length} 个输入区`);
for (const b of out.清单.按钮) console.log(`   按钮 ${JSON.stringify(b.rect)} 「${b.文字}」aria=${b.aria} 图标=${b.图标} 禁用=${b.禁用}`);
for (const a of out.清单.输入区) console.log(`   输入 ${JSON.stringify(a.rect)} ${a.tag} 占位「${a.占位}」`);

out.截图 = 'cm5-点⤢之后弹出的模态.png';
await page.screenshot({ path: resolve(HERE, '.evidence', out.截图) });
out.拍完仍开着 = (await dialogState(page)).模态;
console.log('拍完模态仍开着 =', out.拍完仍开着);

// ② ESC 能不能关
await page.keyboard.press('Escape');
await page.waitForTimeout(1800);
const afterEsc = { 读: await read(page, VID), 模态: await dialogState(page) };
out.ESC后 = afterEsc;
console.log('ESC 后 =', JSON.stringify(afterEsc.读), ' 模态 =', afterEsc.模态.模态);

// 若 ESC 不行，改点遮罩
if (afterEsc.模态.模态) {
  await page.mouse.click(1360, 760);
  await page.waitForTimeout(1800);
  out.点遮罩后 = { 读: await read(page, VID), 模态: await dialogState(page) };
  console.log('点遮罩后 =', JSON.stringify(out.点遮罩后.读), ' 模态 =', out.点遮罩后.模态.模态);
}
out.关掉后 = await read(page, VID);
console.log('关掉后 =', JSON.stringify(out.关掉后));

// ③ 刷新后还选不选中（审 CJ 的「刷新不管用」）
{
  const bb = await page.locator(`.react-flow__node[data-id="${VID}"]`).boundingBox();
  await page.mouse.click(bb.x + bb.width / 2, bb.y + bb.height / 2);
  await page.waitForTimeout(1400);
  const s2 = await read(page, VID);
  const f2 = s2.折叠钮 ? [s2.折叠钮[0] + 14, s2.折叠钮[1] + 14] : null;
  if (f2 && f2[0] < 1440 && f2[1] < 810) {
    await page.mouse.click(f2[0], f2[1]);
    await page.waitForTimeout(1700);
    out.模态态刷新前 = { 读: await read(page, VID), 模态: (await dialogState(page)).模态 };
  }
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6000);
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2600);
  out.刷新后 = await read(page, VID);
  out.刷新后层 = (await layers(page)).filter((x) => x.rect[0] <= 2 && x.rect[1] <= 2 && x.rect[2] >= 1400 && x.rect[3] >= 800 && x.pos !== 'static');
  console.log('刷新后 =', JSON.stringify(out.刷新后));
  console.log('刷新后 铺满视口的固定层 =', JSON.stringify(out.刷新后层));
}

// ④ 音频节点：⤢ 是不是也弹模态
{
  for (const A of ['a-CUfJfmKzUJ', 'a-THmbuJXQj4']) {
    let s = await read(page, A);
    if (!s.在) { console.log(`${A} 不在`); continue; }
    if (s.折叠钮 && (s.折叠钮[0] + 14 > 1440 || s.折叠钮[1] + 14 > 810)) { console.log(`${A} 的 ⤢ 在视口外 ${JSON.stringify(s.折叠钮)} ⛔`); out[`音频_${A}`] = { 读: s, 注: '⤢ 落在视口外' }; continue; }
    const pts = await page.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const q = n.getBoundingClientRect(); const a = [];
      for (const fy of [0.25, 0.4, 0.55, 0.7, 0.85]) for (const fx of [0.1, 0.25, 0.5, 0.75, 0.9]) {
        const x = q.x + q.width * fx, y = q.y + q.height * fy;
        const el = document.elementFromPoint(x, y);
        if (el && el.closest('.react-flow__node') === n && !el.closest('button,a')) a.push([Math.round(x), Math.round(y)]);
      }
      return a;
    }, A);
    for (const p of pts) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1400); s = await read(page, A); if (s.选中 && s.折叠钮) break; }
    if (!s.折叠钮) { console.log(`${A} 拿不到 ⤢`); continue; }
    if (s.折叠钮[0] + 14 > 1440) { console.log(`${A} 的 ⤢ 在视口外 ${JSON.stringify(s.折叠钮)} ⛔`); out[`音频_${A}`] = { 读: s, 注: '⤢ 落在视口外' }; continue; }
    await page.mouse.click(s.折叠钮[0] + 14, s.折叠钮[1] + 14);
    await page.waitForTimeout(1800);
    const d = await dialogState(page);
    out[`音频_${A}`] = { 点前: s, 点后: await read(page, A), 模态: d.模态, 模态rect: d.rect, 模态文字: (d.全文 || '').slice(0, 90) };
    console.log(`${A} 点 ⤢ 后 模态=${d.模态} rect=${JSON.stringify(d.rect)} 「${(d.全文 || '').slice(0, 70)}」`);
    if (d.模态) { await page.keyboard.press('Escape'); await page.waitForTimeout(1500); }
    if (!(await read(page, A)).有提示词框) { await page.mouse.click(1360, 760); await page.waitForTimeout(1500); }
    console.log(`${A} 复原 =`, JSON.stringify(await read(page, A)));
  }
}

await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const ids = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.收尾 = { 节点: ids, 与基线一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)) };
  console.log('\n收尾节点 =', ids.length, ' 与基线逐项一致 =', out.收尾.与基线一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cm5-modal.json'), JSON.stringify(out, null, 2));
