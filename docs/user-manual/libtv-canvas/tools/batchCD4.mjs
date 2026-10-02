// Batch CD-4：⚠️ **把写进用户原有节点的测试文本清掉，并自证清干净。**
//
// 事情经过（如实记）：CD-1 / CD-2 读到的提示词框都是 `val: ""`（原始状态是**空的**），
// 但 CD-3 一进来就发现框里已经有了 `a cat sitting on a warm windowsill at sunrise` ——
// 说明**前面某一轮的键盘输入其实落进去了，而且被存盘**（刷新后仍在）。
// ⭐ 两次「没打进去」的读数都是**探针自己的问题**（框在视口外），
//    但**输入确实生效并落盘了** —— 「没打进去」和「没生效」是两回事。
//
// 这一步：逐个文本节点读一遍 → 把有我测试文本的**清空** → 刷新复核仍是空。
// ⛔ 清空前先记录原文；只删**我打进去的那段**，不动别的字。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_MARK = 'windowsill';
const SEL = '.text-fg-default[contenteditable="true"]';

const { browser, page } = await launch();
const out = { rounds: [] };

await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});

const readAllTextNodes = () => page.evaluate((sel) => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const out2 = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    if (!vis(n)) continue;
    const label = (n.innerText || '').trim();
    if (!label.includes('文本节点')) continue;
    const boxes = [...n.querySelectorAll(sel)].map((el) => {
      const r = el.getBoundingClientRect();
      return { box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        inViewport: r.x >= 0 && r.y >= 0 && r.right <= 1440 && r.bottom <= 810,
        val: (el.innerText || '').trim().slice(0, 120) };
    });
    out2.push({ id: n.getAttribute('data-id'), label: label.slice(0, 20), boxes });
  }
  return out2;
}, SEL);

// ⚠️ 不能叫 `open` —— 那个名字已经从 ./lib.mjs import 进来了，会重复声明
async function reload(url) { await open(page, url); await page.waitForTimeout(900); }

await reload(URL_);
out.round1_before = await readAllTextNodes();

// 逐个处理：选节点 → 平移进视口 → 全选删除
for (const t of (out.round1_before || [])) {
  const dirty = (t.boxes || []).find((b) => b.val.includes(MY_MARK));
  const step = { id: t.id, label: t.label, had: dirty?.val ?? null };
  if (!dirty) { step.action = '干净，跳过'; out.rounds.push(step); continue; }

  await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    n?.click();
  }, t.id);
  await page.waitForTimeout(1800);
  const now = (await readAllTextNodes()).find((x) => x.id === t.id);
  const b = (now?.boxes || [])[0];
  step.box = b?.box;
  if (b && !b.inViewport) {
    const needX = b.box[0] < 0 ? -b.box[0] + 40 : (b.box[0] + b.box[2] > 1440 ? 1440 - (b.box[0] + b.box[2]) - 40 : 0);
    const needY = b.box[1] < 0 ? -b.box[1] + 40 : (b.box[1] + b.box[3] > 810 ? 810 - (b.box[1] + b.box[3]) - 40 : 0);
    await page.mouse.move(900, 400);
    await page.mouse.down({ button: 'middle' });
    await page.mouse.move(900 + needX, 400 + needY, { steps: 18 });
    await page.mouse.up({ button: 'middle' });
    await page.waitForTimeout(1400);
  }
  const b2 = (await readAllTextNodes()).find((x) => x.id === t.id)?.boxes?.[0];
  step.box2 = b2?.box;
  if (b2) {
    await page.mouse.move(b2.box[0] + 50, b2.box[1] + 16, { steps: 8 });
    await page.waitForTimeout(400);
    await page.mouse.click(b2.box[0] + 50, b2.box[1] + 16);
    await page.waitForTimeout(600);
    step.focusOk = await page.evaluate((sel) => document.activeElement === document.querySelector(sel), SEL);
    // ⌘A 全选 + Backspace
    await page.keyboard.press('Meta+a');
    await page.waitForTimeout(400);
    await page.keyboard.press('Backspace');
    await page.waitForTimeout(1200);
    step.after = (await readAllTextNodes()).find((x) => x.id === t.id)?.boxes?.[0]?.val ?? null;
  }
  out.rounds.push(step);
}

// ⭐ 刷新复核：清空是否真的落盘
await reload(URL_);
out.round2_afterReload = await readAllTextNodes();
out.allClean = (out.round2_afterReload || []).every((t) => !(t.boxes || []).some((b) => b.val.includes(MY_MARK)));
out.anyText = (out.round2_afterReload || []).map((t) => ({ id: t.id, vals: (t.boxes || []).map((b) => b.val) }));
await shot(page, 'M-301-文本节点-提示词已清空.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });
await writeFile(resolve(HERE, '.evidence/cd4-restore.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ before: out.round1_before, rounds: out.rounds, afterReload: out.round2_afterReload, allClean: out.allClean }, null, 2).slice(0, 3000));
await browser.close();
