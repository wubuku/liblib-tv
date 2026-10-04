// Batch ER：用 EQ 定位到的根因**重读**面板选中态，并验证根因修法本身对不对。
//
//   根因：边框/底色长在**可交互的父元素**上，innerText 挂在**最内层 span** 上。
//   修法：收到叶子文本后，沿 DOM **上溯**找第一个可交互祖先
//         （button / [role=button] / cursor:pointer），读**它**的样式。
//   ⭐ 同时对图片节点做一次「上溯读法 vs 旧的叶子读法」对照 ——
//     如果根因判断正确，两者对同一块面板必须给出**同一批**白边项。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchER1.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 待测 = [
  { id: 'a-THmbuJXQj4', 名: '音频' },
  { id: 'v-oZNpH99MtM', 名: '智能剪辑' },
  { id: 'i-sODTbgLUm1', 名: '图片', 对照: true },
];

const 找起点 = (page, dx, dy) => page.evaluate((d) => {
  const 好 = [];
  for (let y = 130; y <= 690; y += 20) for (let x = 130; x <= 1310; x += 20) {
    const e = document.elementFromPoint(x, y);
    if (!e) continue;
    if (e.closest('.react-flow__node') || e.closest('button,[role="button"],a')) continue;
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
    if (Object.keys(坐标).some(k => 现[k] && (Math.abs(现[k][0] - 坐标[k][0]) > 1.5 || Math.abs(现[k][1] - 坐标[k][1]) > 1.5))) throw new Error('移动了节点');
  }
  return true;
};

const 找面板 = (page) => page.evaluate(() => {
  let 最佳 = null;
  for (const e of document.querySelectorAll('body *')) {
    if (e.closest('.react-flow__node') || e.closest('.react-flow__nodes') || e.closest('.react-flow__pane')) continue;
    const cs = getComputedStyle(e);
    if (cs.position !== 'absolute' && cs.position !== 'fixed') continue;
    if (+cs.zIndex < 200) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 140 || r.height < 100) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (t.length < 3) continue;
    if (!最佳 || +cs.zIndex > +最佳.z) 最佳 = { z: cs.zIndex, 全文: t, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }
  return 最佳;
});

/**
 * ⭐ 核心：叶子文本 → **上溯**到可交互祖先 → 读**祖先**的样式
 * 两种读法都记，便于对照验证根因。
 */
const 读面板项 = (page, 框) => page.evaluate((B) => {
  const [x0, y0, x1, y1] = B;
  const 出 = [], 见过 = new Set();
  for (const e of document.querySelectorAll('body *')) {
    if (e.closest('.react-flow__node') || e.closest('.react-flow__nodes')) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.width > 400 || r.height < 8 || r.height > 200) continue;
    if (r.left < x0 - 6 || r.top < y0 - 6 || r.right > x1 + 6 || r.bottom > y1 + 6) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 16) continue;
    if ([...e.children].some(c => (c.innerText || '').replace(/\s+/g, ' ').trim() === t)) continue;
    const k = t + '|' + Math.round(r.left) + '|' + Math.round(r.top);
    if (见过.has(k)) continue; 见过.add(k);

    // ---- 旧读法：直接读自己
    const csSelf = getComputedStyle(e);
    const 旧 = { 边框: csSelf.borderColor + ' ' + csSelf.borderWidth, 白边: csSelf.borderColor === 'rgb(255, 255, 255)' };

    // ---- ⭐ 新读法：沿 parentElement 上溯，找第一个可交互祖先
    let 祖先 = null;
    for (let p = e.parentElement, i = 0; p && i < 6; p = p.parentElement, i++) {
      const pr = p.getBoundingClientRect();
      if (pr.width < 8 || pr.width > 400 || pr.height < 8 || pr.height > 200) break;
      if (pr.left < x0 - 6 || pr.top < y0 - 6 || pr.right > x1 + 6 || pr.bottom > y1 + 6) break;
      const cs = getComputedStyle(p);
      const 可交互 = p.tagName === 'BUTTON' || p.getAttribute('role') === 'button' || cs.cursor === 'pointer' || (cs.borderTopWidth !== '0px' && cs.borderTopStyle !== 'none');
      if (可交互) { 祖先 = p; break; }
    }
    let 新 = null;
    if (祖先) {
      const acs = getComputedStyle(祖先);
      const ar = 祖先.getBoundingClientRect();
      新 = {
        tag: 祖先.tagName, 层级: (() => { let n = 0, p = e.parentElement; while (p && p !== 祖先) { n++; p = p.parentElement; } return n; })(),
        边框: acs.borderColor + ' ' + acs.borderWidth,
        背景: acs.backgroundColor,
        白边: acs.borderColor === 'rgb(255, 255, 255)',
        光标: acs.cursor,
        box: [Math.round(ar.left), Math.round(ar.top), Math.round(ar.width), Math.round(ar.height)],
        祖先文本: (祖先.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
      };
    }
    出.push({
      文本: t, 自己box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      自己字重: csSelf.fontWeight, 自己光标: csSelf.cursor,
      旧, 新,
    });
  }
  出.sort((a, b) => (a.自己box[1] - b.自己box[1]) || (a.自己box[0] - b.自己box[0]));
  return 出;
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
  记(`开局坐标偏差：${JSON.stringify(await 核对坐标(page))}`);

  const 全 = {};
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
    const 选 = await page.evaluate((id) => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')), t.id);
    if (选.length !== 1 || 选[0] !== t.id) { 记(`　⛔ 点中了 ${JSON.stringify(选)}`); await page.keyboard.press('Escape'); await page.waitForTimeout(1000); continue; }
    const 下拉 = await page.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      for (const b of n.querySelectorAll('button')) {
        const x = (b.innerText || '').replace(/\s+/g, ' ').trim();
        if (!x.includes('·')) continue;
        const r = b.getBoundingClientRect();
        if (r.bottom < 0 || r.top > innerHeight) continue;
        return { 文字: x, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
      }
      return null;
    }, t.id);
    if (!下拉) { 记('　⛔ 没有摘要下拉'); continue; }
    await page.mouse.click(下拉.中心[0], 下拉.中心[1]);
    await page.waitForTimeout(2000);
    await page.screenshot({ path: EVID + `er1-${t.名}-面板.png` });
    const 面板 = await 找面板(page);
    if (!面板) { 记('　⛔ 没找到面板'); continue; }
    记(`　摘要「${下拉.文字}」｜面板 ${JSON.stringify(面板.box)}`);
    记(`　全文「${面板.全文}」`);
    const 项 = await 读面板项(page, 面板.box);
    记(`　读到 ${项.length} 个叶子：`);
    for (const x of 项) {
      记(`　　「${x.文本}」自己${x.自己box[2]}×${x.自己box[3]} 字重=${x.自己字重} 光标=${x.自己光标}`);
      记(`　　　旧读法：边框=${x.旧.边框} 白边=${x.旧.白边}`);
      记(`　　　新读法：${x.新 ? `<${x.新.tag}> 上溯${x.新.层级}层 ${x.新.box[2]}×${x.新.box[3]} 边框=${x.新.边框} 背景=${x.新.背景} 光标=${x.新.光标}${x.新.白边 ? ' ⭐白边' : ''}` : '⛔ 没找到可交互祖先'}`);
    }
    const 旧白 = 项.filter(x => x.旧.白边).map(x => x.文本);
    const 新白 = 项.filter(x => x.新 && x.新.白边).map(x => x.文本);
    记(`\n　⭐ 旧读法的白边：${JSON.stringify(旧白)}（${旧白.length} 个）`);
    记(`　⭐ 新读法的白边：${JSON.stringify(新白)}（${新白.length} 个）`);
    记(`　⭐ 两法是否一致：${JSON.stringify(旧白) === JSON.stringify(新白) ? '✅ 完全一致' : '⚠️ 不一致（新法多出 ' + 新白.filter(x => !旧白.includes(x)).length + ' 个）'}`);
    const 摘要词 = 下拉.文字.split(/[·\s]+/).filter(Boolean);
    记(`　⭐ 摘要 ${JSON.stringify(摘要词)} 逐个对上：${摘要词.map(w => `${w}=${新白.some(s => s === w) || 项.some(x => x.文本 === w)}`).join(' ')}`);
    全[t.名] = { 摘要: 下拉.文字, 框: 面板.box, 全文: 面板.全文, 项, 旧白, 新白 };
    await page.keyboard.press('Escape'); await page.waitForTimeout(1300);
    await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  }
  结果.读数.全 = 全;
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
  console.log('\n=== 已写 tools/batchER1.json ===');
}
