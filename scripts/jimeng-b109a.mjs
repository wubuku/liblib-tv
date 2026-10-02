// 批次 109 · a 轮：先把「状态串」这个判据本身验明正身，再谈测别的。
//
// 本批要关的三条：
//   ① assets-and-upload.md:208 「文本文件上传会不会也弹出 `<文件名>: Upload complete`」
//      —— 批次 102 的判据写得太严（把祖先节点一并排除了），连**早就在页面上**的
//         `b22-upload.png: Upload complete` 都没取到 ⇒ 读数 `[]` 不能支持任何结论
//   ② create-first-node.md:113 / :207 「视频 / 音频 / 文本文件的上传完成态（只传过 PNG）」
//   ③ 顺带把 PNG 之外已知的旁证（`jimeng-b101-test-avc1.mp4: Upload complete`）复核一遍
//
// 🔴 **本轮只读，不建任何节点、不传任何文件。**
// 📌 第一步必须是**阳性对照**：先证明判据能命中一条**已知一定在页面上**的状态串。
//    否则后面所有「没读到」都只会重演批次 102 的错误 —— 判据坏了却当成产品行为。
//
// 判据设计（与批次 102 的失败版对照）：
//   ❌ 批次 102：`.sr-only,[role=status],[aria-live]` 里**再排掉「有匹配子元素的」**
//      —— 排掉的正是真正的承载者，祖先反而留下了不匹配的噪声
//   ✅ 本轮：**不按子元素过滤**，全量取 textContent → 归一空白 → 去重 → 再筛内容
//      并**逐条报告**命中的 testid / 尺寸 / class，不做任何「我认为它该长什么样」的假设
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a', readonly: true };
const save = () => writeFileSync(new URL('./_tmp-b109a.json', import.meta.url), JSON.stringify(out, null, 1));

const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  return {
    nodes: (t.match(/(\d+) nodes?/) || [])[1],
    sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1],
    zoom: (document.querySelector('[data-testid="canvas-zoom-percent"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    tool: (document.querySelector('[data-testid="canvas-pointer-tool-toggle"]') || { getAttribute: () => null }).getAttribute('aria-label'),
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'),
  };
});

out.start = await status();
log('起点：', JSON.stringify(out.start));
save();

// ---- ① 全量扫「可能承载状态串」的元素：一个字都不提前排除 ----
out.scan = await p.evaluate(() => {
  const sel = '.sr-only,[role=status],[aria-live],[role=log],output';
  const all = Array.from(document.querySelectorAll(sel));
  const rows = all.map((e) => {
    const t = (e.textContent || '').replace(/\s+/g, ' ').trim();
    const r = e.getBoundingClientRect();
    return {
      t: t.slice(0, 120),
      len: t.length,
      testid: e.getAttribute('data-testid'),
      role: e.getAttribute('role'),
      tag: e.tagName,
      cls: (e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className || '').toString().slice(0, 60),
      kids: e.children.length,
      box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    };
  });
  return { matched: all.length, rows };
});
log(`\n=== ① 扫到 ${out.scan.matched} 个候选元素 ===`);
const uploadRows = out.scan.rows.filter((r) => /upload|上传/i.test(r.t));
out.uploadRows = uploadRows;
log(`其中 textContent 含 upload/上传 的：${uploadRows.length} 条`);
for (const r of uploadRows) {
  log(`  · "${r.t}"`);
  log(`      tag=${r.tag} role=${r.role} testid=${r.testid} kids=${r.kids} box=${r.box} cls=${r.cls}`);
}
save();

// ---- ② 阳性对照：页面上「已知存在」的那几条，能不能被上面这个判据命中 ----
const KNOWN = ['b22-upload.png: Upload complete', 'jimeng-b101-test-avc1.mp4: Upload complete'];
out.known = KNOWN.map((k) => {
  const hit = uploadRows.find((r) => r.t.includes(k));
  return { want: k, found: !!hit, via: hit ? { tag: hit.tag, role: hit.role, testid: hit.testid, kids: hit.kids, box: hit.box, cls: hit.cls } : null };
});
log('\n=== ② 阳性对照 ===');
for (const k of out.known) {
  log(`  ${k.found ? '✅' : '🔴'} ${k.want}`);
  if (k.found) log(`      经由 ${k.via.tag} role=${k.via.role} testid=${k.via.testid} kids=${k.via.kids} box=${k.via.box} cls=${k.via.cls}`);
}
out.predicateWorks = out.known.some((k) => k.found);
log('\n判据可用（至少命中一条已知串）=', out.predicateWorks);
save();

// ---- ③ 顺带把「这个判据会读到什么」的全貌记下来：状态串是不是唯一的「播报」通道 ----
out.allTexts = Array.from(new Set(out.scan.rows.map((r) => r.t))).filter(Boolean);
log(`\n=== ③ 去重后共 ${out.allTexts.length} 条文本，逐条（前 40） ===`);
out.allTexts.slice(0, 40).forEach((t, i) => log(`  ${String(i).padStart(2)}. ${t}`));
save();

// ---- ④ 「Upload complete」这个短语的完整分布：它到底出现在哪些元素上 ----
out.phrase = await p.evaluate(() => {
  const hits = [];
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = w.nextNode())) {
    const t = (n.nodeValue || '').replace(/\s+/g, ' ').trim();
    if (!t) continue;
    if (!/Upload complete|上传完成|upload complete/i.test(t)) continue;
    // 逐个祖先问：谁**自己**的文字（含后代）与整段相同
    const chain = [];
    let e = n.parentElement;
    for (let d = 0; e && d < 6; d++, e = e.parentElement) {
      const et = (e.textContent || '').replace(/\s+/g, ' ').trim();
      chain.push({
        d, tag: e.tagName, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'),
        cls: (e.className || '').toString().slice(0, 50),
        srOnly: (() => { try { return getComputedStyle(e).getPropertyValue('clip') !== 'auto'; } catch { return null; } })(),
        box: (() => { const r = e.getBoundingClientRect(); return `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`; })(),
        ownMatches: et === t,
      });
    }
    hits.push({ text: t.slice(0, 100), chain });
  }
  return hits;
});
log(`\n=== ④ 文本节点层面命中 ${out.phrase.length} 处「Upload complete」 ===`);
out.phrase.forEach((h, i) => {
  log(`  [${i}] "${h.text}"`);
  h.chain.forEach((c) => log(`      d=${c.d} ${c.tag} role=${c.role} testid=${c.testid} srOnly=${c.srOnly} box=${c.box} own=${c.ownMatches}`));
});
save();

log('\nDONE a');
process.exit(0);
