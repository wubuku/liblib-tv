// Batch EO-2：精确重取每一类节点的**参数面板**。
//   EO-1 的两个问题：
//   ① 挑下拉挑错了 —— 我按「最长文字」选，结果图片/音频/文本都挑到了**模型**下拉
//      （`Lib Image 2.5 Pro` / `Seed Audio 1.0` / `GVLM 3.1`）而不是参数下拉。
//      ⇒ 本轮按**文字里含「 · 」分隔符**来认参数摘要下拉。
//   ② 视频节点那块不是 Mantine Popover ⇒ 按 class 白名单找面板会漏。
//      ⇒ 本轮加一个**通用浮层读取器**：所有 z≥20 且新出现的绝对定位容器。
//   ③ 智能剪辑的「时长」组读到 0 项 —— 项宽超过了我设的 140px 上限。
//      ⇒ 本轮把项宽上限放宽到 400px。
// ⛔ 只打开面板并读取，不点任何一项。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEO2.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 待测 = [
  { id: 'v-v2hlWY4Br3', 名: '视频' },
  { id: 'a-THmbuJXQj4', 名: '音频' },
  { id: 't-UtVx3lZmrV', 名: '文本' },
  { id: 'v-oZNpH99MtM', 名: '智能剪辑' },
  { id: 'i-sODTbgLUm1', 名: '图片' },
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
    let 净 = 0;
    for (let a = -40; a <= 40; a += 20) for (let b = -40; b <= 40; b += 20) {
      const p = document.elementFromPoint(x + b, y + a);
      if (p && !p.closest('.react-flow__node') && !p.closest('button,[role="button"]')) 净++;
    }
    const 走X = d.dx < 0 ? x - 10 : (1310 - x);
    const 走Y = d.dy < 0 ? y - 10 : (690 - y);
    好.push({ x, y, 净, 走X, 走Y, 够: Math.min(走X / Math.max(1, Math.abs(d.dx)), 走Y / Math.max(1, Math.abs(d.dy))) });
  }
  if (!好.length) return null;
  好.sort((a, b) => (b.够 - a.够) || (b.净 - a.净));
  return 好[0];
}, { dx, dy });

const 守卫 = async (page, 段) => {
  const 现 = await 读全部坐标(page);
  const 真动 = Object.keys(坐标).filter(id => 现[id] && (Math.abs(现[id][0] - 坐标[id][0]) > 1.5 || Math.abs(现[id][1] - 坐标[id][1]) > 1.5));
  if (真动.length) throw new Error('移动了节点，立即中止');
  return 真动.length;
};

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
    await 守卫(page, `第${段 + 1}段`);
  }
  return true;
};

// ⭐ 通用浮层读取器：不认 class，只认「新出现的、z≥20 的绝对/固定定位容器」
const 读浮层 = (page) => page.evaluate(() => {
  const 候选 = [];
  for (const e of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(e);
    if (cs.position !== 'absolute' && cs.position !== 'fixed') continue;
    if (+cs.zIndex < 20) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 140 || r.height < 100) continue;
    if (r.right < 0 || r.bottom < 0 || r.left > innerWidth || r.top > innerHeight) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (t.length < 3) continue;
    候选.push({
      tag: e.tagName, cls: String(e.className).slice(0, 90), z: cs.zIndex, 文本长: t.length, 文本: t.slice(0, 200),
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      面积: Math.round(r.width * r.height),
    });
  }
  // 最内层优先：面积小但文本多的
  候选.sort((a, b) => (b.文本长 / (b.面积 / 10000)) - (a.文本长 / (a.面积 / 10000)));
  return 候选.slice(0, 5);
});

// 读浮层里的项：宽上限放到 400，容忍各种形状
const 读项 = (page, 框) => page.evaluate((B) => {
  const [x0, y0, x1, y1] = B;
  const 项 = [];
  const 见过 = new Set();
  for (const e of document.querySelectorAll('body *')) {
    const r = e.getBoundingClientRect();
    if (r.width < 18 || r.width > 400 || r.height < 16 || r.height > 120) continue;
    // 必须落在浮层框内
    if (r.left < x0 - 4 || r.top < y0 - 4 || r.right > x1 + 4 || r.bottom > y1 + 4) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 12) continue;
    const 有子同文 = [...e.children].some(c => (c.innerText || '').replace(/\s+/g, ' ').trim() === t);
    if (有子同文) continue;
    const k = t + '|' + Math.round(r.left) + '|' + Math.round(r.top);
    if (见过.has(k)) continue; 见过.add(k);
    const cs = getComputedStyle(e);
    const 条 = cs.cursor === 'pointer' || cs.borderRadius !== '0px' || /solid|hidden/.test(cs.borderTopStyle);
    if (!条) continue;
    项.push({
      文本: t,
      白边: cs.borderColor === 'rgb(255, 255, 255)',
      背景: cs.backgroundColor,
      边框: cs.borderColor + ' ' + cs.borderWidth,
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      cls: String(e.className).slice(0, 60),
    });
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
  记(`开局坐标偏差：${JSON.stringify(await 核对坐标(page))}`);

  const 全部 = [];
  for (const t of 待测) {
    记(`\n════ ${t.id} ${t.名} ════`);
    if (!(await page.evaluate((id) => !!document.querySelector(`.react-flow__node[data-id="${id}"]`), t.id))) {
      记('　不在 DOM，先 ⌘0'); await page.keyboard.press('Meta+0'); await page.waitForTimeout(2500);
    }
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

    // ⭐ 参数条上所有带文字的按钮（这一项本身就有价值）
    const 条上 = await page.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      const 出 = [];
      for (const b of n.querySelectorAll('button')) {
        const r = b.getBoundingClientRect();
        if (r.width < 10 || r.width > 520 || r.height < 10 || r.height > 90) continue;
        if (r.bottom < 0 || r.top > innerHeight) continue;
        const t = (b.innerText || '').replace(/\s+/g, ' ').trim();
        if (!t) continue;
        出.push({ 文字: t, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
      }
      return 出;
    }, t.id);
    记(`　⭐ 参数条上带文字的按钮 ${条上.length} 枚：${JSON.stringify(条上.map(b => b.文字))}`);
    结果.读数[t.名 + '_参数条按钮'] = 条上;

    // ⭐ 认参数摘要下拉：文字里含「 · 」
    const 摘要下拉 = 条上.find(b => b.文字.includes('·'));
    if (!摘要下拉) { 记('　⛔ 参数条上**没有**带「 · 」的摘要下拉 —— 这本身就是结论'); 全部.push({ 名: t.名, 结论: '无摘要下拉', 参数条按钮: 条上.map(b => b.文字) }); await page.keyboard.press('Escape'); await page.waitForTimeout(1100); continue; }
    记(`　打开摘要下拉「${摘要下拉.文字}」`);
    await page.mouse.click(摘要下拉.中心[0], 摘要下拉.中心[1]);
    await page.waitForTimeout(2000);
    await page.screenshot({ path: EVID + `eo2-${t.名}-面板.png` });

    const 浮层 = await 读浮层(page);
    记(`　浮层候选 ${浮层.length} 个：`);
    for (const f of 浮层) 记(`　　<${f.tag}> z=${f.z} box=${JSON.stringify(f.box)} 文本长=${f.文本长} cls=${f.cls.slice(0, 56)}｜「${f.文本.slice(0, 70)}」`);

    if (!浮层.length) { 全部.push({ 名: t.名, 结论: '没打开出浮层', 摘要: 摘要下拉.文字 }); await page.keyboard.press('Escape'); await page.waitForTimeout(1100); continue; }
    const 面板 = 浮层[0];
    const 项 = await 读项(page, 面板.box);
    记(`　面板 ${JSON.stringify(面板.box)}，读到 ${项.length} 个可点项：`);
    const 白 = 项.filter(x => x.白边);
    记(`　⭐ 白边（当前值）${白.length} 个：${JSON.stringify(白.map(x => x.文本))}`);
    const 按Y = {};
    for (const x of 项) (按Y[Math.round(x.box[1] / 10) * 10] ||= []).push(x.文本);
    for (const k of Object.keys(按Y).sort((a, b) => a - b)) 记(`　　y≈${k}：${JSON.stringify(按Y[k])}`);
    const 摘要词 = 摘要下拉.文字.split(/[·\s]+/).filter(Boolean);
    记(`　⭐ 摘要「${摘要下拉.文字}」拆成 ${JSON.stringify(摘要词)}，逐个在面板里找：${摘要词.map(w => `${w}=${项.some(x => x.文本 === w || x.文本.includes(w))}`).join(' ')}`);
    全部.push({ 名: t.名, 摘要: 摘要下拉.文字, 面板框: 面板.box, 面板文本: 面板.文本, 项: 项.map(x => ({ 文本: x.文本, 白边: x.白边, box: x.box })), 白边: 白.map(x => x.文本) });

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
    记('⏳ ⌘0 复位 + 静置 15s（三铁律③）…');
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(15000);
    const 现 = await 读全部坐标(page);
    const 真动 = Object.keys(坐标).filter(id => 现[id] && (Math.abs(现[id][0] - 坐标[id][0]) > 1.5 || Math.abs(现[id][1] - 坐标[id][1]) > 1.5));
    记(`⭐ 真的被移动：${真动.length} 个 ${JSON.stringify(真动)}`);
  } catch (e) { console.error(e); }
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEO2.json ===');
}
