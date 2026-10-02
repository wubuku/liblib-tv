// 批次 109 · d 轮：把活区域的结构**不截断**地读一遍，并读本轮自建音频节点的结构。
//
// c 轮的读数把 a 轮的一个 bug 顶了出来：
//   · a 轮 `out.scan.rows` 里每行是 `t.slice(0, 120)` ⇒ **阳性对照第 ② 条是假阴性**。
//     真相：`jimeng-b101-test-avc1.mp4: Upload complete` **一直都在页面上**，
//     只是排在第 24 份 png 之后，落在 120 字截断线之外。
//     ⇒ 📌 **给读数加截断，等于给判据加了一个我自己都不知道的假设**（批次 108 同款教训）
//   · c 轮实测：传完 .wav 后那条活区域里**多出了** `jimeng-b104-test.wav: Upload complete`
//     ⇒ 它是**追加**，不是替换 ⇒ ✅ **音频上传确实有完成态状态串**（关掉 create-first-node.md 的一条）
//   · 完整串是：`png×25 + mp4 + wav + mp4` ⇒ 同一条 mp4 出现**两次**（批次 101 传过一次、批次 105 又传过）
//
// 本轮要读清三件事：
//   ① `role=status` 里每一个子元素**逐条**是什么（哪个是跑马灯副本、哪些是独立条目）
//   ② 本轮音频节点的标题/aria 到底带不带扩展名（PNG 是不带的，这里 innerText 与 aria 似乎不一致）
//   ③ 音频节点从 `正在上传音频 0%` 到 ready 要多久、资源账怎么变
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'd', self: 'node_n62gwfa97f' };
const SELF = out.self;
const save = () => writeFileSync(new URL('./_tmp-b109d.json', import.meta.url), JSON.stringify(out, null, 1));

const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') };
});

// ---- ① 活区域：**不截断**，逐个子元素 ----
out.live = await p.evaluate(() => {
  const st = Array.from(document.querySelectorAll('[role=status]'));
  return st.map((e) => {
    const r = e.getBoundingClientRect();
    return {
      parentBox: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      parentTextFull: (e.textContent || ''),
      parentTextLen: (e.textContent || '').length,
      kids: Array.from(e.children).map((k, i) => {
        const kr = k.getBoundingClientRect();
        return { i, tag: k.tagName, text: (k.textContent || ''), len: (k.textContent || '').length,
          box: `${Math.round(kr.x)},${Math.round(kr.y)} ${Math.round(kr.width)}×${Math.round(kr.height)}` };
      }),
      // 直接挂在 status 下的「裸文本节点」（不在任何子元素里的那些）
      bareText: Array.from(e.childNodes).filter((n) => n.nodeType === 3).map((n) => (n.nodeValue || '').trim()).filter(Boolean),
    };
  });
});
log('=== ① [role=status] 区域 ===');
out.live.forEach((L, i) => {
  log(`\n  区域[${i}] ${L.parentBox}｜textContent 全长 ${L.parentTextLen} 字｜子元素 ${L.kids.length} 个｜裸文本节点 ${L.bareText.length} 个`);
  log(`  裸文本节点逐条：`);
  L.bareText.forEach((t, j) => log(`     [裸${j}] "${t}"`));
  log(`  子元素逐条：`);
  L.kids.forEach((k) => log(`     [子${String(k.i).padStart(2)}] ${k.tag} ${k.box} len=${k.len} "${k.text}"`));
});
save();

// 把完整 textContent 切成「条目」：按已知的重复边界拆
out.parts = out.live.map((L) => {
  // 以「已知前缀」分组统计：统计每个不同字符串出现了几次
  const counts = new Map();
  // 用子元素 + 裸文本节点重建（不截断）
  const seq = [...L.bareText, ...L.kids.map((k) => k.text)];
  seq.forEach((t) => counts.set(t, (counts.get(t) || 0) + 1));
  return { uniq: Array.from(counts.entries()).map(([t, n]) => ({ n, len: t.length, t })) };
});
log('\n=== ① 去重后的条目与出现次数 ===');
out.parts.forEach((P, i) => {
  log(`  区域[${i}]：`);
  P.uniq.forEach((u) => log(`     ×${u.n}  len=${u.len}  "${u.t}"`));
});
save();

// ---- ② 本轮音频节点的结构 ----
out.selfInfo = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  return {
    id: i, cls: n.className,
    aria: n.getAttribute('aria-label'),
    innerText: (n.innerText || '').replace(/\s+/g, ' ').trim(),
    screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    transform: n.style.transform,
    testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    arias: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
    // 标题元素逐个
    texts: Array.from(n.querySelectorAll('*')).filter((e) => e.children.length === 0 && (e.textContent || '').trim())
      .map((e) => { const er = e.getBoundingClientRect();
        return { tag: e.tagName, text: (e.textContent || '').trim().slice(0, 60), box: `${Math.round(er.x)},${Math.round(er.y)} ${Math.round(er.width)}×${Math.round(er.height)}` }; }).slice(0, 12),
  };
}, SELF);
log('\n=== ② 本轮自建音频节点 ===');
log(JSON.stringify(out.selfInfo, null, 1));
save();

// ---- ③ 盯着它从 processing 走到 ready ----
out.timeline = [];
for (let k = 1; k <= 20; k++) {
  await p.waitForTimeout(1500);
  const s = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return { __err: 'gone' };
    return { t: (n.innerText || '').replace(/\s+/g, ' ').trim(), aria: n.getAttribute('aria-label') };
  }, SELF);
  const st = await status();
  out.timeline.push({ k, s, st });
  log(`  #${String(k).padStart(2)} ${JSON.stringify(s.t)}`);
  save();
  if (!/processing|正在上传/.test(s.t || '')) { log('  ⇒ 不再是 processing'); out.settledAt = k * 1500; break; }
}

out.end = await status();
log('\n终点：', JSON.stringify(out.end));
save();
log('\nDONE d');
process.exit(0);
