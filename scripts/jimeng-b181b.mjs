// 批次 181 b 轮：修 a 轮两个问题 ① 指纹里混了 id ⇒ 「同类型不同指纹数」恒等于节点数，
// 那项判据**测的是 id 差异不是组件差异**；② 把图片节点的 `alt` 与文本节点的
// `aria-label` **逐字读全**。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '181b' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 数据 = await p.evaluate(() => {
  const out = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const id = n.getAttribute('data-id');
    const h = document.getElementById(`canvas-node-description-${id}`);
    if (!h) continue;
    const 类型 = (n.className.match(/react-flow__node-(\S+)/) || [])[1] || null;
    // 🔑 指纹里**剔除 id**（`rf__node-node_xxx` 与宿主自身的 id 属性）
    const 链 = [];
    for (let x = h; x && x !== document.body; x = x.parentElement) {
      let c = x.tagName.toLowerCase();
      if (x.dataset?.testid) c += `[testid=${x.dataset.testid}]`;
      if (x.getAttribute('role')) c += `[role=${x.getAttribute('role')}]`;
      if (typeof x.className === 'string' && x.className.trim())
        c += '.' + x.className.trim().split(/\s+/).filter((k) => !k.includes('node_') && k !== 'react-flow__node' && k !== 'react-flow__nodes' && k !== 'react-flow__viewport' && k !== 'xyflow__viewport' && k !== 'react-flow__container' && k !== 'react-flow__pane' && k !== 'react-flow__renderer').slice(0, 4).join('.');
      链.push(c);
      if (链.length >= 4) break;
    }
    out.push({ id, 类型, 指纹: 链.join(' > '), 宿主标签: h.tagName.toLowerCase(),
      innerText: (h.innerText || '').trim(),
      alt: h.getAttribute('alt'),
      宿主ariaLabel: h.getAttribute('aria-label'),
      宿主textContent: (h.textContent || '').trim().slice(0, 160) });
  }
  return out;
});
rec.总数 = 数据.length;
// 剔除 id 后，同类型指纹是否唯一
const 分组 = 数据.reduce((a, x) => { (a[x.类型] ||= []).push(x); return a; }, {});
rec.剔除id后的指纹 = {};
for (const [t, 们] of Object.entries(分组)) {
  const uniq = [...new Set(们.map((x) => x.指纹))];
  rec.剔除id后的指纹[t] = { 节点数: 们.length, 不同指纹数: uniq.length, 指纹们: uniq };
}
// 图片 / 文本 / 音视频：把**所有可能带文案的地方**逐字列出来
rec.文案载体 = {};
for (const [t, 们] of Object.entries(分组)) {
  const s = 们[0];
  rec.文案载体[t] = { 节点数: 们.length, 样本id: s.id,
    宿主标签: s.宿主标签, innerText: s.innerText, alt: s.alt, 宿主ariaLabel: s.宿主ariaLabel, textContent: s.宿主textContent };
}
// 音视频的通用壳：audio 与 external 第 2 层都没有 testid —— 验证一下全页有几个这种「无 testid 的壳」
rec.无testid的壳 = await p.evaluate(() => {
  const 壳 = new Map();
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const h = document.getElementById(`canvas-node-description-${n.getAttribute('data-id')}`);
    if (!h) continue;
    const 父 = h.parentElement; if (!父) continue;
    const k = `${(n.className.match(/react-flow__node-(\S+)/) || [])[1]} → 父[testid=${父.dataset?.testid || '（无）'}] class=${typeof 父.className === 'string' ? 父.className : ''}`;
    壳.set(k, (壳.get(k) || 0) + 1);
  }
  return [...壳.entries()].map(([k, n]) => ({ 壳: k, 节点数: n }));
});
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
