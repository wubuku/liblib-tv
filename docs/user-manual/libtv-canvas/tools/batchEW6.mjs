// Batch EW-6：⭐⭐⭐ 「新功能：支持真人」的**归属**：换节点看它跟不跟着走。
//
// EW-5 的决定性发现：**指针在 y=30 那一整排移动时它都在**，扫了 6 个点全命中。
//   ⇒ ⭐⭐ **它根本不是悬停气泡**。Mantine 的 Tooltip 组件被挂在「常开」状态，
//      一旦挂载就一直显示。**前面几轮「逐枚悬停去试」全部白试 ——
//      因为悬停根本不是它的开关。**
//
// EW-5 顺带扫出画布上另外三枚真·悬停气泡（未选中时就有）：
//   「添加节点」触发点 (584,758) → 元素框 [580,757,32,32]
//   「移动」    触发点 (640,758) → 元素框 [620,757,32,32]
//   「手动生成」触发点 (1256,758) → 元素框 [1231,740,32,32]
//   （第三枚的元素框和触发点对不上，说明那个点上还叠着别的东西，下一轮核）
//
// 本轮只回答一个问题：**它属于谁？**
//   选中 A 节点 → 记它、参数面板、节点卡、模型按钮、参数条 五个框
//   换成 B 节点 → 再记一遍
//   ⭐ **谁跟着节点变，就是它的主人。** 谁都不动，它就是固定元素。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEW6.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

/** 一次量齐所有相关框 */
const 量 = (page) => page.evaluate(() => {
  const 框 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; };
  const 找文字 = (t) => {
    for (const e of document.querySelectorAll('*')) {
      if (e.children.length) continue;
      if ((e.textContent || '').trim() === t) return e;
    }
    return null;
  };
  const 出 = {};
  // ① 那个 tooltip
  for (const e of document.querySelectorAll('[class*="mantine-Tooltip-tooltip"]')) {
    if ((e.innerText || '').trim() === '新功能：支持真人') {
      if (parseFloat(getComputedStyle(e).opacity) >= 0.5) { 出.气泡 = 框(e); break; }
    }
  }
  // ② 选中的节点卡
  const sel = document.querySelector('.react-flow__node.selected, .react-flow__node[aria-selected="true"]');
  if (sel) 出.选中节点 = { id: sel.getAttribute('data-id'), box: 框(sel) };
  // ③ 参数面板：按它自己的标题文字找，不用猜 class
  const 面板锚 = 找文字('描述你想要生成的画面内容');
  if (面板锚) {
    出.面板锚 = 框(面板锚);
    // 往上爬到面板根：找包含它、且宽度最大的祖先
    let p = 面板锚.parentElement, 最好 = 面板锚;
    for (let i = 0; i < 10 && p; i++) {
      const r = p.getBoundingClientRect();
      if (r.width > 240 && r.height > 120) 最好 = p;
      p = p.parentElement;
    }
    出.面板 = 框(最好);
  }
  // ④ 参数条上的模型按钮（形如「2.0 ⌄」或带金色小标的那个）
  const 参数条 = [];
  for (const e of document.querySelectorAll('button,[role="button"]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 20 || r.width > 260 || r.height < 20 || r.height > 60) continue;
    if (r.bottom < 300) continue;                       // 只看画布中下部
    if (r.left < 300) continue;
    参数条.push({ 文字: (e.innerText || '').trim().slice(0, 24), aria: e.getAttribute('aria-label'), box: 框(e), svg数: e.querySelectorAll('svg').length });
  }
  出.参数条 = 参数条;
  // ⑤ 视口内所有节点（算间距用）
  出.节点 = [...document.querySelectorAll('.react-flow__node')].map((n) => ({ id: n.getAttribute('data-id'), 文字: (n.innerText || '').trim().split('\n')[0].slice(0, 14), box: 框(n) }))
    .filter((n) => n.box[0] + n.box[2] > 0 && n.box[0] < 1440);
  return 出;
});

const 点 = async (page, id) => {
  const p = await page.evaluate((nid) => {
    const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + 14)];
  }, id);
  if (!p) return { ok: false, 原因: '不在视口' };
  // ⭐ 落点自证 + 被谁挡住
  const 验 = await page.evaluate(([x, y, nid]) => {
    const e = document.elementFromPoint(x, y);
    const n = e ? e.closest('.react-flow__node') : null;
    return { 落点: n ? n.getAttribute('data-id') : null, 正确: !!(n && n.getAttribute('data-id') === nid), 元素: e ? e.tagName + '.' + String(e.className).slice(0, 40) : null };
  }, [p[0], p[1], id]);
  if (!验.正确) return { ok: false, 点: p, 被挡: 验 };
  await page.mouse.click(p[0], p[1]);
  await page.waitForTimeout(2500);
  return { ok: true, 点: p, 验 };
};

const 浏览器 = await launch();
const page = 浏览器.page;
try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  const 表 = {};
  const 候选 = ['v-v2hlWY4Br3', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'a-THmbuJXQj4', 'i-sODTbgLUm1', 't-UtVx3lZmrV', 'b-mfkcQNULC3', 'n-56F19pXVB4'];

  for (const id of 候选) {
    await page.mouse.click(40, 700);                 // 先取消选中
    await page.waitForTimeout(900);
    const r = await 点(page, id);
    if (!r.ok) { 记(`✗ ${id}：点不到（${r.被挡 ? '被 ' + r.被挡.落点 + ' 挡住' : r.原因}）`); continue; }
    const m = await 量(page);
    表[id] = m;
    记(`✓ ${id} 选中｜气泡=${JSON.stringify(m.气泡)} 面板=${JSON.stringify(m.面板)} 节点卡=${JSON.stringify(m.选中节点 && m.选中节点.box)}`);
    if (m.气泡 && m.面板) {
      记(`     气泡相对面板左上 = [${m.气泡[0] - m.面板[0]}, ${m.气泡[1] - m.面板[1]}]`);
    }
  }
  结果.读数.表 = 表;

  // 逐节点对比：谁在动
  const 有泡 = Object.keys(表).filter((k) => 表[k].气泡);
  记('⭐ 有气泡的节点：' + JSON.stringify(有泡));
  const 泡位 = 有泡.map((k) => [k, 表[k].气泡]);
  记('⭐ 气泡位置：' + JSON.stringify(泡位));
  const 泡动 = new Set(泡位.map((x) => JSON.stringify(x[1])));
  记('⭐ 气泡位置的不同取值个数 = ' + 泡动.size + '（1 = 完全固定，多 = 跟着节点走）');
  const 面板动 = new Set(有泡.map((k) => JSON.stringify(表[k].面板)));
  记('⭐ 面板位置的不同取值个数 = ' + 面板动.size);
  结果.读数.汇总 = { 有泡, 泡位, 泡动取值数: 泡动.size, 面板动取值数: 面板动.size };

  // 参数条明细（只在视频节点选中那组里看）
  if (表['v-v2hlWY4Br3']) {
    记('参数条明细：' + JSON.stringify(表['v-v2hlWY4Br3'].参数条, null, 1));
  }

  await page.mouse.click(40, 700);
  await page.waitForTimeout(1200);
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
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchEW6.json ===');
}
