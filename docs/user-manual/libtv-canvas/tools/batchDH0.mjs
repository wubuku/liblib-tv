// Batch DH-0：`z-[180]` 这个常驻空层**到底是什么**。
//
// DG 已经坐实：它在**基线**里（刚进页面就在，`[0,0,1440,810]`、`pointer-events-none`、
// `opacity: 0`、**直接子元素 0 个**），戳 4 个动作都不变。⇒ 不是「等触发」。
//
// 本轮换个思路：**不问「它什么时候亮」，问「它是什么」** ——
//   ① 打它的**完整 class**（此前只截了前 80 字符，关键信息可能在后半段）；
//   ② 打它的**计算样式全表**里的 `transition-*` —— class 里有 `motion-safe:transition-opacity`，
//      ⭐ **说明它是被动画驱动的**，那么「谁给它加/去某个 class」就是突破口；
//   ③ 用 `getAnimations()` 看它身上**有没有正在跑/挂着的动画**，以及动画的 target；
//   ④ ⭐ 找**它的兄弟节点** —— 一个全屏透明层通常有个兄弟负责「有内容时」的状态；
//   ⑤ ⭐ **全页 CSS 规则**里搜有没有选择器命中它（class 名可能出现在样式表里，
//      那里常有注释或变量名泄露用途）。
//   ⑥ 它**在 body 的哪一层**：父链 + 父的子元素清单。
//
// ⚠️ 不写盘、不点它（`pointer-events-none` 本身也点不到）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = {};

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
await page.waitForTimeout(1500);
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2800);
for (let i = 0; i < 3; i += 1) {
  const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(600);
}
const pk = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
  if (!b) return null; const r = b.getBoundingClientRect();
  return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
});
if (pk) { await page.mouse.click(pk[0], pk[1]); await page.waitForTimeout(1200); }

// ---------- A 它是什么 ----------
out.层 = await page.evaluate(() => {
  const target = [...document.querySelectorAll('body *')].find((e) => {
    const s = getComputedStyle(e);
    return s.position === 'fixed' && s.zIndex === '180' && e.getBoundingClientRect().width > 1000;
  });
  if (!target) return { 找到: false };
  const r = target.getBoundingClientRect();
  const s = getComputedStyle(target);
  // ⭐ 完整 class
  const cls = (target.className || '').toString();
  const parts = cls.split(/\s+/);
  // ⭐ 计算样式里所有 transition / animation / 自定义属性
  const 过渡 = {}; const 动画 = {}; const 变量 = {};
  for (const k of Object.keys(s)) {
    if (k.startsWith('transition')) 过渡[k] = s.getPropertyValue(k);
    else if (k.startsWith('animation')) 动画[k] = s.getPropertyValue(k);
    else if (k.startsWith('--')) 变量[k] = s.getPropertyValue(k);
  }
  // ⭐ 动画对象
  let 动画们 = [];
  try {
    动画们 = target.getAnimations().map((a) => ({
      状态: a.playState, 类型: a.constructor?.name || '',
      目标: a.effect?.target ? `${a.effect.target.tagName.toLowerCase()}.${(a.effect.target.className || '').toString().slice(0, 40)}` : null,
      关键帧数: a.effect?.getKeyframes ? a.effect.getKeyframes().length : null,
    }));
  } catch (e) { 动画们 = [{ 错误: String(e).slice(0, 80) }]; }
  // ⭐ 父链
  const 父链 = [];
  for (let p = target, i = 0; p && i < 6; p = p.parentElement, i += 1) {
    const q = p.getBoundingClientRect();
    父链.push({ i, tag: p.tagName.toLowerCase(), rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)], 子元素数: p.children.length, class: (p.className || '').toString().slice(0, 90) });
  }
  // ⭐ 兄弟节点（父的其它子元素）
  const 父 = target.parentElement;
  const 兄弟 = 父 ? [...父.children].filter((c) => c !== target).map((c) => {
    const q = c.getBoundingClientRect(); const cs = getComputedStyle(c);
    return { tag: c.tagName.toLowerCase(), rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)], pos: cs.position, z: cs.zIndex, op: cs.opacity, class: (c.className || '').toString().slice(0, 70), 文字: (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) };
  }) : [];
  return {
    找到: true,
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    完整class: cls, class段数: parts.length, class段: parts,
    直接子元素: target.children.length,
    计算样式: { position: s.position, zIndex: s.zIndex, opacity: s.opacity, pointerEvents: s.pointerEvents, background: s.backgroundColor, backdropFilter: s.backdropFilter, transitionProperty: s.transitionProperty, transitionDuration: s.transitionDuration, transitionTimingFunction: s.transitionTimingFunction },
    过渡, 动画, 自定义属性: 变量,
    动画们, 父链, 兄弟,
  };
});

if (!out.层.找到) { LOG('⛔ 没找到 z=180 的层'); } else {
  const L = out.层;
  LOG(`rect=${JSON.stringify(L.rect)} 直接子元素=${L.直接子元素}`);
  LOG(`\n⭐ 完整 class（${L.class段数} 段）:`);
  for (const p of L.class段) LOG(`   ${p}`);
  LOG(`\n⭐ 计算样式:`);
  for (const [k, v] of Object.entries(L.计算样式)) LOG(`   ${k} = ${v}`);
  LOG(`\n⭐ 过渡属性（${Object.keys(L.过渡).length} 个）:`);
  for (const [k, v] of Object.entries(L.过渡)) if (v && v !== 'all' && v !== '0s' && v !== 'none' && v !== 'ease' && v !== 'normal') LOG(`   ${k} = ${v}`);
  LOG(`\n⭐ 自定义属性（${Object.keys(L.自定义属性).length} 个）:`);
  for (const [k, v] of Object.entries(L.自定义属性)) LOG(`   ${k} = ${String(v).slice(0, 60)}`);
  LOG(`\n⭐ getAnimations(): ${JSON.stringify(L.动画们)}`);
  LOG(`\n父链:`);
  for (const p of L.父链) LOG(`   [${p.i}] <${p.tag}> ${JSON.stringify(p.rect)} 子${p.子元素数}个 ${p.class}`);
  LOG(`\n⭐ 兄弟节点（${L.兄弟.length} 个）:`);
  for (const s of L.兄弟) LOG(`   <${s.tag}> ${JSON.stringify(s.rect)} pos=${s.pos} z=${s.z} op=${s.op} 「${s.文字}」 ${s.class}`);
}

// ---------- B 样式表里有没有它 ----------
out.样式表 = await page.evaluate((cls) => {
  const 命中 = [];
  const 扫描 = (sheet, label) => {
    let rules; try { rules = sheet.cssRules; } catch { return; }
    if (!rules) return;
    for (const rule of rules) {
      const t = rule.cssText || '';
      if (!t) continue;
      for (const c of cls.split(/\s+/)) {
        if (c && c.length > 3 && t.includes(c)) {
          命中.push({ 源: label, 片段: t.slice(0, 220) });
          break;
        }
      }
    }
  };
  for (const s of document.styleSheets) 扫描(s, s.href ? s.href.slice(-40) : 'inline');
  return { 命中数: 命中.length, 命中: 命中.slice(0, 25) };
}, out.层.找到 ? out.层.完整class : '');
LOG(`\n══════════ 样式表里命中它的规则：${out.样式表.命中数} 条 ══════════`);
for (const h of out.样式表.命中) LOG(`  [${h.源}] ${h.片段}`);

// ---------- C 找一个「有内容时」的对照：大编辑器打开时它变不变 ----------
LOG('\n══════════ C 开大编辑器时它变不变 ══════════');
const probe = () => page.evaluate(() => {
  const t = [...document.querySelectorAll('body *')].find((e) => {
    const s = getComputedStyle(e);
    return s.position === 'fixed' && s.zIndex === '180' && e.getBoundingClientRect().width > 1000;
  });
  if (!t) return { 找到: false };
  const s = getComputedStyle(t);
  return { opacity: s.opacity, transitionDuration: s.transitionDuration, 动画数: (() => { try { return t.getAnimations().length; } catch { return -1; } })() };
});
out.大编辑器前 = await probe();
LOG(`开之前: ${JSON.stringify(out.大编辑器前)}`);
await page.evaluate(() => {
  const n = document.querySelector('.react-flow__node[data-id="i-9nlG6HdjK2"]');
  if (!n) return;
  const b = [...n.querySelectorAll('button')].find((x) => { const r = x.getBoundingClientRect(); return Math.abs(r.width - 28) < 2 && r.y < n.getBoundingClientRect().y + 60; });
  if (b) b.click();
});
await page.waitForTimeout(1200);
out.大编辑器中 = await probe();
LOG(`打开中: ${JSON.stringify(out.大编辑器中)}`);
await page.waitForTimeout(1500);
out.大编辑器后 = await probe();
LOG(`打开后 1.5s: ${JSON.stringify(out.大编辑器后)}`);
await page.keyboard.press('Escape'); await page.mouse.click(20, 20);
await page.waitForTimeout(1500);

await writeFile(new URL('./batchDH0.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDH0.json ===');
await browser.close();
