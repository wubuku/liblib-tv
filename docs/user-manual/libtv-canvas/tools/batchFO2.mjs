// ⭐⭐⭐⭐⭐ Batch FO-2：接上 FO-1 断掉的地方，并结掉一个**新发现的坑**
//
// FO-1 跑到第 ③ 步点开「所有评级」之后，按 `Escape` 想收起下拉 ——
// ⛔ 结果**整个「生成历史」面板被关掉了**：后面三步（时间倒序 / 页签 / 批量操作）
//   全都读不到元素。⇒ 断言当场失败（这正是断言存在的意义）。
//
// ⭐ 用户价值：「在下拉里按 Esc」会把整个面板一起关掉。
//   这一轮要量清楚**到底哪种收法能只收下拉、留住面板**，三种各测一遍：
//     ① 按 Esc          ② 点面板里的空白   ③ 再点一次同一枚按钮
//
// ⛔ 安全边界：只读。只开关面板、开下拉、切页签、拖密度滑块；收尾把读数改回去。
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器, 开底栏, 关面板 } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFO2.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const 浏览器 = await launch();
const page = 浏览器.page;

const 在 = async (...词) => {
  const s = new Set((await 全页文字(page)).map(归一));
  return 词.every((m) => s.has(归一(m)));
};
const 面板开着 = () => 在('全部画布', '本画布', '暂无历史记录');

const 找 = (词, { 前缀 = false } = {}) => page.evaluate(([w, p]) => {
  for (const el of document.querySelectorAll('button,[role="button"],[role="radio"],[role="tab"],a')) {
    const t = (el.innerText || '').replace(/\s+/g, ' ').trim();
    if (p ? !t.startsWith(w) : t !== w) continue;
    const r = el.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
    const hb = document.elementFromPoint(x, y)?.closest('button,[role="button"],[role="radio"],[role="tab"],a');
    return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 点: [x, y], 命中: hb ? (hb.innerText || hb.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 20) : null, title: el.getAttribute('title'), role: el.getAttribute('role'), checked: el.getAttribute('aria-checked') };
  }
  return null;
}, [词, 前缀]);

const 开面板 = async () => {
  if (await 面板开着()) return true;
  return 开底栏(page, '生成历史', { 记, 断言 });
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 90));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  断言(await 开底栏(page, '生成历史', { 记, 断言 }), '打开生成历史');

  // ── ① 三种「收起下拉」的办法各测一遍 ──
  记('—— ① 收下拉的三种办法 ——');
  const 办法 = {};
  for (const 名 of ['按 Esc', '点面板空白', '再点同一枚按钮']) {
    if (!(await 开面板())) { 记(`   ⛔ ${名}：面板没能重开`); continue; }
    const 评级 = await 找('所有评级', { 前缀: true });
    if (!评级) { 办法[名] = { 失败: '找不到评级按钮' }; continue; }
    await page.mouse.click(评级.点[0], 评级.点[1]);
    await page.waitForTimeout(1500);
    const 下拉开着 = await page.evaluate(() => [...document.querySelectorAll('.mantine-Popover-dropdown')].some((e) => e.getBoundingClientRect().width > 0));
    if (名 === '按 Esc') await page.keyboard.press('Escape');
    else if (名 === '点面板空白') { await page.mouse.click(720, 620); }
    else await page.mouse.click(评级.点[0], 评级.点[1]);
    await page.waitForTimeout(1600);
    const 下拉关了 = !(await page.evaluate(() => [...document.querySelectorAll('.mantine-Popover-dropdown')].some((e) => e.getBoundingClientRect().width > 0)));
    const 面板还在 = await 面板开着();
    办法[名] = { 下拉开着, 下拉关了, 面板还在 };
    记(`   ${名}：下拉 ${下拉开着 ? '开' : '—'} → ${下拉关了 ? '关' : '仍在'}；面板 ${面板还在 ? '✅ 还在' : '⛔ 被一起关掉了'}`);
    await page.screenshot({ path: EVID + `fo2-01-收下拉-${名}.png` });
  }
  R.读数.收下拉 = 办法;
  const 只收下拉的 = Object.entries(办法).filter(([, v]) => v.下拉关了 && v.面板还在).map(([k]) => k);
  断言(只收下拉的.length >= 1, '⭐ 至少有一种办法能只收下拉、留住面板', 办法);
  断言(办法['按 Esc'] && 办法['按 Esc'].面板还在 === false, '⭐⭐ 确认「在下拉里按 Esc」会把整个面板一起关掉', 办法['按 Esc']);

  // ── ② 时间倒序：两态循环 ──
  记('—— ② 时间倒序 ——');
  断言(await 开面板(), '面板重开');
  const 态 = [];
  for (let i = 0; i < 4; i++) {
    const c = (await 找('时间倒序', { 前缀: true })) || (await 找('时间正序', { 前缀: true }));
    if (!c) { 记('   ⛔ 第 ' + (i + 1) + ' 轮找不到排序按钮'); break; }
    态.push({ 轮: i + 1, 文字: c.命中, title: c.title });
    await page.mouse.click(c.点[0], c.点[1]);
    await page.waitForTimeout(1300);
  }
  R.读数.时间倒序 = 态;
  记('   四轮 ' + JSON.stringify(态));
  断言(态.length >= 3 && new Set(态.map((s) => s.title)).size >= 2, '⭐「时间倒序」是两态循环（title 在「当前：最新优先 / 最早优先」之间换）', 态);

  // ── ③ 全部画布 / 本画布：是 radio 不是 tab ──
  记('—— ③ 全部画布 / 本画布 ——');
  const 读页签 = () => page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
    return [...document.querySelectorAll('button,[role="radio"],[role="tab"]')].map((el) => {
      const t = 归(el.innerText);
      if (t !== '全部画布' && t !== '本画布') return null;
      const r = el.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) return null;
      return { 文字: t, role: el.getAttribute('role'), ariaChecked: el.getAttribute('aria-checked'), 底色: getComputedStyle(el).backgroundColor, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    }).filter(Boolean);
  });
  const 前 = await 读页签();
  记('   点之前 ' + JSON.stringify(前));
  const 本 = 前.find((p) => p.文字 === '本画布');
  if (本) {
    await page.mouse.click(本.框[0] + 本.框[2] / 2, 本.框[1] + 本.框[3] / 2);
    await page.waitForTimeout(1500);
    const 后 = await 读页签();
    记('   点之后 ' + JSON.stringify(后));
    R.读数.页签 = { 前, 后 };
    断言(JSON.stringify(前) !== JSON.stringify(后), '⭐ 切页签后状态变了（能看出哪个高亮）', { 前, 后 });
    await page.screenshot({ path: EVID + 'fo2-02-切到本画布.png' });
    const 全 = (await 读页签()).find((p) => p.文字 === '全部画布');
    if (全) { await page.mouse.click(全.框[0] + 全.框[2] / 2, 全.框[1] + 全.框[3] / 2); await page.waitForTimeout(1300); 记('   已复原到「全部画布」'); }
  } else 断言(false, '应该找得到「本画布」');

  // ── ④ 批量操作 ──
  记('—— ④ 批量操作 ——');
  const 前层 = await page.evaluate(() => document.querySelectorAll('div').length);
  const 批量 = await 找('批量操作', { 前缀: true });
  记('   ' + JSON.stringify(批量));
  if (批量) {
    await page.mouse.click(批量.点[0], 批量.点[1]);
    await page.waitForTimeout(2000);
    const 后层 = await page.evaluate(() => document.querySelectorAll('div').length);
    const 新增文字 = (await 全页文字(page)).filter((t) => /批量|删除|下载|清空/.test(t));
    R.读数.批量操作 = { 前层数: 前层, 后层数: 后层, 新增文字, 面板还在: await 面板开着() };
    记('   div 数 ' + 前层 + ' → ' + 后层 + '；新增文字 ' + JSON.stringify(新增文字) + '；面板还在=' + R.读数.批量操作.面板还在);
    断言(await 面板开着(), '点「批量操作」后面板**没被关掉**', R.读数.批量操作);
    await page.screenshot({ path: EVID + 'fo2-03-批量操作-无记录时.png' });
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  }

  // ── ⑤ 复原：密度滑块回到默认 2 ──
  记('—— ⑤ 复原 ——');
  const s = await page.evaluate(() => { const el = document.querySelector('input[type=range]'); return el ? { min: el.min, max: el.max, value: el.value, 框: [Math.round(el.getBoundingClientRect().x), Math.round(el.getBoundingClientRect().y), Math.round(el.getBoundingClientRect().width), Math.round(el.getBoundingClientRect().height)] } : null; });
  if (s && s.value !== '2') {
    const r = s.框, 比例 = (2 - Number(s.min)) / (Number(s.max) - Number(s.min));
    const x = Math.round(r[0] + 6 + (r[2] - 12) * 比例), y = Math.round(r[1] + r[3] / 2);
    await page.mouse.move(x, y); await page.mouse.down();
    for (let i = 0; i < 8; i++) { await page.mouse.move(x, y); await page.waitForTimeout(70); }
    await page.mouse.up(); await page.waitForTimeout(1000);
  }
  const 后值 = await page.evaluate(() => { const el = document.querySelector('input[type=range]'); return el ? el.value : null; });
  R.读数.复原 = { 前: s, 后: 后值 };
  记('   密度滑块 ' + s?.value + ' → ' + 后值);
  断言(后值 === '2', '密度滑块复原到默认 2', { 后值 });

  R.读数.关面板 = { 成功: await 关面板(page, ['暂无历史记录'], { 记, 断言 }) };
  记(`—— 共跑了 ${断言.统计.次数} 条断言，失败 ${断言.统计.失败} 条 ——`);
} catch (e) {
  记('❌ ' + (e && e.message ? e.message : String(e)));
} finally {
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
