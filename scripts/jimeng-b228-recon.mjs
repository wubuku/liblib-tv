/**
 * 批次 228 侦察：搞清楚**搜索结果行的 DOM 结构**，
 * 好让后续探针能**只读**地判断「搜到了没有」，而**不用点那一行**。
 *
 * 为什么要只读：批次 221 起就知道，点搜索结果行会触发**取景动画**，
 * 改写 `.react-flow__viewport` 的 transform（缩放 + 平移）⇒ 那是**有副作用**的读法，
 * 而本实验要问的只是「索引里有没有这一行」。
 * 🔴 而且只读还解决一个更麻烦的问题：**每一步都必须有阳性对照**（立规 108 的纪律）——
 * 「搜不到」必须能和「同一时刻搜得到一个早就存在的节点」放在一起说，
 * 否则分不清是「新节点没进索引」还是「搜索功能这一会儿坏了」。
 *
 * 用法：node scripts/jimeng-b228-recon.mjs
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b228-recon.json';
const log = (...a) => console.log(a.join(' '));
// 📌 探针闸门会把 `.slice(0, 90)` 里的 `0, 90)` 误判成「数字开头的键」⇒ 一律走命名常量。
const class上限 = 90;
const 文本上限 = 60;
const 长文本上限 = 160;

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const page = await ctx.newPage();
const out = {};

try {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('.react-flow__node', { timeout: 45000 });
  await page.waitForTimeout(4500);

  // ---- 1. 搜索钮在哪 ----
  const 钮 = await page.evaluate(() => {
    const e = Array.from(document.querySelectorAll('button, [role="button"]'))
      .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { aria: '搜索', 矩形: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      testid: e.getAttribute('data-testid') };
  });
  out.搜索钮 = 钮;
  log('【搜索钮】' + JSON.stringify(钮));
  if (!钮) throw new Error('找不到 aria-label="搜索" 的按钮');

  await page.mouse.click(钮.矩形[0] + 钮.矩形[2] / 2, 钮.矩形[1] + 钮.矩形[3] / 2);
  await page.waitForTimeout(1800);

  // ---- 2. 输入框 & 面板结构 ----
  out.面板 = await page.evaluate(() => {
    const inp = Array.from(document.querySelectorAll('input'))
      .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
    const panel = inp ? inp.closest('[role="dialog"], section, [data-testid]') : null;
    return {
      有输入框: !!inp,
      输入框: inp ? { aria: inp.getAttribute('aria-label'), placeholder: inp.getAttribute('placeholder'), type: inp.type } : null,
      面板标签: panel ? `${panel.tagName}[${panel.getAttribute('data-testid') || ''}]` : null,
      面板矩形: panel ? (() => { const r = panel.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() : null,
      面板内按钮数: panel ? panel.querySelectorAll('button').length : 0,
    };
  });
  log('【面板】' + JSON.stringify(out.面板));

  // ---- 3. 搜一个**早就存在**的节点，把结果行结构原样dump 出来 ----
  await page.evaluate(() => {
    const inp = Array.from(document.querySelectorAll('input'))
      .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
    inp.focus(); inp.select();
  });
  await page.keyboard.type('音频 68', { delay: 90 });
  await page.waitForTimeout(2500);

  out.阳性对照 = await page.evaluate(() => {
    const inp = Array.from(document.querySelectorAll('input'))
      .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
    const panel = inp.closest('[role="dialog"], section, [data-testid]');
    // 候选行：面板里所有带 data-id 的元素，或所有 role=button / 可点 div
    const rows = Array.from(panel.querySelectorAll('*'))
      .filter((e) => {
        const ds = {};
        for (const a of Array.from(e.attributes)) if (a.name.startsWith('data-')) ds[a.name] = a.value;
        if (ds['data-id']) return true;
        const t = (e.innerText || '').trim();
        return e.getAttribute('role') === 'option' && t.length > 0 && t.length < 60;
      })
      .slice(0, 20)
      .map((e) => {
        const ds = {};
        for (const a of Array.from(e.attributes)) if (a.name.startsWith('data-')) ds[a.name] = a.value;
        const r = e.getBoundingClientRect();
        return {
          标签: `${e.tagName}[${e.getAttribute('role') || ''}]`,
          class: typeof e.className === 'string' ? e.className.slice(0, class上限) : null,
          data: ds,
          文本: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 文本上限),
          中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
          宽高: [Math.round(r.width), Math.round(r.height)],
        };
      });
    return { 输入框回读: inp.value, 行数: rows.length, 行: rows };
  });
  log('【阳性对照】输入框回读=' + out.阳性对照.输入框回读 + ' 候选行数=' + out.阳性对照.行数);
  out.阳性对照.行.forEach((r) => log('   ' + JSON.stringify(r)));

  // ---- 4. 搜一个**不存在**的名字，看「空结果」长什么样（阴性对照） ----
  await page.evaluate(() => {
    const inp = Array.from(document.querySelectorAll('input'))
      .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
    inp.focus(); inp.select();
  });
  await page.keyboard.type('zzz绝对不存在的名字zzz', { delay: 60 });
  await page.waitForTimeout(2500);
  out.阴性对照 = await page.evaluate((上限) => {
    const inp = Array.from(document.querySelectorAll('input'))
      .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
    const panel = inp.closest('[role="dialog"], section, [data-testid]');
    const txt = (panel.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 上限);
    return { 输入框回读: inp.value, 面板文本: txt,
      可点元素数: panel.querySelectorAll('[role="option"], [data-id], button').length };
  }, 长文本上限);
  log('【阴性对照】' + JSON.stringify(out.阴性对照));

  // ---- 5. 三种状态下各dump 一次面板文本 + 结构骨架，别再靠猜 ----
  const dump = async (标签) => {
    await page.evaluate(() => {
      const inp = Array.from(document.querySelectorAll('input'))
        .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      inp.focus(); inp.select();
    });
    return page.evaluate(([标签, 文本上限]) => {
      const inp = Array.from(document.querySelectorAll('input'))
        .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      const panel = inp.closest('[role="dialog"], section, [data-testid]');
      const 骨架 = (el, 深) => {
        if (深 <= 0 || !el) return '';
        return Array.from(el.children).slice(0, 14).map((c) => {
          const t = (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 文本上限);
          const r = c.getBoundingClientRect();
          return `${'　'.repeat(深)}<${c.tagName.toLowerCase()}${c.getAttribute('role') ? ' role=' + c.getAttribute('role') : ''}${c.getAttribute('data-testid') ? ' testid=' + c.getAttribute('data-testid') : ''}> ${JSON.stringify(t)} ${Math.round(r.width)}x${Math.round(r.height)}\n` + 骨架(c, 深 - 1);
        }).join('');
      };
      return { 状态: 标签, 输入框回读: inp.value,
        面板文本: (panel.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 文本上限 * 6),
        骨架: 骨架(panel, 4) };
    }, [标签, 文本上限 * 3]);
  };

  out.三态 = [];
  out.三态.push(await dump('空查询'));
  await page.evaluate(() => {
    const inp = Array.from(document.querySelectorAll('input'))
      .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
    inp.focus(); inp.select();
  });
  await page.keyboard.type('音频 68', { delay: 80 });
  await page.waitForTimeout(2200);
  out.三态.push(await dump('查「音频 68」'));
  await page.evaluate(() => {
    const inp = Array.from(document.querySelectorAll('input'))
      .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
    inp.focus(); inp.select();
  });
  await page.keyboard.type('b22', { delay: 80 });
  await page.waitForTimeout(2200);
  out.三态.push(await dump('查「b22」'));
  out.三态.forEach((d) => {
    log(`\n【三态·${d.状态}】回读=${d.输入框回读}`);
    log('  面板文本: ' + d.面板文本);
    log('  骨架:\n' + d.骨架);
  });

  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  log('写入 ' + OUT);
} catch (e) {
  out.出错 = e.message;
  log('🔴 ' + e.message);
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
} finally {
  // 收尾：关浮层 + 把焦点交回画布，别让焦点停在输入框里
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  try { await page.close(); } catch (e) { /* 页签可能被别的会话关掉 */ }
  await b.close();
}