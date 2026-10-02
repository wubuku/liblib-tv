// Batch BI4 — 收口两件事：
//  ① BI3 里文本/音频节点的参数条**掉到视口外**（文本在 y=785 之下、音频在 x=-87），
//     悬停点在视口外 → tooltip 读不到 → 被我标成「（无 tooltip、无文字）」。
//     ⭐ **这不能记成「这两类节点没有该按钮」** —— 那是视口假象，不是事实。
//     治法：先把缩放调小到参数条也进视口，再逐枚悬停。
//  ② 「翻译提示词」在空提示词下点完，提示条读数是 `[""]` —— **空读数**。
//     §34 的纪律：空读数不能直接判「什么都没发生」。
//     治法：⭐ **做阳性对照** —— 同一节点上点「提示词优化」，
//     它在 AW 里已知会弹「提示词为空，请输入内容后点击」。
//     若对照那次**读到了**提示文字、翻译那次**读不到**，
//     那么「翻译不给提示」才是结论；若两次都读不到，说明是**读法失效**。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBI4';
const { browser, page } = await launch();

const BOTTOM_BAR = ['添加节点', '移动', '素材库', '角色造型室', '生成历史', '快捷键', '教程',
  '整理画布，Option+Shift+F', '切换小地图', '隐藏节点连线', '网格吸附', '缩放选项', '资产管理'];

const barButtons = () => page.evaluate((excl) => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const out = [];
  for (const e of document.querySelectorAll('button,[role="button"]')) {
    if (skip.has(e.tagName)) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    const aria = e.getAttribute('aria-label');
    if (aria && excl.includes(aria)) continue;
    const svg = e.querySelector('svg');
    out.push({ text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), aria,
      paths: svg ? svg.querySelectorAll('path').length : 0,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      inView: r.x >= 0 && r.y >= 0 && r.x + r.width <= window.innerWidth && r.y + r.height <= window.innerHeight });
  }
  return out;
}, BOTTOM_BAR);

const readTip = async (x, y) => {
  await page.mouse.move(x, y); await page.waitForTimeout(1500);
  return page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip-tooltip"]')]
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
    .filter((t) => t && !/按 ESC 退出|^新功能/.test(t)));
};

/** 读「页面顶部提示」—— AW 记过它不是 Toast 组件，得按位置捞。 */
const readTopHint = () => page.evaluate(() => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  return [...document.querySelectorAll('body *')].filter((e) => !skip.has(e.tagName))
    .map((e) => { const r = e.getBoundingClientRect();
      return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r }; })
    .filter((x) => x.r.width > 20 && x.r.height > 14 && x.r.y < 160 && x.r.y > 0 && x.t.length < 60)
    .filter((x) => /提示词|为空|请输入/.test(x.t))
    .map((x) => ({ t: x.t, rect: [Math.round(x.r.x), Math.round(x.r.y), Math.round(x.r.width), Math.round(x.r.height)] }));
});

async function selectNode(id, tries = 3) {
  for (let k = 0; k < tries; k++) {
    const pt = await page.evaluate((nid) => {
      const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === nid);
      if (!n) return { err: 'no node' };
      const r = n.getBoundingClientRect();
      if (r.width < 10) return { err: 'node offscreen' };
      for (let fy = 0.18; fy <= 0.85; fy += 0.1) for (let fx = 0.08; fx <= 0.95; fx += 0.06) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const o = document.elementFromPoint(x, y);
        if (o && o.closest('.react-flow__node') === n) return { x, y };
      }
      return { err: 'no exclusive point' };
    }, id);
    if (pt.err) return { ok: false, why: pt.err };
    await page.mouse.click(pt.x, pt.y); await page.waitForTimeout(2400);
    const sel = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
    const who = await page.evaluate(() => document.querySelector('.react-flow__node.selected')?.getAttribute('data-id') ?? null);
    if (sel === 1 && who === id) return { ok: true, at: [pt.x, pt.y] };
  }
  return { ok: false, why: '选中数/选中对象不对' };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1800);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await beginBatch(B, { note: '缩放到参数条进视口 + 阳性对照裁定空读数' });

  const out = {};

  // ═══ ① 先把缩放调小，让参数条也进视口
  console.log('══════ ① 调小缩放，让参数条进视口 ══════');
  const z = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => x.getAttribute('aria-label') === '缩放选项');
    if (!e) return null; const r = e.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  if (z) {
    await page.mouse.click(z[0], z[1]); await page.waitForTimeout(1600);
    const inp = await page.$('input[aria-label="缩放比例"]');
    if (inp) { await inp.fill('35'); await inp.press('Enter'); await page.waitForTimeout(2200); }
    await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  }
  const scale = await page.evaluate(() => {
    const el = document.querySelector('.react-flow__viewport');
    const m = /scale\(([^)]+)\)/.exec(getComputedStyle(el).transform || '');
    return m ? m[1] : null; });
  console.log('  当前 scale =', scale, '视口 =', await page.evaluate(() => [innerWidth, innerHeight]));
  out.scale = scale;

  // ═══ ② 文本 / 音频节点重扫（这次参数条应该在视口内）
  console.log('\n══════ ② 文本 / 音频 节点参数条重扫 ══════');
  for (const nd of [{ id: 't-UtVx3lZmrV', name: '文本节点 1' }, { id: 'a-THmbuJXQj4', name: '音频节点 1' }]) {
    const s = await selectNode(nd.id);
    console.log(`\n  ── ${nd.name}：选中 ${s.ok ? '✅' : '✗ ' + s.why}`);
    if (!s.ok) continue;
    const btns = await barButtons();
    const onScreen = btns.filter((b) => b.inView);
    console.log(`     可交互 ${btns.length} 枚，其中**整枚在视口内** ${onScreen.length} 枚`);
    for (const b of onScreen) {
      if (b.text && b.text.length > 1 && b.rect[3] < 24) continue;   // 跳过画布上的「尝试：」文字项
      const tip = await readTip(b.cx, b.cy);
      console.log(`       [${b.rect}] tooltip=${JSON.stringify(tip)}  自身文字="${b.text}" aria=${b.aria}`);
      btns.find((x) => x.cx === b.cx && x.cy === b.cy).tip = tip;
    }
    out[nd.name] = onScreen.map((b) => ({ rect: b.rect, tip: b.tip, text: b.text, aria: b.aria }));
    await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  }

  // ═══ ③ 阳性对照：同一节点上点「提示词优化」（已知会弹提示），验证读法有效
  console.log('\n══════ ③ 阳性对照：视频节点上分别点「提示词优化」与「翻译提示词」 ══════');
  const sv = await selectNode('v-eMpqKtiLlx');
  console.log('  视频节点选中：', sv.ok ? '✅' : '✗');
  if (sv.ok) {
    const btns = await barButtons();
    const named = [];
    for (const b of btns.filter((x) => x.inView && x.rect[3] >= 24)) {
      const tip = await readTip(b.cx, b.cy);
      named.push({ ...b, tip });
      if (tip[0]) console.log(`    [${b.rect}] ${JSON.stringify(tip)}`);
    }
    const opt = named.find((b) => /提示词优化/.test((b.tip || []).join(' ')));
    const tr = named.find((b) => /翻译/.test((b.tip || []).join(' ')));
    console.log(`  ⭐ 认到：提示词优化=${opt ? JSON.stringify(opt.rect) : '无'}；翻译提示词=${tr ? JSON.stringify(tr.rect) : '无'}`);

    const probe = async (btn, label) => {
      if (!btn) return { label, skipped: '没认到按钮' };
      const fp1 = await fingerprint(page);
      await page.mouse.click(btn.cx, btn.cy); await page.waitForTimeout(3000);
      const fp2 = await fingerprint(page);
      const hint = await readTopHint();
      const ta = await page.evaluate(() => [...document.querySelectorAll('textarea')].map((e) => e.value).join('|'));
      const panels = diffPanels(fp1, fp2);
      await clearToasts(page); await page.waitForTimeout(1200);
      console.log(`  ── 点「${label}」：新增面板 ${panels.length}；顶部提示读数 ${JSON.stringify(hint)}；文本域="${ta}"`);
      return { label, rect: btn.rect, panels: panels.length, hint, ta, hintCount: hint.length };
    };
    const r1 = await probe(opt, '提示词优化');      // 阳性对照：已知会弹
    const r2 = await probe(tr, '翻译提示词');        // 待测
    out.positiveControl = r1;
    out.underTest = r2;
    console.log('\n  ⭐ 阳性对照成立？', r1.hintCount > 0 ? `是（读到 ${JSON.stringify(r1.hint)}）` : '否 —— 说明读法本身失效，结论不成立');
    console.log('  ⭐ 待测项读到提示？', r2.hintCount > 0 ? `是 ${JSON.stringify(r2.hint)}` : '否（0 条）');
  }

  await shot(page, 'M-205-参数条-35缩放全览.png');
  out.shot = 'M-205-参数条-35缩放全览.png';

  await logStep(B, {
    id: 'BI4-params-in-view-and-positive-control',
    title: '参数条进视口重扫 + 阳性对照裁定「翻译提示词无提示」',
    target: 'BI3 里文本/音频的参数条掉到视口外，悬停不到 → tooltip 空 → 被误标成「无名按钮」。'
      + '本轮先缩到 35% 让参数条进视口再逐枚悬停。'
      + '⭐ 「翻译提示词点了没提示」是**空读数**，不能直接当结论 —— '
      + '故同节点上点已知会弹提示的「提示词优化」做**阳性对照**，'
      + '对照读到、待测读不到，才说明是它真不给提示。',
    evidence: out,
    visible_text: JSON.stringify({ scale: out.scale, 文本: out['文本节点 1'], 音频: out['音频节点 1'],
      对照: out.positiveControl, 待测: out.underTest }).slice(0, 3000),
    shot: out.shot,
  });
  console.log('\nBI4 完成');
} finally {
  await browser.close();
}
