// Batch BC2 —— 只做摄像机面板的「关闭」开关。
//
// BC1 打开面板成功（面板全文读到了），但**开关读数是空数组**：
// 我的选择器找 `button/[role=switch]/[class*=Switch]/[class*=Toggle]` 且要求
// `innerText` 含「关闭|开启|启用」—— Mantine 的 Switch **可见文字在旁边的 label 里**，
// 开关本体是空的，所以一个都没匹配上。
//
// 面板实测全文：
//   摄像机 相机 Panavision DXL2 镜头 Arri Signature Prime
//   焦距 8 14 24 35 50 75 125 mm 光圈 ƒ/4 关闭 **正在跟随** 取消 ESC 按 ESC 退出
//  ⭐ 「正在跟随」是本轮新读到的一个状态，手册此前完全没有。
//
// 这轮把面板里的**每一个**可点元素 dump 出来，再按实际结构点开关。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBC2';
const { browser, page } = await launch();

const listNodes = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id') || '?', prefix: (n.getAttribute('data-id') || '?').split('-')[0],
    name: ((n.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] || '').slice(0, 10),
    cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }));

async function exclusivePoint(pg, id) {
  return pg.evaluate((nid) => {
    const t = [...document.querySelectorAll('.react-flow__node')].find((n) => n.getAttribute('data-id') === nid);
    if (!t) return { err: 'no node' };
    const r = t.getBoundingClientRect();
    for (let fy = 0.2; fy <= 0.8; fy += 0.15) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === t) return { x, y };
    }
    return { err: 'no exclusive point' };
  }, id);
}

const panelState = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没选中' };
  const panels = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width >= 480 && o.r.height >= 100)
    .filter((o) => o.e.querySelectorAll('button,[role="button"]').length >= 3);
  if (!panels.length) return { err: 'no panel' };
  const p = panels.sort((a, b) => (b.r.width * b.r.height) - (a.r.width * a.r.height))[0];
  const all = [...p.e.querySelectorAll('button,[role="button"]')].map((x) => { const q = x.getBoundingClientRect();
    return { text: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14), aria: x.getAttribute('aria-label'),
      role: x.getAttribute('role'), rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; })
    .filter((b) => b.rect[2] > 0);
  const maxY = Math.max(...all.map((b) => b.rect[1] + b.rect[3]));
  return { bottom: all.filter((b) => maxY - (b.rect[1] + b.rect[3]) <= 8) };
});

/** 把摄像机面板里**每一个**可交互元素 dump 出来（不筛文字）。 */
const dumpCameraPanel = () => page.evaluate(() => {
  const host = [...document.querySelectorAll('body div,body section')]
    .filter((e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      if (r.width < 200 || r.height < 150) return false;
      if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity <= 0.05) return false;
      if (e.closest('.react-flow')) return false;
      return /摄像机/.test(e.innerText || ''); })
    .sort((a, b) => { const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
      return (ra.width * ra.height) - (rb.width * rb.height); })[0];
  if (!host) return { err: '没找到摄像机面板容器' };
  const hr = host.getBoundingClientRect();
  const els = [...host.querySelectorAll('button,[role="button"],[role="switch"],input,label,[class*="Switch"],[class*="Toggle"],[class*="Checkbox"]')]
    .map((e) => { const r = e.getBoundingClientRect();
      return { tag: e.tagName, role: e.getAttribute('role'), type: e.type || '',
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12),
        aria: e.getAttribute('aria-label'), ariaChecked: e.getAttribute('aria-checked'),
        dataChecked: e.getAttribute('data-checked'), cls: (e.className || '').toString().slice(0, 48),
        checked: e.checked === true,
        cursor: getComputedStyle(e).cursor,
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
    .filter((e) => e.rect[2] > 0 && e.rect[3] > 0);
  return { hostCls: (host.className || '').toString().slice(0, 60),
    hostRect: [Math.round(hr.x), Math.round(hr.y), Math.round(hr.width), Math.round(hr.height)],
    text: (host.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
    n: els.length, els };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1800);
  await beginBatch(B, { note: '摄像机面板「关闭」开关专项：dump 全部可交互元素再按实际结构点' });

  const out = {};
  // 选中图片节点
  let picked = null;
  for (const c of (await listNodes()).filter((n) => n.prefix === 'i')) {
    const pt = await exclusivePoint(page, c.id);
    if (pt.err) { console.log(`${c.id} → ${pt.err}`); continue; }
    await page.mouse.click(pt.x, pt.y); await page.waitForTimeout(3800);
    const ok = await page.evaluate((id) => { const n = document.querySelector('.react-flow__node.selected');
      return n ? n.getAttribute('data-id') === id : false; }, c.id);
    console.log(`${c.id} → ${ok}`);
    if (ok) { picked = c.id; break; }
    await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  }
  if (!picked) throw new Error('没选中图片节点');

  const ps = await panelState();
  if (ps.err) throw new Error('参数面板: ' + ps.err);
  const camIdx = ps.bottom.findIndex((b) => b.aria === null && b.text === '');
  console.log('参数条:', JSON.stringify(ps.bottom.map((b, i) => `${i}:${b.text || b.aria || '(无)'}`)));
  const cam = ps.bottom.find((b) => /摄像机|Panavision/i.test(b.text)) || ps.bottom[3];
  console.log('摄像机按钮:', JSON.stringify(cam));

  await page.mouse.click(cam.rect[0] + cam.rect[2] / 2, cam.rect[1] + cam.rect[3] / 2);
  await page.waitForTimeout(2600); await clearToasts(page);
  const d0 = await dumpCameraPanel();
  console.log('\n=== 摄像机面板全文 ===\n', d0.text);
  console.log(`容器 ${d0.hostCls} [${d0.hostRect}] 共 ${d0.n} 个可交互元素:`);
  (d0.els || []).forEach((e, i) => console.log(` [${String(i).padStart(2)}] ${e.tag.padEnd(7)} role=${(e.role || '-').padEnd(7)} type=${(e.type || '-').padEnd(7)} text=${(e.text || '-').padEnd(10)} aria=${(e.aria || '-').padEnd(10)} checked=${e.checked ? 'Y' : 'n'} ariaChecked=${(e.ariaChecked || '-').padEnd(6)} dataChecked=${(e.dataChecked || '-').padEnd(6)} [${e.rect}]`));
  out.before = d0;
  await shot(page, 'M-177-摄像机面板-全部元素.png');
  out.shot = 'M-177-摄像机面板-全部元素.png';

  // 认开关：优先 role=switch / input[type=checkbox] / class 含 Switch|Toggle
  const sw = (d0.els || []).find((e) => e.role === 'switch' || e.type === 'checkbox' || /Switch|Toggle|Checkbox/i.test(e.cls));
  console.log('\n认定开关:', JSON.stringify(sw));
  if (!sw) {
    console.log('  ⚠ 面板里没有可识别的开关元素 —— 记成 📖，本批只记录面板结构');
    out.switch = { err: '没找到可识别的开关元素（按 role=switch / input[type=checkbox] / class 含 Switch|Toggle 找）' };
  } else {
    const clickSw = async () => {
      await page.mouse.click(sw.rect[0] + sw.rect[2] / 2, sw.rect[1] + sw.rect[3] / 2);
      await page.waitForTimeout(2400); await clearToasts(page);
      return dumpCameraPanel();
    };
    console.log('  ⬆️ 点开关…');
    const d1 = await clickSw();
    const after = (d1.els || []).find((e) => e.role === 'switch' || e.type === 'checkbox' || /Switch|Toggle|Checkbox/i.test(e.cls));
    console.log('  打开后:', JSON.stringify(after));
    console.log('  面板全文:', d1.text);
    out.afterOpen = { switch: after, text: d1.text, els: d1.els };
    await shot(page, 'M-178-摄像机-开关打开后.png');
    out.shotOpen = 'M-178-摄像机-开关打开后.png';
    const changed = JSON.stringify(after) !== JSON.stringify(sw);
    console.log('  开关读数有变化吗:', changed);
    out.switch = { before: sw, after, changed };
    // ✅ 关回去
    console.log('  ⬇️ 关回去…');
    const d2 = await clickSw();
    const back = (d2.els || []).find((e) => e.role === 'switch' || e.type === 'checkbox' || /Switch|Toggle|Checkbox/i.test(e.cls));
    console.log('  复原后:', JSON.stringify(back), '| 与初始一致:', JSON.stringify(back) === JSON.stringify(sw));
    out.restored = { switch: back, sameAsBefore: JSON.stringify(back) === JSON.stringify(sw), text: d2.text };
    await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  }

  await logStep(B, {
    id: 'BC2-camera-switch', title: '摄像机面板「关闭」开关专项',
    target: 'BC1 读到面板全文但**开关读数是空数组** —— Mantine Switch 的可见文字在旁边的 label 里，'
      + '开关本体 `innerText` 为空，按文字找必然落空。这轮把面板里**每个**可交互元素 dump 出来，'
      + '再按 `role=switch` / `input[type=checkbox]` / class 含 Switch|Toggle 认开关。',
    evidence: out,
    visible_text: JSON.stringify({ panelText: out.before && out.before.text,
      switch: out.switch, afterOpen: out.afterOpen && out.afterOpen.text,
      restored: out.restored }).slice(0, 3000),
    shot: out.shot,
  });
  console.log('\nBC2 完成');
} finally {
  await browser.close();
}
