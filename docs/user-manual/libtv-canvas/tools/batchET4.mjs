// Batch ET-4：最后两处不确定，一次问完。
//
//   ET-3 用实拍图坐实了两件事：
//     ① 视频参数面板里「生成音频」标题**右边确实有一枚 ⓘ**（12×12、`.cursor-help`、内含 svg path、无文字）
//     ② ⓘ **确实出气泡** —— 画面左侧那枚黑底「新功能：」就是，
//        box=[176,297,114,27]，**被参数面板挡住，只露出「新功能：」三个字**，剩下的「支持真人」在面板底下。
//        ⇒ ⛔ EQ 批「ⓘ 悬停不出任何气泡」的结论**是错的**，作废。
//
//   但还有两处不能靠推理：
//     ③ 气泡到底归谁？全页共 3 枚 `.cursor-help`：
//        `自动校验素材` [118,586] / `智能引用 AutoLink` [150,625] / `生成音频 ⓘ` [309,332]。
//        本轮**逐枚悬停**，看哪一枚出「新功能：支持真人」—— 这就是归属的阳性对照。
//        另外 ET-3 那次 `elementFromPoint(ⓘ中心)` 返回的是 `.react-flow__pane` 而不是 ⓘ，
//        说明中间有东西挡着；本轮把「移动前 / 移动后」各读一次，看清楚是「面板挡的」还是「ⓘ 不可点」。
//     ④ 音频的 ⚙ 到底是不是 toggle？ET-3 出现一个矛盾：
//        「还没点 ⚙ 就已经有 3 根滑杆」+「点开后还是 3 根」+「Esc 之后变 0 根」。
//        本轮做**受控 A/B/C**：点一次记一次、再点一次记一次、再 Esc 记一次。
//
// ⛔ 只读 + 只点 ⚙（不碰任何滑块、不改任何数值）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchET4.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

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
  for (let 段 = 0; 段 < 7; 段++) {
    const 框 = await page.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; }, id);
    if (!框) { await page.keyboard.press('Meta+0'); await page.waitForTimeout(2200); continue; }
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
  return false;
};

const 安全点 = (page, id) => page.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  for (let a = 1; a < 10; a++) for (let b = 1; b < 10; b++) {
    const x = Math.round(r.left + r.width * a / 10), y = Math.round(r.top + r.height * b / 10);
    if (x < 5 || y < 5 || x > 1435 || y > 805) continue;
    const e = document.elementFromPoint(x, y);
    const g = e && e.closest('.react-flow__node');
    if (g && g.getAttribute('data-id') === i) return [x, y];
  }
  return null;
}, id);

const 数滑杆 = (page, 场景) => page.evaluate((名) => {
  const 出 = [];
  for (const e of document.querySelectorAll('[role="slider"], input[type="number"]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    if (r.bottom < 0 || r.top > innerHeight) continue;
    let 标签 = null, n = e.parentElement;
    for (let i = 0; i < 6 && n; i++) { const t = (n.innerText || '').replace(/\s+/g, ' ').trim(); if (t && t.length <= 8 && !/^\d+(\.\d+)?$/.test(t) && t !== 's') { 标签 = t; break; } n = n.parentElement; }
    出.push({ 场景: 名, tag: e.tagName, role: e.getAttribute('role'), type: e.getAttribute('type'), 标签, ariaMin: e.getAttribute('aria-valuemin'), ariaMax: e.getAttribute('aria-valuemax'), ariaNow: e.getAttribute('aria-valuenow'), 原生value: e.value !== undefined ? String(e.value) : null, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
  }
  return 出;
}, 场景);

/** 读某个点最顶层的元素 + pointer-events 链 */
const 探点 = (page, c) => page.evaluate((p) => {
  const e = document.elementFromPoint(p[0], p[1]);
  if (!e) return null;
  const 链 = [];
  let n = e;
  for (let i = 0; i < 5 && n; i++) {
    const cs = getComputedStyle(n);
    链.push(`${n.tagName}.${String(n.className).slice(0, 26)} pe=${cs.pointerEvents} z=${cs.zIndex}`);
    n = n.parentElement;
  }
  return { 顶层: `${e.tagName}.${String(e.className).slice(0, 40)}`, 链, hover链: [...document.querySelectorAll(':hover')].slice(-4).map(x => x.tagName + '.' + String(x.className).slice(0, 24)) };
}, c);

const 读气泡 = (page) => page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip-tooltip"], [role="tooltip"]')]
  .map(e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return { 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], pe: cs.pointerEvents, op: cs.opacity }; })
  .filter(x => x.文字));

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

  // ① 视频参数面板：逐枚悬停 3 个 cursor-help，找「新功能：支持真人」的主人
  记('\n════ ① 三枚 .cursor-help 逐枚悬停，找「新功能：支持真人」的主人 ════');
  记(`　平移视频节点：${await 平移到左上(page, 'v-v2hlWY4Br3')}`);
  const 落 = await 安全点(page, 'v-v2hlWY4Br3');
  if (落) {
    await page.mouse.click(落[0], 落[1]);
    await page.waitForTimeout(2400);
    const 下拉 = await page.evaluate((i) => {
      const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      for (const b of n.querySelectorAll('button')) { const x = (b.innerText || '').replace(/\s+/g, ' ').trim(); if (!x.includes('·')) continue; const r = b.getBoundingClientRect(); if (r.bottom < 0 || r.top > innerHeight) continue; return { 文字: x, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] }; }
      return null;
    }, 'v-v2hlWY4Br3');
    if (下拉) {
      await page.mouse.click(下拉.中心[0], 下拉.中心[1]);
      await page.waitForTimeout(2200);
      const 图标们 = await page.evaluate(() => [...document.querySelectorAll('.cursor-help')].map((e, i) => {
        const r = e.getBoundingClientRect();
        const 顶层 = (() => { const x = Math.round(r.left + r.width / 2), y = Math.round(r.top + r.height / 2); const h = document.elementFromPoint(x, y); return h ? h.tagName + '.' + String(h.className).slice(0, 30) : null; })();
        return { 序: i, 所属: (e.parentElement ? (e.parentElement.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18) : null), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], 自身pe: getComputedStyle(e).pointerEvents, 父pe: e.parentElement ? getComputedStyle(e.parentElement).pointerEvents : null, 该点顶层: 顶层 };
      }));
      记(`　全页 ${图标们.length} 枚 .cursor-help：${JSON.stringify(图标们)}`);
      全.图标们 = 图标们;
      const 轨迹 = [];
      for (const q of 图标们) {
        await page.mouse.move(1380, 780);          // 先走到空白处「清场」
        await page.waitForTimeout(1200);
        const 清场气泡 = await 读气泡(page);
        await page.mouse.move(q.中心[0], q.中心[1]);
        await page.waitForTimeout(1500);
        const 探 = await 探点(page, q.中心);
        const 气泡 = await 读气泡(page);
        await page.screenshot({ path: EVID + `et4-悬停-${q.序}-${q.所属 || '无'}.png` });
        记(`　▸ #${q.序} 属于「${q.所属}」中心 ${JSON.stringify(q.中心)}`);
        记(`　　　移动前清场气泡：${JSON.stringify(清场气泡.map(x => x.文字))}`);
        记(`　　　该点顶层：${JSON.stringify(探 && 探.顶层)}｜:hover 尾 ${JSON.stringify(探 && 探.hover链)}`);
        记(`　　　⭐ 悬停后气泡：${JSON.stringify(气泡.map(x => ({ 文字: x.文字, box: x.box, pe: x.pe })))}`);
        轨迹.push({ 序: q.序, 所属: q.所属, 中心: q.中心, 自身pe: q.自身pe, 父pe: q.父pe, 该点顶层: q.该点顶层, 探, 清场气泡: 清场气泡.map(x => x.文字), 气泡 });
      }
      全.轨迹 = 轨迹;
      const 主人 = 轨迹.find(t => t.气泡.some(b => /新功能/.test(b.文字)));
      记(`\n　⭐⭐ 「新功能：支持真人」的主人 = ${主人 ? `#${主人.序} 属于「${主人.所属}」` : '三枚都没出这个气泡 ⛔'}`);
      // 阳性对照：滑块手柄（EQ 验过会出「视频时长 5 s」）
      const 手柄 = await page.evaluate(() => { const s = document.querySelector('[role="slider"]'); if (!s) return null; const r = s.getBoundingClientRect(); return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)]; });
      if (手柄) {
        await page.mouse.move(1380, 780); await page.waitForTimeout(1000);
        await page.mouse.move(手柄[0], 手柄[1]); await page.waitForTimeout(1500);
        const 气泡 = await 读气泡(page);
        记(`　▸ 阳性对照 滑块手柄 ${JSON.stringify(手柄)} → 气泡 ${JSON.stringify(气泡.map(x => x.文字))}`);
        await page.screenshot({ path: EVID + 'et4-阳性对照-滑块手柄.png' });
        全.手柄气泡 = 气泡;
      }
      await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
    }
  }

  // ② 音频 ⚙ 受控 A/B/C
  记('\n════ ② 音频节点 ⚙ 受控 A/B/C（点一次记一次，再点一次记一次）════');
  记(`　平移音频节点：${await 平移到左上(page, 'a-THmbuJXQj4')}`);
  const 落2 = await 安全点(page, 'a-THmbuJXQj4');
  if (落2) {
    await page.mouse.click(落2[0], 落2[1]);
    await page.waitForTimeout(2400);
    const 选 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
    记(`　选中 ${JSON.stringify(选)}`);
    if (选.length === 1 && 选[0] === 'a-THmbuJXQj4') {
      const 齿轮 = await page.evaluate((id) => {
        const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
        for (const b of n.querySelectorAll('button')) {
          if (!/text-canvas-controls-text/.test(String(b.className))) continue;
          const r = b.getBoundingClientRect();
          if (r.bottom < 0 || r.top > innerHeight) continue;
          return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
        }
        return null;
      }, 'a-THmbuJXQj4');
      记(`　⚙ 中心 ${JSON.stringify(齿轮)}`);
      const 段 = [];
      const 记一次 = async (名) => { const s = await 数滑杆(page, 名); 段.push({ 状态: 名, 滑杆: s }); 记(`　　【${名}】滑杆 ${s.length} 根 ${JSON.stringify(s.map(x => ({ 标签: x.标签, aria: [x.ariaMin, x.ariaMax, x.ariaNow], value: x.原生value })))}`); };
      if (齿轮) {
        await 记一次('A_刚选中还没碰⚙');
        await page.mouse.click(齿轮[0], 齿轮[1]); await page.waitForTimeout(2000);
        await 记一次('B_点了一次⚙');
        await page.screenshot({ path: EVID + 'et4-音频-B.png' });
        await page.mouse.click(齿轮[0], 齿轮[1]); await page.waitForTimeout(2000);
        await 记一次('C_又点了一次⚙');
        await page.screenshot({ path: EVID + 'et4-音频-C.png' });
        await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
        await 记一次('D_按了Esc');
      }
      全.齿轮AB = 段;
    }
  }

  结果.读数.全 = 全;
  记('\n✅ 完成（未拖滑块、未改数值）');
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
  console.log('\n=== 已写 tools/batchET4.json ===');
}
