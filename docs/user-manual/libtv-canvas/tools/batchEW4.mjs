// Batch EW-4：⭐⭐⭐ 决定性 A/B/C/D —— 「新功能：支持真人」到底跟着谁走。
//
// EW-3 拿到了三条硬事实：
//   ① 它是 `div.m_1b3c8819.mantine-Tooltip-tooltip`，`[541,191,114,27]`，
//      `pointer-events: none`、`opacity: 1` —— **是显示着的，不是残留的壳**。
//   ② 它的**父容器 box = `[0, 810, 1440, 0]`** —— y 正好是视口高度、自身零高
//      ⇒ 这是 Mantine 的 **portal 挂到 `body` 的浮层容器**，不是面板的子元素。
//   ③ 水平方向最近的元素是 **`导演台` 节点 `n-56F19pXVB4`**，间距**正好 58**。
//
// ⛔ **ET 记的「在参数面板左侧 58px」据此判为巧合**：本轮实测参数面板在 `x=1033`，
//    面板左缘减 58 是 975，而那个东西在 **541**，差 492。**58 这个数对的是「导演台」节点。**
//
// 本轮做四组对照，**每组只换一个变量**：
//   A 什么都不选   B 选视频节点   C 选导演台节点   D 选音频节点
// 读两件事：**它在不在**、**它在哪个坐标**。
// 位置跟着谁走，就是谁的。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEW4.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

/** ⭐ 全页找这个气泡：按文字找，并把它连同最近的几个元素一起报出来 */
const 探针 = (page) => page.evaluate(() => {
  let 命中 = null;
  for (const e of document.querySelectorAll('*')) {
    const t = (e.innerText || '').trim();
    if (t !== '新功能：支持真人') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    命中 = {
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      cls: String(e.className),
      html: e.outerHTML.slice(0, 700),
      父box: (() => { const p = e.parentElement; if (!p) return null; const q = p.getBoundingClientRect(); return [Math.round(q.left), Math.round(q.top), Math.round(q.width), Math.round(q.height)]; })(),
      祖先: (() => { const a = []; let p = e.parentElement, i = 0; while (p && i < 4) { a.push(String(p.className).slice(0, 60) || p.tagName); p = p.parentElement; i++; } return a; })(),
    };
    break;
  }
  // 顺便报「此刻哪些节点在视口内、各自的框」，用来算间距
  const 节点 = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const r = n.getBoundingClientRect();
    if (r.right < 0 || r.left > innerWidth || r.bottom < 0 || r.top > innerHeight) continue;
    节点.push({ id: n.getAttribute('data-id'), 文字: (n.innerText || '').trim().split('\n')[0].slice(0, 20), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
  }
  return { 命中, 节点, 节点数: 节点.length };
});

const 点节点 = async (page, id) => {
  const p = await page.evaluate((nid) => {
    const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + 18)];
  }, id);
  if (!p) return { 成功: false, 原因: '节点不在视口' };
  const 验 = await page.evaluate(([x, y, nid]) => {
    const n = document.elementFromPoint(x, y)?.closest('.react-flow__node');
    return n ? n.getAttribute('data-id') : null;
  }, [p[0], p[1], id]);
  if (验 !== id) return { 成功: false, 原因: '落点被挡，落点=' + 验 };
  await page.mouse.click(p[0], p[1]);
  await page.waitForTimeout(2500);
  return { 成功: true, 点: p, 落点自证: 验 };
};

const browser = await launch();
const page = browser.page;
try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));
  const 基线变换 = await page.evaluate(() => {
    const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform);
    return m ? m[1] : null;
  });
  记('基线变换：' + 基线变换);

  const 四组 = {};

  // A 什么都不选
  await page.mouse.move(1200, 200);
  await page.waitForTimeout(1200);
  四组.A_未选中 = await 探针(page);
  记('A 未选中：' + JSON.stringify({ 命中: !!四组.A_未选中.命中, box: 四组.A_未选中.命中?.box }));

  // B 选视频节点
  记('B 点视频：' + JSON.stringify(await 点节点(page, 'v-v2hlWY4Br3')));
  四组.B_选视频 = await 探针(page);
  记('B 选视频：' + JSON.stringify({ box: 四组.B_选视频.命中?.box, 节点: 四组.B_选视频.节点.map((n) => n.id) }));

  // ⭐ 取消选中（点空白）
  await page.mouse.click(60, 690);
  await page.waitForTimeout(1500);
  四组.B2_取消选中 = await 探针(page);
  记('B2 取消选中：' + JSON.stringify({ 命中: !!四组.B2_取消选中.命中, box: 四组.B2_取消选中.命中?.box }));

  // C 选导演台节点
  const c点 = await page.evaluate((id) => {
    const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + 18)];
  }, 'n-56F19pXVB4');
  记('导演台点击点：' + JSON.stringify(c点));
  if (c点) {
    const 验c = await page.evaluate(([x, y, id]) => {
      const n = document.elementFromPoint(x, y)?.closest('.react-flow__node');
      return n ? n.getAttribute('data-id') : null;
    }, [c点[0], c点[1], 'n-56F19pXVB4']);
    记('导演台落点自证：' + 验c);
    if (验c === 'n-56F19pXVB4') {
      await page.mouse.click(c点[0], c点[1]);
      await page.waitForTimeout(2500);
      四组.C_选导演台 = await 探针(page);
      记('C 选导演台：' + JSON.stringify({ box: 四组.C_选导演台.命中?.box }));
    } else {
      四组.C_选导演台 = { 命中: null, 原因: '落点被挡：' + 验c };
    }
  }

  // D 选音频节点
  await page.mouse.click(60, 690);
  await page.waitForTimeout(1200);
  const d点 = await page.evaluate((id) => {
    const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + 18)];
  }, 'a-THmbuJXQj4');
  记('音频点击点：' + JSON.stringify(d点));
  if (d点) {
    const 验d = await page.evaluate(([x, y, id]) => {
      const n = document.elementFromPoint(x, y)?.closest('.react-flow__node');
      return n ? n.getAttribute('data-id') : null;
    }, [d点[0], d点[1], 'a-THmbuJXQj4']);
    记('音频落点自证：' + 验d);
    if (验d === 'a-THmbuJXQj4') {
      await page.mouse.click(d点[0], d点[1]);
      await page.waitForTimeout(2500);
      四组.D_选音频 = await 探针(page);
      记('D 选音频：' + JSON.stringify({ box: 四组.D_选音频.命中?.box }));
    } else {
      四组.D_选音频 = { 命中: null, 原因: '落点被挡：' + 验d };
    }
  }

  // ⭐ 全文扫一遍：所有 Mantine tooltip 此刻都在哪、各自文字
  const 全部气泡 = await page.evaluate(() => {
    const 出 = [];
    for (const e of document.querySelectorAll('[class*="mantine-Tooltip-tooltip"]')) {
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      出.push({ 文字: (e.innerText || '').trim().slice(0, 30), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], opacity: cs.opacity, transform: cs.transform });
    }
    return 出;
  });
  记('此刻全页气泡：' + JSON.stringify(全部气泡));
  结果.读数.全部气泡 = 全部气泡;

  // 悬停试验：把指针放到导演台节点上，看气泡文字会不会变
  记('—— 悬停试验 ——');
  await page.mouse.click(60, 690);
  await page.waitForTimeout(1200);
  const 导台框 = 四组.A_未选中.节点.find((n) => n.id === 'n-56F19pXVB4');
  if (导台框) {
    await page.mouse.move(导台框.box[0] + 导台框.box[2] / 2, 导台框.box[1] + 10);
    await page.waitForTimeout(1500);
    const 悬停后 = await 探针(page);
    记('悬停导演台标题栏后：' + JSON.stringify({ box: 悬停后.命中?.box, 文字: 悬停后.命中?.box }));
    const 气泡2 = await page.evaluate(() => [...document.querySelectorAll('[class*="mantine-Tooltip-tooltip"]')].map((e) => ({ t: (e.innerText || '').trim().slice(0, 30), o: getComputedStyle(e).opacity })));
    记('  气泡列表：' + JSON.stringify(气泡2));
    结果.读数.悬停导演台 = 悬停后;
    结果.读数.悬停导演台气泡 = 气泡2;
  } else {
    记('⛔ 导演台节点不在视口内，跳过悬停试验');
  }

  结果.读数.四组 = 四组;

  // 收尾
  await page.mouse.click(60, 690);
  await page.waitForTimeout(1500);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差, 已渲染: Object.keys(await 读全部坐标(page)).length };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await browser.browser.close();
  console.log('\n=== 已写 tools/batchEW4.json ===');
}
