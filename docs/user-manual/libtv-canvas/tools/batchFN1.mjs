// ⭐⭐⭐⭐⭐ Batch FN-1：重跑「文案 ↔ 界面」对账，这次**把 FM 的判据缺陷修成脚本断言**
//
// FM 算出 1/747 = 0.1% 的命中率，但那是**判据失效**不是真实覆盖率：
//   · 面板是 `w-max` 横向撑开的 5904px 容器，我只抓了可视的一小块
//   · 阳性对照（截图里明明有那两个标签）当场否掉了判据
//
// ⭐ 本轮三处修正，每一处都写成**脚本里的断言**，不再靠人眼：
//   ① **不挑容器，直接全页 dump**（`document.body`）—— 根除「挑错容器」这类失效
//   ② **横向滚动那个面板**再 dump，把屏幕外的角色卡也扫进来
//   ③ ⭐ **断言**：`断言(文字数 >= 阈值, 'dump 到的文字太少，判据可能又失效了')`
//      —— 数字不对就地停下，不让它变成一个「看起来很权威」的假结论
//
// ⭐ 顺带做三件事（都在这一轮里，零风险）：
//   · 对账 `characterStudio*`
//   · 对账**全量** 8189 条，给出手册的真实覆盖率
//   · 扫另外两个底栏面板（`生成历史` / `素材库`），给手册补读数
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, readFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFN1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

// ⭐⭐⭐ 断言：数字不对就地停，不让它变成「看起来很权威」的假结论（FM 缺陷 445/447）
let 断言次数 = 0;
const 断言 = (条件, 说明, 数据) => {
  断言次数++;
  if (!条件) throw new Error('断言失败：' + 说明 + (数据 !== undefined ? '｜数据 ' + JSON.stringify(数据) : ''));
  记('   ✅ 断言通过：' + 说明);
};

const i18n = JSON.parse(readFileSync(EVID + 'i18n-canvas.json', 'utf8'));
const 全表 = i18n.表;

const 浏览器 = await launch();
const page = 浏览器.page;

/** ⭐ 修正①：全页 dump，不再挑容器 */
const 全页文字 = () => page.evaluate(() => {
  const 可见 = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return false;
    const cs = getComputedStyle(el);
    return cs.visibility !== 'hidden' && cs.display !== 'none' && Number(cs.opacity) > 0.01;
  };
  const 集 = new Set();
  for (const el of document.querySelectorAll('body *')) {
    if (!可见(el)) continue;
    for (const n of el.childNodes) {
      if (n.nodeType === 3) { const t = (n.textContent || '').replace(/\s+/g, ' ').trim(); if (t) 集.add(t); }
    }
    for (const a of ['aria-label', 'title', 'placeholder', 'alt']) {
      const v = (el.getAttribute && el.getAttribute(a)) || '';
      if (v && v.trim()) 集.add(v.trim());
    }
  }
  return [...集];
});

/** ⭐ 修正②：把横向撑开的容器滚一遍 */
const 横滚 = async () => {
  const 目标 = await page.evaluate(() => {
    let best = null, bestW = 0;
    for (const el of document.querySelectorAll('div,section')) {
      const r = el.getBoundingClientRect();
      if (r.width > bestW && r.width > window.innerWidth * 1.5) { bestW = r.width; best = el; }
    }
    if (!best) return null;
    return { 宽: Math.round(bestW), 可滚: best.scrollWidth, 当前: Math.round(best.scrollLeft), class: (best.className || '').toString().slice(0, 60) };
  });
  if (!目标) { 记('   （没有宽度超视口 1.5 倍的容器，跳过横滚）'); return null; }
  记(`   横滚目标：宽 ${目标.宽}px｜scrollWidth ${目标.可滚}｜class ${目标.class}`);
  const 收集 = new Set();
  for (let i = 0; i < 6; i++) {
    await page.mouse.move(900, 400);
    await page.mouse.wheel(1200, 0);
    await page.waitForTimeout(700);
    for (const w of await 全页文字()) 收集.add(w);
  }
  记(`   横滚 6 次后累计可见文字 ${收集.size} 条`);
  return [...收集];
};

const 归一 = (s) => s.replace(/[\s　]+/g, '');

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 100));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);

  const 开底栏 = async (aria) => {
    const b = await page.evaluate((a) => {
      for (const x of document.querySelectorAll('button')) {
        if ((x.getAttribute('aria-label') || '') === a) {
          const r = x.getBoundingClientRect();
          if (r.width > 0 && r.top > 700) return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
        }
      }
      return null;
    }, aria);
    if (!b) return false;
    await page.mouse.click(b[0], b[1]);
    await page.waitForTimeout(4000);
    return true;
  };

  // ——— ① 角色造型室 ———
  记('—— ① 角色造型室 ——');
  断言(await 开底栏('角色造型室'), '「角色造型室」按钮能打开');
  let 文字 = await 全页文字();
  记(`   全页 dump：${文字.length} 条`);
  // ⭐⭐ 断言③：FM 就是栽在这里（18 条）。低于 40 就当判据失效。
  断言(文字.length >= 40, '全页 dump 到的文字数够（≥40），判据没失效', 文字.length);
  const 横滚后 = await 横滚();
  if (横滚后) 文字 = [...new Set([...文字, ...横滚后])];
  记(`   ⭐ 合并后可见文字 ${文字.length} 条`);

  const 界面归一 = new Set(文字.map(归一));
  const 角色清单 = Object.entries(全表).filter(([k]) => k.startsWith('characterStudio'));
  const 角色命中 = 角色清单.filter(([, v]) => 界面归一.has(归一(v)));
  记(`⭐ characterStudio* 命中率：${角色命中.length} / ${角色清单.length} = ${(100 * 角色命中.length / 角色清单.length).toFixed(1)}%`);
  for (const [k, v] of 角色命中.slice(0, 30)) 记('   ✅ ' + k + ' = ' + v);
  R.读数.角色对账 = { 文字数: 文字.length, 清单: 角色清单.length, 命中: 角色命中.length, 命中率: Number((100 * 角色命中.length / 角色清单.length).toFixed(1)), 命中样本: 角色命中.slice(0, 25) };
  await page.screenshot({ path: EVID + 'fn1-01-角色造型室-横滚后.png' });

  // ——— ② 全量 8189 条对账 ———
  记('—— ② 全量 8189 条对账（只对这一个面板的状态）——');
  const 全命中 = Object.entries(全表).filter(([, v]) => 界面归一.has(归一(v)));
  记(`   ⭐ 全表命中 ${全命中.length} / ${Object.keys(全表).length} = ${(100 * 全命中.length / Object.keys(全表).length).toFixed(2)}%`);
  R.读数.全表对账 = { 命中: 全命中.length, 总数: Object.keys(全表).length };

  // ——— ③ 顺带扫另外两个底栏面板 ———
  for (const [名, aria] of [['生成历史', '生成历史'], ['素材库', '素材库']]) {
    记(`—— ③ 扫「${名}」——`);
    if (!(await 开底栏(aria))) { 记('   ⛔ 打不开'); continue; }
    const w = await 全页文字();
    断言(w.length >= 12, `「${名}」dump 到的文字数够（≥12）`, w.length);
    记(`   可见文字 ${w.length} 条`);
    const 集 = new Set(w.map(归一));
    const 本组 = Object.entries(全表).filter(([k, v]) => new RegExp('^(' + aria + '|' + ({ 生成历史: 'history', 素材库: 'asset|material' }[名]) + ')', 'i').test(k));
    const 命 = 本组.filter(([, v]) => 集.has(归一(v)));
    记(`   ⭐ ${名} 组命中率：${命.length} / ${本组.length}`);
    for (const [k, v] of 命.slice(0, 20)) 记('      ✅ ' + k + ' = ' + v);
    R.读数[名] = { 文字数: w.length, 清单: 本组.length, 命中: 命.length, 命中样本: 命.slice(0, 15), 界面文字样本: w.slice(0, 25) };
    await page.screenshot({ path: EVID + `fn1-02-${名}.png` });
    await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  }
  记(`—— 共跑了 ${断言次数} 条断言，全部通过 ——`);
} catch (e) {
  记('❌ ' + (e && e.message ? e.message : String(e)));
} finally {
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
