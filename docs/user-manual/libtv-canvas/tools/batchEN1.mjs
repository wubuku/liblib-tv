// Batch EN-1：结掉那条 📖 ——「`当前使用` 在画布节点参数条上长什么样」。
//
//   手册现状（20-reference.md）把 `currentlyInUse` 判成「两个用法」：
//     ① `✧` 悬停出的**模型清单**里，当前行右侧画一枚对勾
//     ② **卡面左下角**的白底徽标
//   ⛔ 但这两处**都不在节点参数条上**。节点参数条上有一个模型下拉
//      （`Lib Image 2.5 Pro ⌄`），它**点开之后当前选中的那一行有没有标记**，
//      一直没人查。
//
// ⛔ 本脚本只**打开下拉并读取**，不点任何一行（不换模型、不触发生成）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEN1.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

// ⭐ 枚举行：把所有「看起来像浮层里的一行」的元素按面积升序列出来，
//    从最小的开始 —— 菜单项可能是 button 也可能是 div（§283 法 + 给「项的类型」留退路）
const 枚举行 = (page) => page.evaluate(() => {
  const 出 = [];
  const 见过 = new Set();
  for (const e of document.querySelectorAll('body *')) {
    const r = e.getBoundingClientRect();
    if (r.width < 30 || r.width > 900 || r.height < 8 || r.height > 200) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 60) continue;
    // 只看有边框/背景/圆角这类「像可点项」的
    const cs = getComputedStyle(e);
    const 像项 = cs.cursor === 'pointer' || cs.borderRadius !== '0px' || /solid|hidden/.test(cs.borderTopStyle);
    if (!像项) continue;
    // 叶子优先：没有子元素也带同样文本的
    const 有子同文 = [...e.children].some(c => (c.innerText || '').replace(/\s+/g, ' ').trim() === t);
    if (有子同文) continue;
    const k = t + '|' + Math.round(r.left) + '|' + Math.round(r.top);
    if (见过.has(k)) continue; 见过.add(k);
    const attrs = {}; for (const a of e.attributes) attrs[a.name] = a.value;
    出.push({
      tag: e.tagName,
      文本: t.slice(0, 50),
      cls: String(e.className || '').slice(0, 90),
      attrs,
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      面积: Math.round(r.width * r.height),
      cursor: cs.cursor,
      ariaSelected: e.getAttribute('aria-selected'),
      ariaChecked: e.getAttribute('aria-checked'),
      role: e.getAttribute('role'),
      有勾: /M20 6 9|check|Check/i.test([...e.querySelectorAll('path')].map(p => p.getAttribute('d') || '').join(' ')),
      svgs: [...e.querySelectorAll('svg')].map(s => String(s.className && s.className.baseVal || '').slice(0, 30) + '|' + (s.querySelector('path')?.getAttribute('d') || '').slice(0, 22)),
      img数: e.querySelectorAll('img').length,
    });
  }
  出.sort((a, b) => a.面积 - b.面积);
  return 出;
});

const 全视口找字 = (page, 词) => page.evaluate((w) => {
  const 命中 = [];
  for (const e of document.querySelectorAll('body *')) {
    if ((e.innerText || '').includes(w)) {
      const r = e.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      const 有子同文 = [...e.children].some(c => (c.innerText || '').includes(w));
      if (有子同文) continue;
      命中.push({ tag: e.tagName, cls: String(e.className || '').slice(0, 70), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
    }
  }
  return 命中;
}, 词);

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
  记(`开局坐标偏差：${JSON.stringify(await 核对坐标(page))}`);

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
  记(`铁律②复核落点 ${JSON.stringify(落点)}`);
  await page.mouse.click(落点[0], 落点[1]);
  await page.waitForTimeout(2600);
  const 选中 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  记(`选中 ${JSON.stringify(选中)}`);
  if (选中.length !== 1 || 选中[0] !== 被测) throw new Error('选中对象不对');

  // ---- 底栏两枚下拉的读数（关着的时候）
  const 底栏 = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) return [];
    const 出 = [];
    for (const b of n.querySelectorAll('button')) {
      const r = b.getBoundingClientRect();
      if (r.top < 600 || r.top > 700) continue;
      const t = (b.innerText || '').replace(/\s+/g, ' ').trim();
      if (!t) continue;
      const attrs = {}; for (const a of b.attributes) attrs[a.name] = a.value;
      出.push({ 文字: t, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], attrs, svg: [...b.querySelectorAll('path')].map(p => (p.getAttribute('d') || '').slice(0, 26))[0] || '' });
    }
    return 出;
  }, 被测);
  记(`\n底栏两枚下拉（关闭态）：`);
  for (const b of 底栏) 记(`　「${b.文字}」 box=${JSON.stringify(b.box)} 中心=${JSON.stringify(b.中心)} svg=${b.svg} 非class属性=${Object.keys(b.attrs).filter(k => k !== 'class').join(',')}`);
  结果.读数.底栏 = 底栏;

  // ---- ⭐ 阳性对照：确认这个页面上「找得到浮层里的行」这件事本身可行
  const 阳性试 = await page.evaluate(() => {
    // 随便找个已知的短文本，验证「按文字能定位到元素」这条链是通的
    const 探 = [...document.querySelectorAll('body *')].filter(e => (e.innerText || '').trim() === '资产管理');
    return 探.length;
  });
  记(`\n⭐ 阳性对照：「资产管理」精确文本命中 ${阳性试} 个元素（证明按文字定位这条链通）`);

  for (const [i, 下拉] of 底栏.entries()) {
    const 名 = `下拉${i + 1}-${下拉.文字.replace(/\s+/g, '_').slice(0, 24)}`;
    记(`\n———— 打开「${下拉.文字}」 ————`);
    await page.mouse.click(下拉.中心[0], 下拉.中心[1]);
    await page.waitForTimeout(1600);
    await page.screenshot({ path: EVID + `en1-${名}-打开.png` });

    const 顶 = await page.evaluate((p) => { const e = document.elementFromPoint(p[0], p[1]); return e ? e.tagName + '.' + String(e.className).slice(0, 40) : 'null'; }, 下拉.中心);
    记(`　点击处最上层元素：${顶}`);

    const 行 = await 枚举行(page);
    记(`　⭐ 浮层候选「行」${行.length} 条（按面积升序，只列叶子项）：`);
    for (const r of 行) {
      记(`　　<${r.tag}> box=${JSON.stringify(r.box)} 面积=${r.面积} 光标=${r.cursor} role=${r.role || '—'} aria-selected=${r.ariaSelected || '—'}`);
      记(`　　　文本「${r.文本}」｜有勾=${r.有勾} img=${r.img数}｜非class属性=${Object.keys(r.attrs).filter(k => k !== 'class').join(',') || '（无）'}`);
      if (r.svgs.length) 记(`　　　svg：${JSON.stringify(r.svgs)}`);
    }
    结果.读数[名] = 行;

    const 找当前使用 = await 全视口找字(page, '当前使用');
    记(`　⭐ 全视口找「当前使用」字样：${找当前使用.length} 个 ${JSON.stringify(找当前使用)}`);
    结果.读数[名 + '_当前使用'] = 找当前使用;

    // 面板容器的完整读数
    const 面板 = await page.evaluate(() => {
      const 出 = [];
      for (const e of document.querySelectorAll('body *')) {
        const r = e.getBoundingClientRect();
        if (r.width < 100 || r.height < 60 || r.width > 900 || r.height > 900) continue;
        const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
        if (!t || t.length < 4) continue;
        const cs = getComputedStyle(e);
        if (cs.position !== 'absolute' && cs.position !== 'fixed') continue;
        if (+cs.zIndex < 20) continue;
        出.push({ tag: e.tagName, 文本条数: t.length, 文本前: t.slice(0, 90), cls: String(e.className).slice(0, 80), z: cs.zIndex, pos: cs.position, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
      }
      出.sort((a, b) => (b.文本前.length - a.文本前.length));
      return 出.slice(0, 6);
    });
    记(`　浮层面板（position 非 static 且 z≥20）候选：`);
    for (const p of 面板) 记(`　　<${p.tag}> z=${p.z} ${p.pos} box=${JSON.stringify(p.box)} 文本「${p.文本前}」 cls=${p.cls}`);
    结果.读数[名 + '_面板'] = 面板;

    await page.screenshot({ path: EVID + `en1-${名}-近景.png`, clip: { x: 400, y: 200, width: 900, height: 560 } });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1200);
  }
  记('\n✅ 两个下拉都读完了（未点任何一行）');
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
    记(`⭐ 收尾核对坐标：${JSON.stringify(真动)}`);
  } catch (e) { console.error(e); }
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEN1.json ===');
}
