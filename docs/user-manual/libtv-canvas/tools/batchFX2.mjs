// ⭐⭐⭐⭐⭐ 紧急复原：FX-1 把两枚开关留在改动态，本脚本只把它们按回去
//
// FX-1 的失误（缺陷 493）：
//   读按钮的 `读开关()` 用 `document.querySelector('[aria-label="隐藏节点连线"]')`，
//   而 FX-1 在**复原前**就去读 —— 那一刻按钮因为 DOM 重排暂时取不到，
//   脚本判定「按钮不在」直接跳过复原 ⇒ **两枚开关都被留在改动态**：
//     `隐藏节点连线` ⇒ 连线仍然隐藏（边 2 → 0）
//     `网格吸附`     ⇒ 仍然开启（背景 rgba(0,0,0,0) → rgba(255,255,255,0.1)）
//
// ⛔ 本脚本**只做一件事**：把这两枚按回去。
//    不开别的、不点别的、不用 Delete/Backspace。
// 复原判据（自证）：
//   ① 连线数回到 2 且路径有 stroke
//   ② 网格吸附按钮背景回到 rgba(0, 0, 0, 0)
// 治法：读按钮**要重试**（最多 8 次 × 400ms），别读一次就放弃。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFX2.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

const 浏览器 = await launch();
const page = 浏览器.page;

// ⭐ 读按钮**带重试**（治缺陷 493）
const 读按钮 = async (aria, 重试 = 8) => {
  for (let i = 0; i < 重试; i++) {
    const t = await page.evaluate((n) => {
      const b = document.querySelector(`[aria-label="${n}"]`);
      if (!b) return null;
      const r = b.getBoundingClientRect();
      if (r.width < 4) return null;
      return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        背景: getComputedStyle(b).backgroundColor };
    }, aria);
    if (t) return t;
    await page.waitForTimeout(400);
  }
  return null;
};

const 读连线 = () => page.evaluate(() => ({
  边: document.querySelectorAll('.react-flow__edge').length,
  路径有stroke: [...document.querySelectorAll('.react-flow__edge path')]
    .filter((p) => getComputedStyle(p).stroke !== 'rgba(0, 0, 0, 0)').length,
}));

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6000);
  await closePromos(page);
  await page.waitForTimeout(3500);
  let 上次 = -1, 稳 = 0;
  for (let i = 0; i < 25; i++) {
    const n = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    if (n === 上次) { 稳++; if (稳 >= 3) { 记(`画布稳定在 ${n}`); break; } } else 稳 = 0;
    上次 = n; await page.waitForTimeout(1200);
  }
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('.mantine-Drawer-inner [aria-label="关闭"], .mantine-Drawer-close')) b.click();
  });
  await page.waitForTimeout(900);

  const l0 = await 读连线();
  记(`开跑：边 ${l0.边}、路径有 stroke ${l0.路径有stroke}（FX-1 之后应该是 0/0）`);

  // ── 按回「隐藏节点连线」
  const b1 = await 读按钮('隐藏节点连线');
  记(`\n「隐藏节点连线」按钮：${b1 ? `中心 ${b1.中心}，背景 ${b1.背景}` : '⛔ 重试 8 次仍取不到'}`);
  if (b1) {
    if (l0.边 === 0) {
      await page.mouse.click(b1.中心[0], b1.中心[1]);
      await page.waitForTimeout(1500);
    } else 记('  当前连线本来就可见，不点');
    const l1 = await 读连线();
    断言('连线已回到可见', l1.边 >= 1 && l1.路径有stroke >= 1, `边 ${l0.边} → ${l1.边}、stroke ${l0.路径有stroke} → ${l1.路径有stroke}`);
  }

  // ── 按回「网格吸附」
  const b2 = await 读按钮('网格吸附');
  记(`\n「网格吸附」按钮：${b2 ? `中心 ${b2.中心}，背景 ${b2.背景}` : '⛔ 取不到'}`);
  if (b2) {
    if (b2.背景 !== 'rgba(0, 0, 0, 0)') {
      await page.mouse.click(b2.中心[0], b2.中心[1]);
      await page.waitForTimeout(1500);
    } else 记('  当前已经是关闭态，不点');
    const b3 = await 读按钮('网格吸附');
    断言('网格吸附已回到关闭', b3 && b3.背景 === 'rgba(0, 0, 0, 0)', `当前背景 ${b3?.背景}`);
  }

  await page.screenshot({ path: resolve(EVID, 'fx2-1-复原后.png') });
  const 终 = await 读连线();
  R.读数.终 = 终;
  记(`\n终态：边 ${终.边}、路径有 stroke ${终.路径有stroke}`);
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFX2.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
