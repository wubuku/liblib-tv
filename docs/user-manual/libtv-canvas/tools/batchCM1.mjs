// Batch CM-1：补完「图片节点点标题」的新会话对照，外加查 `z-[180]` 那个全屏层。
//
// ⛔ CM-0 的复原循环写成了**无上限 `while (!有提示词框)`** ——
//    而图片节点在同会话里**永远不恢复** ⇒ 死循环 ⇒ 浏览器被拖到超时、进程被杀。
//    ✅ 本步所有复原循环一律 `for (let i = 0; i < N; i += 1)`，**必须有上限**。
//
// ① 图片节点：新会话里折完立刻点标题，和同会话的读数对照
//    （同会话已测：连点 3 次都是 `39 → 39`，由 CM-0 记录）。
// ② `z-[180]` 那个 `fixed inset-0` 全屏层：它 class 里同样带 `motion-safe:transition-opacity`，
//    当前 `opacity: 0`、无文字、无可交互元素。查它的祖先链、兄弟节点，
//    以及**它和 z-[305] 那条跟随横幅是不是同一个组件的兄弟**（如果是，说明是同一套浮层容器）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];
const IMG = 'i-sODTbgLUm1';

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
  const fr = fold ? fold.getBoundingClientRect() : null;
  return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'), 折叠钮: fr ? [Math.round(fr.x), Math.round(fr.y)] : null };
}, id);
const clickTitle = async (page, id) => {
  const b = await page.locator(`.react-flow__node[data-id="${id}"]`).boundingBox();
  await page.mouse.click(b.x + 46, b.y + 12);
  await page.waitForTimeout(1600);
};
const exclusive = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  for (const fy of [0.2, 0.35, 0.5, 0.65, 0.8]) for (const fx of [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]) {
    const x = r.x + r.width * fx, y = r.y + r.height * fy;
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n) return [Math.round(x), Math.round(y)];
  }
  return null;
}, id);

const out = {};

// ① 新会话对照
{
  const { browser, page } = await launch();
  await boot(page);
  const pt = await exclusive(page, IMG);
  await page.mouse.click(pt[0], pt[1]);
  await page.waitForTimeout(1600);
  const sel = await read(page, IMG);
  await page.mouse.click(sel.折叠钮[0] + 14, sel.折叠钮[1] + 14);
  await page.waitForTimeout(1600);
  const folded = await read(page, IMG);
  console.log('════ 图片节点（新会话）════');
  console.log('  展开 =', sel.可见后代数, ' 折后 =', folded.可见后代数);
  const tries = [];
  for (let i = 0; i < 3; i += 1) {
    await clickTitle(page, IMG);
    const r = await read(page, IMG);
    tries.push({ 第几次: i + 1, 可见后代数: r.可见后代数, 有提示词框: r.有提示词框 });
    console.log(`  点标题第 ${i + 1} 次 = ${r.可见后代数} 提示词框=${r.有提示词框} ${r.有提示词框 ? '✅ 恢复' : '⛔ 仍折'}`);
    if (r.有提示词框) break;
  }
  out.图片_新会话 = { 展开: sel.可见后代数, 折后: folded.可见后代数, 尝试: tries };
  // 复原（有上限）
  for (let i = 0; i < 4; i += 1) {
    const r = await read(page, IMG);
    if (r.有提示词框) { out.图片_新会话.收尾 = r; console.log('  ✅ 已复原 =', r.可见后代数); break; }
    await clickTitle(page, IMG);
  }
  await browser.close();
}

// ② z-[180] 全屏层
{
  const { browser, page } = await launch();
  await boot(page);
  console.log('\n════ z-[180] 全屏层 ════');
  out.全屏层 = await page.evaluate(() => {
    const el = [...document.querySelectorAll('div')].find((e) => { const c = e.className.toString(); const r = e.getBoundingClientRect(); return c.includes('fixed') && c.includes('inset-0') && c.includes('z-[180]') && r.width > 0; });
    if (!el) return { 找到: false };
    const cs = getComputedStyle(el);
    const chain = [];
    for (let a = el; a && chain.length < 5; a = a.parentElement) { const r = a.getBoundingClientRect(); chain.push({ tag: a.tagName.toLowerCase(), cls: (a.className || '').toString().slice(0, 80), 尺寸: [Math.round(r.width), Math.round(r.height)], 子元素数: a.children.length }); }
    return {
      找到: true, 完整class: (el.className || '').toString(), opacity: cs.opacity, position: cs.position, zIndex: cs.zIndex,
      pointerEvents: cs.pointerEvents, 背景: cs.backgroundColor, 内层HTML: (el.innerHTML || '').slice(0, 200),
      直接子元素: [...el.children].map((c) => ({ tag: c.tagName.toLowerCase(), cls: (c.className || '').toString().slice(0, 60), 文字: (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24) })),
      祖先链: chain,
    };
  });
  if (out.全屏层.找到) {
    console.log('  完整 class =', out.全屏层.完整class);
    console.log('  opacity =', out.全屏层.opacity, ' pointer-events =', out.全屏层.pointerEvents, ' 背景 =', out.全屏层.背景);
    console.log('  直接子元素 =', JSON.stringify(out.全屏层.直接子元素));
    console.log('  祖先链:');
    for (const c of out.全屏层.祖先链) console.log(`    ${c.tag}.${c.cls}  ${JSON.stringify(c.尺寸)} 子=${c.子元素数}`);
  } else console.log('  ⛔ 页面上找不到这一层');

  // ⭐ 它和 z-[305] 跟随横幅是不是同一个容器下的兄弟？
  out.两者关系 = await page.evaluate(() => {
    const a = [...document.querySelectorAll('div')].find((e) => e.className.toString().includes('z-[180]'));
    const b = [...document.querySelectorAll('div')].find((e) => e.className.toString().includes('z-[305]'));
    if (!a || !b) return { 说明: '有一层没找到' };
    const common = (x, y) => { const s = new Set(); for (let p = x; p; p = p.parentElement) s.add(p); let last = null; for (let p = y; p; p = p.parentElement) if (s.has(p)) last = p; return last; };
    const c = common(a, b);
    return {
      是兄弟: a.parentElement === b.parentElement,
      最近公共祖先: c ? `${c.tagName.toLowerCase()}.${(c.className || '').toString().slice(0, 60)}` : null,
      公共祖先的直接子元素: c ? [...c.children].map((x) => (x.className || '').toString().slice(0, 40)) : null,
    };
  });
  console.log('  与 z-[305] 跟随横幅的关系 =', JSON.stringify(out.两者关系));
  await browser.close();
}

// 收尾复核
{
  const { browser, page } = await launch();
  await boot(page);
  const ids = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.收尾 = { 节点: ids, 与基线一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)) };
  console.log('\n收尾节点 =', ids.length, ' 与基线逐项一致 =', out.收尾.与基线一致);
  await browser.close();
}
await writeFile(resolve(HERE, '.evidence/cm1-image-new-session-and-z180.json'), JSON.stringify(out, null, 2));
console.log('\n（不扣积分、不点生成、不点取消）');
