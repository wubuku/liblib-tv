// 批次 157-i —— 找项目副本的**删除**路径（项目切换器里没有：更多菜单只有「在新窗口打开」「复制项目」）
//
// ⚠️ 在**新页签**里操作，绝不把画布页导航走 —— 画布是共享的，导航走会让别人看到空页。
import fs from 'node:fs';
import { chromium } from 'playwright';

const rec = { 批次: '157i', 目的: '在首页/项目页找删除项目的入口' };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b157i.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };
const 本批 = 'f43b795d-db00-4faa-9d9b-c899db06fb07';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const 画布页 = ctx.pages().find((x) => x.url().includes('ai-canvas'));
rec.画布页URL = 画布页 ? 画布页.url() : null;

let hp = ctx.pages().find((x) => x.url().includes('/ai-tool/home'));
if (!hp) { hp = await ctx.newPage(); await hp.goto('https://jimeng.jianying.com/ai-tool/home', { waitUntil: 'domcontentloaded', timeout: 90000 }); }
await hp.waitForTimeout(6000);

const dump = (tag) => hp.evaluate((t) => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
  const 可见 = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  return { 阶段: t, URL: location.href, 标题: document.title,
    testid: Array.from(new Set(Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))).sort().slice(0, 60),
    链接: Array.from(document.querySelectorAll('a[href]')).filter(可见).map((e) => ({ href: e.getAttribute('href'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), 盒: 盒(e) })).slice(0, 40),
    危险: Array.from(document.querySelectorAll('button,a,[role=button],[role=menuitem],li,div,span'))
      .filter((e) => { const t2 = (e.innerText || '').replace(/\s+/g, ' ').trim();
        if (t2.length > 20 || !t2) return false;
        if (!/删除|移除|管理|我的项目|项目管理|回收站/.test(t2)) return false;
        if (!可见(e)) return false;
        if (e.children.length && Array.from(e.children).some((c) => (c.innerText || '').replace(/\s+/g, ' ').trim() === t2)) return false;
        return true; }).map((e) => ({ tag: e.tagName, testid: e.getAttribute('data-testid'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(), 盒: 盒(e) })),
    正文前: (document.body.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 500) };
}, tag);

try {
  rec.首页 = await dump('首页');
  落盘();
  console.log('🆕 首页 testid', 串(rec.首页.testid, 1400));
  console.log('🆕 首页链接', 串(rec.首页.链接, 1800));
  console.log('🆕 首页危险词', 串(rec.首页.危险, 800));
  console.log('🆕 首页正文', rec.首页.正文前.slice(0, 300));

  // 逐个试「管理/我的项目」类链接
  const 目标 = (rec.首页.链接 || []).filter((z) => /项目|管理|workspace|project|工作空间/i.test((z.href || '') + z.逐字));
  rec.目标链接 = 目标;
  console.log('\n🆕 项目/管理类链接', 串(目标, 1000));
  for (const z of 目标.slice(0, 6)) {
    await hp.goto(z.href, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
    await hp.waitForTimeout(4500);
    const d = await dump('试:' + z.逐字);
    const 命中 = d.危险.length || /ai-canvas/.test(d.URL);
    console.log(`  → ${z.逐字} | ${d.URL.slice(0, 90)} | 危险词 ${d.危险.length} | testid ${d.testid.length}`);
    if (d.危险.length) { rec.命中页 = d; rec.命中来源 = z; break; }
  }
  落盘();
  if (rec.命中页) {
    console.log('\n🆕 命中页', 串({ URL: rec.命中页.URL, testid: rec.命中页.testid, 危险: rec.命中页.危险, 正文: rec.命中页.正文前 }, 2600));
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 800); 落盘(); }
console.log('本批副本 uuid:', 本批, '| 画布页仍在:', 画布页 ? 画布页.url().slice(-40) : '没了');
process.exit(0);
