// 批次 157 截图 —— 3 张，全部**拍前逐条断言**
//
// ① 116-create-team-is-a-purchase-page.png  「创建团队」实际打开的是**团队会员付费页**
// ② 117-project-panel-8-projects.png        项目面板（8 个项目，逐行带「更多」钮）
// ③ 118-project-more-menu-2-items.png       行尾「更多」菜单：**只有两项、没有删除**
//
// ⛔ **不给分享面板配图**（沿用 canvas-context.md:303-307 的既有决定）：
//    那个面板里有一行**明文画布链接**，截进图片等于把链接公开。
//    本轮虽然验成了「复制链接」，但截图这一条仍然不做。
import fs from 'node:fs';
import { chromium } from 'playwright';

const rec = { 批次: '157shots', 目的: '3 张：创建团队=付费页 / 项目面板 / 更多菜单无删除' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b157shots.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const 高亮 = (page, sel) => page.evaluate((s) => {
  const es = Array.from(document.querySelectorAll(s));
  const e = es.find((x) => { const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  if (!e) return { 命中: false, 候选数: es.length };
  const r = e.getBoundingClientRect();
  let ov = document.getElementById('__hl__');
  if (!ov) { ov = document.createElement('div'); ov.id = '__hl__'; document.body.appendChild(ov); }
  ov.style.cssText = 'position:fixed;pointer-events:none;z-index:2147483647;border:3px solid rgb(255,146,48);border-radius:10px;box-sizing:border-box;';
  ov.style.left = (r.x - 4) + 'px'; ov.style.top = (r.y - 4) + 'px';
  ov.style.width = (r.width + 8) + 'px'; ov.style.height = (r.height + 8) + 'px';
  return { 命中: true, 候选数: es.length, 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] };
}, sel);
const 摘高亮 = (page) => page.evaluate(() => { const e = document.getElementById('__hl__'); if (e) e.remove(); return true; });

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const 画布 = ctx.pages().find((x) => x.url().includes('ai-canvas'));
if (!画布) { console.log('❌ 没有画布页'); process.exit(1); }
await 画布.waitForTimeout(2500);

try {
  rec.起点 = { URL: 画布.url(), 状态行: await 画布.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0] || null) };
  console.log('起点', JSON.stringify(rec.起点));

  // ================= ① 分享 → 创建团队 =================
  const S = await 画布.evaluate(() => { const e = document.querySelector('[data-testid="canvas-share-trigger"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (S) {
    await 画布.mouse.click(S[0], S[1]); await 画布.waitForTimeout(1900);
    const 建队 = await 画布.evaluate(() => {
      const s = document.querySelector('[data-testid="canvas-share-panel"]'); if (!s) return null;
      const b = Array.from(s.querySelectorAll('button')).find((x) => (x.innerText || '').trim() === '创建团队');
      if (!b) return null; const r = b.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2), Math.round(r.width), Math.round(r.height)]; });
    rec.建队钮 = 建队;
    断言('⓪ 分享面板里找得到「创建团队」', !!建队, 建队);
    if (建队) {
      await 画布.mouse.click(建队[0], 建队[1]); await 画布.waitForTimeout(2600);
      rec.付费页 = await 画布.evaluate(() => {
        const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
        const 层 = Array.from(document.querySelectorAll('[data-state=open],[role=dialog]')).filter((x) => x.getBoundingClientRect().width > 400);
        const d = 层[层.length - 1];
        const buy = d ? Array.from(d.querySelectorAll('button')).find((x) => (x.innerText || '').trim() === '购买团队会员') : null;
        return d ? { 命中: true, 盒: 盒(d),
          逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 220),
          购买钮: buy ? { 盒: 盒(buy), disabled: buy.getAttribute('aria-disabled') } : null,
          席位钮: Array.from(d.querySelectorAll('button')).filter((x) => /Decrease quantity|Increase quantity/.test(x.getAttribute('aria-label') || '')).map((x) => ({ aria: x.getAttribute('aria-label'), 盒: 盒(x) })) } : { 命中: false }; });
      落盘();
      console.log('🆕 付费页', JSON.stringify(rec.付费页).slice(0, 700));
      断言('① 「创建团队」打开的是**整屏付费页**且含「购买团队会员」',
        (rec.付费页 || {}).命中 === true && !!rec.付费页.购买钮, rec.付费页);
      断言('② 席位有增减钮（aria 逐字 Decrease/Increase quantity）', ((rec.付费页 || {}).席位钮 || []).length >= 2, (rec.付费页 || {}).席位钮);
      if ((rec.付费页 || {}).命中) {
        await 画布.screenshot({ path: new URL('./116-create-team-is-a-purchase-page.png', 出图).pathname });
        rec.图1 = 'screenshots/116-create-team-is-a-purchase-page.png';
        console.log('① 已拍');
      }
      for (let k = 0; k < 4; k++) { await 画布.keyboard.press('Escape'); await 画布.waitForTimeout(700); }
    }
    for (let k = 0; k < 3; k++) { await 画布.keyboard.press('Escape'); await 画布.waitForTimeout(600); }
  }

  // ================= ②③ 项目面板 / 更多菜单 =================
  const T = await 画布.evaluate(() => { const e = document.querySelector('[data-testid="canvas-project-trigger"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (T) {
    await 画布.mouse.click(T[0], T[1]); await 画布.waitForTimeout(1900);
    rec.面板 = await 画布.evaluate(() => {
      const p = document.querySelector('[data-testid="canvas-project-panel-popover"]'); if (!p) return { 命中: false };
      const r = p.getBoundingClientRect();
      return { 命中: true, aria: p.getAttribute('aria-label'), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
        逐字: (p.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300),
        行数: p.querySelectorAll('[data-testid^="project-more-ordinary-"]').length }; });
    落盘();
    console.log('\n🆕 项目面板', JSON.stringify(rec.面板));
    断言('③ 项目面板打开，含 8 个项目的「更多」钮', (rec.面板 || {}).命中 === true && (rec.面板 || {}).行数 === 8, rec.面板);
    if ((rec.面板 || {}).命中) {
      await 高亮(画布, '[data-testid="canvas-project-panel-popover"]');
      await 画布.waitForTimeout(400);
      await 画布.screenshot({ path: new URL('./117-project-panel-8-projects.png', 出图).pathname });
      rec.图2 = 'screenshots/117-project-panel-8-projects.png';
      await 摘高亮(画布);
      console.log('② 已拍');
    }
    // 点第一行的「更多」
    const M = await 画布.evaluate(() => { const e = document.querySelector('[data-testid^="project-more-ordinary-"]'); if (!e) return null;
      const r = e.getBoundingClientRect(); return { 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid') }; });
    rec.更多钮 = M;
    if (M) {
      await 画布.mouse.click(M.点[0], M.点[1]); await 画布.waitForTimeout(1900);
      rec.更多菜单 = await 画布.evaluate(() => {
        const ms = Array.from(document.querySelectorAll('[role=menu]')).filter((x) => x.getBoundingClientRect().width > 60);
        if (!ms.length) return { 命中: false };
        const m = ms[ms.length - 1]; const r = m.getBoundingClientRect();
        return { 命中: true, 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
          逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
          项: Array.from(m.querySelectorAll('[role=menuitem]')).map((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20)) }; });
      落盘();
      console.log('🆕 更多菜单', JSON.stringify(rec.更多菜单));
      断言('④ 行尾「更多」菜单逐字是「在新窗口打开 / 复制项目」两项，**没有删除**',
        (rec.更多菜单 || {}).命中 === true && (rec.更多菜单 || {}).项.length === 2 &&
        !/删除/.test((rec.更多菜单 || {}).逐字 || ''), rec.更多菜单);
      if ((rec.更多菜单 || {}).命中) {
        await 高亮(画布, '[role=menu]');
        await 画布.waitForTimeout(400);
        await 画布.screenshot({ path: new URL('./118-project-more-menu-2-items.png', 出图).pathname });
        rec.图3 = 'screenshots/118-project-more-menu-2-items.png';
        await 摘高亮(画布);
        console.log('③ 已拍');
      }
      for (let k = 0; k < 3; k++) { await 画布.keyboard.press('Escape'); await 画布.waitForTimeout(600); }
    }
    for (let k = 0; k < 3; k++) { await 画布.keyboard.press('Escape'); await 画布.waitForTimeout(600); }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 800); 落盘(); }
rec.收尾 = { URL: 画布.url(), 浮层: await 画布.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length) };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
process.exit(0);
