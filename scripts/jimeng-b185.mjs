// 批次 185：**把「从导演台返回画布」那个未取证的返回入口拍出来。**
//
// 手册 `director-node.md` 写着「从导演台返回画布：使用其界面自带的返回入口
// （**本手册未取证其具体形态**）」，并在常见错误表里让用户「用其自带返回入口回到画布」。
// ⇒ 一条**用户被要求去做、但手册没告诉他长什么样**的操作。而该页只有 2 张图 / 301 行，
// 是全册最薄的一页。
//
// 步骤：① 记录标签页与 URL（⛔ 万一进得去出不来，用 URL 兜底回去）；
//       ② 选中导演台节点、读它节点内的操作项；
//       ③ 点「进入导演台」，等页面稳定，**先只读不点**；
//       ④ 找返回入口：按 aria / 逐字文案 / testid 三路找，并**读它的几何与可点性**；
//       ⑤ **截图**（本页缺图，截图是本批的主要交付物之一）；
//       ⑥ 点它，验「真的回到画布」（URL、节点数、状态行都对）。
//
// ⛔ 不生成、不分享、不下载、不点「保存到主体库」；**不点任何会扣费的按钮**。
//    导演台的 3D 工作台本身不在本手册范围，本批只取「怎么回来」这一件事。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';
import fs from 'node:fs';

const 画布URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '185' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 搜索选中 = async (关键词) => {
  if (typeof 关键词 !== 'string' || !关键词.trim()) return { 成功: false, 原因: '关键词非法' };
  const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!开) return { 成功: false, 原因: '没有搜索按钮' };
  await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
  const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!输入) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: '搜索面板没有输入框' }; }
  await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
  await p.fill('[data-testid="canvas-search-panel"] input', 关键词); await p.waitForTimeout(1400);
  const 命中 = await p.evaluate((w) => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60),
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }).filter((x) => !w || x.文字.includes(w)), 关键词);
  if (!命中.length) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: `没命中「${关键词}」` }; }
  await p.mouse.click(命中[0].点[0], 命中[0].点[1]); await p.waitForTimeout(1400);
  const s = await 选中集(); await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  return { 成功: s.length >= 1, 选中集: s, 命中: 命中.slice(0, 2) };
};

const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), URL: p.url() };
rec.起点.标签页数 = b.contexts()[0].pages().length;

// 导演台节点
const 导演 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-external'); if (!n) return null;
  const t = n.querySelector('[data-testid="flow-node-title"]');
  return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null, aria: n.getAttribute('aria-label') }; });
rec.导演台节点 = 导演;

/** 页面里所有**看起来能点**的控件（限视口内、面积 > 8），用来找返回入口。 */
const 找控件 = () => p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button],a[href]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { 标签: e.tagName, 逐字: (e.innerText || '').trim().replace(/\n/g, ' ').slice(0, 40), aria: e.getAttribute('aria-label'),
      testid: e.getAttribute('data-testid'), title: e.getAttribute('title'), href: e.getAttribute('href'),
      屏上: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
      禁用: e.getAttribute('aria-disabled') === 'true' || e.disabled === true,
      在视口内: r.width > 1 && r.height > 1 && r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight }; })
  .filter((x) => x.在视口内 && x.屏上.w >= 8 && x.屏上.h >= 8));

try {
  if (!导演) { rec.结论 = '画布上没有导演台节点'; }
  else {
    // ② 节点内的操作项（点选后读）
    const S = await 搜索选中(导演.标题);
    rec.选中导演台 = S;
    if (S.成功 && S.选中集.includes(导演.id)) {
      rec.节点内控件 = await p.evaluate((i) => {
        const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
        return Array.from(n.querySelectorAll('button,[role=button]')).map((e) => { const r = e.getBoundingClientRect();
          return { 标签: e.tagName, 逐字: (e.innerText || '').trim().replace(/\n/g, ' ').slice(0, 40), aria: e.getAttribute('aria-label'),
            testid: e.getAttribute('data-testid'), 屏上: { w: Math.round(r.width), h: Math.round(r.height) },
            点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 禁用: e.getAttribute('aria-disabled') === 'true' }; });
      }, 导演.id);
      // ③ 点「进入导演台」
      const 入 = (rec.节点内控件 || []).find((c) => (c.逐字 || '').includes('进入导演台') || (c.aria || '').includes('进入导演台'));
      rec.进入按钮 = 入 || null;
      if (入 && !入.禁用) {
        await p.mouse.click(入.点[0], 入.点[1]);
        await p.waitForTimeout(6000);
        rec.进入后 = { URL: p.url(), 标签页数: b.contexts()[0].pages().length,
          标题: await p.title(), 节点数: await 节点数(),
          在画布上: p.url().includes('ai-canvas') && (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) > 0 };
        // ④ 找返回入口
        rec.返回候选 = (await 找控件()).filter((c) => /返回|回到|画布|退出|关闭|back|canvas|close/i.test([c.逐字, c.aria, c.testid, c.title].join(' ')));
        rec.进导演台后所有视口内控件 = await 找控件();
        if (rec.进入后.在画布上) {
          rec.说明 = '「进入导演台」没有离开画布（可能是浮层），改按浮层里的控件找返回入口';
        } else {
          // ⑤ 截图
          await p.screenshot({ path: 'docs/user-manual/jimeng-canvas/screenshots/_tmp-185-director-return.png' });
          rec.已截图 = true;
          const 返 = (rec.返回候选 || []).find((c) => !c.禁用);
          rec.返回按钮 = 返 || null;
          if (返) {
            await p.mouse.click(返.屏上.x + Math.round(返.屏上.w / 2), 返.屏上.y + Math.round(返.屏上.h / 2));
            await p.waitForTimeout(6000);
            rec.返回后 = { URL: p.url(), 标签页数: b.contexts()[0].pages().length, 节点数: await 节点数(),
              在画布上: p.url().includes('ai-canvas') && (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) > 0 };
          }
        }
      }
    }
  }
} catch (e) { rec.异常 = String(e).slice(0, 200); }

// ═════════ 兜底：无论如何回到画布
if (!p.url().includes('ai-canvas') || !(await p.evaluate(() => document.querySelectorAll('.react-flow__node').length))) {
  rec.兜底 = '用 URL 直接回画布';
  await p.goto(画布URL, { waitUntil: 'domcontentloaded' }); await pinViewport(p);
  const t0 = Date.now();
  while (Date.now() - t0 < 60000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(500); }
  await p.waitForTimeout(3000);
}
await p.keyboard.press('Escape'); await p.waitForTimeout(500);
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t1 = Date.now();
while (Date.now() - t1 < 60000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(500); }
await p.waitForTimeout(3000);
const 末 = await id集();
rec.收尾核验 = { 现在节点数: 末.length, 起点节点数: 前id.length, 残留id: 末.filter((i) => !前id.includes(i)),
  丢失id: 前id.filter((i) => !末.includes(i)), 原有仍在: 前id.filter((i) => 末.includes(i)).length, 标签页数: b.contexts()[0].pages().length };
rec.收尾 = { URL: p.url(), 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays() };
const 截图存在 = fs.existsSync('docs/user-manual/jimeng-canvas/screenshots/_tmp-185-director-return.png');
rec.截图 = 截图存在 ? fs.statSync('docs/user-manual/jimeng-canvas/screenshots/_tmp-185-director-return.png').size + ' 字节' : '没拍到';
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
