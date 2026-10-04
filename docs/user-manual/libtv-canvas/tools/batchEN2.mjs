// Batch EN-2：把 EN-1 看见的两种「选中态」用 CSS 读数钉死。
//   EN-1 肉眼看到：模型下拉里当前那行底色更亮；参数面板里选中项是白色描边。
//   但「更亮」「白描边」都得给出可复现的读数，否则手册只能写一句模糊的话。
//
// ⭐ 判据要点：**不能只找一个「特别的那一个」** ——
//   要把每一项的样式都读出来，按「样式值的分组」看谁和谁不同，
//   再核对那个「不同」的文本 == 触发按钮上显示的摘要文字，两头对上才算结案。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEN2.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

// 模型下拉：把所有行连同样式读出来
const 读模型行 = (page) => page.evaluate(() => {
  const 出 = [];
  for (const e of document.querySelectorAll('body *')) {
    const r = e.getBoundingClientRect();
    // 行 = 宽约 302、高 36 或 64（选中行多一行描述）
    if (r.width < 250 || r.width > 400) continue;
    if (r.height < 30 || r.height > 90) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 70) continue;
    const cs = getComputedStyle(e);
    // 必须是可点的行
    if (cs.cursor !== 'pointer') continue;
    const 子图 = e.querySelectorAll('img').length;
    出.push({
      文本: t,
      高度: Math.round(r.height),
      背景: cs.backgroundColor,
      边框: cs.borderColor + ' / ' + cs.borderWidth,
      圆角: cs.borderRadius,
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      ariaSelected: e.getAttribute('aria-selected'),
      role: e.getAttribute('role'),
      图标块: 子图,
      含勾: /M20 6 9|check/i.test([...e.querySelectorAll('path')].map(p => p.getAttribute('d') || '').join(' ')),
      cls: String(e.className).slice(0, 80),
    });
  }
  return 出;
});

// 参数面板：按标题分组读每一项的样式
const 读面板 = (page) => page.evaluate(() => {
  // 找到那个 Mantine Popover
  let 面板 = null;
  for (const e of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(e);
    if (!/Popover-dropdown|popover/i.test(String(e.className))) continue;
    const r = e.getBoundingClientRect();
    if (r.width > 100 && r.height > 100) { 面板 = e; break; }
  }
  if (!面板) return null;
  const 分组 = [];
  let 当前 = null;
  for (const e of 面板.querySelectorAll('*')) {
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    const cs = getComputedStyle(e);
    const 是项 = cs.cursor === 'pointer' && r.height >= 20 && r.height <= 90 && t && t.length <= 8;
    if (是项) {
      const 项 = {
        文本: t, 分组: 当前 ? 当前.标题 : null,   // ⭐ 存标题字符串；存对象会构成循环引用，JSON.stringify 直接崩
        背景: cs.backgroundColor, 边框色: cs.borderColor, 边框宽: cs.borderWidth,
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        ariaPressed: e.getAttribute('aria-pressed'),
        ariaChecked: e.getAttribute('aria-checked'),
        dataAttrs: [...e.attributes].filter(a => a.name.startsWith('data-')).map(a => a.name + '=' + a.value).join(' ') || '（无）',
      };
      if (当前) 当前.项.push(项); else 分组.push({ 标题: '（无标题）', 项: [项] });
    } else if (t && t.length <= 8 && r.height < 40 && r.width < 200 && cs.fontWeight >= 500 && !/button/.test(e.tagName.toLowerCase())) {
      当前 = { 标题: t, 项: [] };
      分组.push(当前);
    }
  }
  return { 面板框: (() => { const r = 面板.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })(), 分组 };
});

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 7000 });
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === '知道了'); if (b) b.click(); });
  await page.waitForTimeout(800);
  await page.evaluate(() => {
    const 条 = [...document.querySelectorAll('div')].filter(d => /开启浏览器通知/.test(d.innerText || ''));
    if (条.length) { 条.sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width); const btn = [...条[条.length - 1].querySelectorAll('button')].find(b => (b.innerText || '').trim() === ''); if (btn) btn.click(); }
  });
  await page.waitForTimeout(700);
  await page.evaluate(() => { for (const b of document.querySelectorAll('button')) if (b.getAttribute('aria-label') === '关闭' && b.getBoundingClientRect().width < 40) { b.click(); return; } });
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3200);

  const 被测 = 'i-sODTbgLUm1';
  const 落点 = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    for (let i = 1; i < 10; i++) for (let j = 1; j < 10; j++) {
      const x = Math.round(r.left + r.width * i / 10), y = Math.round(r.top + r.height * j / 10);
      const e = document.elementFromPoint(x, y);
      const g = e && e.closest('.react-flow__node');
      if (g && g.getAttribute('data-id') === id) return [x, y];
    }
    return null;
  }, 被测);
  await page.mouse.click(落点[0], 落点[1]);
  await page.waitForTimeout(2600);

  const 按钮 = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    const 出 = [];
    for (const b of n.querySelectorAll('button')) {
      const r = b.getBoundingClientRect();
      if (r.top < 600 || r.top > 700) continue;
      const t = (b.innerText || '').replace(/\s+/g, ' ').trim();
      if (!t) continue;
      出.push({ 文字: t, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] });
    }
    return 出;
  }, 被测);
  记(`两枚下拉触发器：${JSON.stringify(按钮.map(b => b.文字))}`);

  // ---- 模型下拉
  记('\n———— 模型下拉：每行的样式读数 ————');
  await page.mouse.click(按钮[0].中心[0], 按钮[0].中心[1]);
  await page.waitForTimeout(1800);
  const 模型行 = await 读模型行(page);
  记(`读到 ${模型行.length} 行`);
  // 按「背景色」分组，找众数组和异类
  const 按背景 = {};
  for (const r of 模型行) (按背景[r.背景] ||= []).push(r.文本.slice(0, 26));
  记('⭐ 按 background-color 分组：');
  for (const [k, v] of Object.entries(按背景)) 记(`　${k} → ${v.length} 行：${JSON.stringify(v)}`);
  const 异类 = Object.entries(按背景).filter(([k, v]) => v.length === 1);
  记(`⭐ 唯一的「异类」组：${JSON.stringify(异类)}`);
  记(`⭐ 触发按钮上的文字是「${按钮[0].文字}」⇒ ${异类.length === 1 && 异类[0][1][0].startsWith(按钮[0].文字) ? '✅ 对得上' : '❌ 对不上'}`);
  记(`⭐ 含勾的行：${JSON.stringify(模型行.filter(r => r.含勾).map(r => r.文本.slice(0, 20)))}`);
  记(`⭐ 有 aria-selected / role=option 的行：${JSON.stringify(模型行.filter(r => r.ariaSelected || r.role === 'option').map(r => [r.文本.slice(0, 18), r.ariaSelected, r.role]))}`);
  记(`⭐ 行高分组：${JSON.stringify(模型行.reduce((m, r) => (m[r.高度] = (m[r.高度] || 0) + 1, m), {}))}`);
  记(`⭐ 图标块数量分组：${JSON.stringify(模型行.reduce((m, r) => (m[r.图标块] = (m[r.图标块] || 0) + 1, m), {}))}`);
  结果.读数.模型行 = 模型行;
  await page.screenshot({ path: EVID + 'en2-模型下拉-样式.png' });
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1200);

  // ---- 参数面板
  记('\n———— 参数面板：逐组逐项的样式读数 ————');
  await page.mouse.click(按钮[1].中心[0], 按钮[1].中心[1]);
  await page.waitForTimeout(1800);
  const 面板 = await 读面板(page);
  if (!面板) { 记('⛔ 没找到 Popover 面板'); }
  else {
    记(`面板框 ${JSON.stringify(面板.框)}，读到 ${面板.分组.length} 组`);
    for (const g of 面板.分组) {
      const 组读 = g.项.length ? [...new Set(g.项.map(x => `${x.边框色}|${x.边框宽}|${x.背景}`))] : [];
      记(`　【${g.标题}】${g.项.length} 项｜样式种类 ${组读.length}：${JSON.stringify(组读)}`);
      for (const it of g.项) {
        const 异 = 组读.findIndex(s => s === `${it.边框色}|${it.边框宽}|${it.背景}`);
        记(`　　「${it.文本}」 边框=${it.边框色} ${it.边框宽} 背景=${it.背景} 样式组#${异} ${异 === 0 ? '' : '⭐'} aria-pressed=${it.ariaPressed || '—'} data=${it.dataAttrs}`);
      }
    }
    结果.读数.面板 = 面板;
    await page.screenshot({ path: EVID + 'en2-参数面板-样式.png' });
  }
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1200);
  记('\n✅ 完成（未点任何一项，没有换过模型/参数）');
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  try {
    记('⏳ ⌘0 复位 + 静置 15s（三铁律③）…');
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(15000);
    const 现 = await 读全部坐标(page);
    const 真动 = Object.keys(坐标).filter(id => 现[id] && (Math.abs(现[id][0] - 坐标[id][0]) > 1.5 || Math.abs(现[id][1] - 坐标[id][1]) > 1.5));
    记(`⭐ 真的被移动：${真动.length} 个 ${JSON.stringify(真动)}`);
  } catch (e) { console.error(e); }
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEN2.json ===');
}
