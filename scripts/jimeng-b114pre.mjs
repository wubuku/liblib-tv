// 批次 114 · 预诊断（**只读**，不点任何东西）。
//
// 靶子出处（三处都记着同一条悬案）：
//   · `20-reference.md`「二级子菜单」：`四类内容实测逐字都是 暂无相关节点`
//     「🔴 空列表成因**未能确认**（空节点被排除 / 当前节点自身被排除 / 两者叠加）
//      —— 观测条件下画布只有一个空的「视频 1」」
//   · `prepare-generation.md:216`：同样一句「未能确认『空节点是否被排除』」
//   · 本批弹药变化：**画布上现在有 68 个音频节点**，而批次 61 当时只有 1 个空视频节点
//     ⇒ 「空节点是否被排除」现在**可以**直接测了。
//
// 这一轮只回答：画布上**有什么可当弹药**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b114-pre' };
const save = () => writeFileSync(new URL('./_tmp-b114pre.json', import.meta.url), JSON.stringify(out, null, 1));

out.nodes = await p.evaluate(() => {
  const res = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const id = n.getAttribute('data-id');
    const cls = (n.getAttribute('class') || '').toString();
    const type = (cls.match(/react-flow__node-(\w+)/) || [])[1] || '?';
    const inner = (n.innerText || '').replace(/\s+/g, ' ').trim();
    const aria = n.getAttribute('aria-label') || '';
    // 资源账：可能在 innerText（视频/音频），也可能在 aria-label（图片）
    const ledInner = (inner.match(/(\d+) resources?:[\s\S]{0,60}/) || [])[0] || null;
    const ledAria = (aria.match(/(\d+) resources?:[\s\S]{0,60}/) || [])[0] || null;
    const m = (ledInner || ledAria || '').match(/(\d+) ready, (\d+) processing, (\d+) failed/);
    const title = (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || '';
    res.push({ id, type, title: (title || '').replace(/\s+/g, ' ').trim().slice(0, 30),
      ready: m ? +m[1] : null, processing: m ? +m[2] : null, failed: m ? +m[3] : null,
      ledgerSource: ledInner ? 'innerText' : (ledAria ? 'aria-label' : null),
      tids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid'))))
        .filter((t) => /-node-result$|-node-empty$|simple-player|image-node|video-node|preview/.test(t)) });
  }
  return res;
});
const byType = {};
for (const n of out.nodes) {
  const k = n.type;
  byType[k] = byType[k] || { total: 0, withReady: 0, empty: 0, unknown: 0, samples: [] };
  byType[k].total++;
  if (n.ready === null) byType[k].unknown++;
  else if (n.ready > 0) byType[k].withReady++;
  else byType[k].empty++;
  if (byType[k].samples.length < 3) byType[k].samples.push({ id: n.id, title: n.title, ready: n.ready, src: n.ledgerSource, tids: n.tids });
}
out.byType = byType;
log('节点总数：', out.nodes.length);
log('\n按类型统计：');
for (const [k, v] of Object.entries(byType)) {
  log(`  ${k.padEnd(10)} 共 ${String(v.total).padStart(3)} ｜ 有 ready ${v.withReady} ｜ 空 ${v.empty} ｜ 账读不到 ${v.unknown}`);
  v.samples.forEach((s) => log(`      ${JSON.stringify(s)}`));
}

out.zoom = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
out.sel = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
out.credits = await p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
log('\n缩放：', out.zoom, '｜选中：', out.sel, '｜积分：', out.credits);
save();
log('\nDONE pre');
process.exit(0);
