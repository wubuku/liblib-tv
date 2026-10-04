// Batch EO-1：逐类节点打开参数面板，列出各自的组与项。
//   EN 批发现图片节点的参数面板是「画质 5 / 清晰度 3 / 背景 3 / 比例 13 / 生成数量 3」共 27 项，
//   ⭐ 但视频节点底栏的摘要写的是 `16:9 · 720P · 5s · 1个` —— 明显是**另一套**参数。
//   本轮把每一类节点的参数面板都开一遍，逐组逐项读出来，并和触发按钮摘要两头核对。
//
// ⭐ 沿用 EM-3/EM-4 的两招：
//   ① 卡片在画面外就用**中键拖**平移进去（缩放没用，锚点在视口中心）
//   ② 守卫区分「真的被移动」和「没渲染」
// ⛔ 只打开面板并读取，**不点任何一项**（不换参数、不触发生成）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEO1.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

// 五类节点各挑一个（图片/音频/文本/视频/智能剪辑），逐帧拉片与导演台先看有没有这枚下拉
const 待测 = [
  { id: 'i-sODTbgLUm1', 名: '图片' },
  { id: 'v-v2hlWY4Br3', 名: '视频' },
  { id: 'a-THmbuJXQj4', 名: '音频' },
  { id: 't-UtVx3lZmrV', 名: '文本' },
  { id: 'v-oZNpH99MtM', 名: '智能剪辑' },
  { id: 'b-mfkcQNULC3', 名: '逐帧拉片' },
  { id: 'n-56F19pXVB4', 名: '导演台' },
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
    const 够 = Math.min(走X / Math.max(1, Math.abs(d.dx)), 走Y / Math.max(1, Math.abs(d.dy)));
    好.push({ x, y, 净, 走X, 走Y, 够 });
  }
  if (!好.length) return null;
  好.sort((a, b) => (b.够 - a.够) || (b.净 - a.净));
  return 好[0];
}, { dx, dy });

const 守卫 = async (page, 段) => {
  const 现 = await 读全部坐标(page);
  const 真动 = Object.keys(坐标).filter(id => 现[id] && (Math.abs(现[id][0] - 坐标[id][0]) > 1.5 || Math.abs(现[id][1] - 坐标[id][1]) > 1.5));
  const 未渲染 = BASE.filter(id => !现[id]);
  记(`　　${段}：已渲染 ${Object.keys(现).length}/11，未渲染 ${未渲染.length}，**真的被移动 ${真动.length}**`);
  if (真动.length) throw new Error('移动了节点，立即中止');
};

// 把节点平移到 (200,150)
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

// 读参数面板：逐组逐项
const 读面板 = (page) => page.evaluate(() => {
  let 面板 = null;
  for (const e of document.querySelectorAll('body *')) {
    if (!/Popover-dropdown|popover/i.test(String(e.className))) continue;
    const r = e.getBoundingClientRect();
    if (r.width > 150 && r.height > 150 && r.top > 0 && r.left > 0) { 面板 = e; break; }
  }
  if (!面板) return null;
  const pr = 面板.getBoundingClientRect();
  const 分组 = [];
  let 当前 = null;
  for (const e of 面板.querySelectorAll('*')) {
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    const cs = getComputedStyle(e);
    // 项：窄、矮、可点
    if (cs.cursor === 'pointer' && r.height >= 20 && r.height <= 90 && r.width <= 140 && t && t.length <= 10 && !/Popover|dropdown/.test(String(e.className))) {
      const 项 = {
        文本: t, 背景: cs.backgroundColor, 边框: cs.borderColor + ' ' + cs.borderWidth,
        白边: cs.borderColor === 'rgb(255, 255, 255)',
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        分组: 当前 ? 当前.标题 : null,   // ⭐ 存字符串；存对象会构成循环引用
      };
      if (当前) 当前.项.push(项); else 分组.push({ 标题: '（无标题）', 项: [项] });
    } else if (t && t.length <= 8 && r.height < 40 && r.width < 220 && r.top > pr.top && r.top < pr.bottom) {
      const 是标题 = /^(h[1-6]|div|span|p|label)$/i.test(e.tagName) && cs.fontWeight >= 500 && [...e.children].every(c => (c.innerText || '').trim() === t);
      if (是标题) { 当前 = { 标题: t, 项: [] }; 分组.push(当前); }
    }
  }
  return { 框: [Math.round(pr.left), Math.round(pr.top), Math.round(pr.width), Math.round(pr.height)], 分组 };
});

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
    const 在DOM = await page.evaluate((id) => !!document.querySelector(`.react-flow__node[data-id="${id}"]`), t.id);
    if (!在DOM) { 记('　不在 DOM（被平移推出视口了），先 ⌘0'); await page.keyboard.press('Meta+0'); await page.waitForTimeout(2500); }
    const ok = await 平移到左上(page, t.id);
    if (!ok) { 记('　平移未成功'); await page.screenshot({ path: EVID + `eo1-${t.名}-平移失败.png` }); continue; }
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

    // 读参数条上的所有带文字的按钮（找那枚参数下拉）
    const 条上按钮 = await page.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      const 出 = [];
      for (const b of n.querySelectorAll('button')) {
        const r = b.getBoundingClientRect();
        if (r.width < 10 || r.width > 500 || r.height < 10 || r.height > 90) continue;
        if (r.top > 810 || r.bottom < 0) continue;
        const t = (b.innerText || '').replace(/\s+/g, ' ').trim();
        if (!t) continue;
        // 有 ⌄ 形状的子元素 ⇒ 大概率是下拉
        const 有箭头 = /M6\.2\.12a\.4\.4|lucide-chevron|chevron-down/i.test([...b.querySelectorAll('path')].map(p => p.getAttribute('d') || '').join(' ') + ' ' + String(b.className));
        出.push({ 文字: t, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 像下拉: 有箭头 });
      }
      return 出;
    }, t.id);
    记(`　参数条上带文字的按钮：${JSON.stringify(条上按钮.map(b => b.文字))}`);

    const 下拉 = 条上按钮.find(b => b.像下拉 && b.文字.length > 6) || 条上按钮.find(b => b.文字.length > 6);
    if (!下拉) { 记('　⛔ 参数条上没有可点的下拉（这可能本身就是结论）'); 全部.push({ id: t.id, 名: t.名, 结论: '参数条上没有长文字下拉' }); await page.keyboard.press('Escape'); await page.waitForTimeout(1000); continue; }
    记(`　打开下拉「${下拉.文字}」`);
    await page.mouse.click(下拉.中心[0], 下拉.中心[1]);
    await page.waitForTimeout(1900);
    await page.screenshot({ path: EVID + `eo1-${t.名}-面板打开.png` });
    const 面板 = await 读面板(page);
    if (!面板) { 记('　⛔ 没找到 Popover 面板 —— 可能是另一类浮层'); 全部.push({ id: t.id, 名: t.名, 结论: '无 Popover', 触发器: 下拉.文字 }); }
    else {
      记(`　面板 ${JSON.stringify(面板.框)}，共 ${面板.分组.length} 组：`);
      const 选中集 = [];
      for (const g of 面板.分组) {
        const 选中 = g.项.filter(x => x.白边).map(x => x.文本);
        选中集.push(...选中);
        记(`　　【${g.标题}】${g.项.length} 项：${JSON.stringify(g.项.map(x => x.文本))}`);
        记(`　　　白边（当前值）：${选中.length ? JSON.stringify(选中) : '⛔ 这一组一个都没有'}`);
      }
      const 拼接 = 选中集.join(' ');
      记(`　⭐ 五组当前值拼起来 = 「${拼接}」｜触发器摘要 = 「${下拉.文字}」`);
      记(`　⭐ 触发器摘要里的每个词都能在面板里找到：${下拉.文字.split(/[·\s]+/).filter(Boolean).map(w => `${w}=${选中集.some(s => s.includes(w) || w.includes(s))}`).join(' ')}`);
      全部.push({ id: t.id, 名: t.名, 触发器: 下拉.文字, 框: 面板.框, 分组: 面板.分组.map(g => ({ 标题: g.标题, 项: g.项.map(x => x.文本), 选中: g.项.filter(x => x.白边).map(x => x.文本) })) });
    }
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1300);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(900);
  }
  结果.读数.全部 = 全部;
  记('\n✅ 七类节点的面板读完了（未点任何一项）');
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
  console.log('\n=== 已写 tools/batchEO1.json ===');
}
