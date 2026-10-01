// 批次 62 取证：审「与 AI 对话」抽屉两条「未验证」的理由。
//
// 手册原话（ai-agent-drawer.md:59-62）：
//   「未实测，按产品提示使用」（本轮为守住扣费边界，全程未输入、未发送）
//   4. 点击某个技能 chip 后会展开对应的输入引导——**未验证**
//   5. 在输入卡输入想法，`/` 唤起技能、`@` 引用主体——**未验证**
//
// 批次 61 已经把这个推理链打断过一次：「属扣费前置动作」不等于扣费。
// 这里要用同样的尺子问一遍：**点 chip、在输入框打字，到底扣不扣积分？**
//
// 🔑 本脚本的顺序是刻意的：
//   1. **先做阳性对照**（点「收起」→ 抽屉关闭 → 再打开）。
//      在抽屉里点任何东西之前，先证明「我的点击在抽屉里有效」。
//      否则「点 chip 没反应」这个阴性读数毫无意义 —— 批次 50–61 反复栽在这。
//   2. 再逐个点 5 个技能 chip，记录展开内容 + 积分。
//   3. 最后才在输入卡打字（**不发送**），看 `/` 与 `@`。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OUT = new URL('./_tmp-b62-agent.json', import.meta.url);

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);

const credit = () => p.evaluate(() => {
  const t = document.body.innerText;
  const m = t.match(/(\d[\d,]*)\s*基础会员/);
  return m ? { raw: m[1], num: parseInt(m[1].replace(/,/g, ''), 10) } : { raw: null, num: null };
});
const statusLine = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const nodeIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));

// 抽屉：不是一个 data-testid，得自己找。先探。
const drawerDump = () => p.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; };
  // 候选：所有 fixed/absolute 且宽约 400、从 x≈868 起、右侧贴边的大面板
  const cands = Array.from(document.querySelectorAll('div,aside,section')).filter((e) => {
    const r = e.getBoundingClientRect();
    if (r.width < 340 || r.width > 460) return false;
    if (r.right < innerWidth - 12) return false;
    if (r.height < innerHeight * 0.6) return false;
    return vis(e);
  });
  if (!cands.length) return { open: false };
  // 取最外层（children 里不再包含另一个候选）
  let root = cands[0];
  for (const c of cands) if (!c.contains(root)) root = c;
  const r = root.getBoundingClientRect();
  const btn = (e) => { const bb = e.getBoundingClientRect();
    return { tag: e.tagName, aria: e.getAttribute('aria-label'), text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
      box: `${Math.round(bb.width)}x${Math.round(bb.height)}@${Math.round(bb.x)},${Math.round(bb.y)}` }; };
  return {
    open: true, box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    text: (root.innerText || '').replace(/\n{2,}/g, '\n').trim(),
    buttons: Array.from(root.querySelectorAll('button,[role="button"]')).filter(vis).map(btn),
    inputs: Array.from(root.querySelectorAll('input,textarea,[contenteditable="true"]')).filter(vis).map((e) => {
      const bb = e.getBoundingClientRect();
      return { tag: e.tagName, ph: e.getAttribute('placeholder'), aria: e.getAttribute('aria-label'),
        testid: e.getAttribute('data-testid'), ce: e.getAttribute('contenteditable'),
        box: `${Math.round(bb.width)}x${Math.round(bb.height)}@${Math.round(bb.x)},${Math.round(bb.y)}`,
        value: e.value !== undefined ? e.value : (e.innerText || '') }; }),
    // 面板里所有 role=listbox/menu/popover（/ 和 @ 唤起后要看的）
    popovers: Array.from(root.querySelectorAll('[role="listbox"],[role="menu"],[data-testid*="popover"],[data-testid*="mention"],[data-testid*="suggest"]')).filter(vis)
      .map((e) => ({ role: e.getAttribute('role'), tid: e.getAttribute('data-testid'),
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300) })),
  };
});

const openDrawer = async () => {
  const d = await drawerDump();
  if (d.open) return { already: true };
  const rb = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role="button"]'))
      .find((x) => /与\s*AI\s*对话|和\s*AI\s*对话/.test(x.getAttribute('aria-label') || x.innerText || ''));
    if (!e) return null; const r = e.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), aria: e.getAttribute('aria-label') }; });
  if (!rb) return { err: '找不到「与 AI 对话」按钮' };
  await p.mouse.click(rb.cx, rb.cy);
  await p.waitForTimeout(1500);
  return { clicked: rb };
};
const clickInDrawer = async (re) => {
  const hit = await p.evaluate((src) => {
    const rx = new RegExp(src);
    const e = Array.from(document.querySelectorAll('button,[role="button"],[role="menuitem"]'))
      .filter((x) => { const r = x.getBoundingClientRect(); return r.width > 1 && r.height > 1; })
      .find((x) => rx.test(x.getAttribute('aria-label') || '') || rx.test((x.innerText || '').trim()));
    if (!e) return null;
    const r = e.getBoundingClientRect();
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const top = document.elementFromPoint(cx, cy);
    return { cx, cy, text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
      aria: e.getAttribute('aria-label'), landedInside: !!(top && top.closest('button,[role="button"]') &&
        (top.closest('button,[role="button"]') === e || e.contains(top.closest('button,[role="button"]')))) };
  }, re.source || re);
  if (!hit) return { ok: false, why: 'notfound' };
  if (!hit.landedInside) return { ok: false, why: 'occluded', hit };
  await p.mouse.click(hit.cx, hit.cy);
  await p.waitForTimeout(1200);
  return { ok: true, hit };
};

const out = { startedAt: new Date().toISOString() };
const c0 = await credit();
console.log('=== 批次 62：「与 AI 对话」抽屉的未验证条目重审 ===\n');
console.log('起点:', await statusLine(), '| 积分', JSON.stringify(c0), '\n');
console.log('尺子活性自测: 正则捕获到数字?', c0.num !== null, c0.num !== null ? 'OK(尺子在读数)' : 'FAILED(尺子坏了,后续所有读数不可信)');
if (c0.num === null) { console.error('ABORT: 积分尺子失效'); await b.close(); process.exit(2); }
out.creditStart = c0;

// ── 步骤 0：打开抽屉
const o = await openDrawer();
console.log('打开抽屉:', JSON.stringify(o));
let d = await drawerDump();
if (!d.open) { console.error('ABORT: 抽屉没打开'); await b.close(); process.exit(2); }
console.log('抽屉:', d.box);
console.log('可见按钮', d.buttons.length, '个:');
for (const x of d.buttons) console.log('   ', JSON.stringify(x));
console.log('可见输入框:', JSON.stringify(d.inputs));
console.log('--- 抽屉全文 ---'); console.log(d.text); console.log('--- / ---');
out.drawerInitial = d;

// ── 步骤 1：阳性对照 —— 点「收起」，抽屉应关闭；再打开
console.log('\n[阳性对照] 点「收起」，证明我的点击在抽屉里有效');
const collapse = await clickInDrawer(/收起/);
await p.waitForTimeout(1200);
const afterCollapse = await drawerDump();
console.log('  点收起 =', JSON.stringify(collapse.ok ? collapse.hit : collapse));
console.log('  点后抽屉 open =', afterCollapse.open, afterCollapse.open ? '<< 阳性对照失败' : '<< 阳性对照通过(点击确实生效)');
out.positiveControl = { collapse, closedAfter: !afterCollapse.open };
if (afterCollapse.open) { console.error('ABORT: 阳性对照失败,后续点击读数全部不可信'); await b.close(); process.exit(3); }

await openDrawer(); await p.waitForTimeout(1000);

// ── 步骤 2：逐个点 5 个技能 chip
const CHIPS = ['视频反解', '创作分镜', '全流程广告片导演', '剧本开发', '剧情短片'];
out.chips = [];
for (const name of CHIPS) {
  const before = await credit();
  const r = await clickInDrawer(new RegExp('^/?\\s*' + name + '\\s*$'));
  await p.waitForTimeout(1600);
  const after = await drawerDump();
  const afterCredit = await credit();
  const rec = { name, click: r, box: after.box,
    boxChanged: after.box !== d.box,
    popovers: after.popovers, inputs: after.inputs,
    textHead: after.text.slice(0, 600),
    credit: { before: before.num, after: afterCredit.num, delta: afterCredit.num - before.num } };
  console.log(`\n--- chip「/${name}」 ---`);
  console.log('  点击:', JSON.stringify(r.ok ? r.hit : r));
  console.log('  面板 box:', d.box, '->', after.box, rec.boxChanged ? '(变了)' : '(没变)');
  console.log('  积分:', before.num, '->', afterCredit.num, 'Δ=', rec.credit.delta);
  console.log('  弹层:', JSON.stringify(after.popovers));
  console.log('  输入框:', JSON.stringify(after.inputs));
  console.log('  抽屉文本前 600 字:\n' + after.text.slice(0, 600).split('\n').map((s) => '    | ' + s).join('\n'));
  out.chips.push(rec);
  d = after;
}

// ── 步骤 3：「使用技能」按钮
console.log('\n--- 「使用技能」按钮 ---');
const useSkill = await clickInDrawer(/使用技能/);
await p.waitForTimeout(1400);
const afterSkill = await drawerDump();
console.log('  点击:', JSON.stringify(useSkill.ok ? useSkill.hit : useSkill));
console.log('  面板 box:', d.box, '->', afterSkill.box);
console.log('  弹层:', JSON.stringify(afterSkill.popovers));
console.log('  抽屉文本前 600 字:\n' + afterSkill.text.slice(0, 600).split('\n').map((s) => '    | ' + s).join('\n'));
out.useSkill = { click: useSkill, box: afterSkill.box, popovers: afterSkill.popovers, textHead: afterSkill.text.slice(0, 600) };

// ── 步骤 4：在输入卡打字（**不发送**），观察 `/` 与 `@`
const ta = await p.evaluate(() => {
  const e = document.querySelector('textarea,input,[contenteditable="true"]');
  if (!e) return null;
  e.scrollIntoView({ block: 'center' });
  const r = e.getBoundingClientRect();
  return { tag: e.tagName, testid: e.getAttribute('data-testid'), ph: e.getAttribute('placeholder'),
    cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + Math.min(r.height / 2, 20)) };
});
console.log('\n--- 输入卡打字（不发送） ---');
console.log('  输入框:', JSON.stringify(ta));
out.typing = [];
if (ta) {
  const before = await credit();
  await p.mouse.click(ta.cx, ta.cy);
  await p.waitForTimeout(500);
  await p.keyboard.type('测试一下', { delay: 45 });
  await p.waitForTimeout(900);
  let snap = await drawerDump();
  const cAfterType = await credit();
  console.log('  打字后输入值:', JSON.stringify(snap.inputs.map((i) => i.value)));
  console.log('  积分:', before.num, '->', cAfterType.num, 'Δ=', cAfterType.num - before.num);
  out.typing.push({ step: 'type-text', value: snap.inputs.map((i) => i.value), credit: { before: before.num, after: cAfterType.num }, textHead: snap.text.slice(0, 400) });

  // `/` 唤起技能
  await p.keyboard.press('/');
  await p.waitForTimeout(1100);
  snap = await drawerDump();
  console.log('\n  按「/」后弹层:', JSON.stringify(snap.popovers));
  console.log('  抽屉文本前 500 字:\n' + snap.text.slice(0, 500).split('\n').map((s) => '    | ' + s).join('\n'));
  out.typing.push({ step: 'slash', popovers: snap.popovers, textHead: snap.text.slice(0, 500) });

  // `@` 唤起主体
  await p.keyboard.press('Backspace');
  await p.waitForTimeout(300);
  await p.keyboard.type('@');
  await p.waitForTimeout(1400);
  snap = await drawerDump();
  const cAfterAt = await credit();
  console.log('\n  按「@」后弹层:', JSON.stringify(snap.popovers));
  console.log('  抽屉文本前 500 字:\n' + snap.text.slice(0, 500).split('\n').map((s) => '    | ' + s).join('\n'));
  console.log('  积分累计:', before.num, '->', cAfterAt.num, 'Δ=', cAfterAt.num - before.num);
  out.typing.push({ step: 'at', popovers: snap.popovers, textHead: snap.text.slice(0, 500), credit: { after: cAfterAt.num } });

  // 清空输入（不留字）
  await p.keyboard.press('Backspace');
  await p.waitForTimeout(300);
  const cleaned = await p.evaluate(() => { const e = document.querySelector('textarea,input,[contenteditable="true"]');
    return e ? (e.value !== undefined ? e.value : e.innerText) : null; });
  console.log('  清空后输入值:', JSON.stringify(cleaned));
  out.typing.push({ step: 'clean', value: cleaned });
}

// ── 收尾
const c1 = await credit();
console.log('\n=== 积分全程 ===', c0.num, '->', c1.num, 'Δ=', c1.num - c0.num);
out.creditEnd = c1;
await clickInDrawer(/收起/).catch(() => {});
await p.waitForTimeout(1200);
for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(300); }
const fin = await nodeIds();
console.log('终态:', await statusLine(), '| 节点', fin.length, '| 抽屉 open =', (await drawerDump()).open);
console.log('节点是否等于基线 6 个:', JSON.stringify(fin.sort()) === JSON.stringify(Object.keys(BASELINE.nodes || BASELINE).filter((k) => !k.startsWith('_')).sort()));
out.end = { status: await statusLine(), nodes: fin, drawerOpen: (await drawerDump()).open };
writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log('写入', OUT.pathname);
await b.close();
