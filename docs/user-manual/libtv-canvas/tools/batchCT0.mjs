// Batch CT-0：给 `[959,664]` 那枚匿名按钮定名。
//
// CR 留下的 📖：图片大编辑器底栏 `[959,664]` 是一枚
//   `data-practice-generator-lock`（空值）、`viewBox="0 0 19.71 18"`、
//   path `M15.52 7.2c.16 0 .31.1.37.26l3.8 10a.4.4…`（一根斜杆）的按钮，
//   功能未定名；而且它**和** `[999,664]` 的「高级设置」**共用同一个属性值**。
//
// ⭐ 疑点先摆出来：属性值相同、功能不同 ⇒ **这个属性不是「锁定按钮」的标记**，
//   它更像是「生成器这一行」的分组标记。要给按钮定名，光看属性不够。
//
// 本步（全部只读，⛔ 一个都不点）：
//   ① 大编辑器打开后**全页枚举所有 data-* 属性**（名字不限 —— CR/§142 说过
//      判据的范围本身就是要审的对象，CR 限死 `practice` 才发现属性分三家，
//      这次干脆一个都不限，看还剩多少「认控件」的路子）
//   ② 大编辑器内 `data-feature-id` 的完整清单
//   ③ 那两枚 `data-practice-generator-lock` 的**全部属性 + 完整 class +
//      完整祖先链 + 全部 svg 路径 + aria-disabled + 尺寸**（§140 的治法）
//   ④ 底栏一整排按钮的身份普查（谁有锚点、谁没有）
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const IMG = 'i-9nlG6HdjK2';   // 图片节点

const boot = async (page) => {
  await open(page, URL_);
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2600);
  for (let i = 0; i < 3; i += 1) {
    const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
    if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(600);
  }
  const t = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
    if (!b) return false;
    const r = b.getBoundingClientRect();
    return r.width > 0;
  });
  if (t) {
    const p = await page.evaluate(() => {
      const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
      const r = b.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    });
    await page.mouse.click(p[0], p[1]);
    await page.waitForTimeout(1200);
  }
};

const LOG = (x) => { console.log(x); };

const { browser, page } = await launch();
await boot(page);

// ---- 打开图片节点的大编辑器 -------------------------------------------------
const opened = await page.evaluate(async (nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { ok: false, why: 'no-node' };
  n.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: n.getBoundingClientRect().x + 40, clientY: n.getBoundingClientRect().y + 20 }));
  return { ok: true };
}, IMG);
await page.waitForTimeout(900);
LOG(`选节点: ${JSON.stringify(opened)}`);

const foldPoint = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const f = [...n.querySelectorAll('button')].find((b) => {
    const c = (b.className || '').toString();
    return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2');
  });
  if (!f) return null;
  const r = f.getBoundingClientRect();
  for (let dx = 4; dx < r.width; dx += 3) {
    for (let dy = 4; dy < r.height; dy += 3) {
      const x = r.x + dx, y = r.y + dy;
      const el = document.elementFromPoint(x, y);
      if (el && (el === f || f.contains(el) || el.contains(f))) return [Math.round(x), Math.round(y), f.getBoundingClientRect().width];
    }
  }
  return null;
}, IMG);
LOG(`⤢ 落点: ${JSON.stringify(foldPoint)}`);
if (foldPoint) {
  await page.mouse.click(foldPoint[0], foldPoint[1]);
  await page.waitForTimeout(1400);
}

const modalOpen = await page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  return !!d;
});
LOG(`大编辑器开着: ${modalOpen}`);

// ---- ① 全页枚举所有 data-*（名字不限） ---------------------------------------
const allData = await page.evaluate(() => {
  const tally = {};
  for (const e of document.querySelectorAll('body *')) {
    for (const a of e.attributes) {
      if (!a.name.startsWith('data-')) continue;
      if (a.name === 'data-id' || a.name === 'data-testid') continue;
      const k = `${a.name}=${JSON.stringify(a.value)}`;
      (tally[k] ||= { 属性: a.name, 值: a.value, 数量: 0, 样例: [] }).数量 += 1;
      const t = tally[k];
      if (t.样例.length < 3) {
        const r = e.getBoundingClientRect();
        t.样例.push({ tag: e.tagName.toLowerCase(), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
      }
    }
  }
  return Object.values(tally).sort((a, b) => b.数量 - a.数量);
});
LOG(`\n===== ① 全页所有 data-*（名字不限） 共 ${allData.length} 个取值 =====`);
for (const d of allData) LOG(`  ${d.数量.toString().padStart(3)}×  ${d.属性}="${d.值}"   e.g. ${d.样例[0].tag} "${d.样例[0].文字}" @${JSON.stringify(d.样例[0].rect)}`);

// ---- ② 大编辑器内 data-feature-id 完整清单 -----------------------------------
const featIds = await page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!d) return null;
  return [...d.querySelectorAll('[data-feature-id]')].map((e) => {
    const r = e.getBoundingClientRect();
    return {
      值: e.getAttribute('data-feature-id'), tag: e.tagName.toLowerCase(),
      文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 22),
      aria: e.getAttribute('aria-label'),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    };
  });
});
LOG(`\n===== ② 大编辑器内 data-feature-id（${featIds?.length ?? 'N/A'} 个） =====`);
for (const f of featIds ?? []) LOG(`  "${f.值}"  <${f.tag}> "${f.文字}" aria=${f.aria} @${JSON.stringify(f.rect)}`);

// ---- ③ 两枚 data-practice-generator-lock 的完整身份 --------------------------
const locks = await page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!d) return [];
  return [...d.querySelectorAll('[data-practice-generator-lock]')].map((b) => {
    const r = b.getBoundingClientRect();
    const 祖先 = [];
    for (let e = b, i = 0; e && i < 7; e = e.parentElement, i += 1) {
      祖先.push({ tag: e.tagName.toLowerCase(), class: (e.className || '').toString().slice(0, 90) });
    }
    return {
      全部属性: Object.fromEntries([...b.attributes].map((a) => [a.name, a.value])),
      完整class: (b.className || '').toString(),
      祖先链: 祖先,
      ariaDisabled: b.getAttribute('aria-disabled'),
      disabled: b.disabled,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cursor: getComputedStyle(b).cursor,
      外层HTML: b.outerHTML.slice(0, 400),
      兄弟: [...(b.parentElement?.children ?? [])].map((s) => ({
        tag: s.tagName.toLowerCase(), text: (s.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16),
        svgPaths: [...s.querySelectorAll('svg path')].map((p) => p.getAttribute('d')),
        hasPractice: s.hasAttribute('data-practice-generator-lock'),
        hasFeature: s.getAttribute('data-feature-id') || null,
        aria: s.getAttribute('aria-label'),
      })),
    };
  });
});
LOG(`\n===== ③ data-practice-generator-lock 命中 ${locks.length} 个 =====`);
for (const l of locks) {
  LOG(`\n  --- @${JSON.stringify(l.rect)} cursor=${l.cursor} aria-disabled=${l.ariaDisabled} disabled=${l.disabled}`);
  LOG(`      全部属性: ${JSON.stringify(l.全部属性)}`);
  LOG(`      完整class: ${l.完整class}`);
  LOG(`      祖先链: ${l.祖先链.map((a) => `<${a.tag}.${a.class}>`).join(' ← ')}`);
  LOG(`      外层HTML: ${l.外层HTML}`);
  LOG(`      同排兄弟 ${l.兄弟.length} 个:`);
  for (const s of l.兄弟) LOG(`         <${s.tag}> "${s.text}" svg=${JSON.stringify(s.svgPaths).slice(0, 150)} practice=${s.hasPractice} feature=${s.hasFeature} aria=${s.aria}`);
}

// ---- ④ 底栏一整排按钮身份普查 ------------------------------------------------
const bottom = await page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!d) return null;
  // 底栏 = y 在 640~700 之间的那批按钮
  const bs = [...d.querySelectorAll('button')].map((b) => {
    const r = b.getBoundingClientRect();
    return { b, r };
  }).filter(({ r }) => r.y > 620 && r.y < 720 && r.width > 0).sort((a, z) => a.r.x - z.r.x);
  return bs.map(({ b, r }) => ({
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    文字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
    aria: b.getAttribute('aria-label'),
    ariaDisabled: b.getAttribute('aria-disabled'),
    dataAttrs: Object.fromEntries([...b.attributes].filter((a) => a.name.startsWith('data-')).map((a) => [a.name, a.value])),
    svgPaths: [...b.querySelectorAll('svg path')].map((p) => (p.getAttribute('d') || '').slice(0, 60)),
    完整class: (b.className || '').toString().slice(0, 120),
  }));
});
LOG(`\n===== ④ 大编辑器底栏按钮 ${bottom?.length ?? 'N/A'} 枚 =====`);
for (const b of bottom ?? []) {
  LOG(`  @${JSON.stringify(b.rect)} "${b.文字}" aria=${b.aria} aria-disabled=${b.ariaDisabled}`);
  LOG(`      data: ${JSON.stringify(b.dataAttrs)}`);
  LOG(`      svg: ${JSON.stringify(b.svgPaths)}`);
  LOG(`      class: ${b.完整class}`);
}

await writeFile(new URL('./batchCT0.json', import.meta.url), JSON.stringify({ allData, featIds, locks, bottom }, null, 2));
LOG('\n已写 tools/batchCT0.json');
await browser.close();
