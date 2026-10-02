// Batch CJ-2：把 CJ-1 里被污染的读数逐条隔离重测。
//
// ⛔ CJ-1 自己废掉的两处，必须先说清楚：
//   ① 那轮「四类节点里有没有 ⤢」的扫描是在**一个节点都没选中**时做的 ——
//      参数卡不挂载，扫描器自然 11 个全报「没有」。**这轮扫描零信息量**，不能拿来答音频节点。
//   ② ③ 双击之后冒出一个 `1244×700` 的东西，从那以后 ④⑤⑥ 全被污染 ——
//      连**阳性对照（刷新）都失效了**（刷新没恢复，与 CG 的读数相反）。
//      ⇒ CJ-1 里只有 ①② 两条是干净的：**① 重新点节点 = 不恢复**、
//         **② 点节点标题 = 恢复（42 → 169，浮层 292×164 → 660×192）**。
//
// 本步逐条隔离：
//   A 逐个**选中**四类节点，看那枚 `⤢` 到底在不在（这才答得上音频节点那个问题）；
//   B 每条恢复路径**前都重新折一次**，保证起点一致，谁污染谁一目了然；
//   C 收起到底**会不会存盘** —— 折完开**全新浏览器会话**再读（CG 当年栽在同名节点上，
//     所以这次全程锁 `data-id`）。
// ⛔ 不扣积分、不点生成、不点「取消」。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const TID = 'v-v2hlWY4Br3';

const boot = async (page) => {
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
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2600);
  // ⭐ 抽屉必须收着，否则靠右的参数卡连同它右上角的 ⤢ 会被整个盖住
  const d = page.locator('.mantine-Drawer-inner').first().locator('button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 6000 }).catch(() => {});
  await page.waitForTimeout(1600);
};

const probe = (page) => page.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!n) return { 在: false };
  const vis = [...n.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const fold = [...n.querySelectorAll('button')].find((b) => {
    const c = b.className.toString();
    return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2');
  });
  const big = vis.map((e) => ({ e, r: e.getBoundingClientRect() })).filter((x) => x.r.width > 400 || x.r.height > 400);
  return {
    在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length,
    有折叠钮: !!fold,
    折叠钮rect: fold ? (() => { const r = fold.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() : null,
    有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'),
    超大元素: big.slice(0, 3).map((x) => `${x.e.tagName.toLowerCase()}.${(x.e.className || '').toString().slice(0, 34)} ${Math.round(x.r.width)}x${Math.round(x.r.height)}`),
  };
}, TID);

const out = {};
const { browser, page } = await launch();
await boot(page);

// ── A 逐个选中四类节点，看 ⤢ 在不在 ──────────────────────────────
out.A = [];
for (const id of ['v-v2hlWY4Br3', 'i-sODTbgLUm1', 'a-THmbuJXQj4', 't-UtVx3lZmrV']) {
  const b = await page.locator(`.react-flow__node[data-id="${id}"]`).boundingBox();
  await page.mouse.click(b.x + b.width / 2, b.y + b.height - 12);
  await page.waitForTimeout(1500);
  const p = await probe(page, id).catch(() => null);
  // probe() 锁的是 TID，这里改用通用读法
  const r = await page.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!n) return { 在: false };
    const vis = [...n.querySelectorAll('*')].filter((e) => { const x = e.getBoundingClientRect(); return x.width > 0 && x.height > 0; });
    const fold = [...n.querySelectorAll('button')].find((x) => {
      const c = x.className.toString();
      return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2');
    });
    return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 有折叠钮: !!fold, 折叠钮rect: fold ? [Math.round(fold.getBoundingClientRect().x), Math.round(fold.getBoundingClientRect().y)] : null, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]') };
  }, id);
  console.log(`  ${id.padEnd(18)} 选中=${r.选中} 可见后代=${String(r.可见后代数).padStart(3)} ⤢=${r.有折叠钮 ? '@' + JSON.stringify(r.折叠钮rect) : '⛔ 没有'} 提示词框=${r.有提示词框}`);
  out.A.push({ id, ...r });
}
void probe;

// ── B 逐条隔离测恢复路径：每条前重新折一次 ──────────────────────
const clickFold = async () => {
  const p = await probe(page);
  if (!p.在 || !p.有折叠钮) return null;
  await page.mouse.click(p.折叠钮rect[0] + 14, p.折叠钮rect[1] + 14);
  await page.waitForTimeout(1500);
  return probe(page);
};

out.B = [];
const step = async (name, act) => {
  // 先把节点重新折起来（若已展开就折，已折就跳过）
  let st = await probe(page);
  if (st.在 && st.有提示词框) { await clickFold(); st = await probe(page); }
  const before = st;
  const actRet = await act();
  await page.waitForTimeout(1700);
  const after = await probe(page);
  const 恢复了 = after.在 && after.可见后代数 > before.可见后代数;
  console.log(`  ${恢复了 ? '✅' : '⛔'} ${name.padEnd(24)} ${before.可见后代数} → ${after.可见后代数} 提示词框 ${before.有提示词框}→${after.有提示词框}` +
    (actRet ? ` | ${JSON.stringify(actRet).slice(0, 90)}` : ''));
  out.B.push({ 路径: name, 恢复了, 前: before, 后: after, 附注: actRet });
};

console.log('\n════ B 逐条恢复路径（每条前重新折）════');
// 先把目标节点选中并确认可折
{
  const b = await page.locator(`.react-flow__node[data-id="${TID}"]`).boundingBox();
  await page.mouse.click(b.x + b.width / 2, b.y + b.height - 12);
  await page.waitForTimeout(1400);
}
await step('① 重新点一下节点', async () => {
  const b = await page.locator(`.react-flow__node[data-id="${TID}"]`).boundingBox();
  await page.mouse.click(b.x + b.width / 2, b.y + b.height - 12);
  return null;
});
await step('② 点节点标题', async () => {
  const b = await page.locator(`.react-flow__node[data-id="${TID}"]`).boundingBox();
  await page.mouse.click(b.x + 46, b.y + 12);
  return null;
});
await step('⑤ ⌘0 适合屏幕', async () => {
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1400);
  return null;
});
await step('⑥ 刷新页面', async () => {
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6500);
  await closePromos(page);
  await page.waitForTimeout(1600);
  return null;
});

// 超大元素是什么（CJ-1 那个 1244×700）
const bb = await probe(page);
console.log('\n当前超大元素 =', JSON.stringify(bb.超大元素));
out.超大元素 = bb.超大元素;
await browser.close();

// ── C 收起会不会存盘：折一次，开**全新会话**再读 ─────────────────
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const t = await p2.locator(`.react-flow__node[data-id="${TID}"]`).boundingBox();
  await p2.mouse.click(t.x + t.width / 2, t.y + t.height - 12);
  await p2.waitForTimeout(1500);
  const r0 = await p2.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    const vis = [...n.querySelectorAll('*')].filter((e) => { const x = e.getBoundingClientRect(); return x.width > 0 && x.height > 0; });
    return { 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]') };
  }, TID);
  console.log(`\n════ C 存盘检查 ════\n  全新会话刚打开：${JSON.stringify(r0)}`);
  const f = await p2.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    const btn = [...n.querySelectorAll('button')].find((x) => { const c = x.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
    if (!btn) return null;
    const r = btn.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y)];
  }, TID);
  console.log('  ⤢@', JSON.stringify(f));
  if (f) {
    await p2.mouse.click(f[0] + 14, f[1] + 14);
    await p2.waitForTimeout(1600);
    const r1 = await p2.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const vis = [...n.querySelectorAll('*')].filter((e) => { const x = e.getBoundingClientRect(); return x.width > 0 && x.height > 0; });
      return { 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]') };
    }, TID);
    console.log('  折完：', JSON.stringify(r1));
    // 全新浏览器会话
    const { browser: b3, page: p3 } = await launch();
    await boot(p3);
    const r2 = await p3.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      if (!n) return { 不在视口: true };
      const vis = [...n.querySelectorAll('*')].filter((e) => { const x = e.getBoundingClientRect(); return x.width > 0 && x.height > 0; });
      return { 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]') };
    }, TID);
    console.log('  ⭐ 另一个全新浏览器会话读同一节点：', JSON.stringify(r2), r2.有提示词框 === false ? '⇒ ⛔ 收起**存盘了**' : '⇒ 展开（没存盘）');
    out.C = { 折前: r0, 折后: r1, 全新会话: r2 };
    await b3.close();
  } else out.C = { 说明: '目标节点上没有 ⤢，本项没测到' };
  await b2.close();
}

await writeFile(resolve(HERE, '.evidence/cj2-isolated.json'), JSON.stringify(out, null, 2));
console.log('\n（不扣积分、不点生成、不点取消）');
