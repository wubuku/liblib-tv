// ⭐⭐⭐⭐⭐ Batch FY-4：下拉项的点击**根本没切换画布** —— 查落点，别再盲点
//
// FY-3 的读数自证失败：点了「画布 3/4/5/6」之后
//   URL 仍是主画布的 projectId=34226ef1…，节点数恒为 12
// ⇒ ⛔ **根本没切换过去。** 而 FY-3 当时**只记了结果、没记落点自证**
//    ⇒ 又是一次「以为点了、其实没点」（缺陷 496 的变种）。
//
// ⭐ 关键疑点：FY-3 读下拉项时用的是
//   `if (e.children.length) continue;`  —— 只看**叶子节点**，
//   然后取 `e.getBoundingClientRect()` 的中心去点。
//   ⛔ 叶子节点可能**只有文字那一小块**，点上去不一定命中整行。
//
// 本轮只做一件事：把「画布 3」那一行的**完整结构**读出来
// （外层容器、内层、每个子元素的框），再决定点哪里。
// ⛔ 纯读，不点。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFY4.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(主画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6000);
  await closePromos(page);
  await page.waitForTimeout(4000);

  记('--- 打开项目下拉 ---');
  await page.mouse.click(200, 24);
  await page.waitForTimeout(1600);
  await page.screenshot({ path: resolve(EVID, 'fy4-1-下拉开着.png') });

  // ⭐ 把「画布 3」这一行从上到下的整条祖先链读出来
  记('\n--- 「画布 3」这一行的完整祖先链 ---');
  const 链 = await page.evaluate(() => {
    let 目标 = null;
    for (const e of document.querySelectorAll('*')) {
      if (e.children.length) continue;
      if ((e.innerText || '').trim() !== '画布 3') continue;
      const r = e.getBoundingClientRect();
      if (r.width < 20 || r.x < 100) continue;
      目标 = e; break;
    }
    if (!目标) return { 错: '没找到「画布 3」的叶子节点' };
    const o = [];
    let p = 目标;
    for (let i = 0; i < 7 && p; i++) {
      const r = p.getBoundingClientRect();
      const cs = getComputedStyle(p);
      o.push({ 层级: i, tag: p.tagName, cls: (p.className || '').toString().slice(0, 90),
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        文: (p.innerText || '').trim().slice(0, 30), 子数: p.children.length,
        cursor: cs.cursor, pointerEvents: cs.pointerEvents,
        中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] });
      p = p.parentElement;
    }
    return { 链: o };
  });
  R.读数.祖先链 = 链;
  if (链.错) { 记(`  ⛔ ${链.错}`); }
  else {
    链.链.forEach((h) => 记(`   L${h.层级} <${h.tag}> ${h.框.join(',')} cursor=${h.cursor} pe=${h.pointerEvents} 子${h.子数} 文「${h.文}」\n       cls=${h.cls}`));

    // ⭐ 逐层做 elementFromPoint，看点哪一层才真的落在这一行上
    记('\n--- 逐层落点自证：点每一层的中心，看命中什么 ---');
    for (const h of 链.链) {
      const 落 = await page.evaluate(({ x, y }) => {
        const e = document.elementFromPoint(x, y);
        if (!e) return null;
        // 往上找，看这一行的祖先里有没有它
        let p = e, 归属 = [];
        for (let i = 0; i < 8 && p; i++) {
          归属.push(`${p.tagName}.${(p.className || '').toString().slice(0, 34)}`);
          p = p.parentElement;
        }
        return { tag: e.tagName, 文: (e.innerText || '').trim().slice(0, 20), 归属 };
      }, { x: h.中心[0], y: h.中心[1] });
      const 属于本行 = 落 && 落.文.includes('画布 3');
      记(`   点 L${h.层级} 中心(${h.中心.join(',')}) → ${落 ? `${落.tag}「${落.文}」` : 'null'} ${属于本行 ? '✅ 落在本行' : '⛔ 不在本行'}`);
    }
  }

  // ⭐ 换一个思路：看这行有没有「真正可点」的祖先（带 onClick 的 React 组件
  //    在 DOM 上通常表现为 role / tabindex / cursor:pointer）
  记('\n--- 这一行里带 role / tabindex / cursor:pointer 的元素 ---');
  const 可点 = await page.evaluate(() => {
    const o = [];
    for (const e of document.querySelectorAll('[role], [tabindex], [data-project-id], [data-id]')) {
      const r = e.getBoundingClientRect();
      if (r.width < 20 || r.x < 100 || r.x > 700) continue;
      if (r.y < 30 || r.y > 700) continue;
      const t = (e.innerText || '').trim();
      if (!/^画布/.test(t) || t.length > 12) continue;
      o.push({ tag: e.tagName, 文: t, role: e.getAttribute('role'), tabindex: e.getAttribute('tabindex'),
        dataId: e.getAttribute('data-id'), projectId: e.getAttribute('data-project-id'),
        cls: (e.className || '').toString().slice(0, 70),
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
    }
    return o;
  });
  R.读数.可点元素 = 可点;
  记(`  ${可点.length} 个：`);
  可点.forEach((e) => 记(`   <${e.tag}> 「${e.文}」 role=${e.role} tabindex=${e.tabindex} data-id=${e.dataId} ${e.框.join(',')}\n       cls=${e.cls}`));
  if (!可点.length) 记('  ⛔ 这一行没有任何 role/tabindex/data-* 标记 ⇒ 可能真的只是个文本列表');

  await page.screenshot({ path: resolve(EVID, 'fy4-2-末态.png') });
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFY4.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
