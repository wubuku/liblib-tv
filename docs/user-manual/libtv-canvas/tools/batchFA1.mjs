// Batch FA-1：⭐⭐⭐ 节点参数条上三枚「没有名字」的控件，像素坐标到底可不可复现？
//
// 手册 PROGRESS 未验清单里挂着这一条：
//   「节点参数条上三枚『没有名字』的控件（`⤢` 箭头 / `⚙` 滑块）的像素坐标不可复现」。
//
// ⚠️ 先分清两件不同的事，混起来就会得出「不可复现」的错结论：
//   ① **`⤢` 根本不在参数条上** —— 它压在参数卡片的右上角，28×28；
//      参数条上的按钮全是 32×32（手册 create-nodes.md 已写死）。
//   ② 真正待测的是**同一枚控件的框，在「选中 A → 取消 → 选中 A → 选中 B → 回 A」
//      这四轮里是否逐字相同**。
//
// 本轮判据：**同一个节点连读两轮**（同会话、不动任何东西）先立基线，
// 再跨「取消重选」「换节点」「换回来」三轮复测。
// ⭐ 每一轮都按 **path `d` 的前 40 字符**认同一枚控件 ——
//   只按「x 坐标」认会把两枚长得一样的 `32×32` 认串。
//
// ⛔ 只点节点本体（选中/取消选中），不点参数条上任何控件，不动任何参数。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchFA1.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const A = 'v-v2hlWY4Br3';   // 视频节点（参数条最复杂）
const B = 'i-sODTbgLUm1';   // 图片节点

const 浏览器 = await launch();
const page = 浏览器.page;

/**
 * 选中节点的参数卡片里所有按钮：框 + aria + 文字 + path 指纹。
 * ⚠️ 第一版写成 `const 参数条 = () => page.evaluate(浏览器函数, null)`，
 *    调用处又套了一层 `page.evaluate(参数条, A)` ——
 *    等于**把 Node 侧函数塞进浏览器**，报 `page is not defined`。
 *    ⇒ 浏览器函数就直接交给 `page.evaluate(fn, arg)`，不要再包一层箭头。
 */
const 参数条 = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  // ⭐ 不在这里 return「未选中」就完事 —— 那样只会得到一个不知道原因的 0。
  //   节点刚被点选时 `.selected` 明明在，稍后再读又没了 ⇒ **先把类名和全页选中集一起报出来**。
  const 选中集 = [...document.querySelectorAll('.react-flow__node.selected')].map((x) => x.getAttribute('data-id'));
  // 参数卡片 = 选中节点内部、含工具按钮的那一层
  const 按钮 = [];
  for (const b of n.querySelectorAll('button, [role=button], [class*="cursor-pointer"]')) {
    const r = b.getBoundingClientRect();
    if (r.width < 10 || r.height < 10) continue;
    if (r.width > 420 || r.height > 420) continue;
    const svg = b.querySelector('svg');
    按钮.push({
      aria: b.getAttribute('aria-label'),
      title: b.getAttribute('title'),
      文字: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 16),
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      svg数: svg ? 1 : 0,
      path: (b.querySelector('path')?.getAttribute('d') || '').slice(0, 40),
      图形: [...(b.querySelectorAll('svg *') || [])].map((e) => e.tagName.toLowerCase()).join('+').slice(0, 30),
      tag: b.tagName.toLowerCase(),
    });
  }
  const 卡 = n.getBoundingClientRect();
  return {
    存在: true, 选中: n.classList.contains('selected'),
    类名: (n.className || '').toString(),
    全页选中: 选中集,
    节点框: [Math.round(卡.left), Math.round(卡.top), Math.round(卡.width), Math.round(卡.height)],
    按钮数: 按钮.length, 按钮,
  };
}, id);

/** ⭐⭐⭐ 悬停某枚控件，读它有没有气泡 —— 同时留一枚已知会响应的做阳性对照 */
const 悬停读气泡 = async (box, 标签) => {
  const p = [Math.round(box[0] + box[2] / 2), Math.round(box[1] + box[3] / 2)];
  await page.mouse.move(p[0], p[1]);
  await page.waitForTimeout(1300);
  const 出 = await page.evaluate(() => [...document.querySelectorAll('[class*="mantine-Tooltip-tooltip"], [role=tooltip]')]
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 4 && r.height > 4 && parseFloat(getComputedStyle(e).opacity) > 0.5; })
    .map((e) => { const r = e.getBoundingClientRect(); return { 文字: (e.innerText || '').trim().slice(0, 40), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }; }));
  记(`    悬停【${标签}】→ 气泡 ${JSON.stringify(出)}`);
  await page.mouse.move(720, 250);
  await page.waitForTimeout(600);
  return 出;
};

const 选中 = async (id) => {
  // ⭐⭐ 第一版只点「节点上缘 +14px」这一个位置，点完就往下走，
  //   结果后面读到的参数条说「未选中」——**点完必须立刻自证选上了没有**。
  //   `elementFromPoint` 只证明「点在那张卡上」，不证明「点出了选中」。
  const 点位 = await page.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return {
      上缘: [Math.round(r.left + r.width / 2), Math.round(r.top + 14)],
      中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
      下缘: [Math.round(r.left + r.width / 2), Math.round(r.bottom - 20)],
      框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
    };
  }, id);
  if (!点位) throw new Error('节点 ' + id + ' 没渲染');
  let 成的 = null;
  for (const 键 of ['上缘', '中心', '下缘']) {
    const p = 点位[键];
    const v = await page.evaluate(([x, y]) => {
      const e = document.elementFromPoint(x, y);
      const n = e ? e.closest('.react-flow__node') : null;
      return { id: n && n.getAttribute('data-id'), tag: e && e.tagName, cls: e && (e.className || '').toString().slice(0, 30) };
    }, p);
    if (v.id && v.id !== id) { 记(`    落点【${键}】被 ${v.id} 挡住，跳过`); continue; }
    if (!v.id) 记(`    落点【${键}】在空白上（id=null），可以点`);
    await page.mouse.move(p[0], p[1]); await page.waitForTimeout(380);
    await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(950);
    await page.mouse.move(720, 250); await page.waitForTimeout(600);
    const 选中态 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map((n) => n.getAttribute('data-id')));
    记(`    落点【${键}】点击后 .selected = ${JSON.stringify(选中态)}`);
    if (选中态.includes(id)) { 成的 = 键; break; }
    // 没选中就再点一次把它切回去（点选是开关）
    await page.mouse.move(p[0], p[1]); await page.waitForTimeout(350);
    await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(700);
    await page.mouse.move(720, 250); await page.waitForTimeout(400);
  }
  if (!成的) throw new Error('点了三个落点都没把 ' + id + ' 选上');
  记(`  ✅ ${id} 用【${成的}】选中（节点框 ${JSON.stringify(点位.框)}）`);
  return 成的;
};

const 取消选中 = async () => {
  await page.mouse.move(720, 700);
  await page.waitForTimeout(400);
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(900);
  await page.mouse.move(720, 250);
  await page.waitForTimeout(500);
  const 剩 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map((n) => n.getAttribute('data-id')));
  return 剩;
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));
  const 渲染 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  记('渲染节点：' + JSON.stringify(渲染));
  if (!渲染.includes(A) || !渲染.includes(B)) throw new Error('A/B 有一个没渲染：' + JSON.stringify(渲染));

  // ---------- 轮 1 / 轮 2：同一节点连读两次（同会话、不动任何东西）----------
  记('—— 轮 1/2：选中 ' + A + '，连读两次 ——');
  await 选中(A);
  const r1 = await 参数条(A);
  const r2 = await 参数条(A);
  if (!r1) throw new Error('轮 1 读不到节点');
  记(`  轮 1：选中=${r1.选中}｜全页选中=${JSON.stringify(r1.全页选中)}｜类名="${(r1.类名 || '').slice(0, 80)}"`);
  记(`  参数条 ${r1.按钮数} 枚按钮；节点框 ${JSON.stringify(r1.节点框)}`);
  const 同一 = JSON.stringify(r1.按钮) === JSON.stringify(r2.按钮);
  记(`  ⭐ 同节点连读两次，逐字相同？ ${同一}`);
  if (!同一) {
    for (let i = 0; i < r1.按钮.length; i++) {
      if (JSON.stringify(r1.按钮[i]) !== JSON.stringify(r2.按钮[i])) 记(`    差异 #${i}：${JSON.stringify(r1.按钮[i])} → ${JSON.stringify(r2.按钮[i])}`);
    }
  }
  结果.读数.轮1 = r1; 结果.读数.轮2 = r2; 结果.读数.同节点两次相同 = 同一;

  // 三枚无名控件：无 aria、无 title、无文字
  const 无名 = r1.按钮.filter((b) => !b.aria && !b.title && !b.文字);
  记(`  ⭐ 三枚候选（无 aria / 无 title / 无文字）：${无名.length} 枚`);
  for (const b of 无名) 记(`     box=${JSON.stringify(b.box)} svg=${b.svg数} 图形=${b.图形} path="${b.path}"`);

  // ---------- 悬停气泡 + 阳性对照 ----------
  if (无名.length) {
    记('  —— 逐枚悬停找气泡 ——');
    for (const b of 无名) await 悬停读气泡(b.box, `无名 path="${b.path.slice(0, 16)}…"`);
    const 有名 = r1.按钮.find((b) => b.aria || b.文字);
    if (有名) { 记('  —— ⭐ 阳性对照：悬停一枚有名字的 ——'); await 悬停读气泡(有名.box, `「${有名.aria || 有名.文字}」`); }
  }

  // ---------- 轮 3：取消 → 重选 ----------
  记('—— 轮 3：取消选中 → 重选 ——');
  const 剩 = await 取消选中();
  记('  取消后仍选中：' + JSON.stringify(剩));
  await 选中(A);
  const r3 = await 参数条(A);
  记(`  轮 3 与轮 1 逐字相同？ ${JSON.stringify(r1.按钮) === JSON.stringify((r3 || {}).按钮)}`);
  结果.读数.轮3 = r3;

  // ---------- 轮 4：换成图片节点 B ----------
  记('—— 轮 4：换选图片节点 ' + B + ' ——');
  // ⭐ 必须先取消选中：选中视频节点时它的参数卡会展开，**盖住图 B 的上缘和中心**
  //    （第一版连着三个落点全被 v-v2hlWY4Br3 挡住）。
  await 取消选中();
  await 选中(B);
  const r4 = await 参数条(B);
  if (r4 && r4.按钮数) {
    记(`  图片节点参数条 ${r4.按钮数} 枚；节点框 ${JSON.stringify(r4.节点框)}`);
    const 无名4 = r4.按钮.filter((b) => !b.aria && !b.title && !b.文字);
    记(`  图片节点上的无名控件：${无名4.length} 枚`);
    for (const b of 无名4) 记(`     box=${JSON.stringify(b.box)} 图形=${b.图形} path="${b.path}"`);
    结果.读数.轮4 = r4;
  } else {
    记('  ⛔ 图片节点没弹出参数条');
  }

  // ---------- 轮 5：回到 A ----------
  记('—— 轮 5：换回视频节点 ' + A + ' ——');
  await 选中(A);
  const r5 = await 参数条(A);
  记(`  轮 5 与轮 1 逐字相同？ ${JSON.stringify(r1.按钮) === JSON.stringify((r5 || {}).按钮)}`);
  结果.读数.轮5 = r5;
  if (r5 && r5.按钮数) {
    await page.screenshot({ path: EVID + 'fa1-参数条-无名控件.png' });
    记('  已拍 fa1-参数条-无名控件.png');
    if (无名.length) {
      const b = 无名[无名.length - 1];
      await page.screenshot({ path: EVID + 'fa1-最后一枚无名控件特写.png', clip: { x: b.box[0] - 60, y: b.box[1] - 40, width: 180, height: 110 } });
      记('  已拍 fa1-最后一枚无名控件特写.png');
    }
  }

  await 取消选中();
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
  console.log('\n=== 已写 tools/batchFA1.json ===');
}
