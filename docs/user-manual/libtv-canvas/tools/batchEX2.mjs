// Batch EX-2：⭐⭐ 两条待验的小结论，顺手做掉。
//
// ① **「置灰的按钮不出悬停气泡」** —— EX-1 扫 TV Director 面板顶排时，
//    7 枚里读出 5 枚气泡，**唯独缺手册标注为「灰」的那两枚**
//    （`新对话无法分享`、`TV Director 全局设置`）。
//    ⇒ 要验：它们确实在扫描区域里、确实处于禁用态、悬停确实不出气泡。
//    ⭐ 顺带把「置灰」的三种读法并排量一遍（`disabled` / `aria-disabled` / 视觉态），
//       因为本项目早就吃过「只看 disabled 就判可用性」的亏。
//
// ② **开关翻开时，悬停气泡的文案跟不跟着改？** —— EU 批已知
//    `隐藏节点连线` 的 `aria-label` 会改名 ⇄ `显示节点连线`，
//    但**气泡文案**从来没读过。两者是不同来源，值得单独一问。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEX2.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

const 读气泡 = (page) => page.evaluate(() => {
  const 出 = [];
  for (const e of document.querySelectorAll('[class*="mantine-Tooltip-tooltip"]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    if (parseFloat(getComputedStyle(e).opacity) < 0.5) continue;
    出.push({ 文字: (e.innerText || '').trim().slice(0, 40), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
  }
  return 出;
});

const 找按钮 = (page, 文) => page.evaluate((t) => {
  for (const e of document.querySelectorAll('button,[role="button"]')) {
    if ((e.getAttribute('aria-label') || '') !== t) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    const cs = getComputedStyle(e);
    return {
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
      disabled: e.disabled === true, ariaDisabled: e.getAttribute('aria-disabled'),
      不透明: cs.opacity, 光标: cs.cursor, pointerEvents: cs.pointerEvents,
      背景: cs.backgroundColor,
    };
  }
  return null;
}, 文);

try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      const t = (b.innerText || '').trim();
      if (t === '知道了' || t === '开启') { try { b.click(); } catch (e) {} }
    }
  });
  await page.waitForTimeout(1500);
  await page.mouse.move(20, 20);
  await page.waitForTimeout(800);

  // ════════ ① 两枚「灰」按钮：状态 + 悬停有没有气泡 ════════
  // 需要 TV Director 抽屉开着才有这两枚；先看在不在
  const 在不在 = await page.evaluate(() => {
    const 出 = [];
    for (const e of document.querySelectorAll('button')) {
      const a = e.getAttribute('aria-label') || '';
      if (!/新对话无法分享|TV Director 全局设置|当前已是新对话|停靠到右侧/.test(a)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 8) continue;
      const cs = getComputedStyle(e);
      出.push({ aria: a, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], disabled: e.disabled === true, ariaDisabled: e.getAttribute('aria-disabled'), 不透明: cs.opacity, 光标: cs.cursor, pointerEvents: cs.pointerEvents, 背景: cs.backgroundColor });
    }
    return 出;
  });
  记('TV Director 顶排相关按钮（抽屉未开时）：' + JSON.stringify(在不在, null, 1));
  结果.读数.抽屉未开 = 在不在;

  if (在不在.length) {
    for (const b of 在不在) {
      const c = [Math.round(b.box[0] + b.box[2] / 2), Math.round(b.box[1] + b.box[3] / 2)];
      await page.mouse.move(c[0], c[1]);
      await page.waitForTimeout(900);
      const 泡 = await 读气泡(page);
      记(`  悬停「${b.aria}」 disabled=${b.disabled} ariaDisabled=${b.ariaDisabled} opacity=${b.不透明} cursor=${b.光标} → 气泡=${JSON.stringify(泡)}`);
      (结果.读数.逐枚 ||= []).push({ aria: b.aria, 状态: b, 气泡: 泡 });
    }
  } else {
    记('⛔ 抽屉没开，这两枚不在 DOM 里 —— 本轮不测这条；先开抽屉');
    // 打开 TV Director 抽屉
    const d = await page.evaluate(() => {
      const e = document.querySelector('[data-guide-target="agent-entry"]');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
    });
    记('TV Director 入口 ' + JSON.stringify(d));
    if (d) {
      await page.mouse.click(d[0], d[1]);
      await page.waitForTimeout(2500);
      const 在2 = await page.evaluate(() => {
        const 出 = [];
        for (const e of document.querySelectorAll('button')) {
          const a = e.getAttribute('aria-label') || '';
          if (!/新对话无法分享|TV Director 全局设置|当前已是新对话|历史对话|LibTV Plugin|停靠到右侧|关闭/.test(a)) continue;
          const r = e.getBoundingClientRect();
          if (r.width < 8) continue;
          const cs = getComputedStyle(e);
          出.push({ aria: a, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], disabled: e.disabled === true, ariaDisabled: e.getAttribute('aria-disabled'), 不透明: cs.opacity, 光标: cs.cursor, 背景: cs.backgroundColor });
        }
        return 出;
      });
      记('抽屉打开后：' + JSON.stringify(在2, null, 1));
      结果.读数.抽屉打开 = 在2;
      结果.读数.逐枚 = [];
      for (const b of 在2) {
        const c = [Math.round(b.box[0] + b.box[2] / 2), Math.round(b.box[1] + b.box[3] / 2)];
        await page.mouse.move(c[0], c[1]);
        await page.waitForTimeout(900);
        const 泡 = await 读气泡(page);
        记(`  悬停「${b.aria}」 disabled=${b.disabled} ariaDisabled=${b.ariaDisabled} opacity=${b.不透明} cursor=${b.光标} → 气泡=${JSON.stringify(泡)}`);
        结果.读数.逐枚.push({ aria: b.aria, 状态: b, 气泡: 泡 });
      }
      await page.screenshot({ path: EVID + 'ex2-TVDirector顶排.png' });
      记('已拍 ex2-TVDirector顶排.png');
      // 关抽屉
      const c2 = await 找按钮(page, '关闭');
      if (c2) { await page.mouse.click(c2.中心[0], c2.中心[1]); await page.waitForTimeout(1500); }
    }
  }

  // ════════ ② 开关翻开时气泡文案跟不跟着改 ════════
  // 锁定：按「底栏按 left 排序取索引」+ aria 交叉验
  const 定位 = async () => {
    const 栏 = await page.evaluate(() => {
      const out = [];
      for (const e of document.querySelectorAll('button')) {
        const r = e.getBoundingClientRect();
        if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
        if (e.querySelector('button')) continue;
        out.push({ aria: e.getAttribute('aria-label'), 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], box: Math.round(r.left), svg数: e.querySelectorAll('svg').length });
      }
      out.sort((a, b) => a.box - b.box);
      return out;
    });
    const 枚 = 栏.find((b) => b.svg数 === 1 || b.svg数 === 2);
    return 栏, 枚;
  };
  const [栏, 枚] = await 定位();
  记('底栏：' + JSON.stringify(栏.map((b) => ({ a: b.aria, svg: b.svg数, left: b.box }))));
  if (枚) {
    记('锁定枚 ' + JSON.stringify(枚));
    // 关态气泡
    await page.mouse.move(枚.中心[0], 枚.中心[1]);
    await page.waitForTimeout(1100);
    const 关泡 = await 读气泡(page);
    记('关态气泡：' + JSON.stringify(关泡));
    // 点开
    await page.mouse.down(); await page.mouse.up();
    await page.waitForTimeout(1100);
    await page.mouse.move(700, 300); await page.waitForTimeout(600);
    const [, 枚2] = await 定位();
    记('点开后枚：' + JSON.stringify(枚2));
    // 开态气泡（枚2 中心应与枚相同，因为是同一枚）
    await page.mouse.move(枚2.中心[0], 枚2.中心[1]);
    await page.waitForTimeout(1100);
    const 开泡 = await 读气泡(page);
    记('⭐ 开态气泡：' + JSON.stringify(开泡));
    结果.读数.开关气泡 = { 关态: { aria: 枚.aria, 气泡: 关泡 }, 开态: { aria: 枚2.aria, 气泡: 开泡 } };
    // 点回去
    await page.mouse.down(); await page.mouse.up();
    await page.waitForTimeout(1100);
    await page.mouse.move(700, 300); await page.waitForTimeout(600);
    const [, 枚3] = await 定位();
    记('复原枚：' + JSON.stringify(枚3));
    结果.读数.复原 = 枚3;
  }

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
  console.log('\n=== 已写 tools/batchEX2.json ===');
}
