// Batch CM-4：CM-3 撞出「收起后画布上留着一层全屏遮罩」——逐节点类型钉死它。
//
// CM-3 读数（图片节点 i-sODTbgLUm1）：
//   点节点本体 / 节点中心 → 落点是 `div.`（空 class，**不在** `.react-flow__node` 内）→ ⛔ 不恢复
//   点画布空白(720,60)/(1360,700) → 落点是 `div.z-(--z-overlay) fixed inset-0 bg-black/50` → ✅ 39 → 131
// ⭐ 我上一轮把 (720,60) 判成「空白」纯属判据漏洞（判据只查 `.react-flow__node`）。
//
// 但 CJ 记的是「**视频**节点点标题能恢复 `42 → 169`」——
// 与「点空白才恢复」不是一回事。本步对**四种节点各测一遍**，同时回答：
//   ① 展开态 / 收起态，body 下到底有没有那层 `z-(--z-overlay)`？
//   ② 节点标题栏那个点，此刻的落点是谁？（标题栏是独立 `.node-floating-ui`）
//   ③ 收起态截图到底长什么样 —— 遮罩应该把整块画布压暗，能一锤定音。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];
// 四种类型各挑一个；文本挑**两个** —— 一个点 ⤢ 正常、一个不正常，CM-0 已复现过这个分叉
const SUBJ = [
  { 名: '视频节点', id: 'v-oZNpH99MtM' },
  { 名: '图片节点', id: 'i-sODTbgLUm1' },
  { 名: '文本节点(⤢正常)', id: 't-2AK3Ukyxj3' },
  { 名: '文本节点(⤢失灵)', id: 't-UtVx3lZmrV' },
];

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

// ⭐ body 直接子元素逐个读 —— 这是「画布上铺着几层」最干净的枚举
const layers = (page) => page.evaluate(() => [...document.body.children].map((e) => {
  const s = getComputedStyle(e); const r = e.getBoundingClientRect();
  return {
    tag: e.tagName.toLowerCase(), cls: (e.className || '').toString().slice(0, 76),
    pos: s.position, z: s.zIndex, op: s.opacity, pe: s.pointerEvents, disp: s.display,
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    子元素数: e.children.length, 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 26),
  };
}));

// ⭐ 落点的完整祖先链 —— 认出「谁在挡」
const chain = (page, x, y) => page.evaluate(([px, py]) => {
  const el = document.elementFromPoint(px, py);
  if (!el) return [{ 落点: 'null' }];
  const out = []; let a = el;
  for (let i = 0; a && i < 8; i += 1, a = a.parentElement) {
    const s = getComputedStyle(a); const r = a.getBoundingClientRect();
    out.push({ i, tag: a.tagName.toLowerCase(), cls: (a.className || '').toString().slice(0, 54), pos: s.position, z: s.zIndex, pe: s.pointerEvents, op: s.opacity, disp: s.display, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 文字: (a.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 22) });
  }
  return out;
}, [x, y]);

// 节点自己的标题栏（独立 .node-floating-ui，y 允许差 40）
const title = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const nr = n.getBoundingClientRect();
  let best = null;
  for (const f of document.querySelectorAll('.node-floating-ui')) {
    const r = f.getBoundingClientRect();
    if (r.width > 0 && Math.abs(r.x - nr.x) < 12 && r.y < nr.y && nr.y - r.y < 60) {
      if (!best || r.height < best.getBoundingClientRect().height) best = f;
    }
  }
  if (!best) return null;
  const r = best.getBoundingClientRect();
  return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 文字: (best.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) };
}, id);

const out = { 轮次: [] };
const { browser, page } = await launch();
await boot(page);

for (const S of SUBJ) {
  const ID = S.id;
  console.log(`\n========== ${S.名} ${ID}`);
  const R = { 名: S.名, id: ID };
  // 选中（点不压任何按钮的点）
  const pts = await page.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!n) return [];
    const q = n.getBoundingClientRect(); const a = [];
    for (const fy of [0.25, 0.4, 0.55, 0.7, 0.85]) for (const fx of [0.1, 0.25, 0.5, 0.75, 0.9]) {
      const x = q.x + q.width * fx, y = q.y + q.height * fy;
      const el = document.elementFromPoint(x, y);
      if (el && el.closest('.react-flow__node') === n && !el.closest('button,a')) a.push([Math.round(x), Math.round(y)]);
    }
    return a;
  }, ID);
  if (!pts.length) { console.log('  ⛔ 取不到可选中的落点'); out.轮次.push(R); continue; }
  let sel = { 在: false };
  for (const p of pts) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1400); sel = await read(page, ID); if (sel.选中 && sel.折叠钮) break; }
  R.选中后 = sel;
  console.log('  选中后 =', JSON.stringify(sel));
  if (!sel.折叠钮) { console.log('  ⛔ 没拿到带 ⤢ 的状态'); out.轮次.push(R); continue; }

  // ① 展开态的层
  R.展开态层 = await layers(page);
  const ovExp = R.展开态层.filter((x) => /overlay|inset-0|backdrop/i.test(x.cls) || (x.rect[0] <= 2 && x.rect[1] <= 2 && x.rect[2] >= 1400 && x.rect[3] >= 800 && x.pos === 'fixed'));
  R.展开态遮罩 = ovExp;
  console.log('  展开态 铺满视口的固定层 =', JSON.stringify(ovExp));

  const t0 = await title(page, ID);
  R.展开态标题栏 = t0;
  if (t0) { const [tx, ty, tw, th] = t0.rect; R.展开态标题栏落点 = await chain(page, tx + 46, ty + Math.round(th / 2)); console.log('  展开态 点标题栏的落点链 =', JSON.stringify((R.展开态标题栏落点 || [])[0])); }

  // ② 折
  await page.mouse.click(sel.折叠钮[0] + 14, sel.折叠钮[1] + 14);
  await page.waitForTimeout(1700);
  const folded = await read(page, ID);
  R.折后 = folded;
  console.log('  折后 =', JSON.stringify(folded));

  // ③ 收起态的层（决定性对照）
  R.折后层 = await layers(page);
  const ovFold = R.折后层.filter((x) => /overlay|inset-0|backdrop/i.test(x.cls) || (x.rect[0] <= 2 && x.rect[1] <= 2 && x.rect[2] >= 1400 && x.rect[3] >= 800 && x.pos === 'fixed'));
  R.折后遮罩 = ovFold;
  console.log('  折后 铺满视口的固定层 =', JSON.stringify(ovFold));

  const nx = folded.节点rect[0] + Math.round(folded.节点rect[2] / 2);
  const ny = folded.节点rect[1] + Math.round(folded.节点rect[3] / 2);
  R.折后_节点中心链 = await chain(page, nx, ny);
  R.折后_空白链 = await chain(page, 1360, 700);
  console.log('  折后 节点中心落点链 =', JSON.stringify((R.折后_节点中心链 || []).slice(0, 3)));

  // ④ 收起态截图：遮罩若在，整块画布应被压暗
  R.折后截图 = `cm4-${S.名.replace(/[^\w]/g, '')}.png`;
  await page.screenshot({ path: resolve(HERE, '.evidence', R.折后截图) });
  R.拍完仍折着 = (await read(page, ID)).有提示词框 === false;
  console.log('  拍完是否仍折着 =', R.拍完仍折着);

  // ⑤ 点标题栏
  const t1 = await title(page, ID);
  R.折后标题栏 = t1;
  if (t1) {
    const [tx, ty, , th] = t1.rect;
    R.折后标题栏落点 = await chain(page, tx + 46, ty + Math.round(th / 2));
    await page.mouse.click(tx + 46, ty + Math.round(th / 2));
    await page.waitForTimeout(1700);
    const a1 = await read(page, ID);
    R.点标题栏后 = a1;
    console.log(`  点标题栏 → ${folded.可见后代数} → ${a1.可见后代数}  恢复=${a1.有提示词框 ? '✅' : '⛔'}`);
    console.log('      落点链 =', JSON.stringify((R.折后标题栏落点 || [])[0]));
  }

  // ⑥ 还没恢复就点画布空白
  if (!(await read(page, ID)).有提示词框) {
    await page.mouse.click(1360, 700);
    await page.waitForTimeout(1700);
    const a2 = await read(page, ID);
    R.点空白后 = a2;
    console.log(`  点空白   → 恢复=${a2.有提示词框 ? '✅' : '⛔'} (${a2.可见后代数})`);
  }

  // ⑦ 复原
  for (let i = 0; i < 4; i += 1) {
    const q = await read(page, ID);
    if (q.有提示词框) break;
    await page.mouse.click(1360, 700); await page.waitForTimeout(1200);
    const q2 = await read(page, ID);
    if (!q2.有提示词框) { for (const p of pts) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1200); if ((await read(page, ID)).有提示词框) break; } }
  }
  R.复原后 = await read(page, ID);
  console.log('  复原后 =', JSON.stringify(R.复原后));
  out.轮次.push(R);
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
await writeFile(resolve(HERE, '.evidence/cm4-overlay.json'), JSON.stringify(out, null, 2));
