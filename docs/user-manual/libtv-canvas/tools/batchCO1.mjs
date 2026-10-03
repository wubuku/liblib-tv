// Batch CO-1：把图片节点大编辑器里**四枚匿名按钮**（aria=null、无文字）对上身份。
//
// CO-0 读到的（按点击顺序）：`参考`→10 条 / `标记`→3 条 / `风格`→129 条 /
//   模型→41 条 / 规格→32 条 / `预设`→19 条 / [744,664]→17 条(摄像机/镜头/焦距/光圈) /
//   [959,664]→1 条(`提示词为空，请输入内容后点击`) / [999,664]→5 条(高级设置) /
//   [1079,664]→8 条 / [1083,114]→关掉模态。
// ⛔ 其中 [1079,664] 实测 `disabled: true`（描述为空时的发送键），
//    **CO-0 的过滤条件按 `aria === '发送'` 排除，没排掉它**（图片模态的发送键没有 aria）。
//    本步把它单独隔离测一次，顺带用悬停给四枚匿名按钮认名。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];
const IMG = 'i-sODTbgLUm1';

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
};
const killPromo = async (page) => {
  const b = await page.evaluate(() => {
    const t = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
    if (!t) return null; const r = t.getBoundingClientRect(); return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
  });
  if (!b) return false;
  await page.mouse.click(b[0], b[1]); await page.waitForTimeout(1200); return true;
};
const read = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { 在: false };
  const vis = [...n.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const fold = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
  return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'), 折叠钮: !!fold };
}, id);
const modal = (page) => page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  return d ? { 开: true, 全文: (d.innerText || '').replace(/\s+/g, ' ').trim() } : { 开: false };
});
const snap = (page) => page.evaluate(() => {
  const out = new Map();
  for (const e of document.querySelectorAll('body *')) {
    if (e.children.length) continue;
    const s = getComputedStyle(e); if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) continue;
    const r = e.getBoundingClientRect(); if (!r.width || !r.height) continue;
    const t = (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim(); if (!t || t.length > 30) continue;
    const host = e.closest('body > *');
    if (host && (getComputedStyle(host).zIndex === '600' || /ysf-chat-layer/.test((host.className || '').toString()))) continue;
    out.set(`${t}@${Math.round(r.x)},${Math.round(r.y)}`, { 文字: t, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
  }
  return [...out.values()];
});
const diff = (a, b) => b.filter((x) => !a.some((y) => y.文字 === x.文字 && y.rect[0] === x.rect[0] && y.rect[1] === x.rect[1]));
const modalButtons = (page) => page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!d) return null;
  return [...d.querySelectorAll('button')].map((b) => {
    const r = b.getBoundingClientRect();
    const p = b.querySelector('svg path');
    return { 文字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 22), aria: b.getAttribute('aria-label'), title: b.getAttribute('title'), 禁用: b.disabled, cursor: getComputedStyle(b).cursor, 类: (b.className || '').toString().slice(0, 40), 图标: p ? (p.getAttribute('d') || '').slice(0, 22) : null, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }).filter((b) => b.rect[2] > 0);
});
// 悬停读气泡（只认新出现的小浮层文字）
const bubble = (page, x, y) => page.mouse.move(x, y).then(() => page.waitForTimeout(1300)).then(() => page.evaluate(([px, py]) => {
  const 前 = new Set([...document.querySelectorAll('body *')].filter((e) => !e.children.length).map((e) => (e.innerText || '').trim()));
  const 命中 = [];
  for (const e of document.querySelectorAll('body *')) {
    if (e.children.length) continue;
    const s = getComputedStyle(e); if (s.visibility === 'hidden' || s.display === 'none' || +s.opacity === 0) continue;
    const r = e.getBoundingClientRect(); if (!r.width || !r.height || r.width > 400 || r.height > 100) continue;
    if (Math.abs(r.x + r.width / 2 - px) > 260 || Math.abs(r.y + r.height / 2 - py) > 220) continue;
    const t = (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
    if (t && t.length <= 24) 命中.push({ 文字: t, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
  }
  return 命中;
}, [x, y]));
const openModal = async (page) => {
  for (let i = 0; i < 3; i += 1) {
    if ((await modal(page)).开) return true;
    const pts = await page.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const q = n.getBoundingClientRect(); const a = [];
      for (const fy of [0.25, 0.4, 0.55, 0.7, 0.85]) for (const fx of [0.1, 0.25, 0.5, 0.75, 0.9]) {
        const x = q.x + q.width * fx, y = q.y + q.height * fy;
        const el = document.elementFromPoint(x, y);
        if (el && el.closest('.react-flow__node') === n && !el.closest('button,a')) a.push([Math.round(x), Math.round(y)]);
      }
      return a;
    }, IMG);
    let ok = false;
    for (const p of pts) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1300); const s = await read(page, IMG); if (s.选中 && s.折叠钮) { ok = true; break; } }
    if (!ok) return false;
    const fp = await page.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const f = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
      if (!f) return null; const r = f.getBoundingClientRect();
      for (const fy of [0.2, 0.35, 0.5, 0.65, 0.8]) for (const fx of [0.3, 0.5, 0.7]) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const el = document.elementFromPoint(x, y);
        if (el && el.closest('button') && el.closest('button').className.toString().includes('size-7') && x < 1440 && y < 810) return [x, y];
      }
      return null;
    }, IMG);
    if (!fp) return false;
    await page.mouse.click(fp[0], fp[1]);
    await page.waitForTimeout(1900);
  }
  return (await modal(page)).开;
};

const out = {};
const { browser, page } = await launch();
await boot(page);
out.促销 = await killPromo(page);
if (!(await openModal(page))) { console.log('⛔ 开不出模态'); await browser.close(); process.exit(0); }

out.按钮 = await modalButtons(page);
console.log('=== 图片节点大编辑器全部按钮（含 cursor / disabled / title）===');
for (const b of out.按钮) console.log(`  ${JSON.stringify(b.rect)} 文字「${b.文字}」aria=${b.aria} title=${b.title} 禁用=${b.禁用} cursor=${b.cursor} 图标=${b.图标}`);

// 逐枚悬停，认名
out.悬停 = [];
for (const b of out.按钮) {
  if (b.文字) continue;                      // 有文字的不用认
  const [x, y, w, h] = b.rect;
  const 泡 = await bubble(page, x + w / 2, y + h / 2);
  out.悬停.push({ rect: b.rect, 禁用: b.禁用, cursor: b.cursor, 气泡: 泡 });
  console.log(`  悬停 ${JSON.stringify(b.rect)} 禁用=${b.禁用} → 气泡 ${JSON.stringify(泡).slice(0, 200)}`);
}
await page.mouse.move(200, 300);
await page.waitForTimeout(500);

// ⭐ 单独隔离测「描述为空时的发送键」
{
  const send = out.按钮.find((b) => b.禁用) || out.按钮[out.按钮.length - 2];
  out.发送键 = { 按钮: send };
  const s0 = await snap(page);
  const 积分0 = await page.evaluate(() => { const m = document.body.innerText.match(/(\d+)\s*\n?\s*$/); return document.querySelectorAll('body *').length && (document.body.innerText.includes('20') ? '见顶栏' : '?'); });
  await page.mouse.click(send.rect[0] + send.rect[2] / 2, send.rect[1] + send.rect[3] / 2);
  await page.waitForTimeout(1600);
  const s1 = await snap(page);
  out.发送键.新出现 = diff(s0, s1);
  out.发送键.toast = await page.evaluate(() => {
    const 命中 = [];
    for (const e of document.querySelectorAll('body *')) {
      if (e.children.length) continue;
      const s = getComputedStyle(e); if (s.display === 'none' || +s.opacity === 0) continue;
      const r = e.getBoundingClientRect(); if (!r.width || !r.height) continue;
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (t && t.length <= 40 && /提示|不能|请|空|失败|不足/.test(t)) 命中.push({ 文字: t, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 动画: getComputedStyle(e).animationName });
    }
    return 命中;
  });
  out.发送键.顶栏积分 = await page.evaluate(() => {
    const b = [...document.querySelectorAll('body *')].find((e) => !e.children.length && /^\d{1,4}$/.test((e.innerText || '').trim()) && e.getBoundingClientRect().y < 60);
    return b ? b.innerText.trim() : null;
  });
  console.log(`\n=== 发送键 ${JSON.stringify(send.rect)} 禁用=${send.禁用}`);
  console.log(`  点它之后 新出现 ${out.发送键.新出现.length} 条:`, out.发送键.新出现.map((x) => x.文字).join(' / '));
  console.log(`  提示元素:`, JSON.stringify(out.发送键.toast));
  console.log(`  顶栏积分读到 =`, out.发送键.顶栏积分);
  out.发送键截图 = 'co1-描述为空点发送.png';
  await page.screenshot({ path: resolve(HERE, '.evidence', out.发送键截图) });
  if (!(await modal(page)).开) { console.log('  模态被关掉了，重开'); await openModal(page); }
}

// 标记 / 风格 两个面板各拍一张
for (const 名 of ['标记', '风格']) {
  const b = (await modalButtons(page)).find((x) => x.文字 === 名);
  if (!b) continue;
  await page.mouse.click(b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2);
  await page.waitForTimeout(1600);
  out[`面板_${名}`] = { 按钮: b, 图: `co1-${名}面板.png` };
  await page.screenshot({ path: resolve(HERE, '.evidence', out[`面板_${名}`].图) });
  console.log(`\n${名} 面板已开，图：${out[`面板_${名}`].图}`);
  // 用「返回节点」回去
  const back = (await modalButtons(page)).find((x) => x.文字 === '返回节点') || (await page.evaluate(() => {
    const t = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').trim() === '返回节点');
    if (!t) return null; const r = t.getBoundingClientRect(); return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }));
  if (back) { await page.mouse.click(back.rect[0] + back.rect[2] / 2, back.rect[1] + back.rect[3] / 2); await page.waitForTimeout(1400); }
  if (!(await modal(page)).开) { console.log('  ⛔ 模态没了，重开'); if (!(await openModal(page))) break; }
}

console.log('\n收尾 =', JSON.stringify(await read(page, IMG)));
await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const ids = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.收尾 = { 节点: ids, 与基线一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)) };
  console.log('收尾节点 =', ids.length, ' 与基线逐项一致 =', out.收尾.与基线一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/co1-identify.json'), JSON.stringify(out, null, 2));
