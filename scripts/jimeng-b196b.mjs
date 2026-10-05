// 批次 196 b 轮：🔴 验一件事 —— 画布上传的素材到底进不进资产库？
//
// 手册 assets-and-upload.md:397-402 逐字写着：
//   「画布节点与资产库是两套东西 —— 可这些上传件**从来没有进过资产库**」
//   「资产库是账号级素材库，画布上传不进这里」
// 而 a 轮实测：左栏「资产库」→ 切到**视频**页，找到了本轮（批次 195）刚上传的两条：
//   `jimeng-b195-test.mp4: Upload complete` / `jimeng-b195b-test.mp4: Upload complete`
// ⇒ 🔴 **这两条直接矛盾。** 本轮要回答的是：矛盾在哪一边。
//
// 🔴 判据设计（避免「看到了就是进了」这种想当然）：
//   要区分「**资产库列的是账号级素材**」与「**资产库列的是本画布上传件**」，只有一条路：
//   **把画布上的节点删掉，看资产库里的条目会不会跟着消失。**
//   批次 195 已经删过两个由上传建出的节点（护栏有据），所以现在可以直接读资产库。
//
// 另：手册 391 行还挂着一条「**仍未实测**：资产库内点选素材 → 确认 的插入动作」——
//   本轮顺带把它跑掉（用自己刚上传的素材，插入后再删）。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const MINE = ['jimeng-b195-test', 'jimeng-b195b-test'];
const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
await settle(p, R);
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b196b', 我的素材: MINE, 前提: '画布上这两个节点已在批次 195 收尾时被删掉' };

// 画布上是否还有同名的节点（应当没有）
out.画布上有无同名节点 = await p.evaluate((ns) => Array.from(document.querySelectorAll('.react-flow__node'))
  .map((n) => n.getAttribute('aria-label') || '').filter((a) => ns.some((x) => a.includes(x))), MINE);
log('画布上同名节点：', JSON.stringify(out.画布上有无同名节点));

const 开资产库 = async () => {
  const 入口 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button'))
    .find((x) => (x.getAttribute('aria-label') || '') === '资产库' && x.getBoundingClientRect().width > 0);
    if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!入口) return null;
  await p.mouse.click(入口[0], 入口[1]); await p.waitForTimeout(2000);
  return await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
    const r = d ? d.getBoundingClientRect() : null;
    return { 在: !!d, 屏上: r ? [r.x, r.y, r.width, r.height].map(Math.round) : null, 文本: d ? d.innerText.replace(/\s+/g, ' ').trim().slice(0, 300) : null }; });
};

const 扫各页签 = async () => {
  const 页签 = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]'); if (!d) return [];
    return Array.from(d.querySelectorAll('button,[role="tab"]')).map((e) => { const r = e.getBoundingClientRect();
      return { 文字: (e.getAttribute('aria-label') || e.innerText || '').trim(), 屏上: [r.x, r.y, r.width, r.height].map(Math.round) }; })
      .filter((x) => x.文字 && x.屏上[2] > 0); });
  const 结果 = {};
  for (const t of 页签) {
    if (!/资产|主体|图片|视频|音频|文档|时间/.test(t.文字)) continue;
    if (t.屏上[2] < 8) continue;
    await p.mouse.click(t.屏上[0] + t.屏上[2] / 2, t.屏上[1] + t.屏上[3] / 2); await p.waitForTimeout(1100);
    const r = await p.evaluate((ns) => {
      const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]'); if (!d) return null;
      const 空态 = /暂无[^。]*素材/.exec(d.innerText);
      return { 空态: 空态 ? 空态[0] : null,
        命中我的: ns.filter((x) => d.innerText.includes(x)),
        img: d.querySelectorAll('img').length, video: d.querySelectorAll('video').length,
        卡片候选数: d.querySelectorAll('[class*="card"],[class*="item"],[class*="asset"]').length,
        文本前200: d.innerText.replace(/\s+/g, ' ').trim().slice(0, 200) };
    }, MINE);
    结果[t.文字] = r;
    log(`页签「${t.文字}」：`, JSON.stringify(r));
  }
  return 结果;
};

out.资产库 = await 开资产库();
log('资产库：', JSON.stringify(out.资产库));
out.各页签 = await 扫各页签();
await p.keyboard.press('Escape'); await p.waitForTimeout(1000);

fs.writeFileSync('/tmp/b196b.json', JSON.stringify(out, null, 1));
out.收尾 = await endState(p, R, 基线);
log('收尾：', JSON.stringify(out.收尾));
await b.close();
