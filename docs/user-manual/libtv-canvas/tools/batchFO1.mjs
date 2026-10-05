// ⭐⭐⭐⭐⭐ Batch FO-1：把「生成历史」面板从**只有内部审计记录**变成**用户向的一页**
//
// 缺口：`task-inventory.yml` 里 `assets-page`（生成历史 / 个人资产库 / 可灵资产库）
// 的 `manual_pages` 只挂了 `20-reference.md` —— `10-tasks/` 下**没有这一页**，
// 全手册**一张生成历史的截图都没有**。而 AUDIT.md 里其实堆着 Batch AL/AM/AN/AO
// 四批的实点读数（六档评级下拉、时间倒序两态、批量操作无浮层…）。
// ⇒ 这一轮把那些内部读数**翻译成用户能照着做的一页**，缺的当场补测。
//
// ⭐ 本轮全部走 FN 固化的判据工具（`lib.mjs` 的 开底栏/关面板/断言器/全页文字），
//   ⛔ 不再各脚本自写 —— 这正是缺陷 447/449 说的「教训必须变成工具」。
//
// ⛔ 安全边界：只读。只开关面板、开下拉、切页签、拖密度滑块。
//   ⛔ 不点任何记录卡（会载入素材）、不点「批量操作」里任何会写数据的项。
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器, 开底栏, 关面板, 量浮层 } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFO1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const 独占 = ['暂无历史记录'];

const 浏览器 = await launch();
const page = 浏览器.page;

/** 在当前页面上按可见文字找一枚可点元素，返回落点（并自证属主）。 */
const 找文字 = (词, { 限前缀 = false } = {}) => page.evaluate(([w, 前]) => {
  for (const el of document.querySelectorAll('button,[role="button"],[role="tab"],a')) {
    const t = (el.innerText || '').replace(/\s+/g, ' ').trim();
    if (前 ? !t.startsWith(w) : t !== w) continue;
    const r = el.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
    const hit = document.elementFromPoint(x, y);
    const hb = hit && hit.closest('button,[role="button"],[role="tab"],a');
    return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 点: [x, y], 命中: hb ? (hb.innerText || hb.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 24) : null, title: el.getAttribute('title'), aria: el.getAttribute('aria-label') };
  }
  return null;
}, [词, 限前缀]);

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 100));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);

  // ── ① 打开并把整个面板的结构逐条量出来 ──
  记('—— ① 打开生成历史 ——');
  断言(await 开底栏(page, '生成历史', { 记, 断言 }), '「生成历史」打开成功（落点自证通过）');
  let 文字 = await 全页文字(page);
  断言(文字.some((t) => t.includes('全部画布')) && 文字.includes('暂无历史记录'), '⭐ 面板确实打开了（阳性对照：独有文案在场）', 文字.length);
  R.读数.面板文字 = 文字;

  const 结构 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
    const 可见 = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const 控件 = [];
    for (const el of document.querySelectorAll('button,[role="button"],[role="tab"],[role="slider"],input')) {
      if (!可见(el)) continue;
      const r = el.getBoundingClientRect();
      if (r.y < 60 || r.y > 400) continue;   // 只要标题栏 + 筛选栏那一段
      const cs = getComputedStyle(el);
      控件.push({
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        文字: 归(el.innerText).slice(0, 24),
        aria: el.getAttribute('aria-label'),
        title: el.getAttribute('title'),
        role: el.getAttribute('role'),
        tag: el.tagName,
        bg: cs.backgroundColor,
        高亮: cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && cs.backgroundColor !== 'transparent',
      });
    }
    // 面板外壳
    const 壳 = [...document.querySelectorAll('div,section')]
      .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 600 && r.height > 300 && r.width < 1440 && r.height < 800 && el.innerText && el.innerText.includes('全部画布') && el.innerText.includes('暂无历史记录'); })
      .map((el) => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], class: String(el.className || '').slice(0, 120), z: cs.zIndex, position: cs.position }; })
      .sort((a, b) => (a.框[2] * a.框[3]) - (b.框[2] * b.框[3]))[0] || null;
    // 滑块（密度）
    const 滑 = [...document.querySelectorAll('input[type=range],[role="slider"]')].filter(可见).map((el) => {
      const r = el.getBoundingClientRect();
      return { tag: el.tagName, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], min: el.min, max: el.max, step: el.step, value: el.value, aria: el.getAttribute('aria-label'), ariaValueNow: el.getAttribute('aria-valuenow'), class: String(el.className || '').slice(0, 90) };
    });
    return { 控件, 壳, 滑 };
  });
  R.读数.结构 = 结构;
  记('   壳 ' + JSON.stringify(结构.壳));
  记('   滑块 ' + JSON.stringify(结构.滑));
  for (const c of 结构.控件) 记('   · ' + JSON.stringify(c));
  await page.screenshot({ path: EVID + 'fo1-01-生成历史-空态.png' });

  // ── ② 密度滑块：有没有刻度，能不能拖 ──
  记('—— ② 密度滑块 ——');
  if (结构.滑.length) {
    const s = 结构.滑[0];
    const 拖前 = await page.screenshot({ clip: { x: Math.max(0, s.框[0] - 90), y: s.框[1] - 12, width: s.框[2] + 180, height: s.框[3] + 24 }, path: EVID + 'fo1-02-密度滑块-前.png' });
    const 拖后 = [];
    for (const 目标 of [s.max, String((Number(s.min) + Number(s.max)) / 2), s.min]) {
      const r = s.框;
      const 比例 = (Number(目标) - Number(s.min)) / (Number(s.max) - Number(s.min) || 1);
      const x = Math.round(r[0] + 6 + (r[2] - 12) * 比例), y = Math.round(r[1] + r[3] / 2);
      await page.mouse.move(x, y);
      await page.mouse.down();
      for (let i = 1; i <= 10; i++) { await page.mouse.move(x, y + (i % 2)); await page.waitForTimeout(60); }
      await page.mouse.up();
      await page.waitForTimeout(1200);
      const v = await page.evaluate(() => { const el = document.querySelector('input[type=range],[role="slider"]'); return el ? { value: el.value, aria: el.getAttribute('aria-valuenow') } : null; });
      拖后.push({ 拖到: 目标, 读到: v });
    }
    R.读数.密度滑块 = { 滑: s, 拖后 };
    记('   拖动读数 ' + JSON.stringify(拖后));
    断言(new Set(拖后.map((d) => d.读到 && d.读到.value)).size > 1, '⭐ 密度滑块真的能改值（不是装饰）', 拖后);
  } else { 记('   ⛔ 没找到滑块'); 断言(false, '应该能找到密度滑块'); }
  await page.screenshot({ path: EVID + 'fo1-03-生成历史-拖过密度.png' });

  // ── ③ 所有评级 ▾：真下拉还是两态切换 ──
  记('—— ③ 所有评级 ——');
  const 评级 = await 找文字('所有评级', { 限前缀: true });
  记('   控件 ' + JSON.stringify(评级));
  if (评级) {
    await page.mouse.click(评级.点[0], 评级.点[1]);
    await page.waitForTimeout(1500);
    const 下拉 = await page.evaluate(() => {
      const 可见 = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
      const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
      const 层 = [...document.querySelectorAll('.mantine-Popover-dropdown,[role="listbox"]')].filter(可见).map((el) => { const r = el.getBoundingClientRect(); return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 项: [...el.querySelectorAll('*')].filter(可见).map((c) => 归(c.innerText)).filter((t) => t && t.length <= 8).slice(0, 20) }; });
      return 层;
    });
    R.读数.评级下拉 = 下拉;
    记('   下拉 ' + JSON.stringify(下拉));
    断言(下拉.length > 0 && 下拉[0].项.length >= 5, '⭐「所有评级」是真下拉，展开有 6 档', 下拉);
    await page.screenshot({ path: EVID + 'fo1-04-所有评级-六档.png' });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1200);
  }

  // ── ④ 时间倒序：两态切换 ──
  记('—— ④ 时间倒序 ——');
  const 排序 = await 找文字('时间倒序', { 限前缀: true });
  const 态 = [];
  for (let i = 0; i < 3; i++) {
    const c = await 找文字(i % 2 === 0 ? '时间倒序' : '时间正序', { 限前缀: true }) || await 找文字(i % 2 === 0 ? '时间倒序' : '时间正序');
    if (!c) break;
    态.push({ 第几轮: i + 1, 文字: c.文字, title: c.title, aria: c.aria });
    await page.mouse.click(c.点[0], c.点[1]);
    await page.waitForTimeout(1200);
  }
  R.读数.时间倒序 = 态;
  记('   三轮 ' + JSON.stringify(态));
  断言(态.length >= 2 && new Set(态.map((s) => s.title)).size >= 2, '⭐「时间倒序」是两态循环切换（看 title 里的「当前：…」）', 态);

  // ── ⑤ 全部画布 / 本画布 ──
  记('—— ⑤ 全部画布 / 本画布 ——');
  const 页签 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
    return [...document.querySelectorAll('button,[role="tab"]')].map((el) => {
      const t = 归(el.innerText);
      if (t !== '全部画布' && t !== '本画布') return null;
      const r = el.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) return null;
      return { 文字: t, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 底色: getComputedStyle(el).backgroundColor };
    }).filter(Boolean);
  });
  R.读数.页签 = 页签;
  记('   ' + JSON.stringify(页签));
  断言(页签.length === 2 && 页签[0].底色 !== 页签[1].底色, '⭐ 两个页签靠底色区分高亮', 页签);
  await page.screenshot({ path: EVID + 'fo1-05-页签高亮对照.png' });

  // ── ⑥ 批量操作 ──
  记('—— ⑥ 批量操作 ——');
  const 批量 = await 找文字('批量操作', { 限前缀: true });
  记('   ' + JSON.stringify(批量));
  if (批量) {
    await page.mouse.click(批量.点[0], 批量.点[1]);
    await page.waitForTimeout(1800);
    const 后 = await 量浮层(page, 'div');
    const 新层 = 后.filter((l) => l.文字 && l.文字.includes('批量'));
    R.读数.批量操作 = { 点前: 批量, 点后新层: 新层.slice(0, 3) };
    记('   点后疑似层 ' + JSON.stringify(新层.slice(0, 3)).slice(0, 500));
    await page.screenshot({ path: EVID + 'fo1-06-批量操作-点开.png' });
    await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  }

  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  R.读数.关面板 = { 成功: await 关面板(page, 独占, { 记, 断言 }) };
  记(`—— 共跑了 ${断言.统计.次数} 条断言，失败 ${断言.统计.失败} 条 ——`);
} catch (e) {
  记('❌ ' + (e && e.message ? e.message : String(e)));
} finally {
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
