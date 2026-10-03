// Batch CT-3：重做 CT-2 的 ② ③ —— CT-2 作废。
//
// ⛔ **CT-2 的实验作废，原因在我自己的脚本**：
//    ① 之后我为了「关掉面板」执行了 `page.mouse.click(20, 20)`。
//       大编辑器是 `fixed left-1/2 top-1/2` 的 `800×600`，起点 `[320,105]`
//       ⇒ `[20,20]` **在它外面、就在压暗遮罩上** ⇒ 点它 = 关闭大编辑器。
//    ② 于是 ③ 里那三次点击**全都落在画布上**，不是大编辑器里。
//    ⇒ 阳性对照（真提交键 `gen.submit`）也没弹任何 toast ——
//    ⭐ **阳性对照不通过时，输出只能是「没测到」**。这三条读数全部作废。
//
// 还有一条判据缺陷（§147）：`两面板相同 = false` 是废话 ——
//    一方是 17 个、另一方是 0 个，比出来必然不同，**它不能证明「两者不同」**，
//    只能证明「滑块那侧没测到东西」。
//
// 治法（本脚本全部照做）：
//   A. `ensureModal()` —— 每次实验前**断言** `z-index:601` 那个大编辑器在；
//      不在就重新打开。绝不用点遮罩来「重置」。
//   B. 判据换成**全页文字叶子的新增差集**（不是正则找 toast）。
//      「提示词为空，请输入内容后点击」作为**新增**出现就会被抓到，
//      而「图片反推提示词」这种常驻按钮文字天然被基线排除 ——
//      ⭐ CT-2 那个 `toasts()` 正则把常驻按钮当成了 toast，是同一个坑。
//   C. 每个 probe 之间**只按 ESC**，不点画布空白。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const IMG = 'i-9nlG6HdjK2';
const LOG = console.log;

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
  const p = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
    if (!b) return null; const r = b.getBoundingClientRect();
    return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
  });
  if (p) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1200); }
};

const modalOn = (page) => page.evaluate(() =>
  !!([...document.body.children].find((e) => getComputedStyle(e).zIndex === '601' && e.getBoundingClientRect().width > 0)));

async function ensureModal(page) {
  if (await modalOn(page)) return 'already';
  await page.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    n.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: n.getBoundingClientRect().x + 40, clientY: n.getBoundingClientRect().y + 20 }));
  }, IMG);
  await page.waitForTimeout(800);
  const fp = await page.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    const f = [...n.querySelectorAll('button')].find((b) => {
      const c = (b.className || '').toString();
      return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2');
    });
    if (!f) return null;
    const r = f.getBoundingClientRect();
    for (let dx = 4; dx < r.width; dx += 3) for (let dy = 4; dy < r.height; dy += 3) {
      const el = document.elementFromPoint(r.x + dx, r.y + dy);
      if (el && (el === f || f.contains(el) || el.contains(f))) return [Math.round(r.x + dx), Math.round(r.y + dy)];
    }
    return null;
  }, IMG);
  if (!fp) return 'no-fold-btn';
  await page.mouse.click(fp[0], fp[1]);
  await page.waitForTimeout(1300);
  return (await modalOn(page)) ? 'reopened' : 'failed';
}

// ⭐ 全页可见文字叶子（根从 body 起；跳过遮罩/客服层）
const leaves = (page) => page.evaluate(() => {
  const res = [];
  for (const e of document.querySelectorAll('body *')) {
    if (e.children.length) continue;
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) continue;
    const r = e.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const t = (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 60) continue;
    const host = e.closest('body > *');
    const hc = host ? (host.className || '').toString() : '';
    if (host && (getComputedStyle(host).zIndex === '600' || /ysf-chat-layer/.test(hc))) continue;
    res.push(`${t}@${Math.round(r.x)},${Math.round(r.y)}`);
  }
  return res;
});
const newLeaves = (a, b) => {
  const sa = new Set(a);
  return b.filter((x) => !sa.has(x));
};

const { browser, page } = await launch();
await boot(page);
LOG(`初始 ensureModal → ${await ensureModal(page)}`);
LOG(`大编辑器开着: ${await modalOn(page)}`);

// 描述框必须是空的 —— 这是 ③ 的硬前置
const desc = await page.evaluate(() => {
  const host = document.querySelector('[data-practice-anchor="gen.prompt"]');
  const ta = host?.querySelector('textarea,[contenteditable="true"]');
  return ta ? { 值: (ta.value ?? ta.textContent ?? '').slice(0, 30), 节点: host.getBoundingClientRect().width > 0 } : null;
});
LOG(`硬前置 —— 描述框: ${JSON.stringify(desc)}`);
if (!desc || desc.值 !== '') { LOG('⛔ 描述框非空，实验作废'); await browser.close(); process.exit(1); }

const out = { desc, probes: [] };

// ---- probe：点一��按钮，采样 8 次 ×300ms，报「新增文字」 ----------------------
const probe = async (label, x, { escBetween = true } = {}) => {
  const pre = await ensureModal(page);
  const before = await leaves(page);
  await page.mouse.move(x + 16, 664 + 16);
  await page.waitForTimeout(250);
  await page.mouse.click(x + 16, 664 + 16);
  const series = [];
  for (let i = 0; i < 8; i += 1) { await page.waitForTimeout(300); series.push(newLeaves(before, await leaves(page))); }
  const all = [...new Set(series.flat().map((s) => s.split('@')[0]))];
  LOG(`\n--- ${label} @x=${x}  (ensureModal=${pre}) ---`);
  LOG(`    8 次采样(每 300ms)累计新增文字 ${all.length} 种:`);
  for (const t of all) LOG(`       "${t}"`);
  if (escBetween) { await page.keyboard.press('Escape'); await page.waitForTimeout(700); }
  const rec = { label, x, pre, 新增: all, 时间线: series.map((s) => [...new Set(s.map((z) => z.split('@')[0]))]) };
  out.probes.push(rec);
  return rec;
};

// ---- ② 滑块 [999,664]：这次大编辑器确实开着 --------------------------------
const r滑块 = await probe('滑块（lucide sliders-horizontal，CR 记的「高级设置」）', 999);
LOG(`    大编辑器此刻还开着: ${await modalOn(page)}`);
out.滑块后面板全文 = await page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  return d ? (d.innerText || '').replace(/\s+/g, ' ').trim() : null;
});
LOG(`    滑块点开后大编辑器全文（前 400 字）: ${JSON.stringify((out.滑块后面板全文 || '').slice(0, 400))}`);

// 复位：ESC 可能没关掉弹层，再确保一次
await page.keyboard.press('Escape'); await page.waitForTimeout(500);

// ---- ③ toast 归属三连：翻译 / 阴性对照(球) / 阳性对照(真提交) -----------------
const r翻译 = await probe('翻译提示词（libtv「A+斜杠」）', 959);
const r球 = await probe('阴性对照 彩色球（点它也会开相机面板，但不该有提示词校验）', 744);
const r提交 = await probe('阳性对照 真提交键 gen.submit', 1079);

out.对照判定 = {
  翻译有提示: r翻译.新增.length > 0,
  球有提示: r球.新增.length > 0,
  提交有提示: r提交.新增.length > 0,
  阳性对照通过: r提交.新增.length > 0,
};
LOG(`\n===== ③ 判定 =====`);
LOG(JSON.stringify(out.对照判定, null, 2));
if (!out.对照判定.阳性对照通过) LOG('⛔ 阳性对照不通过 ⇒ 翻译/球这两条读数只能记「没测到」，不能写成行为。');

await writeFile(new URL('./batchCT3.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n已写 tools/batchCT3.json');
await browser.close();
