// Batch ET-2：修 ET-1 的两处缺口，并结清「新功能」提示条的归属。
//
//   ET-1 的收获（已成立，不必重测）：
//     · 视频时长  aria-valuemin=4  aria-valuemax=15  aria-valuenow=5
//     · 智能剪辑  aria-valuemin=0  aria-valuemax=300 aria-valuenow=30
//     · 两处都另有一枚 <input type=number>，原生 min/max/value 与 aria 完全一致 ⇒ 两路互证
//     · 基线「视口里 0 根滑杆」这个阴性结论，**同一支扫描器在 ②③ 里读出 4 条** ⇒ 扫描器本身是好的
//
//   本轮补两件事：
//     ① ⓘ 问号图标 ET-1 读出 **0 枚**。⛔ 判据是「innerText 等于 ⓘ/?/i 的无子元素」。
//        但 EQ 已验过它**不是文字节点**（按语义查必然 0 命中）⇒ 又一次「0 个要怀疑判据」。
//        这次改成**从「生成音频」那个组标题出发，列出它周围所有兄弟与后代**，
//        顺带把 svg 的 `<path d>` 记下来（供手册用 class/path 定位，别用坐标）。
//     ② 归属结清：**不靠悬停、不靠同框出现**，纯问 DOM 关系——
//        提示条是不是参数面板的后代？ⓘ 是不是提示条的后代？两者的共同祖先是谁？
//        ET-1 已经露出线索：提示条的**父元素 innerText 同时含「新功能：支持真人」和「比例 Auto 16:9…」**
//        ⇒ 父元素里既住了提示条、又住了整块面板 ⇒ **它们是兄弟，不是父子**。这轮坐实。
//     ③ 音频节点 ⚙ 高级设置：ET-1 里节点不在 DOM（没先 ⌘0）导致整段被跳过，这轮补上。
//
// ⛔ 只读：不开浮层、不点开关、不拖滑块。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchET2.json';
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

/** ⭐ 找出参数面板根元素（沿用 ES-2 的判据：z-index≥200 的 absolute/fixed 容器，取最高的那个） */
const 找面板根 = (page) => page.evaluate(() => {
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
    if (!最佳 || +cs.zIndex > +最佳.z) 最佳 = { e, z: +cs.zIndex, 全文: t, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }
  if (最佳) delete 最佳.e;
  return 最佳;
});

/** ⭐⭐ 纯 DOM 关系结清归属：提示条 / ⓘ / 面板 三者的包含关系 */
const 查归属 = (page) => page.evaluate(() => {
  const 面板候选 = [];
  for (const e of document.querySelectorAll('body *')) {
    if (e.closest('.react-flow__node') || e.closest('.react-flow__nodes') || e.closest('.react-flow__pane')) continue;
    const cs = getComputedStyle(e);
    if (cs.position !== 'absolute' && cs.position !== 'fixed') continue;
    if (+cs.zIndex < 200) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 140 || r.height < 100) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (t.length < 3) continue;
    面板候选.push({ e, z: +cs.zIndex, 全文: t, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
  }
  面板候选.sort((a, b) => b.z - a.z || b.box[3] - a.box[3]);
  const 面板 = 面板候选.find(p => /比例|清晰度|语种|画质/.test(p.全文) && !/新功能/.test(p.全文)) || 面板候选[0];

  // 提示条：只含「新功能」两字、不含面板正文的最内层元素
  let 提示条 = null;
  for (const e of document.querySelectorAll('body *')) {
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!/^新功能[：:]/.test(t)) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 60 || r.width > 400 || r.height > 60) continue;
    if (!提示条 || r.width < 提示条.r.width) 提示条 = { e, r, 文字: t };
  }
  // ⓘ：从「生成音频」组标题出发找它右边的图标（**不靠文字，找 svg/小尺寸元素**）
  let 标题 = null;
  for (const e of document.querySelectorAll('body *')) {
    if (e.children.length) continue;
    if ((e.innerText || '').trim() !== '生成音频') continue;
    标题 = e; break;
  }
  const 标题信息 = 标题 ? { 文字: '生成音频', box: (() => { const r = 标题.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })(), 父cls: String(标题.parentElement && 标题.parentElement.className).slice(0, 60) } : null;
  const 图标 = [];
  if (标题) {
    const 组 = 标题.parentElement;               // 「生成音频」所在那一行
    for (const e of [组, ...组.querySelectorAll('*')]) {
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.width > 26 || r.height < 4 || r.height > 26) continue;
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      const path = e.querySelector('path');
      图标.push({
        tag: e.tagName, 文字: t, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        cls: String(e.className).slice(0, 60), 有svg: !!e.querySelector('svg'),
        pathd: path ? path.getAttribute('d').slice(0, 70) : null,
        title: e.getAttribute('title'), aria: e.getAttribute('aria-label'),
      });
    }
  }
  const 包含 = (a, b) => !!(a && b && a.contains(b));
  const 共同祖先 = (a, b) => {
    if (!a || !b) return null;
    const 集 = new Set(); let x = a; while (x) { 集.add(x); x = x.parentElement; }
    let y = b, 命中 = null; while (y) { if (集.has(y)) { 命中 = y; break; } y = y.parentElement; }
    return 命中 ? { tag: 命中.tagName, cls: String(命中.className).slice(0, 50), 文字: (命中.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50) } : null;
  };
  const 提示条信息 = 提示条 ? { 文字: 提示条.文字, box: [Math.round(提示条.r.left), Math.round(提示条.r.top), Math.round(提示条.r.width), Math.round(提示条.r.height)], 父cls: String(提示条.e.parentElement && 提示条.e.parentElement.className).slice(0, 50), 父文字: (提示条.e.parentElement ? (提示条.e.parentElement.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) : null) } : null;
  return {
    面板: 面板 && { box: 面板.box, 全文: 面板.全文.slice(0, 90), cls: String(面板.e.className).slice(0, 50) },
    提示条: 提示条信息,
    生成音频标题: 标题信息,
    该行里的小元素: 图标,
    关系: {
      提示条在面板内: 包含(面板 && 面板.e, 提示条 && 提示条.e),
      面板在提示条内: 包含(提示条 && 提示条.e, 面板 && 面板.e),
      提示条与面板的共同祖先: 共同祖先(提示条 && 提示条.e, 面板 && 面板.e),
      提示条与生成音频标题的共同祖先: 共同祖先(提示条 && 提示条.e, 标题),
    },
  };
});

/** 扫滑杆，这次把**每一层**短文字祖先都收下来，标签离线挑 */
const 扫滑杆 = (page, 场景) => page.evaluate((名) => {
  const 出 = [];
  const seen = new Set();
  for (const e of document.querySelectorAll('[role="slider"], input[type="number"], [class*="Slider-thumb"]')) {
    if (seen.has(e)) continue; seen.add(e);
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    if (r.bottom < 0 || r.top > innerHeight) continue;
    const 链 = [];
    let n = e.parentElement, 层 = 0;
    while (n && 层 < 6) {
      const t = (n.innerText || '').replace(/\s+/g, ' ').trim();
      const cs = getComputedStyle(n);
      if (t && t.length <= 12) 链.push({ 文字: t, 粗: cs.fontWeight, 号: cs.fontSize });
      n = n.parentElement; 层++;
    }
    出.push({
      场景: 名, tag: e.tagName, role: e.getAttribute('role'), type: e.getAttribute('type'),
      cls: String(e.className || '').slice(0, 60),
      ariaMin: e.getAttribute('aria-valuemin'), ariaMax: e.getAttribute('aria-valuemax'), ariaNow: e.getAttribute('aria-valuenow'),
      原生min: e.getAttribute('min'), 原生max: e.getAttribute('max'),
      原生value: e.value !== undefined ? String(e.value) : null,
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      短文祖先链: 链,
    });
  }
  return 出;
}, 场景);

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

  // ① 视频参数面板：ⓘ 与提示条的归属
  记('\n════ ① 视频参数面板：ⓘ 与「新功能」提示条归属（纯 DOM 关系）════');
  记(`　平移视频节点：${await 平移到左上(page, 'v-v2hlWY4Br3')}`);
  let 落 = await 安全点(page, 'v-v2hlWY4Br3');
  if (落) {
    await page.mouse.click(落[0], 落[1]);
    await page.waitForTimeout(2500);
    const 选 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
    记(`　选中 ${JSON.stringify(选)}`);
    const 下拉 = await page.evaluate((i) => {
      const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      for (const b of n.querySelectorAll('button')) {
        const x = (b.innerText || '').replace(/\s+/g, ' ').trim();
        if (!x.includes('·')) continue;
        const r = b.getBoundingClientRect();
        if (r.bottom < 0 || r.top > innerHeight) continue;
        return { 文字: x, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
      }
      return null;
    }, 'v-v2hlWY4Br3');
    if (下拉) {
      await page.mouse.click(下拉.中心[0], 下拉.中心[1]);
      await page.waitForTimeout(2200);
      await page.screenshot({ path: EVID + 'et2-视频-面板带新功能条.png' });
      const 归 = await 查归属(page);
      全.归属 = 归;
      记(`　面板 ${JSON.stringify(归.面板 && 归.面板.box)}｜${JSON.stringify(归.面板 && 归.面板.全文)}`);
      记(`　提示条 ${JSON.stringify(归.提示条)}`);
      记(`　⭐⭐ **归属判定**：提示条在面板内=${归.关系.提示条在面板内}｜面板在提示条内=${归.关系.面板在提示条内}`);
      记(`　　两者的共同祖先 = ${JSON.stringify(归.关系.提示条与面板的共同祖先)}`);
      记(`　　提示条与「生成音频」标题的共同祖先 = ${JSON.stringify(归.关系.提示条与生成音频标题的共同祖先)}`);
      记(`　「生成音频」标题本身 ${JSON.stringify(归.生成音频标题)}`);
      记(`　⭐ 该行里 4~26px 的小元素 ${归.该行里的小元素.length} 个：`);
      for (const q of 归.该行里的小元素) 记(`　　<${q.tag}> 文字=${JSON.stringify(q.文字)} box=${JSON.stringify(q.box)} 有svg=${q.有svg} title=${JSON.stringify(q.title)} aria=${JSON.stringify(q.aria)} cls=${q.cls.slice(0, 40)} path=${q.pathd}`);
      全.滑杆视频 = await 扫滑杆(page, '视频参数面板');
      for (const x of 全.滑杆视频) 记(`　　滑杆 <${x.tag} role=${x.role}> aria=[${x.ariaMin} ~ ${x.ariaMax}] now=${x.ariaNow}｜input 原生[${x.原生min}~${x.原生max}] value=${x.原生value}｜短文祖先链=${JSON.stringify(x.短文祖先链)}`);
      await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
      await page.keyboard.press('Escape'); await page.waitForTimeout(800);
    }
  }

  // ② 音频节点 ⚙ 高级设置（ET-1 因节点不在 DOM 整段跳过，这轮先 ⌘0 再平移）
  记('\n════ ② 音频节点 ⚙ 高级设置（a-THmbuJXQj4）════');
  记(`　平移音频节点：${await 平移到左上(page, 'a-THmbuJXQj4')}`);
  落 = await 安全点(page, 'a-THmbuJXQj4');
  记(`　安全落点 ${JSON.stringify(落)}`);
  if (落) {
    await page.mouse.click(落[0], 落[1]);
    await page.waitForTimeout(2400);
    const 选 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
    记(`　选中 ${JSON.stringify(选)}`);
    if (选.length === 1 && 选[0] === 'a-THmbuJXQj4') {
      const 按钮们 = await page.evaluate((id) => {
        const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
        return [...n.querySelectorAll('button')].map(b => { const r = b.getBoundingClientRect(); return { 文字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], aria: b.getAttribute('aria-label'), title: b.getAttribute('title'), cls: String(b.className).slice(0, 44), 可见: r.bottom > 0 && r.top < innerHeight }; });
      }, 'a-THmbuJXQj4');
      记(`　参数条上共 ${按钮们.length} 枚按钮：`);
      for (const b of 按钮们) 记(`　　「${b.文字}」 box=${JSON.stringify(b.box)} 可见=${b.可见} aria=${JSON.stringify(b.aria)} title=${JSON.stringify(b.title)} cls=${b.cls}`);
      const 齿轮 = 按钮们.find(b => !b.文字 && b.可见);
      if (齿轮) {
        await page.mouse.click(齿轮.box[0] + 齿轮.box[2] / 2, 齿轮.box[1] + 齿轮.box[3] / 2);
        await page.waitForTimeout(1900);
        await page.screenshot({ path: EVID + 'et2-音频-高级设置.png' });
        const 面板 = await 找面板根(page);
        记(`　高级设置面板 ${JSON.stringify(面板 && 面板.box)}：${JSON.stringify(面板 && 面板.全文)}`);
        全.音频面板全文 = 面板 && 面板.全文;
        全.滑杆音频 = await 扫滑杆(page, '音频高级设置');
        for (const x of 全.滑杆音频) 记(`　　滑杆 <${x.tag} role=${x.role}> aria=[${x.ariaMin} ~ ${x.ariaMax}] now=${x.ariaNow}｜input 原生[${x.原生min}~${x.原生max}] value=${x.原生value}｜短文祖先链=${JSON.stringify(x.短文祖先链)}`);
        await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
      } else 记('　⛔ 没找到无文字按钮');
    }
  }

  结果.读数.全 = 全;
  记('\n✅ 完成（未拖滑块、未点开关）');
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
  console.log('\n=== 已写 tools/batchET2.json ===');
}
