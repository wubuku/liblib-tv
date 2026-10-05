// 会话 mvs_fb62b78 · 批次 211 d 轮：测**机制**，不是现象。
//
// c 轮已在**同一缩放**下带阳性对照复现了现象：
//   `b22-upload`（图片｜**有 `<img>`**）→ before ⊕ **0** / after ⊕ 1
//   `视频 1`（视频｜空 `video-node-empty`）→ before ⊕ **1** / after ⊕ 1
//   `音频 68`（音频｜空 `audio-node-empty`）→ before ⊕ **1** / after ⊕ 1
// ⇒ 批次 59/73 的观测成立，且**排掉了 `20-reference.md:309` 记的「不同缩放互比」那个坑**。
//
// 🔴 但「机制未验证」还挂着。本轮验一个具体假设：
//
//   **H（上下文提供者假说）**：before ⊕ 那个入口叫「**添加上下文**」，
//   它的存在意义是「给这个节点喂素材」。**一旦节点自己已经有素材了，
//   它就从「需要被投喂的容器」变成了「可以投喂别人的上下文提供者」，
//   于是这个入口对它自己就不必要了。**
//
//   可测的推论：① 空节点的 before ⊕ 菜单里，各类型项多半因
//   「**没有可用的就绪资源**」而灰；② 而 `b22-upload` 这种**带素材的图片节点**，
//   应当在**别的节点**的「添加上下文」菜单里**变成可选项**（它是可用的上下文）。
//   ⇒ 若 ② 成立，H 就拿到了直接证据；若 `b22-upload` 在那里也是灰的，H 就被否掉。
//
// 本轮**只读**：只打开菜单读结构，不点任何菜单项；读完用 Esc 关闭并断言浮层归零。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { idsOf, selCount } from './jimeng-b139-lib.mjs';

const 目标集 = ['视频 1', '音频 68'];   // 两个空节点，各读一次它的 before ⊕ 菜单
const OUT = 'scripts/_tmp-b211d.json';
const rec = { 批次: '211d', 假设: 'H：before ⊕ 是「喂素材」的入口；节点自己有素材后它变成了上下文提供者，于是这个入口对它自己消失',
  判据: '看带素材的 b22-upload 在别人的「添加上下文」菜单里是不是可选项', 目标集, 菜单: {}, 无效臂: 0 };
const 落盘 = () => fs.writeFileSync(OUT, JSON.stringify(rec, null, 1));
let 全过 = true;
const 断言 = (名, ok, d) => { const v = !!ok; if (!v) 全过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(d).slice(0, 240))); return v; };

const { b, p } = await openCanvas();
const R = readers(p);

const 读浮层 = () => p.evaluate(() => {
  const 菜单 = document.querySelector('[data-testid="canvas-context-menu"],[role=menu]');
  if (!菜单) return null;
  const r = 菜单.getBoundingClientRect();
  const cs = getComputedStyle(菜单);
  const 项 = Array.from(菜单.querySelectorAll('[role=menuitem],li,button')).map((e) => {
    const q = e.getBoundingClientRect();
    const c = getComputedStyle(e);
    return {
      内文: (e.innerText || '').replace(/\s+/g, ' ').trim(),
      aria: e.getAttribute('aria-label'), ariaDisabled: e.getAttribute('aria-disabled'),
      尺寸: [Math.round(q.width), Math.round(q.height)],
      颜色: c.color, cursor: c.cursor, pointerEvents: c.pointerEvents,
    };
  });
  return { testid: 菜单.getAttribute('data-testid'), role: 菜单.getAttribute('role'),
    标题: (菜单.innerText || '').split('\n')[0].trim(), 盒: [Math.round(r.width), Math.round(r.height)],
    display: cs.display, 项数: 项.length, 项 };
});

try {
  rec.起点 = { 缩放: await R.zoom(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 积分: await R.credits(), 浮层: await R.overlays() };
  console.log('起点', JSON.stringify(rec.起点));
  断言('⓪ 76 节点 / 0 选中 / 浮层 0', rec.起点.节点数 === 76 && rec.起点.选中 === 0, rec.起点);

  const 索引 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
    id: n.getAttribute('data-id'), 标题: ((n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || '').trim() })));

  for (const 标题 of 目标集) {
    const hit = 索引.find((x) => x.标题 === 标题);
    if (!hit) { rec.菜单[标题] = { 无效: '找不到节点' }; rec.无效臂++; 落盘(); continue; }
    try {
      // 选中它（归属判据 + 硬断言，沿用 c 轮）
      const 候选 = await p.evaluate((nid) => {
        const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
        const r = n.getBoundingClientRect(); const 好 = [];
        for (let fy = 0.15; fy <= 0.86; fy += 0.14) for (let fx = 0.15; fx <= 0.86; fx += 0.14) {
          const x = r.x + r.width * fx, y = r.y + r.height * fy;
          if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
          const e = document.elementFromPoint(x, y);
          if (e && n.contains(e)) { 好.push([Math.round(x), Math.round(y)]); if (好.length >= 24) break; }
        }
        return 好;
      }, hit.id);
      if (!候选 || !候选.length) { rec.菜单[标题] = { 无效: '无归属候选点' }; rec.无效臂++; 落盘(); continue; }
      let 选中集 = [], 补点 = 0;
      for (let k = 0; k < 3; k++) {
        await p.mouse.click(候选[0][0], 候选[0][1]); 补点 = k + 1; await p.waitForTimeout(1500);
        选中集 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
        if (选中集.length === 1 && 选中集[0] === hit.id) break;
      }
      断言(`${标题}：选中集是它自己`, 选中集.length === 1 && 选中集[0] === hit.id, { 选中集, 补点 });

      // 点它的 **before ⊕**
      const btn = await p.evaluate((nid) => {
        const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
        const e = n.querySelector('[data-testid="flow-node-target-connection-menu-button"]'); if (!e) return null;
        const r = e.getBoundingClientRect();
        return { aria: e.getAttribute('aria-label'), 尺寸: [Math.round(r.width), Math.round(r.height)],
          点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
      }, hit.id);
      if (!btn) { rec.菜单[标题] = { 无效: '这个节点没有 before ⊕（读不到按钮）', 选中集 }; rec.无效臂++;
        console.log(标题, '⛔ 没有 before ⊕'); 落盘(); continue; }
      console.log(`\n[${标题}] before ⊕ ${JSON.stringify(btn.aria)} ${JSON.stringify(btn.尺寸)}`);
      await p.mouse.click(btn.点[0], btn.点[1]);
      await p.waitForTimeout(1500);
      // 🔴 打开模态后**绝不调 settle()**（它会连按 Esc 把刚开的菜单关掉 —— 立规 153）
      const 浮层数 = await R.overlays();
      const 菜单 = await 读浮层();
      rec.菜单[标题] = { id: hit.id, before按钮: btn, 补点, 浮层数, 菜单 };
      if (菜单) {
        console.log(`   菜单 ${菜单.testid}/${菜单.role} 标题「${菜单.标题}」 ${JSON.stringify(菜单.盒)} 共 ${菜单.项数} 项`);
        for (const it of 菜单.项) {
          console.log(`     · ${JSON.stringify(it.内文).padEnd(18)} aria=${JSON.stringify(it.aria)} disabled=${it.ariaDisabled} ${JSON.stringify(it.尺寸)} ${it.颜色} cursor=${it.cursor}`);
        }
      } else {
        console.log('   ⛔ 没读到菜单结构（浮层数 ' + 浮层数 + '）');
        rec.菜单[标题].无效 = '菜单 DOM 没读到';
        rec.无效臂++;
      }
      // 关掉，断言浮层归零
      await p.keyboard.press('Escape');
      await p.waitForTimeout(900);
      const 浮层后 = await R.overlays();
      rec.菜单[标题].关后浮层数 = 浮层后;
      断言(`${标题}：Esc 能关掉菜单（浮层归零）`, 浮层后 === 0, { 浮层后 });
    } catch (e) { rec.菜单[标题] = { 出错: e.message }; rec.无效臂++; console.log(标题, '🔴', e.message); }
    finally { 落盘(); }
  }
} finally {
  try {
    await p.keyboard.press('Escape'); await p.waitForTimeout(300);
    if (await selCount(p) > 0) { await p.mouse.click(30, 660); await p.waitForTimeout(700); }
  } catch (e) { rec.清场错 = e.message; }
  rec.收尾 = { 缩放: await R.zoom(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(), 积分: await R.credits(), 状态行: await R.status() };
  console.log('\n收尾', JSON.stringify(rec.收尾));
  断言('② 收尾：76 节点 / 0 选中 / 0 边 / 浮层 0 / 积分未变',
    rec.收尾.节点数 === 76 && rec.收尾.选中 === 0 && rec.收尾.浮层 === 0
    && rec.收尾.积分 === rec.起点.积分 && /0 edges/.test(rec.收尾.状态行 || ''), { 起点: rec.起点, 收尾: rec.收尾 });
  rec.断言全过 = 全过;
  落盘();
  await b.close();
}
