// 批次 90 · E：抓手态下，底部 dock 的「选择工具」按钮去哪了。
//
// 现象：连续四轮跑 `jimeng-troubleshoot-predicates.mjs`，每轮都
//   - 读到当前工具是 **抓手工具**
//   - 点节点**选不中**（`sel` 恒 0）
//   - 恢复动作报 **`no-button`** —— 找不到 `aria-label="选择工具"` 的按钮
//
// ⇒ 三种可能，必须分开：
//   (a) 抓手态下 dock **根本不渲染**「选择工具」那个钮（那 P03 判据也不完整）；
//   (b) 钮在，但 aria 逐字**变了**；
//   (c) 钮在视口外 / 被遮挡，点不到。
//
// ⇒ **P1**：把底部 dock 全部可点元素连 aria、class、几何一起打出来。
//   另：抓手态下点一个**视口内、elementFromPoint 属于它**的节点，sel 是不是真的不动？
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const selCount = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);

out.dock = await p.evaluate(() => {
  const all = Array.from(document.querySelectorAll('button,[role="button"],a'));
  return all.map((e) => { const r = e.getBoundingClientRect();
    return { tag: e.tagName, aria: e.getAttribute('aria-label'), tid: e.getAttribute('data-testid'),
      title: e.getAttribute('title'), text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18),
      cls: String(e.className || '').slice(0, 44), pe: getComputedStyle(e).pointerEvents,
      box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; })
    .filter((x) => x.box.split('@')[1].split(',').map(Number)[1] >= 640)   // 底部 dock 大致区域
    .filter((x) => x.box !== '0×0@0,0');
});
log('══ 底部区域可点元素 ' + out.dock.length + ' 个：');
for (const d of out.dock) log(`   aria=${JSON.stringify(d.aria)} tid=${d.tid} text=${JSON.stringify(d.text)} ${d.box} pe=${d.pe}`);

out.tools = out.dock.filter((d) => d.aria && /工具|选择|抓手/.test(d.aria));
log('\n══ 与「工具」有关的：' + JSON.stringify(out.tools, null, 1));

// 抓手态下点一个视口内、elementFromPoint 属于它的节点
const pt = await p.evaluate(() => {
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const r = n.getBoundingClientRect();
    if (!(r.left >= 0 && r.top >= 0 && r.right <= 1280 && r.bottom <= 720)) continue;
    for (let fx = 0.3; fx <= 0.7; fx += 0.2) for (let fy = 0.3; fy <= 0.7; fy += 0.2) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const el = document.elementFromPoint(x, y);
      if (el && el.closest('.react-flow__node') === n) return { id: n.getAttribute('data-id'), x, y };
    }
  }
  return null;
});
log('\n落点：', JSON.stringify(pt));
if (pt) {
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1100);
  out.clickInGrab = { sel: await selCount() };
  log('抓手态下点节点后 sel =', out.clickInGrab.sel);
  // 对照：双击（抓手态下双击通常不冲突）
  await p.mouse.dblclick(pt.x, pt.y); await p.waitForTimeout(1100);
  out.dblclickInGrab = { sel: await selCount() };
  log('双击后 sel =', out.dblclickInGrab.sel);
}
out.end = { sel: await selCount() };
writeFileSync(new URL('./_tmp-b90e.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
