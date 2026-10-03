// Batch CN-3：盘「参考选择模式」，并补上时长滑杆的参数。
//
// CN-2 撞出来的两件事：
// ① 点模态里的 `参考`，**不是在模态里开面板** —— 大编辑器整个消失，画布放大，
//    顶栏正中浮出一条**蓝色横幅**「从画布或资产管理选择参考」+「返回节点」+「×」。
// ② 时长是**滑杆**不是离散选项（CN-2 的文字快照漏了它，因为 `30` 在 input 的 value 里）。
//
// ⛔ 安全边界：**不点任何候选节点**（那会真的把素材接进节点、写盘）。
//    只读：横幅结构、画布缩放、哪些节点被标成候选、悬停时出现什么。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];
const VID = 'v-oZNpH99MtM';

const boot = async (page) => {
  await open(page, URL_);
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2600);
  for (let i = 0; i < 3; i += 1) {
    const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
    if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(600);
  }
};
const killPromo = async (page) => {
  const b = await page.evaluate(() => {
    const t = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
    if (!t) return null; const r = t.getBoundingClientRect(); return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
  });
  if (!b) return false;
  await page.mouse.click(b[0], b[1]); await page.waitForTimeout(1200); return true;
};
const read = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { 在: false };
  const vis = [...n.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const fold = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
  return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'), 折叠钮: !!fold };
}, id);
const modal = (page) => page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  return d ? { 开: true, 全文: (d.innerText || '').replace(/\s+/g, ' ').trim() } : { 开: false };
});
// 画布缩放：读 transform / viewport
const zoom = (page) => page.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  return vp ? { transform: getComputedStyle(vp).transform, class: (vp.className || '').toString().slice(0, 60) } : null;
});
const btnRect = (page, 起始) => page.evaluate((t) => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!d) return null;
  const b = [...d.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith(t));
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 全名: (b.innerText || '').replace(/\s+/g, ' ').trim() };
}, 起始);
const openModal = async (page) => {
  for (let i = 0; i < 3; i += 1) {
    if ((await modal(page)).开) return true;
    const pts = await page.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const q = n.getBoundingClientRect(); const a = [];
      for (const fy of [0.25, 0.4, 0.55, 0.7, 0.85]) for (const fx of [0.1, 0.25, 0.5, 0.75, 0.9]) {
        const x = q.x + q.width * fx, y = q.y + q.height * fy;
        const el = document.elementFromPoint(x, y);
        if (el && el.closest('.react-flow__node') === n && !el.closest('button,a')) a.push([Math.round(x), Math.round(y)]);
      }
      return a;
    }, VID);
    let ok = false;
    for (const p of pts) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1300); const s = await read(page, VID); if (s.选中 && s.折叠钮) { ok = true; break; } }
    if (!ok) return false;
    const fx = await page.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const f = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
      if (!f) return null; const r = f.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y)];
    }, VID);
    if (!fx || fx[0] + 14 > 1440 || fx[1] + 14 > 810) return false;
    await page.mouse.click(fx[0] + 14, fx[1] + 14);
    await page.waitForTimeout(1700);
  }
  return (await modal(page)).开;
};
const out = {};
const { browser, page } = await launch();
await boot(page);
out.促销 = await killPromo(page);

if (!(await openModal(page))) { console.log('⛔ 开不出模态'); await browser.close(); process.exit(0); }
out.进模式前 = { 缩放: await zoom(page), 节点: await read(page, VID) };

// ① 时长滑杆参数（在进参考模式之前读，因为那时候下拉还在）
{
  const b = await btnRect(page, '16:9');
  await page.mouse.click(b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2);
  await page.waitForTimeout(1500);
  out.规格面板 = await page.evaluate(() => {
    const dlg = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
    const 滑杆 = [...dlg.querySelectorAll('input[type="range"]')].map((r) => ({ min: r.min, max: r.max, step: r.step, value: r.value, rect: (() => { const b = r.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; })() }));
    const 数字框 = [...dlg.querySelectorAll('input:not([type="range"])')].map((r) => ({ value: r.value, type: r.type, 宽: Math.round(r.getBoundingClientRect().width) }));
    const 分组 = [...dlg.querySelectorAll('*')].filter((e) => e.children.length === 0 && ['比例', '时长', '清晰度'].includes((e.innerText || '').trim())).map((e) => (e.innerText || '').trim());
    return { 滑杆, 数字框, 分组 };
  });
  console.log('规格面板 =', JSON.stringify(out.规格面板));
  out.规格图 = 'cn3-规格面板.png';
  await page.screenshot({ path: resolve(HERE, '.evidence', out.规格图) });
  await page.mouse.click(b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2);
  await page.waitForTimeout(1200);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1200);
  if (!(await modal(page)).开) { console.log('ESC 把模态关了，重开'); await openModal(page); }
}

// ② 点 `参考` 进参考选择模式
const rk = await btnRect(page, '参考');
console.log('\n参考按钮 =', JSON.stringify(rk));
await page.mouse.click(rk.rect[0] + rk.rect[2] / 2, rk.rect[1] + rk.rect[3] / 2);
await page.waitForTimeout(1900);
out.进模式后 = {
  模态: await modal(page), 缩放: await zoom(page), 节点: await read(page, VID),
};
console.log('进模式后 模态 =', JSON.stringify(out.进模式后.模态), '\n  缩放 =', JSON.stringify(out.进模式后.缩放));

// 横幅：找出含「从画布或资产管理选择参考」的那个容器
out.横幅 = await page.evaluate(() => {
  for (const e of document.querySelectorAll('body *')) {
    if (e.children.length) continue;
    if ((e.innerText || '').replace(/\s+/g, ' ').trim() !== '从画布或资产管理选择参考') continue;
    let a = e; for (let i = 0; i < 4 && a.parentElement; i += 1) a = a.parentElement;
    const r = a.getBoundingClientRect(); const s = getComputedStyle(a);
    return {
      容器class: (a.className || '').toString().slice(0, 90), pos: s.position, z: s.zIndex, bg: s.backgroundColor,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      文字: (a.innerText || '').replace(/\s+/g, ' ').trim(),
      按钮: [...a.querySelectorAll('button')].map((x) => { const q = x.getBoundingClientRect(); return { 文字: (x.innerText || '').replace(/\s+/g, ' ').trim(), aria: x.getAttribute('aria-label'), rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; }),
    };
  }
  return null;
});
console.log('横幅 =', JSON.stringify(out.横幅, null, 0).slice(0, 600));

// 候选节点：哪些卡片上多了「参考」标记
out.候选 = await page.evaluate(() => {
  const out = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const r = n.getBoundingClientRect();
    if (r.width === 0) continue;
    const t = (n.innerText || '').replace(/\s+/g, ' ').trim();
    out.push({ id: n.getAttribute('data-id'), 选中: n.classList.contains('selected'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 文字: t.slice(0, 46), 含参考: t.includes('参考') });
  }
  return out;
});
for (const c of out.候选) console.log(`  候选 ${c.id} ${JSON.stringify(c.rect)} 选中=${c.选中} 含「参考」=${c.含参考} 「${c.文字}」`);

out.参考模式图 = 'cn3-参考选择模式.png';
await page.screenshot({ path: resolve(HERE, '.evidence', out.参考模式图) });

// ③ 悬停一个候选节点，看会不会浮出「参考」按钮 —— ⛔ 只悬停，不点
const cand = out.候选.find((c) => !c.选中 && !c.含参考);
if (cand) {
  const cx = cand.rect[0] + cand.rect[2] / 2, cy = cand.rect[1] + cand.rect[3] / 2;
  await page.mouse.move(cx, cy);
  await page.waitForTimeout(1500);
  out.悬停后 = await page.evaluate(([px, py]) => {
    const n = document.elementFromPoint(px, py);
    const node = n ? n.closest('.react-flow__node') : null;
    if (!node) return { 无节点: true };
    const btns = [...node.querySelectorAll('button')].map((b) => { const r = b.getBoundingClientRect(); return { 文字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
    const fl = [...document.querySelectorAll('.node-floating-ui')].map((f) => { const r = f.getBoundingClientRect(); return r.width > 0 ? { 文字: (f.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] } : null; }).filter(Boolean);
    return { 节点id: node.getAttribute('data-id'), 按钮: btns, 浮层: fl };
  }, [cx, cy]);
  console.log('\n悬停候选节点 =', JSON.stringify(out.悬停后).slice(0, 500));
  await page.mouse.move(1360, 780);
  await page.waitForTimeout(600);
}

// ④ 用横幅上的 `×` 退出（不是点画布空白 —— 顺便验证 `×` 有用）
if (out.横幅 && out.横幅.按钮.length) {
  const last = out.横幅.按钮[out.横幅.按钮.length - 1];
  out.退出按钮 = last;
  await page.mouse.click(last.rect[0] + last.rect[2] / 2, last.rect[1] + last.rect[3] / 2);
  await page.waitForTimeout(1800);
  out.退出后 = { 缩放: await zoom(page), 节点: await read(page, VID), 横幅还在: !!(await page.evaluate(() => document.body.innerText.includes('从画布或资产管理选择参考'))) };
  console.log('\n点 × 之后 =', JSON.stringify(out.退出后));
}

console.log('\n收尾 =', JSON.stringify(await read(page, VID)));
await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const ids = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.收尾 = { 节点: ids, 与基线一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)) };
  console.log('收尾节点 =', ids.length, ' 与基线逐项一致 =', out.收尾.与基线一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cn3-refmode.json'), JSON.stringify(out, null, 2));
