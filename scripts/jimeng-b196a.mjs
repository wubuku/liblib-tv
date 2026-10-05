// 批次 196 a 轮：走通「删除左栏资产库里的素材」这条路径。
//
// 批次 195 如实记了一条遗留：画布节点删了，但**左栏资产库里那两条自造素材还在**
// （`jimeng-b195-test` / `jimeng-b195b-test`）。本轮把它清掉，
// 同时——**删除素材这条路手册从未写过**，正好是 assets-and-upload.md 的缺口。
//
// 🔴 护栏：只删**本批自己那两条**，且每删一条都先读出它的逐字标识再点确认。
//    任何「看起来像但不确定是不是我的」的条目一律跳过并记录。
import fs from 'node:fs';
import { openCanvas, readers, settle, endState } from './jimeng-b135-lib.mjs';

const MINE = ['jimeng-b195-test', 'jimeng-b195b-test'];
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
await settle(p, R);
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b196a', 要删的: MINE };

// ---- 打开资产库（先打印真实属性值，再写选择器：立规 67）----
const 入口 = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role="button"],[data-testid]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { tag: e.tagName, aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'),
             x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.w > 0 && x.h > 0 && /资产|素材|上传|媒体/.test((x.aria || '') + (x.testid || ''))));
out.入口候选 = 入口;
log('入口候选：', JSON.stringify(入口));

if (!入口.length) { out.中止 = '找不到资产库入口'; }
else {
  // 优先用 testid 明确的，其次用 aria 里带「资产」的
  const 选 = 入口.find((x) => /asset|素材|资产库/i.test(x.testid || '')) || 入口.find((x) => /资产/.test(x.aria || '')) || 入口[0];
  out.选了哪个 = 选;
  await p.mouse.click(选.x + 选.w / 2, 选.y + 选.h / 2);
  await p.waitForTimeout(2200);

  out.开面板后 = await p.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"]')).filter((e) => e.getBoundingClientRect().width > 1);
    const 层 = dlg.map((e) => ({ role: e.getAttribute('role'), 屏上: [e.getBoundingClientRect().x, e.getBoundingClientRect().y, e.getBoundingClientRect().width, e.getBoundingClientRect().height].map(Math.round),
      testid: e.getAttribute('data-testid'), 文本前200: e.innerText.replace(/\s+/g, ' ').trim().slice(0, 200) }));
    return { 浮层数: dlg.length, 层 };
  });
  log('开面板后：', JSON.stringify(out.开面板后, null, 1));

  // 列出面板里所有可见条目，找出自造素材
  out.条目 = await p.evaluate((names) => {
    const 命中 = [];
    for (const n of document.querySelectorAll('*')) {
      const r = n.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      const t = (n.getAttribute('aria-label') || n.getAttribute('title') || n.innerText || '').trim();
      if (!t || t.length > 80) continue;
      if (!names.some((x) => t.includes(x))) continue;
      命中.push({ tag: n.tagName, testid: n.getAttribute('data-testid'), 文本: t,
        屏上: [r.x, r.y, r.width, r.height].map((z) => Math.round(z * 100) / 100) });
    }
    return 命中;
  }, MINE);
  log('命中自造素材的元素：', JSON.stringify(out.条目, null, 1));
}

out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
fs.writeFileSync('/tmp/b196a.json', JSON.stringify(out, null, 1));
await b.close();
