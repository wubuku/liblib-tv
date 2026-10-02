// Batch CG-6：`⤢` 坐实是「折叠/展开参数卡片」，但**必须先回答一个更要命的问题**：
// 折叠之后，这枚按钮本身还在不在？用户还能不能把它点回来？
//
// CG-5 的读数（无歧义）：
//   最大浮层 660x248 → 292x23 ；浮层数 2 → 1 ；提示词 "" → null；
//   节点内文字 113 字 → 6 字 ；「含高级设置面板」true → false
//   ⭐ 整张 660 宽的参数卡片（提示词框 + 模型 + 规格 + 135 + 生成按钮）**整体消失**，
//     节点只剩一条 292 宽的标题栏。⇒ 它是**折叠/展开**，而且**默认是展开态**。
//
// ⛔ CG-5 末尾那轮 `el.click()` 的读数**无效**，不能写成「el.click() 对它无效」：
//    那一轮是在**真鼠标已经折叠之后**跑的，参数卡片连同这枚按钮**已经从 DOM 里消失**，
//    脚本遍历时压根没找到目标 —— 是「目标不存在」，不是「点了没反应」。
//
// ⚠️ 本步的三件事（按重要性排序）：
//   ① **它还能不能被点回来**（能不能撤销）—— 决定这是不是个单向陷阱；
//   ② **折叠状态落不落盘**（刷新两轮独立复核）—— 决定用户下次打开画布是什么样；
//   ③ 四类节点是不是都这样，以及手册说的「图片节点上 not-allowed」是否属实。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { fingerprint, diffPanels } from './scenario.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const EXPAND = 'M1.4 8.9c.22 0 .4.18.4.4v5.54l5.26-5.26a.4.4 0 0 1 .57 0l.7.71';
const NODES = [
  { id: 'v-eMpqKtiLlx', kind: '视频节点 3' },
  { id: 'i-9nlG6HdjK2', kind: '图片节点 2' },
  { id: 'a-CUfJfmKzUJ', kind: '音频节点 6' },
  { id: 't-2AK3Ukyxj3', kind: '文本节点 1' },
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

const balance = () => page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const t = [...document.querySelectorAll('header *,nav *')].filter(vis).map((e) => (e.innerText || '').trim()).filter((x) => /^\d{1,4}$/.test(x));
  return t.length ? Number(t[t.length - 1]) : null;
});

// 判据：列出节点内**所有**浮层（含尺寸与位置），并点名最大的那块
const truth = (nid) => page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { err: 'node not in DOM' };
  const fus = [...node.querySelectorAll('.node-floating-ui')].map((el) => {
    const r = el.getBoundingClientRect();
    return { 尺寸: `${Math.round(r.width)}x${Math.round(r.height)}`, 面积: Math.round(r.width * r.height), cls: (el.className || '').toString().slice(0, 34) };
  }).filter((x) => x.面积 > 0).sort((a, b) => b.面积 - a.面积);
  const txt = (node.innerText || '').replace(/\s+/g, ' ').trim();
  const prompt = node.querySelector('.text-fg-default[contenteditable="true"]');
  return {
    浮层清单: fus.map((f) => `${f.尺寸}`),
    最大浮层: fus[0] ? fus[0].尺寸 : '无',
    提示词框在不在: !!prompt,
    提示词: prompt ? (prompt.innerText || '').trim() : null,
    文字长度: txt.length,
    文字: txt.slice(0, 300),
  };
}, nid);

const locate = (nid, pre) => page.evaluate(({ n, p }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { found: false, why: 'node not in DOM' };
  for (const b of node.querySelectorAll('button,[role="button"]')) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (!d.includes(p)) continue;
    const r = b.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    return {
      found: true, cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      尺寸: `${Math.round(r.width)}x${Math.round(r.height)}`,
      disabled: b.disabled === true, cursor: getComputedStyle(b).cursor,
      inViewport: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight,
    };
  }
  return { found: false, why: '节点内找不到该路径的按钮' };
}, { n: nid, p: pre });

const clickReal = async (loc) => {
  await page.mouse.move(5, 5);
  await page.waitForTimeout(350);
  await page.mouse.move(loc.cx, loc.cy);
  await page.waitForTimeout(500);
  await page.mouse.click(loc.cx, loc.cy);
  await page.waitForTimeout(1500);
};

async function selectNode(nid) {
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2200);
  await page.evaluate((n) => document.querySelector(`.react-flow__node[data-id="${n}"]`)?.click(), nid);
  await page.waitForTimeout(2000);
  return page.evaluate((n) => {
    const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
    return { inDom: !!el, selected: !!el && el.className.includes('selected') };
  }, nid);
}

out.balance0 = await balance();

// ═══① 视频节点：展开 → 折叠 → 能不能点回来 ═══
const V = NODES[0];
let sel = await selectNode(V.id);
if (!sel.selected) { console.log('!! 没选中'); await browser.close(); process.exit(1); }
out.视频 = {};
out.视频.选中后 = await truth(V.id);
out.视频.按钮 = await locate(V.id, EXPAND);
if (out.视频.按钮.found) {
  await clickReal(out.视频.按钮);
  out.视频.折叠后 = await truth(V.id);
  await shot(page, 'M-312-参数卡片折叠后.png');
  // ⭐ 折叠后按钮还在不在？—— 决定能不能撤销
  out.视频.折叠后按钮 = await locate(V.id, EXPAND);
  console.log('折叠后 浮层 =', out.视频.折叠后.最大浮层, '| 浮层清单 =', JSON.stringify(out.视频.折叠后.浮层清单),
    '| 提示词框在不在 =', out.视频.折叠后.提示词框在不在, '| 文字长度 =', out.视频.折叠后.文字长度);
  console.log('折叠后 那枚按钮 =', JSON.stringify(out.视频.折叠后按钮));

  if (out.视频.折叠后按钮.found) {
    await clickReal(out.视频.折叠后按钮);
    out.视频.再点后 = await truth(V.id);
    console.log('再点后 浮层 =', out.视频.再点后.最大浮层, '| 提示词框在不在 =', out.视频.再点后.提示词框在不在, '| 文字长度 =', out.视频.再点后.文字长度);
    out.视频.可逆 = out.视频.再点后.最大浮层 === out.视频.选中后.最大浮层 && out.视频.再点后.提示词框在不在 === out.视频.选中后.提示词框在不在;
  } else {
    out.视频.可逆 = false;
    out.视频.可逆说明 = '折叠后按钮不在 DOM 里 —— 没法用它点回来';
  }
} else {
  out.视频.折叠后按钮 = out.视频.按钮;
}

// ═══② 折叠状态落不落盘：先确保处于折叠态，刷新两轮独立复核 ═══
if (out.视频.折叠后 && out.视频.折叠后.最大浮层 !== out.视频.选中后.最大浮层) {
  out.落盘 = {};
  for (const tag of ['刷新1', '刷新2']) {
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(4500);
    await closePromos(page);
    await page.waitForTimeout(900);
    // 刷新后**重新选中**再读，否则看不到参数卡片
    const s2 = await selectNode(V.id);
    out.落盘[tag] = { 选中: s2.selected, ...(await truth(V.id)) };
    console.log(`${tag} 选中后 浮层 =`, out.落盘[tag].最大浮层, '| 提示词框在不在 =', out.落盘[tag].提示词框在不在, '| 文字长度 =', out.落盘[tag].文字长度);
  }
  out.落盘.判定 = (out.落盘.刷新1.最大浮层 === out.视频.折叠后.最大浮层)
    ? '⭐ 折叠状态【落盘】了 —— 刷新后仍然是折叠的'
    : '折叠状态【没落盘】 —— 刷新后恢复成展开';
}

// ═══③ 其余三类 ═══
for (const nd of NODES.slice(1)) {
  const s = await selectNode(nd.id);
  const rec = { kind: nd.kind, id: nd.id, 选中: s.selected };
  if (!s.selected) { rec.abort = '没选中'; out.rows.push(rec); continue; }
  rec.选中后 = await truth(nd.id);
  rec.按钮 = await locate(nd.id, EXPAND);
  if (rec.按钮.found) {
    await clickReal(rec.按钮);
    rec.点后 = await truth(nd.id);
    rec.真的折叠了 = rec.选中后.最大浮层 !== rec.点后.最大浮层;
    rec.折叠后按钮 = await locate(nd.id, EXPAND);
    if (rec.折叠后按钮.found) {   // 复原：点回去
      await clickReal(rec.折叠后按钮);
      rec.复原后 = await truth(nd.id);
      rec.复原成功 = rec.复原后.最大浮层 === rec.选中后.最大浮层;
    } else {
      // 点不回来时，只能靠重新选中复原
      const s3 = await selectNode(nd.id);
      rec.重新选中后 = await truth(nd.id);
      rec.重新选中能恢复 = s3.selected && rec.重新选中后.最大浮层 === rec.选中后.最大浮层;
    }
  }
  out.rows.push(rec);
  console.log(`\n[${rec.kind}] 按钮 =`, JSON.stringify(rec.按钮));
  console.log(`   选中后 ${rec.选中后.最大浮层}(${rec.选中后.文字长度}字) → 点后 ${rec.点后 ? rec.点后.最大浮层 + '(' + rec.点后.文字长度 + '字)' : '?'} | 真的折叠了 =`, rec.真的折叠了);
  console.log(`   折叠后按钮 =`, JSON.stringify(rec.折叠后按钮), '| 复原成功 =', rec.复原成功, '| 重新选中能恢复 =', rec.重新选中能恢复);
}

out.balance1 = await balance();

// 收尾：确保视频节点回到展开态
const sEnd = await selectNode(V.id);
const endT = await truth(V.id);
const endBtn = await locate(V.id, EXPAND);
if (endBtn.found && !endT.提示词框在不在) { await clickReal(endBtn); out.收尾复原 = (await truth(V.id)).提示词框在不在; }
else out.收尾复原 = '本来就是展开态，未动';
console.log('\n收尾复原 =', out.收尾复原, '| 余额', out.balance0, '→', out.balance1);

await writeFile(resolve(HERE, '.evidence/cg6-collapse.json'), JSON.stringify(out, null, 2));
await browser.close();
