// Batch EU-3：⭐⭐ **先把 EU-2 留下的状态残留修回去**，顺带用正确判据补完读数。
//
//   EU-2 的收尾读数：`隐藏节点连线` 的 `aria-label` **查不到了**
//   （关态是 `aria-label="隐藏节点连线"`，开了之后这个选择器就匹配不上）。
//   ⛔ 两种可能，EU-2 分不出来：① aria **改了名**（§289 说改成 `显示节点连线`）
//      ② aria **被整个删掉**。因为 `读底栏` 是**按名字查**的，查不到就返回 null。
//   ⇒ 判据缺陷：⛔ **「按 aria 查不到」不能推出「属性没了」**，只能说「这个名字没有」。
//      必须**枚举**底栏全部按钮，再逐个看它们的 aria / svg 数 / 背景。
//
//   本轮两件事：
//     ① ⭐ **先复原**：枚举底栏 → 找到那枚「当前是开态」的 → 点一次 → 再枚举确认复原。
//     ② 补完 A/B 读数：全程用「枚举」而不是「按名查」。
//
// ⛔ 只点「隐藏节点连线」这一枚（纯视图开关），不动别的。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEU3.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

/** ⭐ 枚举画布左下角那一排按钮（y 落在 750~805、x 落在 0~320 的那一段） */
const 枚举底栏 = (page) => page.evaluate(() => {
  const 出 = [];
  for (const e of document.querySelectorAll('button,[aria-label],[role="button"]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 14 || r.height < 14) continue;
    if (r.bottom < 740 || r.top > 810) continue;
    if (r.right > 340) continue;
    if (e.querySelector('button,[role="button"]')) continue;
    const cs = getComputedStyle(e);
    const svgs = [...e.querySelectorAll('svg')];
    出.push({
      tag: e.tagName,
      文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
      aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
      子数: e.children.length, svg数: svgs.length,
      svg路径: svgs.map(s => { const p = s.querySelector('path'); return p ? p.getAttribute('d').slice(0, 44) : '(无 path)'; }),
      背景: cs.backgroundColor, 边框: cs.borderColor, 边框宽: cs.borderTopWidth,
      cls: String(e.className).slice(0, 120),
    });
  }
  出.sort((a, b) => a.box[0] - b.box[0]);
  return 出;
});

/** 独立的第四种读数：画布上**真的有几条连线**（不依赖按钮属性） */
const 数连线 = (page) => page.evaluate(() => {
  const e = document.querySelectorAll('.react-flow__edge, .react-flow__edgepath, path.react-flow__edge-path');
  let 可见 = 0, 共 = e.length;
  for (const x of e) { const r = x.getBoundingClientRect(); if (r.width > 0 && r.height > 0) 可见++; }
  return { 共, 可见, 样本: [...e].slice(0, 3).map(x => { const r = x.getBoundingClientRect(); const cs = getComputedStyle(x); return { cls: String(x.className).slice(0, 34), 尺寸: [Math.round(r.width), Math.round(r.height)], 描边: cs.stroke, 不透明: cs.opacity, 可见性: cs.visibility }; }) };
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
  await page.waitForTimeout(3500);
  记(`开局坐标偏差：${JSON.stringify(await 核对坐标(page))}`);

  const 全 = {};
  const 打印 = (名, 栏) => {
    记(`　　【${名}】底栏 ${栏.length} 枚：`);
    for (const b of 栏) 记(`　　<${b.tag}> 「${b.文字}」 aria=${JSON.stringify(b.aria)} title=${JSON.stringify(b.title)} box=${JSON.stringify(b.box)} 子数=${b.子数} svg数=${b.svg数} 背景=${b.背景}`);
  };

  // ① 当前状态（继承自 EU-2 的残留）
  记('\n════ ① 当前状态（EU-2 留下的残留）════');
  const 栏0 = await 枚举底栏(page);
  打印('当前', 栏0);
  const 连0 = await 数连线(page);
  记(`　　⭐ 连线读数：${JSON.stringify(连0)}`);
  await page.screenshot({ path: EVID + 'eu3-底栏-当前态.png' });

  // ② 找出那枚「疑似开态」的
  const 找开态 = (栏) => 栏.filter(b => b.svg数 >= 2 || (b.aria && /显示/.test(b.aria)));
  const 开态们 = 找开态(栏0);
  记(`　　疑似开态的按钮：${JSON.stringify(开态们.map(b => ({ aria: b.aria, 文字: b.文字, svg数: b.svg数, 中心: b.中心, 路径: b.svg路径 })))}`);

  // ③ 点掉它复原
  for (const b of 开态们) {
    const 验 = await page.evaluate((c) => { const e = document.elementFromPoint(c[0], c[1]); return e ? `${e.tagName}.${String(e.className).slice(0, 34)}` : null; }, b.中心);
    记(`　　准备点 box=${JSON.stringify(b.box)} 中心 ${JSON.stringify(b.中心)}｜elementFromPoint 自证 ${JSON.stringify(验)}`);
    await page.mouse.click(b.中心[0], b.中心[1]);
    await page.waitForTimeout(1800);
    const 栏1 = await 枚举底栏(page);
    打印('点后', 栏1);
    const 连1 = await 数连线(page);
    记(`　　⭐ 连线读数：${JSON.stringify(连1)}`);
    await page.screenshot({ path: EVID + 'eu3-底栏-点后.png' });
    全.点后 = { 栏: 栏1, 连线: 连1 };
  }

  // ④ 再点一次拿反向的 A/B，然后复原
  const 栏2 = await 枚举底栏(page);
  const 反向 = 找开态(栏2);
  记(`\n════ ② 反向 A/B：再点一次拿另一态 ════`);
  记(`　　当前开态：${JSON.stringify(反向.map(b => ({ aria: b.aria, svg数: b.svg数, 路径: b.svg路径, 背景: b.背景 })))}`);
  for (const b of 反向) {
    await page.mouse.click(b.中心[0], b.中心[1]);
    await page.waitForTimeout(1800);
    const 栏3 = await 枚举底栏(page);
    打印('再点后', 栏3);
    全.再点后 = { 栏: 栏3, 连线: await 数连线(page) };
    记(`　　⭐ 连线读数：${JSON.stringify(全.再点后.连线)}`);
    await page.screenshot({ path: EVID + 'eu3-底栏-再点后.png' });
    // 复原：再点一次
    const 栏4 = await 枚举底栏(page);
    const 仍开 = 找开态(栏4);
    for (const c of 仍开) { await page.mouse.click(c.中心[0], c.中心[1]); await page.waitForTimeout(1600); }
    const 栏5 = await 枚举底栏(page);
    全.复原 = { 栏: 栏5, 连线: await 数连线(page) };
    打印('复原后', 栏5);
    记(`　　⭐⭐ 复原后连线读数：${JSON.stringify(全.复原.连线)}`);
    记(`　　⭐⭐ 复原后仍有开态的：${JSON.stringify(找开态(栏5).map(x => x.aria))}（应为空）`);
  }
  if (!反向.length) 记('　　（当前没有开态按钮，无需再点）');

  记('\n✅ 完成（只点纯视图开关，已复原）');
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  try {
    记('⏳ ⌘0 复位 + 静置 15s…');
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(15000);
    const 现 = await 读全部坐标(page);
    const 真动 = Object.keys(坐标).filter(id => 现[id] && (Math.abs(现[id][0] - 坐标[id][0]) > 1.5 || Math.abs(现[id][1] - 坐标[id][1]) > 1.5));
    记(`⭐ 真的被移动：${真动.length} 个 ${JSON.stringify(真动)}`);
  } catch (e) { console.error(e); }
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEU3.json ===');
}
