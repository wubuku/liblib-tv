// Batch CG-7：诊断 + **复原**。画布可能被我留在折叠态，必须先修好再谈别的。
//
// CG-6 留下的隐患（自查发现的，不是用户造成的）：
//   - `⤢` 点下去，参数卡片连同这枚按钮**一起从 DOM 消失** ⇒ **没法用它点回来**；
//   - CG-6 的复原分支只覆盖了「折叠后按钮还在」的情况，
//     **图片节点和文本节点走的是「按钮消失」那条分支**，只读没复原；
//   - 收尾只查了视频节点（「本来就是展开态，未动」）。
//   ⇒ 图片 / 文本很可能**还留在折叠态**。先查、先修。
//
// ⚠️ 另一个必须分辨的歧义 —— CG-6 报的「重新选中能恢复 = false」有两种解释：
//   (a) 真的恢复不了；
//   (b) **`click()` 打在已选中的节点上是「取消选中」** ——
//       于是所谓「重新选中」实际执行的是取消，读到的是未选中态（本来就没有浮层），
//       判据自然判 false。**这是 toggle，不是恢复失败。**
//   本步用两种手法分开验：① 先点**画布空白**把选中态解除，再点节点；
//   ② 直接刷新（已知折叠态**不落盘**，刷新必然回到展开）—— ② 是**保底复原手段**。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const NODES = [
  { id: 'v-eMpqKtiLlx', kind: '视频节点 3' },
  { id: 'i-9nlG6HdjK2', kind: '图片节点 2' },
  { id: 'a-CUfJfmKzUJ', kind: '音频节点 6' },
  { id: 't-2AK3Ukyxj3', kind: '文本节点 1' },
  { id: 'b-mfkcQNULC3', kind: '逐帧拉片' },
  { id: 'n-56F19pXVB4', kind: '导演台 5' },
  { id: 'v-oZNpH99MtM', kind: '智能剪辑 4' },
  { id: 'a-THmbuJXQj4', kind: '音频节点 1' },
  { id: 'i-sODTbgLUm1', kind: '图片节点 2' },
  { id: 'v-v2hlWY4Br3', kind: '视频节点 3' },
];

const { browser, page } = await launch();
const out = { rows: [] };

await open(page, URL_);
await closePromos(page);
await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.waitForTimeout(800);

const truth = (nid) => page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { err: 'node not in DOM' };
  const fus = [...node.querySelectorAll('.node-floating-ui')].map((el) => {
    const r = el.getBoundingClientRect();
    return { 尺寸: `${Math.round(r.width)}x${Math.round(r.height)}`, 面积: Math.round(r.width * r.height) };
  }).filter((x) => x.面积 > 0).sort((a, b) => b.面积 - a.面积);
  const prompt = node.querySelector('.text-fg-default[contenteditable="true"]');
  return {
    最大浮层: fus[0] ? fus[0].尺寸 : '无',
    提示词框在不在: !!prompt,
    文字长度: (node.innerText || '').replace(/\s+/g, ' ').trim().length,
    selected: node.className.includes('selected'),
  };
}, nid);

// 点画布**空白**（没有节点的地方）来解除选中 —— 这是与「直接点节点」分开的第二种手法
async function deselect() {
  const pt = await page.evaluate(() => {
    // 找一个既没有节点、也没有浮层按钮的点
    for (const [x, y] of [[720, 120], [1300, 200], [200, 400], [1000, 90]]) {
      const el = document.elementFromPoint(x, y);
      if (el && !el.closest('.react-flow__node') && !el.closest('button,[role="button"]')) return { x, y };
    }
    return null;
  });
  if (!pt) return false;
  await page.mouse.click(pt.x, pt.y);
  await page.waitForTimeout(900);
  return true;
}

async function selectNode(nid) {
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2200);
  const r = await page.evaluate((n) => {
    const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
    if (!el) return { inDom: false };
    const b = el.getBoundingClientRect();
    return { inDom: true, cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2) };
  }, nid);
  if (!r.inDom) return { inDom: false, selected: false };
  await page.mouse.move(r.cx, r.cy);
  await page.waitForTimeout(300);
  await page.mouse.click(r.cx, r.cy);
  await page.waitForTimeout(1700);
  return page.evaluate((n) => {
    const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
    return { inDom: true, selected: !!el && el.className.includes('selected') };
  }, nid);
}

// ── 步骤 1：逐个查当前状态（每个都先解除选中再真点，确保是「选中」而不是 toggle）──
for (const nd of NODES) {
  const rec = { kind: nd.kind, id: nd.id };
  await deselect();
  const s = await selectNode(nd.id);
  rec.选中 = s;
  if (!s.inDom) { rec.note = '不在 DOM（可能被视口虚拟化，先 ⌘0 过仍没有）'; out.rows.push(rec); continue; }
  if (!s.selected) { rec.note = '点不中，判据作废'; out.rows.push(rec); continue; }
  rec.状态 = await truth(nd.id);
  // ⭐ 有提示词框 = 参数卡片是展开的（这四类节点才有参数卡片）
  rec.看起来是展开的 = rec.状态.提示词框在不在 || rec.状态.最大浮层.startsWith('660');
  out.rows.push(rec);
  console.log(`[${rec.kind} ${nd.id}] ${rec.状态.最大浮层} 提示词框=${rec.状态.提示词框在不在} ${rec.状态.文字长度}字 → 展开=${rec.看起来是展开的}`);
}

// ── 步骤 2：复原 —— 对任何看起来是折叠的，先试「解除选中 + 真点」，不行就刷新 ──
const folded = out.rows.filter((r) => r.状态 && !r.看起来是展开的);
out.疑似折叠 = folded.map((r) => `${r.kind} ${r.id}`);
console.log('\n疑似仍折叠 =', JSON.stringify(out.疑似折叠));
out.复原过程 = [];
if (folded.length) {
  for (const f of folded) {
    await deselect();
    const s = await selectNode(f.id);
    const t = await truth(f.id);
    const ok = t.提示词框在不在 || t.最大浮层.startsWith('660');
    out.复原过程.push({ id: f.id, kind: f.kind, 手法: '解除选中 + 真点节点', 选中: s.selected, 结果: t, 恢复: ok });
    console.log(`复原[${f.kind}] 解除选中后真点 → ${t.最大浮层} 提示词框=${t.提示词框在不在} 恢复=${ok}`);
  }
}
// 保底：刷新（折叠态已知不落盘）
if (out.复原过程.some((x) => !x.恢复)) {
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(4500);
  await closePromos(page);
  await page.waitForTimeout(1000);
  for (const f of folded) {
    await deselect();
    const s = await selectNode(f.id);
    const t = await truth(f.id);
    const ok = t.提示词框在不在 || t.最大浮层.startsWith('660');
    out.复原过程.push({ id: f.id, kind: f.kind, 手法: '刷新后重新选中', 选中: s.selected, 结果: t, 恢复: ok });
    console.log(`复原[${f.kind}] 刷新后 → ${t.最大浮层} 提示词框=${t.提示词框在不在} 恢复=${ok}`);
  }
}

// ── 步骤 3：收尾复核 + 余额 ──
out.收尾 = [];
for (const nd of NODES) {
  await deselect();
  const s = await selectNode(nd.id);
  if (!s.selected) { out.收尾.push({ kind: nd.kind, id: nd.id, 选中: false }); continue; }
  const t = await truth(nd.id);
  out.收尾.push({ kind: nd.kind, id: nd.id, 展开: t.提示词框在不在 || t.最大浮层.startsWith('660'), 最大浮层: t.最大浮层 });
}
out.还有折叠的吗 = out.收尾.filter((r) => r.选中 && !r.展开).map((r) => `${r.kind} ${r.id}`);
console.log('\n=== 收尾复核 ===');
for (const r of out.收尾) console.log(`  ${r.kind} ${r.id} 展开=${r.展开} ${r.最大浮层 || ''}`);
console.log('还有折叠的 =', JSON.stringify(out.还有折叠的吗));

out.balance = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const t = [...document.querySelectorAll('header *,nav *')].filter(vis).map((e) => (e.innerText || '').trim()).filter((x) => /^\d{1,4}$/.test(x));
  return t.length ? Number(t[t.length - 1]) : null;
});
console.log('余额 =', out.balance);

await writeFile(resolve(HERE, '.evidence/cg7-diagnose-restore.json'), JSON.stringify(out, null, 2));
await browser.close();
