// Batch ES-2：把参数面板里**每一枚按钮的全部计算样式**原样倒出来，离线找判据。
//
//   ES-1 的教训：⛔ 「白边不是统一机制」是**错误结论**。真因是我自己的判据有缺陷 ——
//   面板框是 [left, top, width, height]，却被解构成 [x0, y0, x1, y1]，
//   采样区从 342 宽被压成 158 宽，只截到每行最左一列。
//   ⭐⭐ 五轮下来，凡「单一判据 + 边跑边判」都会漏。这轮改成：
//        1) 不做任何「哪些是项」的预筛 —— 面板里所有 <button> 全量记录；
//        2) 每枚按钮记录 20+ 个计算属性（border 四边色/宽、background、boxShadow、
//           outline、opacity、fontWeight、color、cursor、aria/data-* 全量）；
//        3) 离线拿**答案已知的两个对照**（图片 5 个 / 视频 4 个）做回归，
//           找出能同时切分两者的属性，再拿去读音频 / 智能剪辑。
// ⛔ 只打开面板读属性，不点任何一项。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchES2.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

// 前两个是**答案已知**的对照组（EN-2 / EP 从实拍图读出），后两个是待测
const 待测 = [
  { id: 'i-sODTbgLUm1', 名: '图片', 角色: '对照', 已知: ['标准画质', '2K', '自动', '16:9', '1张'] },
  { id: 'v-v2hlWY4Br3', 名: '视频', 角色: '对照', 已知: ['16:9', '720P', '开启', '1个'] },
  { id: 'a-THmbuJXQj4', 名: '音频', 角色: '待测', 已知: null },
  { id: 'v-oZNpH99MtM', 名: '智能剪辑', 角色: '待测', 已知: null },
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

/**
 * 找参数面板根元素，并把它里面**所有 <button>** 的全量计算样式倒出来。
 * ⭐ 面板框按 [left, top, width, height] 正确展开成区域，不再压成 158 宽。
 */
const 倾倒面板 = (page) => page.evaluate(() => {
  const 候选 = [];
  for (const e of document.querySelectorAll('body *')) {
    if (e.closest('.react-flow__node') || e.closest('.react-flow__nodes') || e.closest('.react-flow__pane')) continue;
    const cs = getComputedStyle(e);
    if (cs.position !== 'absolute' && cs.position !== 'fixed') continue;
    if (+cs.zIndex < 200) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 140 || r.height < 100) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (t.length < 3) continue;
    候选.push({ e, z: +cs.zIndex, 全文: t, box: [r.left, r.top, r.width, r.height] });
  }
  if (!候选.length) return null;
  候选.sort((a, b) => b.z - a.z || b.box[3] - a.box[3]);
  const 根 = 候选[0];
  const [L, T, W, H] = 根.box;

  const 属性 = (e) => {
    const cs = getComputedStyle(e);
    const r = e.getBoundingClientRect();
    const 自己的字 = [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join(' ').replace(/\s+/g, ' ').trim();
    const 全字 = (e.innerText || '').replace(/\s+/g, ' ').trim();
    const attrs = {};
    for (const a of e.attributes) {
      if (/^(aria|data-)/.test(a.name)) attrs[a.name] = a.value.slice(0, 40);
    }
    return {
      tag: e.tagName,
      自己字: 自己的字, 文字: 全字, 字数: 全字.length,
      文字直: Array.from(e.childNodes).some(n => n.nodeType === 3 && n.textContent.trim()),
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      在面板内: r.left >= L - 8 && r.top >= T - 8 && r.right <= L + W + 8 && r.bottom <= T + H + 8,
      cls: String(e.className),
      边框: [cs.borderTopColor, cs.borderRightColor, cs.borderBottomColor, cs.borderLeftColor].join(' | '),
      边框宽: [cs.borderTopWidth, cs.borderRightWidth, cs.borderBottomWidth, cs.borderLeftWidth].join(' | '),
      背景: cs.backgroundColor,
      阴影: cs.boxShadow,
      描边: cs.outline + ' / ' + cs.outlineColor,
      透明: cs.opacity,
      粗细: cs.fontWeight,
      字色: cs.color,
      光标: cs.cursor,
      attrs,
    };
  };

  const 按钮 = [...根.e.querySelectorAll('button')].map(属性);
  // 面板内所有「有背景或边框」的非按钮元素，防止漏掉不是 <button> 的项
  const 其它 = [...根.e.querySelectorAll('*')].filter(e => e.tagName !== 'BUTTON').map(属性)
    .filter(x => x.在面板内 && (x.文字 || x.边框宽.includes('0px') === false || x.背景 !== 'rgba(0, 0, 0, 0)'));
  return { 面板框: 根.box.map(Math.round), 全文: 根.全文, 按钮, 其它 };
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

  const 全 = {};
  for (const t of 待测) {
    记(`\n════ ${t.名}（${t.角色}）${t.id} ════`);
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
    const 选 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
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
    await page.waitForTimeout(2100);
    await page.screenshot({ path: EVID + `es2-${t.名}-面板.png` });
    const d = await 倾倒面板(page);
    if (!d) { 记('　⛔ 没找到面板'); continue; }
    记(`　摘要「${下拉.文字}」｜面板 ${JSON.stringify(d.面板框)}（left/top/w/h）｜按钮 ${d.按钮.length} 枚`);
    // 只打印「有自己文字」的按钮：项本身 vs 纯容器
    const 项 = d.按钮.filter(b => b.文字);
    记(`　⭐ 其中**有文字**的 ${项.length} 枚，逐枚倾倒：`);
    for (const b of 项) 记(`　　「${b.文字}」 ${b.box[2]}×${b.box[3]} 边框=${b.边框} 宽=${b.边框宽} 背景=${b.背景} 粗=${b.粗细} 光标=${b.光标} 透明=${b.透明} 在面板内=${b.在面板内}`);
    记(`　⭐ 全部按钮边框色取值统计：${JSON.stringify(项.reduce((a, b) => (a[b.边框] = (a[b.边框] || 0) + 1, a), {}))}`);
    记(`　⭐ 全部按钮背景色取值统计：${JSON.stringify(项.reduce((a, b) => (a[b.背景] = (a[b.背景] || 0) + 1, a), {}))}`);
    全[t.名] = { 角色: t.角色, 摘要: 下拉.文字, ...d, 已知: t.已知 };
    await page.keyboard.press('Escape'); await page.waitForTimeout(1300);
    await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  }
  结果.读数.全 = 全;
  记('\n✅ 全量倾倒完成（未点任何一项）');
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
  console.log('\n=== 已写 tools/batchES2.json ===');
}
