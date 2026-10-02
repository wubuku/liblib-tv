// Batch BI3 — 正确定位并实点「翻译提示词」。
//
// BI2 的教训：点节点中心**没选中**（`.react-flow__node.selected` 四次都读到 null），
// 于是根本没采到参数条，只采到底栏那 12 枚全局按钮 —— 判据没错，是**状态没造出来**。
// 这与 §34「每个动作要配一个它一定会产生变化的初始状态」同源。
//
// 本轮改三件事：
//  ① 用**独占点**点节点（扫 rect 内各点，elementFromPoint 归属校验），
//     每次点完**断言选中数 == 1**，不满足就重试，绝不带着假状态往下走；
//  ② 参数条区域用**上一批图片节点参数条的实测 y 区间**收窄（y 740~800），
//     并把底栏那 12 枚按 aria 名单排除；
//  ③ ⭐ 用**悬停读 tooltip** 给每枚无名按钮正名（AZ 立的老规矩，只读不触发），
//     认准了再点 —— 不靠猜、不靠下标（BD4 就是靠下标点错了按钮）。
//
// ⚠️ 安全边界：只在**提示词为空**的节点上点「翻译提示词」；
//    若它对有内容的节点会发翻译请求，本轮不制造那种状态，也不碰任何生成按钮。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBI3';
const { browser, page } = await launch();

/** 找一个**只属于**这个节点的点，并点它；返回点选是否真的成功。 */
async function selectNode(id, tries = 3) {
  for (let k = 0; k < tries; k++) {
    const pt = await page.evaluate((nid) => {
      const n = [...document.querySelectorAll('.react-flow__node')].find((x) => x.getAttribute('data-id') === nid);
      if (!n) return { err: 'no node' };
      const r = n.getBoundingClientRect();
      if (r.width < 10) return { err: 'node offscreen' };
      for (let fy = 0.18; fy <= 0.85; fy += 0.1) {
        for (let fx = 0.08; fx <= 0.95; fx += 0.06) {
          const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
          const o = document.elementFromPoint(x, y);
          if (o && o.closest('.react-flow__node') === n) return { x, y };
        }
      }
      return { err: 'no exclusive point' };
    }, id);
    if (pt.err) return { ok: false, why: pt.err };
    await page.mouse.click(pt.x, pt.y);
    await page.waitForTimeout(2400);
    const sel = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
    if (sel === 1) return { ok: true, at: [pt.x, pt.y] };
  }
  return { ok: false, why: '选中数始终不是 1' };
}

/** 参数条区域的可交互元素；底栏那 12 枚按 aria 名单排除。 */
const BOTTOM_BAR = ['添加节点', '移动', '素材库', '角色造型室', '生成历史', '快捷键', '教程',
  '整理画布，Option+Shift+F', '切换小地图', '隐藏节点连线', '网格吸附', '缩放选项', '资产管理'];

const barButtons = () => page.evaluate((excl) => {
  const skip = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  const out = [];
  for (const e of document.querySelectorAll('button,[role="button"]')) {
    if (skip.has(e.tagName)) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    if (r.y < 600) continue;                                  // 参数条在画面下方
    const aria = e.getAttribute('aria-label');
    if (aria && excl.includes(aria)) continue;                // 排掉底栏全局按钮
    if ((e.innerText || '').trim() && r.y < 740 && r.x < 700) continue; // 排掉左侧工具条文字项
    const svg = e.querySelector('svg');
    out.push({
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
      aria, title: e.getAttribute('title'),
      paths: svg ? svg.querySelectorAll('path').length : 0,
      circles: svg ? svg.querySelectorAll('circle').length : 0,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
    });
  }
  return out;
}, BOTTOM_BAR);

/** 悬停读 Mantine Tooltip（只读不触发，AZ 的老规矩）。 */
const readTip = async (x, y) => {
  await page.mouse.move(x, y); await page.waitForTimeout(1500);
  return page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip-tooltip"]')]
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim())
    .filter((t) => t && !/按 ESC 退出|^新功能/.test(t)));
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(2000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '独占点选节点 + 悬停读 tooltip 正名 + 空提示词下实点翻译提示词' });

  const out = { perNode: [] };
  const NODES = [
    { id: 't-UtVx3lZmrV', name: '文本节点 1' },
    { id: 'i-9nlG6HdjK2', name: '图片节点 2' },
    { id: 'v-eMpqKtiLlx', name: '视频节点 3' },
    { id: 'a-THmbuJXQj4', name: '音频节点 1' },
  ];

  let translateBtn = null;
  for (const nd of NODES) {
    console.log(`\n══════ ${nd.name}（${nd.id}）══════`);
    const s = await selectNode(nd.id);
    if (!s.ok) { console.log('  ✗ 没能选中：', s.why); out.perNode.push({ ...nd, select: s }); continue; }
    const who = await page.evaluate(() => { const n = document.querySelector('.react-flow__node.selected');
      return n ? (n.getAttribute('data-id')) : null; });
    console.log(`  ✅ 选中成功：${who}（点 ${s.at}）`);
    if (who !== nd.id) { console.log('  ⚠️ 选中的不是目标节点，放弃这一项'); out.perNode.push({ ...nd, select: s, wrongNode: who }); await page.keyboard.press('Escape'); await page.waitForTimeout(1000); continue; }

    // 提示词框内容 —— ⚠️ 只有确认为空才允许点「翻译提示词」
    const prompt = await page.evaluate(() => [...document.querySelectorAll('textarea,[contenteditable="true"]')]
      .map((e) => { const r = e.getBoundingClientRect();
        return { ph: e.getAttribute('placeholder') || '', val: (e.value || e.innerText || '').slice(0, 40),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
      .filter((x) => x.rect[2] > 120));
    const empty = prompt.length === 0 || prompt.every((p) => !p.val.trim());
    console.log(`  提示词框：${JSON.stringify(prompt)} → ${prompt.length ? (empty ? '**全空** ✅ 可点' : '**有内容** ⛔ 不点') : '没找到框（该类型可能用别的输入形态）'}`);

    const btns = await barButtons();
    console.log(`  参数条可交互元素 ${btns.length} 枚，逐个悬停读 tooltip：`);
    const named = [];
    for (const b of btns) {
      const tip = await readTip(b.cx, b.cy);
      const label = tip[0] || (b.text ? `文字「${b.text}」` : '（无 tooltip、无文字）');
      console.log(`    [${b.rect}] ${label}   ← 自身文字 "${b.text}" aria=${b.aria} path=${b.paths} circle=${b.circles}`);
      named.push({ ...b, tip, label });
    }

    const tr = named.find((b) => /翻译/.test((b.tip || []).join(' ')) || /翻译/.test(b.text || '') || /翻译/.test(b.aria || ''));
    console.log(`  ⭐ 认出的「翻译提示词」：${tr ? `[${tr.rect}] tooltip=${JSON.stringify(tr.tip)}` : '**这一类节点上没有**'}`);
    if (tr) translateBtn = translateBtn || { node: nd.name, btn: tr };

    if (tr && empty) {
      console.log(`  → 在空提示词节点上实点「翻译提示词」…`);
      const fp1 = await fingerprint(page);
      const domBefore = await page.evaluate(() => ({ ta: [...document.querySelectorAll('textarea')].map((e) => e.value).join('|'),
        node: (document.querySelector('.react-flow__node.selected')?.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) }));
      await page.mouse.click(tr.cx, tr.cy);
      await page.waitForTimeout(3000);
      const fp2 = await fingerprint(page);
      const toast = await page.evaluate(() => [...document.querySelectorAll('[class*="Toast"],[class*="toast"],[role="alert"],[role="status"]')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
        .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()));
      const domAfter = await page.evaluate(() => ({ ta: [...document.querySelectorAll('textarea')].map((e) => e.value).join('|'),
        node: (document.querySelector('.react-flow__node.selected')?.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) }));
      const panels = diffPanels(fp1, fp2);
      console.log(`     新增面板 ${panels.length} 个；提示条 ${JSON.stringify(toast)}`);
      console.log(`     文本域内容 改前="${domBefore.ta}" 改后="${domAfter.ta}"；节点文本 改前="${domBefore.node}" 改后="${domAfter.node}"`);
      out.translate = { node: nd.name, panels: panels.length, toast, before: domBefore, after: domAfter };
      await shot(page, 'M-204-翻译提示词-空提示词.png');
      out.shot = 'M-204-翻译提示词-空提示词.png';
    }

    out.perNode.push({ ...nd, select: s, prompt, empty, buttons: named.length,
      names: named.map((b) => b.label), translate: !!tr });
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  }

  console.log('\n══════ 汇总 ══════');
  for (const p of out.perNode) {
    console.log(`  ${p.name}：选中=${p.select?.ok} 参数条=${p.buttons ?? '—'} 枚 翻译提示词=${p.translate ?? '—'}`);
  }
  console.log('  各节点参数条实名：');
  for (const p of out.perNode) if (p.names) console.log(`    ${p.name}：${JSON.stringify(p.names)}`);

  await logStep(B, {
    id: 'BI3-translate-prompt-button',
    title: '四类节点参数条逐枚悬停实名 + 空提示词下实点「翻译提示词」',
    target: 'BI2 因为「没选中节点」而只采到底栏 12 枚全局按钮。本轮改用独占点选 + '
      + '断言选中数==1，再逐枚悬停读 tooltip 正名（AZ 的老规矩），认准了才点。'
      + '⚠️ 只在提示词为空的节点上点。',
    evidence: out,
    visible_text: JSON.stringify({ perNode: out.perNode?.map?.((p) => ({ 节点: p.name, 选中: p.select?.ok,
      条: p.buttons, 翻译: p.translate, 空提示词: p.empty })), translate: out.translate }).slice(0, 3000),
    shot: out.shot,
  });
  console.log('\nBI3 完成');
} finally {
  await browser.close();
}
