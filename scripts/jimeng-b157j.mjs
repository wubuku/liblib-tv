// 批次 157-j —— 最后一次找删除入口：悬停首页「画布」列表里「测试项目5」那张卡
//
// 已经排除的路径（本轮逐条实测）：
//   ① 项目切换器的「更多」菜单 → 只有「在新窗口打开」「复制项目」，**没有删除**
//   ② 首页 `/ai-tool/home` 的「画布」区 → 逐字「全部 测试项目5 测试项目 测试项目4 测试项目3
//      测试项目2 测试项目1 更多 积分商城」，**页面上没有任何「删除/移除/管理」字样**
// 本轮只做一件事：把鼠标移到「测试项目5」那张卡上，看有没有**悬停才出现**的 ⋯ / ✕。
import fs from 'node:fs';
import { chromium } from 'playwright';

const rec = { 批次: '157j', 目的: '悬停首页画布卡片找删除入口（最后一次尝试）' };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b157j.json', import.meta.url), JSON.stringify(rec, null, 1));
const 串 = (x, n) => { const s = JSON.stringify(x, null, 1); return s === undefined ? 'undefined' : s.slice(0, n || 2000); };
const 目标名 = '测试项目5';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
let hp = ctx.pages().find((x) => x.url().includes('/ai-tool/home'));
if (!hp) { hp = await ctx.newPage(); await hp.goto('https://jimeng.jianying.com/ai-tool/home', { waitUntil: 'domcontentloaded', timeout: 90000 }); await hp.waitForTimeout(6000); }

const 签名 = (阶段) => hp.evaluate((t) => {
  const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
  const 可见 = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const 集 = [];
  const 加 = (类, e) => { if (!可见(e)) return;
    集.push({ 类, tag: e.tagName, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'),
      aria: (e.getAttribute('aria-label') || '').slice(0, 40), 逐字: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40), 盒: 盒(e) }); };
  for (const e of document.querySelectorAll('button,a,[role=button],[role=menuitem]')) 加('点', e);
  for (const e of document.querySelectorAll('[data-testid]')) 加('testid', e);
  return { 阶段: t, 总数: 集.length, 集 };
}, 阶段);
const 差 = (A, B) => {
  const key = (z) => [z.类, z.role || '', z.testid || '', z.aria || '', z.逐字 || ''].join('');
  const ma = new Map(A.集.map((z) => [key(z), z]));
  return B.集.filter((z) => !ma.has(key(z)));
};

try {
  const 前 = await 签名('前');
  const 目标 = await hp.evaluate((名) => {
    const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
    const es = Array.from(document.querySelectorAll('a,button,div,span,[role=button]'))
      .filter((e) => { const t = (e.innerText || '').replace(/\s+/g, ' ').trim(); return t === 名; });
    for (const e of es) {
      const r = e.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) {
        // 往上找 3 层，看哪一层像「卡片」
        let card = e; for (let k = 0; k < 3; k++) { if (card.parentElement) card = card.parentElement; }
        const cr = card.getBoundingClientRect();
        return { 元素盒: 盒(e), 元素点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
          卡片盒: [Math.round(cr.width), Math.round(cr.height), Math.round(cr.x), Math.round(cr.y)],
          卡片中心: [Math.round(cr.x + cr.width / 2), Math.round(cr.y + cr.height / 2)] };
      }
    }
    return null;
  }, 目标名);
  rec.目标 = 目标;
  console.log('🆕 目标', JSON.stringify(目标));
  落盘();

  if (目标) {
    // 逐个悬停位置：元素中心、卡片中心、卡片右上角（⋯/✕ 惯常位置）
    const 试 = [
      { 名: '元素中心', 点: 目标.元素点 },
      { 名: '卡片中心', 点: 目标.卡片中心 },
      { 名: '卡片右上', 点: [目标.卡片盒[2] + 目标.卡片盒[0] - 16, 目标.卡片盒[3] + 20] },
      { 名: '元素右侧', 点: [目标.元素盒[2] + 目标.元素盒[0] + 30, 目标.元素盒[3] + 目标.元素盒[1] / 2] },
    ];
    rec.悬停尝试 = [];
    for (const z of 试) {
      await hp.mouse.move(z.点[0], z.点[1]);
      await hp.waitForTimeout(1400);
      const 后 = await 签名('悬停:' + z.名);
      const 新 = 差(前, 后);
      rec.悬停尝试.push({ 名: z.名, 点: z.点, 新增: 新 });
      落盘();
      console.log(`\n悬停「${z.名}」(${z.点}) → 新增 ${新.length}`);
      if (新.length) console.log(串(新, 1200));
      if (新.some((q) => /删除|移除|管理|×|✕|\.\.\.|more/i.test(q.逐字 + (q.aria || '') + (q.testid || '')))) break;
    }
    // 最后点一次看有没有菜单
    await hp.mouse.move(目标.卡片中心[0], 目标.卡片中心[1]);
    await hp.waitForTimeout(900);
    await hp.mouse.click(目标.卡片中心[0], 目标.卡片中心[1]);
    await hp.waitForTimeout(2200);
    rec.点后 = await hp.evaluate(() => {
      const 盒 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
      return { URL: location.href,
        浮层: Array.from(document.querySelectorAll('[role=menu],[role=dialog],[data-state=open]'))
          .filter((x) => x.getBoundingClientRect().width > 60)
          .map((m) => ({ role: m.getAttribute('role'), testid: m.getAttribute('data-testid'), 盒: 盒(m),
            逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200) })) };
    });
    落盘();
    console.log('\n🆕 点卡片后', 串(rec.点后, 1200));
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 800); 落盘(); }
console.log('异常', rec.异常 || '无');
process.exit(0);
