// Batch ES-1：把「当前值」用**直接命中**的判据读出来，并先在已知答案的样本上验证。
//
//   ER 批的教训：筛「哪些是项」的所有单一判据都只对一部分。
//   ⭐⭐ 本轮换一个**不筛项、直接命中答案**的判据：
//        枚举面板内 `borderColor === 'rgb(255,255,255)'` 且 `borderWidth ≠ 0px` 的元素
//        —— **选中态本身就是判据**，选中项一定会在这份名单里。
//   ⭐⭐ 先在**答案已知**的两个样本上跑这个方法（对照）：
//        图片节点 已知 5 个（标准画质/2K/自动/16:9/1张，EN-2 验过）
//        视频节点 已知 4 个（16:9/720P/开启/1个，EP 从截图读出）
//      跑通了才拿去读音频和智能剪辑。
// ⛔ 只读面板，不点任何一项。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchES1.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

// 顺序很重要：先两个「对照组」，后两个「待测」
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
 * ⭐⭐ 直接命中判据：面板内**所有白边元素**，不筛「哪些是项」。
 *   同时把「同位置的兄弟节点」也带出来（同一父容器里其它文字），
 *   方便把「容器」和「项本身」区分开。
 */
const 找白边 = (page, 框) => page.evaluate((B) => {
  const [x0, y0, x1, y1] = B;
  const 命中 = [];
  for (const e of document.querySelectorAll('body *')) {
    if (e.closest('.react-flow__node') || e.closest('.react-flow__nodes')) continue;
    const cs = getComputedStyle(e);
    if (cs.borderColor !== 'rgb(255, 255, 255)') continue;
    const w = [cs.borderTopWidth, cs.borderRightWidth, cs.borderBottomWidth, cs.borderLeftWidth].map(parseFloat);
    if (!w.some(x => x > 0)) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.width > 400 || r.height < 8 || r.height > 200) continue;
    if (r.left < x0 - 6 || r.top < y0 - 6 || r.right > x1 + 6 || r.bottom > y1 + 6) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    命中.push({
      tag: e.tagName, 文本: t.slice(0, 30), 文本长: t.length,
      边框宽: cs.borderTopWidth, 背景: cs.backgroundColor,
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      cls: String(e.className).slice(0, 60),
      子数: e.children.length,
    });
  }
  命中.sort((a, b) => (a.box[1] - b.box[1]) || (a.box[0] - b.box[0]));
  return 命中;
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
  let 对照全过 = true;
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
    await page.waitForTimeout(2100);
    await page.screenshot({ path: EVID + `es1-${t.名}-面板.png` });
    const 面板 = await 找面板(page);
    if (!面板) { 记('　⛔ 没找到面板'); continue; }
    记(`　摘要「${下拉.文字}」｜面板 ${JSON.stringify(面板.box)}`);
    const 白 = await 找白边(page, 面板.box);
    记(`　⭐ 面板内**白边元素** ${白.length} 个：`);
    for (const x of 白) 记(`　　<${x.tag}> 「${x.文本 || '（无文字）'}」 ${x.box[2]}×${x.box[3]} 边框=${x.边框宽} 背景=${x.背景} 子数=${x.子数} cls=${x.cls.slice(0, 44)}`);
    const 短 = 白.filter(x => x.文本长 > 0 && x.文本长 <= 8).map(x => x.文本);
    记(`　⭐ 其中**带短文字**的（就是「项」本身）：${JSON.stringify(短)}`);
    if (t.已知) {
      const 缺 = t.已知.filter(k => !短.includes(k));
      const 多 = 短.filter(k => !t.已知.includes(k));
      记(`　⭐ 对照：已知 ${JSON.stringify(t.已知)}｜读出 ${JSON.stringify(短)}`);
      记(`　　　漏 ${JSON.stringify(缺)}｜多 ${JSON.stringify(多)}｜${缺.length === 0 && 多.length === 0 ? '✅ 完全一致' : '❌ 不一致'}`);
      if (缺.length || 多.length) 对照全过 = false;
    }
    const 摘要词 = 下拉.文字.split(/[·\s]+/).filter(Boolean);
    记(`　⭐ 摘要 ${JSON.stringify(摘要词)} 逐个对上：${摘要词.map(w => `${w}=${短.includes(w)}`).join(' ')}`);
    全[t.名] = { 角色: t.角色, 摘要: 下拉.文字, 框: 面板.box, 全文: 面板.全文, 白边: 白, 短, 已知: t.已知 };
    await page.keyboard.press('Escape'); await page.waitForTimeout(1300);
    await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  }
  结果.读数.全 = 全;
  记(`\n⭐⭐ 判据验证结论：两个对照组${对照全过 ? '**全部复现已知答案** ✅ 这套判据可用' : '**没全部复现** ⛔ 读数不可信，不采用'}`);
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
  console.log('\n=== 已写 tools/batchES1.json ===');
}
