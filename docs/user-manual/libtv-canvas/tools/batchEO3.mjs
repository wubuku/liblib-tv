// Batch EO-3：修掉 EO-2 的浮层排序，取全参数面板的逐项读数。
//   EO-2 的 `读浮层` 按「文本密度」排序 ⇒ 选中了 **z=1000 的节点本身**（react-flow__node），
//   真正的面板（z=300 的 mantine-Popover-dropdown）排在第 4 位，于是读到 0 项。
//   ⇒ 本轮直接把 `.react-flow__node` / `.react-flow__nodes` 排除，再取 z 最高的那个。
//   ⭐ 顺带把面板的完整文本取全（EO-2 只截了前 200 字，视频那一组被截断了）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEO3.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 待测 = [
  { id: 'v-v2hlWY4Br3', 名: '视频' },
  { id: 'a-THmbuJXQj4', 名: '音频' },
  { id: 'v-oZNpH99MtM', 名: '智能剪辑' },
];

const 找起点 = (page, dx, dy) => page.evaluate((d) => {
  const 好 = [];
  for (let y = 130; y <= 690; y += 20) for (let x = 130; x <= 1310; x += 20) {
    const e = document.elementFromPoint(x, y);
    if (!e) continue;
    if (e.closest('.react-flow__node')) continue;
    if (e.closest('button,[role="button"],input,textarea,select,a')) continue;
    const r = e.getBoundingClientRect();
    if (r.width < innerWidth && r.height < innerHeight) continue;
    if (!/react-flow/i.test(String(e.className)) && !/canvas/i.test(String(e.className))) continue;
    const 走X = d.dx < 0 ? x - 10 : (1310 - x), 走Y = d.dy < 0 ? y - 10 : (690 - y);
    好.push({ x, y, 走X, 走Y, 够: Math.min(走X / Math.max(1, Math.abs(d.dx)), 走Y / Math.max(1, Math.abs(d.dy))) });
  }
  if (!好.length) return null;
  好.sort((a, b) => b.够 - a.够);
  return 好[0];
}, { dx, dy });

const 平移到左上 = async (page, id) => {
  for (let 段 = 0; 段 < 6; 段++) {
    const 框 = await page.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; }, id);
    if (!框) return false;
    const dx = 200 - 框[0], dy = 150 - 框[1];
    if (Math.abs(dx) < 12 && Math.abs(dy) < 12) return true;
    const 起 = await 找起点(page, dx, dy);
    if (!起) return false;
    const 本X = Math.round(Math.max(-起.走X, Math.min(起.走X, dx)));
    const 本Y = Math.round(Math.max(-起.走Y, Math.min(起.走Y, dy)));
    if (Math.abs(本X) < 10 && Math.abs(本Y) < 10) return false;
    await page.mouse.move(起.x, 起.y);
    await page.mouse.down({ button: 'middle' });
    for (let i = 1; i <= 12; i++) await page.mouse.move(起.x + 本X * i / 12, 起.y + 本Y * i / 12);
    await page.mouse.up({ button: 'middle' });
    await page.waitForTimeout(1600);
    const 现 = await 读全部坐标(page);
    if (Object.keys(坐标).some(id => 现[id] && (Math.abs(现[id][0] - 坐标[id][0]) > 1.5 || Math.abs(现[id][1] - 坐标[id][1]) > 1.5))) throw new Error('移动了节点');
  }
  return true;
};

// ⭐ 排除 react-flow 容器，取 z 最高的浮层
const 找面板 = (page) => page.evaluate(() => {
  let 最佳 = null;
  for (const e of document.querySelectorAll('body *')) {
    if (e.closest('.react-flow__node') || e.closest('.react-flow__nodes')) continue;
    if (e.closest('.react-flow__pane')) continue;
    const cs = getComputedStyle(e);
    if (cs.position !== 'absolute' && cs.position !== 'fixed') continue;
    if (+cs.zIndex < 200) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 140 || r.height < 100) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (t.length < 3) continue;
    if (!最佳 || +cs.zIndex > +最佳.z) 最佳 = { tag: e.tagName, cls: String(e.className).slice(0, 80), z: cs.zIndex, 全文: t, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }
  return 最佳;
});

const 读项 = (page, 框) => page.evaluate((B) => {
  const [x0, y0, x1, y1] = B;
  const 项 = [], 见过 = new Set();
  for (const e of document.querySelectorAll('body *')) {
    const r = e.getBoundingClientRect();
    if (r.width < 18 || r.width > 400 || r.height < 16 || r.height > 130) continue;
    if (r.left < x0 - 4 || r.top < y0 - 4 || r.right > x1 + 4 || r.bottom > y1 + 4) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 12) continue;
    if ([...e.children].some(c => (c.innerText || '').replace(/\s+/g, ' ').trim() === t)) continue;
    const k = t + '|' + Math.round(r.left) + '|' + Math.round(r.top);
    if (见过.has(k)) continue; 见过.add(k);
    const cs = getComputedStyle(e);
    if (!(cs.cursor === 'pointer' || cs.borderRadius !== '0px' || /solid|hidden/.test(cs.borderTopStyle))) continue;
    项.push({ 文本: t, 白边: cs.borderColor === 'rgb(255, 255, 255)', 背景: cs.backgroundColor, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
  }
  return 项;
}, 框);

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 7000 });
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === '知道了'); if (b) b.click(); });
  await page.waitForTimeout(800);
  await page.evaluate(() => {
    const 条 = [...document.querySelectorAll('div')].filter(d => /开启浏览器通知/.test(d.innerText || ''));
    if (条.length) { 条.sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width); const btn = [...条[条.length - 1].querySelectorAll('button')].find(b => (b.innerText || '').trim() === ''); if (btn) btn.click(); }
  });
  await page.waitForTimeout(700);
  await page.evaluate(() => { for (const b of document.querySelectorAll('button')) if (b.getAttribute('aria-label') === '关闭' && b.getBoundingClientRect().width < 40) { b.click(); return; } });
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3200);

  const 全部 = [];
  for (const t of 待测) {
    记(`\n════ ${t.名} ${t.id} ════`);
    if (!(await page.evaluate((id) => !!document.querySelector(`.react-flow__node[data-id="${id}"]`), t.id))) { await page.keyboard.press('Meta+0'); await page.waitForTimeout(2500); }
    if (!(await 平移到左上(page, t.id))) { 记('　平移未成功'); continue; }
    const 落点 = await page.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) return null;
      const r = n.getBoundingClientRect();
      for (let i = 1; i < 10; i++) for (let j = 1; j < 10; j++) {
        const x = Math.round(r.left + r.width * i / 10), y = Math.round(r.top + r.height * j / 10);
        if (x < 5 || y < 5 || x > 1435 || y > 805) continue;
        const e = document.elementFromPoint(x, y);
        const g = e && e.closest('.react-flow__node');
        if (g && g.getAttribute('data-id') === id) return [x, y];
      }
      return null;
    }, t.id);
    if (!落点) { 记('　⛔ 无安全落点'); continue; }
    await page.mouse.click(落点[0], 落点[1]);
    await page.waitForTimeout(2600);
    const 选中 = await page.evaluate((id) => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')), t.id);
    if (选中.length !== 1 || 选中[0] !== t.id) { 记(`　⛔ 点中了 ${JSON.stringify(选中)}`); await page.keyboard.press('Escape'); await page.waitForTimeout(1000); continue; }

    const 下拉 = await page.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      for (const b of n.querySelectorAll('button')) {
        const t2 = (b.innerText || '').replace(/\s+/g, ' ').trim();
        if (!t2.includes('·')) continue;
        const r = b.getBoundingClientRect();
        if (r.bottom < 0 || r.top > innerHeight) continue;
        return { 文字: t2, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
      }
      return null;
    }, t.id);
    if (!下拉) { 记('　⛔ 没有摘要下拉'); continue; }
    记(`　打开「${下拉.文字}」`);
    await page.mouse.click(下拉.中心[0], 下拉.中心[1]);
    await page.waitForTimeout(2000);
    const 面板 = await 找面板(page);
    if (!面板) { 记('　⛔ 没找到 z≥200 的浮层'); await page.keyboard.press('Escape'); await page.waitForTimeout(1100); continue; }
    记(`　面板 <${面板.tag}> z=${面板.z} ${JSON.stringify(面板.box)} cls=${面板.cls.slice(0, 50)}`);
    记(`　⭐ 面板全文：「${面板.全文}」`);
    const 项 = await 读项(page, 面板.box);
    记(`　读到 ${项.length} 个可点项，按 y 排列：`);
    const 按Y = {};
    for (const x of 项) (按Y[Math.round(x.box[1] / 8) * 8] ||= []).push((x.白边 ? '【' + x.文本 + '】' : x.文本) + `${x.box[2]}×${x.box[3]}`);
    for (const k of Object.keys(按Y).sort((a, b) => a - b)) 记(`　　y≈${k}：${JSON.stringify(按Y[k])}`);
    记(`　⭐ 白边（当前值）：${JSON.stringify(项.filter(x => x.白边).map(x => x.文本))}`);
    await page.screenshot({ path: EVID + `eo3-${t.名}-面板.png` });
    全部.push({ 名: t.名, 摘要: 下拉.文字, 面板: { 框: 面板.box, 全文: 面板.全文, cls: 面板.cls }, 项: 项.map(x => ({ 文本: x.文本, 白边: x.白边, box: x.box })) });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1300);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(900);
  }
  结果.读数.全部 = 全部;
  记('\n✅ 完成（未点任何一项）');
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  try {
    记('⏳ ⌘0 复位 + 静置 15s…');
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(15000);
    const 现 = await 读全部坐标(page);
    const 真动 = Object.keys(坐标).filter(id => 现[id] && (Math.abs(现[id][0] - 坐标[id][0]) > 1.5 || Math.abs(现[id][1] - 坐标[id][1]) > 1.5));
    记(`⭐ 真的被移动：${真动.length} 个 ${JSON.stringify(真动)}`);
  } catch (e) { console.error(e); }
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEO3.json ===');
}
