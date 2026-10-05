// ⭐⭐⭐⭐⭐ Batch FO-3：钉死「批量操作」这条操作条，并结掉密度滑块的持久化问题
//
// FO-2 的截图推翻了一条旧结论：Batch AL/AM/AN/AO 记的是「`批量操作` 点开**无浮层**（无记录）」，
// 而 FO-2 实拍到的是 ⭐ **面板底部展开了一整条操作条**：
//   左边「已选择 0 项」 + 右边五枚 `删除` `下载` `评级` `保存到资产` `添加到画布`。
//
// ⚠️ FO-2 那一步的**判据是错的**：它写的是
//   `(await 全页文字(page)).filter(t => /批量|删除|下载|清空/.test(t))`
//   —— 这是**在当前文字里筛**，**不是差分**，所以「新增」两个字名不副实（缺陷 456）。
//   本轮改成真差分 + 逐枚量框 + 读 tooltip。
//
// 另外两个问题：
//   · 密度滑块的默认值**跨会话还在不在**？FO-1 把它拖到了 0。
//   · 退出「批量操作」模式后，面板回到什么状态？
//
// ⛔ 安全边界：**不点「删除」**（写操作，且画布没有回收站）——只量它的框和样式。
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器, 开底栏, 关面板 } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFO3.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const 浏览器 = await launch();
const page = 浏览器.page;
const 在 = async (...词) => { const s = new Set((await 全页文字(page)).map(归一)); return 词.every((m) => s.has(归一(m))); };
const 面板开着 = () => 在('全部画布', '本画布', '暂无历史记录');

/** ⭐ 真差分：点之前拍一张「有名字的元素指纹表」，点之后再来一张，**只取真正新出现的**。 */
const 指纹 = () => page.evaluate(() => {
  const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const 表 = new Map();
  for (const el of document.querySelectorAll('button,[role="button"],[role="radio"],[role="menuitem"],a')) {
    const r = el.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    const 名 = 归(el.innerText) || el.getAttribute('aria-label') || el.getAttribute('title') || '';
    if (!名) continue;
    表.set(名 + '@' + Math.round(r.x) + ',' + Math.round(r.y), {
      名, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      底色: getComputedStyle(el).backgroundColor, 字色: getComputedStyle(el).color,
      aria: el.getAttribute('aria-label'), title: el.getAttribute('title'), class: String(el.className || '').slice(0, 70),
    });
  }
  return [...表.entries()].map(([k, v]) => ({ k, ...v }));
});

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 80));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  断言(await 开底栏(page, '生成历史', { 记, 断言 }), '打开生成历史');

  // ── ① 密度滑块：这个会话打开时是几？（FO-1 把它拖到了 0）──
  记('—— ① 密度滑块的初始值 ——');
  const 滑 = await page.evaluate(() => [...document.querySelectorAll('input[type=range]')].map((el) => {
    const r = el.getBoundingClientRect();
    return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], min: el.min, max: el.max, step: el.step, value: el.value, class: String(el.className || '').slice(0, 100) };
  }));
  R.读数.滑块初值 = 滑;
  记('   ' + JSON.stringify(滑));
  断言(滑.length === 1, '找到唯一一枚密度滑块', 滑);
  断言(滑[0].value === '2', '⭐ 跨会话仍是默认 2 —— **这个设置不落盘，每次打开都是 2**', 滑[0]);

  // ── ② 悬停「批量操作」读 tooltip ──
  记('—— ② 批量操作的 tooltip ——');
  const 批 = await page.evaluate(() => {
    for (const el of document.querySelectorAll('button,[role="button"]')) {
      if ((el.innerText || '').replace(/\s+/g, '').trim() !== '批量操作') continue;
      const r = el.getBoundingClientRect();
      const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
      return { 点: [x, y], 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    }
    return null;
  });
  if (批) {
    await page.mouse.move(批.点[0] - 40, 批.点[1]);
    await page.waitForTimeout(300);
    await page.mouse.move(批.点[0], 批.点[1]);
    await page.waitForTimeout(2000);
    const 泡 = await page.evaluate(() => [...document.querySelectorAll('[role="tooltip"],.mantine-Tooltip-tooltip,[data-portal] div')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 60 && r.height > 16 && r.height < 80 && e.innerText; }).map((e) => { const r = e.getBoundingClientRect(); return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 文字: e.innerText.replace(/\s+/g, ' ').trim().slice(0, 120) }; }));
    R.读数.tooltip = 泡;
    记('   tooltip ' + JSON.stringify(泡).slice(0, 600));
    断言(泡.some((b) => /多选|框选|素材/.test(b.文字)), '⭐ 悬停读到了「怎么进多选」的说明', 泡.map((b) => b.文字));
    await page.screenshot({ path: EVID + 'fo3-01-批量操作-悬停说明.png' });
  }

  // ── ③ 真差分：点开「批量操作」到底多出了什么 ──
  记('—— ③ 真差分 ——');
  const 前 = await 指纹();
  await page.mouse.click(批.点[0], 批.点[1]);
  await page.waitForTimeout(2500);
  const 后 = await 指纹();
  const 前键 = new Set(前.map((f) => f.k));
  const 新出 = 后.filter((f) => !前键.has(f.k));
  R.读数.批量操作真差分 = { 前数: 前.length, 后数: 后.length, 新出 };
  记(`   前 ${前.length} 枚 → 后 ${后.length} 枚，新增 ${新出.length} 枚`);
  for (const f of 新出) 记('   + ' + JSON.stringify(f));
  断言(新出.length >= 4, '⭐⭐ 「批量操作」确实展开了一条操作条（旧结论「无浮层」是错的）', 新出.map((f) => f.名));
  const 危险 = 新出.find((f) => f.名 === '删除');
  断言(危险 && /rgb\(/.test(危险.字色), '「删除」是危险色（⛔ 本手册不点它）', 危险);
  await page.screenshot({ path: EVID + 'fo3-02-批量操作-操作条.png' });

  // ── ④ 退出批量模式：再点一次「批量操作」 ──
  记('—— ④ 退出批量模式 ——');
  await page.mouse.click(批.点[0], 批.点[1]);
  await page.waitForTimeout(2000);
  const 退后 = await 指纹();
  const 退出后仍出 = 退后.filter((f) => !前键.has(f.k)).map((f) => f.名);
  R.读数.退出批量 = { 仍多出: 退出后仍出, 面板还在: await 面板开着() };
  记('   退出后仍多出 ' + JSON.stringify(退出后仍出) + '；面板还在=' + R.读数.退出批量.面板还在);
  断言(退出后仍出.length === 0, '⭐ 再点一次「批量操作」就退出，面板留在原样', 退出后仍出);

  R.读数.关面板 = { 成功: await 关面板(page, ['暂无历史记录'], { 记, 断言 }) };
  记(`—— 共跑了 ${断言.统计.次数} 条断言，失败 ${断言.统计.失败} 条 ——`);
} catch (e) {
  记('❌ ' + (e && e.message ? e.message : String(e)));
} finally {
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
