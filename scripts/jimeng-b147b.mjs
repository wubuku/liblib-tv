// 批次 147 b 轮 —— 顺着 a 轮的两个反证往下挖：音频面板的真身容器 + 展开/收起两态。
//
// 🔑 a 轮的两个反证（都不是假设，是读数）：
//   ① 选中一个音频节点时，全页 **`.node-toolbar` 实例数 = 0** —— 面板**不是** `.node-toolbar`。
//      （但批次 29 / 131 都把「音频生成表单」记在 `node-toolbar` 名下。）
//   ② **`展开音频生成器` 每次都出现 1 次**（`<BUTTON 40×40>`、**无 testid**、**不在 `.node-toolbar` 内**）
//      —— 批次 137 记的「两次都没出现」被推翻。
//
// 🔑 合起来只有一个解释：**音频面板默认是收起态**，屏上只有那一枚 40×40 的展开钮；
//   批次 29 量到的 `680×204` / 「11 个 svg」是**展开态**。
//   ⇒ 那批次 29 在展开态里记下的 aria 逐字「展开音频生成器」就值得怀疑：
//   展开后这个按钮**到底还叫不叫「展开」**？
//
// 本轮四问：
//   Q1 **收起态**与**展开态**各自的容器是谁（从按钮往上走祖先链，逐层记 tag/class/testid/pe）
//   Q2 展开态的面板盒、按钮全表、svg 数 ⇒ 与批次 29 的 `680×204` / 11 svg / 批次 131 的 10 按钮 对账
//   Q3 展开态下 `.node-toolbar` 实例数 ⇒ 批次 131 把音频表单记在 `node-toolbar` 名下是否成立
//   Q4 收起回去之后是否**逐字复原**（可逆性）
//   Q5 对照：点一个**文本节点**，`.node-toolbar` 是不是就出现了 ⇒ 它属于哪一族
//
// ⚠️ 只做「展开 / 收起 / 选节点 / 点空白」，**不按生成、不输入一个字**。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 147, 轮: 'b', 目的: '音频面板真身容器 + 展开/收起两态 + node-toolbar 归属' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };

/** 逐层祖先链：从命中的 aria 元素往上 8 层，逐层记身份。 */
const 祖先链 = (aria) => p.evaluate((a) => {
  const e = Array.from(document.querySelectorAll('[aria-label]')).find((q) => q.getAttribute('aria-label') === a);
  if (!e) return { __err: 'not-found' };
  const 链 = []; let n = e;
  for (let i = 0; i < 9 && n; i++, n = n.parentElement) {
    const r = n.getBoundingClientRect(); const cs = getComputedStyle(n);
    链.push({ 级: i, tag: n.tagName, cls: String(n.getAttribute('class') || '').slice(0, 70),
      testid: n.getAttribute('data-testid'), role: n.getAttribute('role'), aria: n.getAttribute('aria-label'),
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
      可见: cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0.01, pe: cs.pointerEvents, z: cs.zIndex });
  }
  return 链;
}, aria);

/** 面板总普查：候选容器一律列出，并给每个面板状祖先做按钮/svg 计数。 */
const 面板普查 = () => p.evaluate(() => {
  const 容器候选 = ['node-toolbar', 'generation-form', 'react-flow__node-toolbar', 'node-feature-chrome-host',
    'selection-context-toolbar', 'default-feature-overlay-interaction-boundary'];
  const 出 = {};
  for (const c of 容器候选) {
    const els = Array.from(document.querySelectorAll('.' + c));
    出[c] = els.map((e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
        可见: cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0.01,
        按钮数: e.querySelectorAll('button,[role=button]').length, svg数: e.querySelectorAll('svg').length,
        逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 70),
        在节点内: !!e.closest('.react-flow__node') }; });
  }
  // 兜底：找「含那个 40×40 展开钮」的最小的有面积祖先
  const 钮 = Array.from(document.querySelectorAll('[aria-label="展开音频生成器"]'))[0];
  let 面板 = null;
  if (钮) { let n = 钮; while (n && !(n.getBoundingClientRect().width > 200)) n = n.parentElement; 面板 = n; }
  const 面板读 = 面板 ? (() => { const r = 面板.getBoundingClientRect(); const cs = getComputedStyle(面板);
    return { tag: 面板.tagName, cls: String(面板.getAttribute('class') || '').slice(0, 70),
      testid: 面板.getAttribute('data-testid'), role: 面板.getAttribute('role'), aria: 面板.getAttribute('aria-label'),
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
      pe: cs.pointerEvents, z: cs.zIndex, display: cs.display,
      在节点内: !!面板.closest('.react-flow__node'),
      按钮数: 面板.querySelectorAll('button,[role=button]').length, svg数: 面板.querySelectorAll('svg').length,
      逐字: (面板.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 110),
      按钮: Array.from(面板.querySelectorAll('button,[role=button]')).map((b, k) => { const q = b.getBoundingClientRect();
        return { 序: k, tag: b.tagName, aria: b.getAttribute('aria-label'), testid: b.getAttribute('data-testid'),
          ariaDisabled: b.getAttribute('aria-disabled'), dataDisabled: b.getAttribute('data-disabled'),
          盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10],
          svg数: b.querySelectorAll('svg').length }; }) }; })() : null;
  return { 容器候选: 出, 面板读, 浮层数: document.querySelectorAll('[role=dialog],[data-testid="generation-form"]').length };
});

const 清零 = async () => {
  for (let k = 0; k < 4 && (await selCount(p)) > 0; k++) {
    const 空 = await p.evaluate(() => {
      const 坏 = (x, y) => { const h = document.elementFromPoint(x, y);
        if (!h) return 1;
        if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]')) return 1;
        if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
        return !(h.classList && h.classList.contains('react-flow__pane')); };
      for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
      return { __err: 'no-free-pane' };
    });
    if (空.__err) break;
    await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1000);
  }
  return selCount(p);
};

/** 找一个可点的目标节点，返回落点。 */
const 选一个 = async (id) => {
  await 清零();
  for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
  if (落.__err) return { __err: 'no-point:' + 落.__err };
  const 归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
    const n = h && h.closest('.react-flow__node');
    return { 命中: n ? n.getAttribute('data-id') : null, 对: !!(n && n.getAttribute('data-id') === i),
      是按钮: !!(h && (h.tagName === 'BUTTON' || h.closest('button,[role=button]'))) }; }, [落.x, 落.y, id]);
  if (!归属.对) return { __err: 'wrong-target', 归属 };
  if (归属.是按钮) return { __err: 'landing-is-button', 归属 };
  await p.mouse.click(落.x, 落.y); await p.waitForTimeout(2400); await settle(p, R);
  return { 落, 归属 };
};

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits() };

  const 可点 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const r = n.getBoundingClientRect(); let 好 = 0;
    for (let y = Math.ceil(r.y) + 4; y <= r.y + r.height - 4; y += 4)
      for (let x = Math.ceil(r.x) + 4; x <= r.x + r.width - 4; x += 4) {
        if (x < 1 || y < 1 || x >= innerWidth || y >= innerHeight) continue;
        const h = document.elementFromPoint(x, y); if (h && (h === n || n.contains(h))) 好++; }
    return { id: n.getAttribute('data-id'), 独占像素: 好, 态: n.querySelector('[data-testid="audio-node-empty"]') ? 'audio'
      : (n.querySelector('.ProseMirror') || n.querySelector('[data-testid*="text"]') ? 'text' : 'other'),
      aria: (n.getAttribute('aria-label') || '').slice(0, 24) };
  }).filter((q) => q.独占像素 > 0).sort((a, b2) => b2.独占像素 - a.独占像素));
  rec.可点数 = { 音频: 可点.filter((q) => q.态 === 'audio').length, 文本: 可点.filter((q) => q.态 === 'text').length, 其他: 可点.filter((q) => q.态 === 'other').length };

  // ============ Q1–Q4：音频节点 收起态 → 展开态 → 复原 ============
  const 音频 = 可点.find((q) => q.态 === 'audio');
  if (!音频) rec.中止 = '无可点音频节点';
  else {
    rec.目标音频 = 音频;
    rec.选中 = await 选一个(音频.id);
    if (rec.选中.__err) rec.中止 = '选中失败:' + rec.选中.__err;
    else {
      rec.收起态 = { 普查: await 面板普查(), 祖先链: await 祖先链('展开音频生成器') };

      // 🔴 点之前先断言：那必须是一枚 BUTTON，且**不是**生成/扣费按钮
      const 钮位 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('[aria-label="展开音频生成器"]'))[0];
        if (!e) return { __err: 'no-button' };
        const r = e.getBoundingClientRect();
        return { tag: e.tagName, 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          是生成类: /生成|generate/i.test(e.getAttribute('aria-label') || '') && !/展开|收起|折叠/.test(e.getAttribute('aria-label') || ''),
          逐字: (e.innerText || '').trim(), 在视口内: r.x >= 0 && r.y >= 0 && r.width > 0 };
      });
      rec.钮位 = 钮位;
      if (钮位.__err || 钮位.tag !== 'BUTTON' || 钮位.是生成类 || !钮位.在视口内) rec.中止 = '钮位不安全:' + JSON.stringify(钮位);
      else {
        await p.mouse.click(钮位.盒[0] + Math.round(钮位.盒[2] / 2), 钮位.盒[1] + Math.round(钮位.盒[3] / 2));
        await p.waitForTimeout(2600); await settle(p, R);
        rec.展开态 = { 普查: await 面板普查(), 状态行: await R.status(),
          展开词还在吗: await p.evaluate(() => ({ 展开: document.querySelectorAll('[aria-label="展开音频生成器"]').length,
            收起: document.querySelectorAll('[aria-label*="收起"]').length,
            收起逐字: Array.from(document.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')).filter((a) => /收起|折叠/.test(a || '')) })) };

        // Q4 复原：再点一次同一个钮
        const 再钮 = await p.evaluate(() => {
          const c = Array.from(document.querySelectorAll('[aria-label="展开音频生成器"]'));
          if (c.length) { const r = c[0].getBoundingClientRect();
            return { 命中: '展开音频生成器', 盒: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }
          const d = Array.from(document.querySelectorAll('[aria-label*="收起"]'));
          if (d.length) { const r = d[0].getBoundingClientRect();
            return { 命中: d[0].getAttribute('aria-label'), 盒: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }
          return { __err: 'no-toggle' };
        });
        rec.再钮 = 再钮;
        if (!再钮.__err) {
          await p.mouse.click(再钮.盒[0], 再钮.盒[1]);
          await p.waitForTimeout(2400); await settle(p, R);
          rec.复原态 = await 面板普查();
        }
      }
    }
  }

  // ============ Q5：点一个文本节点，看 `.node-toolbar` 是否出现 ============
  const 文本 = 可点.find((q) => q.态 === 'text');
  if (文本) {
    rec.目标文本 = 文本;
    rec.选中文本 = await 选一个(文本.id);
    if (!rec.选中文本.__err) rec.文本态 = await 面板普查();
  } else rec.文本对照 = '无可点文本节点';
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

await 清零();
for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits(),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };

// ---- 出表 ----
rec.摘要 = {
  收起态面板: rec.收起态 && rec.收起态.普查 && rec.收起态.普查.面板读 && {
    cls: rec.收起态.普查.面板读.cls, 盒: rec.收起态.普查.面板读.盒,
    按钮数: rec.收起态.普查.面板读.按钮数, svg数: rec.收起态.普查.面板读.svg数 },
  展开态面板: rec.展开态 && rec.展开态.普查.面板读 && {
    cls: rec.展开态.普查.面板读.cls, 盒: rec.展开态.普查.面板读.盒,
    按钮数: rec.展开态.普查.面板读.按钮数, svg数: rec.展开态.普查.面板读.svg数 },
  展开态nodeToolbar实例: rec.展开态 && rec.展开态.普查.容器候选['node-toolbar'].length,
  收起态nodeToolbar实例: rec.收起态 && rec.收起态.普查.容器候选['node-toolbar'].length,
  文本态nodeToolbar实例: rec.文本态 && rec.文本态.容器候选['node-toolbar'].map((q) => ({ 盒: q.盒, 可见: q.可见, 按钮数: q.按钮数 })),
};
console.log(JSON.stringify(rec.摘要, null, 1));
console.log('展开态按钮表:', JSON.stringify(rec.展开态 && rec.展开态.普查.面板读 && rec.展开态.普查.面板读.按钮, null, 1));
console.log('展开词还在吗:', JSON.stringify(rec.展开态 && rec.展开态.展开词还在吗));
console.log('收起态祖先链:', JSON.stringify(rec.收起态 && rec.收起态.祖先链, null, 1));
console.log('收尾:', JSON.stringify(rec.收尾), '| 中止:', rec.中止 || '无', '| 异常:', rec.异常 || '无');

断言('① 走完 收起→展开→复原 三步（无一中止）', !rec.中止 && rec.展开态 && rec.复原态, { 中止: rec.中止 });
if (rec.展开态 && rec.展开态.普查.面板读) {
  断言('② 展开态面板的**祖先链里每一层都记到了身份**', rec.收起态.祖先链 && rec.收起态.祖先链.length >= 6, { 层数: rec.收起态.祖先链 && rec.收起态.祖先链.length });
  断言('③ 展开态下 `.node-toolbar` **仍然 0 个**（⇒ 批次 131 的归属不成立）',
    (rec.展开态.普查.容器候选['node-toolbar'].length) === 0, rec.展开态.普查.容器候选['node-toolbar'].length);
  断言('④ 展开后那枚钮**仍然逐字叫「展开音频生成器」**（aria 不随展开态翻转）',
    rec.展开态.展开词还在吗.展开 === 1, rec.展开态.展开词还在吗);
}
rec.断言全过 = 断言过;
fs.writeFileSync(new URL('./_tmp-b147b.json', import.meta.url), JSON.stringify(rec, null, 1));
await b.close();
