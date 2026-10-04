// Batch ET-3：把 ET-2 暴露的三处不确定一次问清。
//
//   ET-2 的收获（成立，不重测）：
//     · 视频时长  aria=[4 ~ 15] now=5，input 原生 [4~15] value=5  ⇒ 两路互证
//     · 智能剪辑  aria=[0 ~ 300] now=30（与手册一致）
//     · 提示条「新功能：支持真人」box=[176,297,114,27]，
//       **提示条在面板内 = false，面板在提示条内 = false** ⇒ 两者是**兄弟**，
//       共同祖先是一个无 class 的 DIV，innerText 同时含两者全文
//     · ⓘ 图标 = <DIV class="cursor-help"> 12×12，**里面是 svg path，没有任何文字**
//       ⇒ ET-1 用 innerText 找「ⓘ」读到 0 枚，**是判据错了，不是没有**
//
//   ⛔ ET-2 暴露的三处不确定（这轮专门查）：
//     ① 我点错了按钮（点到「翻译提示词」，弹了 toast「提示词为空」），
//        高级设置**根本没打开**，可三根滑杆还是读出来了 ——
//        ⭐ 说明它们**在 DOM 里但不可见**。ET-2 的扫描器只判尺寸和视口范围、
//        **没判可见性** ⇒ 读到的 aria-valuenow 可能是隐藏态的旧值。
//        而 M-143 实拍图上音量数值框写的是 `1.0`，ET-2 读出 `6.2`，**对不上**。
//     ② ⓘ 有 `cursor-help` 却悬停不出气泡（EQ 逐个试过 14 枚）——
//        这轮**精确压在图标中心**（12×12 的正中），并用 `:hover` 命中链自证指针真压上去了。
//     ③ 「新功能：支持真人」与 asset-library.md 早先的「全页搜『新功能』0 命中」矛盾。
//        这轮在同一会话里做**开/关 3 轮**，数它到底在不在。
//
// ⛔ 只读：不开浮层、不点开关、不拖滑块。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchET3.json';
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

/**
 * ⭐⭐ 滑杆扫描器 v2：**判可见性**。
 *   判据（缺一不可）：
 *     ① 自身与**每一层祖先**的 `visibility` 都是 `visible`、`opacity` 都 > 0
 *     ② `elementFromPoint(中心)` 命中链里**包含这个元素**（真能点到）
 *   ET-2 漏了这条 ⇒ 把隐藏面板里的旧值当成了当前值。
 */
const 扫滑杆v2 = (page, 场景) => page.evaluate((名) => {
  const 可见链 = (e) => {
    let n = e, 层 = 0;
    while (n && 层 < 40) {
      const cs = getComputedStyle(n);
      if (cs.visibility === 'hidden' || cs.visibility === 'collapse') return { 可见: false, 原因: `第${层}层 visibility=${cs.visibility}`, 挡: n.tagName + '.' + String(n.className).slice(0, 30) };
      if (parseFloat(cs.opacity) === 0) return { 可见: false, 原因: `第${层}层 opacity=0`, 挡: n.tagName + '.' + String(n.className).slice(0, 30) };
      n = n.parentElement; 层++;
    }
    return { 可见: true, 原因: null, 挡: null };
  };
  const 出 = [];
  const seen = new Set();
  for (const e of document.querySelectorAll('[role="slider"], input[type="number"]')) {
    if (seen.has(e)) continue; seen.add(e);
    const r = e.getBoundingClientRect();
    const 尺寸 = { 宽: Math.round(r.width), 高: Math.round(r.height) };
    const 在视口 = r.bottom >= 0 && r.top <= innerHeight && r.right >= 0 && r.left <= innerWidth;
    const 链 = 可见链(e);
    let 命中 = false;
    if (在视口 && r.width >= 2 && r.height >= 2) {
      const x = Math.round(r.left + r.width / 2), y = Math.round(r.top + r.height / 2);
      const hit = document.elementFromPoint(x, y);
      命中 = !!(hit && (hit === e || e.contains(hit) || hit.contains(e)));
    }
    const 标签 = (() => {
      let n = e.parentElement;
      for (let i = 0; i < 6 && n; i++) {
        const t = (n.innerText || '').replace(/\s+/g, ' ').trim();
        if (t && t.length <= 8 && !/^\d+(\.\d+)?$/.test(t) && t !== 's') return t;
        n = n.parentElement;
      }
      return null;
    })();
    出.push({
      场景: 名, tag: e.tagName, role: e.getAttribute('role'), type: e.getAttribute('type'),
      cls: String(e.className || '').slice(0, 52), 标签,
      ariaMin: e.getAttribute('aria-valuemin'), ariaMax: e.getAttribute('aria-valuemax'), ariaNow: e.getAttribute('aria-valuenow'),
      原生min: e.getAttribute('min'), 原生max: e.getAttribute('max'),
      原生value: e.value !== undefined ? String(e.value) : null,
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      尺寸, 在视口, 样式可见: 链.可见, 不可见原因: 链.原因, 遮挡层: 链.挡, 指针能点到: 命中,
      可信: 链.可见 && 命中,
    });
  }
  return 出;
}, 场景);

/** 数一数「新功能」提示条在不在（先全页搜文字，再看有没有那个 114×27 的元素） */
const 数提示条 = (page) => page.evaluate(() => {
  const 全页文字 = (document.body.innerText || '').includes('新功能');
  const 元素 = [...document.querySelectorAll('body *')].filter(e => /^新功能[：:]/.test((e.innerText || '').replace(/\s+/g, ' ').trim()));
  const 最内 = 元素.filter(e => ![...e.children].some(c => /^新功能[：:]/.test((c.innerText || '').replace(/\s+/g, ' ').trim())));
  return {
    全页innerText含新功能: 全页文字,
    命中元素数: 元素.length,
    最内元素: 最内.slice(0, 3).map(e => { const r = e.getBoundingClientRect(); return { 文字: (e.innerText || '').trim(), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], cls: String(e.className).slice(0, 40) }; }),
  };
});

/** 精确悬停 ⓘ：先 elementFromPoint 自证，再读 Mantine 气泡 */
const 测悬停 = async (page, 中心, 名) => {
  await page.mouse.move(中心[0] - 60, 中心[1] - 60);
  await page.waitForTimeout(500);
  await page.mouse.move(中心[0], 中心[1]);
  await page.waitForTimeout(1400);
  const 自证 = await page.evaluate((c) => {
    const e = document.elementFromPoint(c[0], c[1]);
    if (!e) return { 命中: null, 链: [] };
    const 链 = [];
    let n = e;
    for (let i = 0; i < 6 && n; i++) { 链.push(n.tagName + '.' + String(n.className).slice(0, 34)); n = n.parentElement; }
    return { 命中: e.tagName + '.' + String(e.className).slice(0, 40), 链, hover链: [...document.querySelectorAll(':hover')].slice(-6).map(x => x.tagName + '.' + String(x.className).slice(0, 30)) };
  }, 中心);
  await page.screenshot({ path: EVID + `et3-悬停-${名}.png` });
  const 气泡 = await page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip"], [role="tooltip"]')].map(e => { const r = e.getBoundingClientRect(); return { cls: String(e.className).slice(0, 50), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }; }).filter(x => x.文字));
  记(`　　${名}：指针落在 ${JSON.stringify(自证.命中)}｜:hover 链尾 ${JSON.stringify(自证.hover链)}`);
  记(`　　　气泡读数：${JSON.stringify(气泡)}`);
  return { 自证, 气泡 };
};

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

  // ① 基线：什么都没打开时，提示条在不在？滑杆在不在？
  记('\n════ ① 基线（无选中、无面板）════');
  全.提示条 = { 基线: await 数提示条(page) };
  记(`　「新功能」全页 innerText 命中 = ${全.提示条.基线.全页innerText含新功能}，最内元素 ${JSON.stringify(全.提示条.基线.最内元素)}`);
  const 基线滑杆 = await 扫滑杆v2(page, '基线');
  记(`　滑杆/数值框 ${基线滑杆.length} 个（其中可信 ${基线滑杆.filter(x => x.可信).length} 个）`);
  for (const s of 基线滑杆) 记(`　　<${s.tag}> 标签=${JSON.stringify(s.标签)} 样式可见=${s.样式可见} 可信=${s.可信} 原因=${s.不可见原因} 挡=${s.遮挡层} box=${JSON.stringify(s.box)}`);
  全.基线滑杆 = 基线滑杆;

  // ② 音频节点：先用 v2 扫（未打开），再点真正的 ⚙ 打开，扫 v2，再扫 v1 做对照
  记('\n════ ② 音频节点高级设置：打开前后各扫一次（v2 判可见性）════');
  记(`　平移音频节点：${await 平移到左上(page, 'a-THmbuJXQj4')}`);
  const 落 = await 安全点(page, 'a-THmbuJXQj4');
  记(`　安全落点 ${JSON.stringify(落)}`);
  if (落) {
    await page.mouse.click(落[0], 落[1]);
    await page.waitForTimeout(2400);
    const 选 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
    记(`　选中 ${JSON.stringify(选)}`);
    if (选.length === 1 && 选[0] === 'a-THmbuJXQj4') {
      const 未开 = await 扫滑杆v2(page, '音频-未打开');
      记(`　★ **还没点 ⚙**：滑杆 ${未开.length} 个，其中**可信** ${未开.filter(x => x.可信).length} 个`);
      for (const s of 未开) 记(`　　<${s.tag} ${s.role || s.type}> 标签=${JSON.stringify(s.标签)} 可信=${s.可信} 样式可见=${s.样式可见} 挡=${s.遮挡层} aria=[${s.ariaMin}~${s.ariaMax}] now=${s.ariaNow} value=${s.原生value}`);

      const 按钮们 = await page.evaluate((id) => {
        const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
        return [...n.querySelectorAll('button')].map(b => { const r = b.getBoundingClientRect(); return { 文字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], cls: String(b.className).slice(0, 56), 可见: r.bottom > 0 && r.top < innerHeight && r.width > 0 }; });
      }, 'a-THmbuJXQj4');
      记(`　参数条上无文字且可见的按钮：${JSON.stringify(按钮们.filter(b => !b.文字 && b.可见))}`);
      // ⭐ 按 class 精确定位 ⚙：上一轮点到「翻译提示词」是因为「取第一个无文字按钮」
      const 齿轮 = 按钮们.find(b => !b.文字 && b.可见 && /text-canvas-controls-text/.test(b.cls));
      记(`　⭐ 认定的 ⚙ = ${JSON.stringify(齿轮)}`);
      if (齿轮) {
        const 中心 = [齿轮.box[0] + Math.round(齿轮.box[2] / 2), 齿轮.box[1] + Math.round(齿轮.box[3] / 2)];
        const 验 = await page.evaluate((c) => { const e = document.elementFromPoint(c[0], c[1]); const g = e && e.closest('button'); return g ? { cls: String(g.className).slice(0, 56), 文字: (g.innerText || '').trim() } : null; }, 中心);
        记(`　　点前 elementFromPoint 自证：${JSON.stringify(验)}`);
        await page.mouse.click(中心[0], 中心[1]);
        await page.waitForTimeout(2000);
        await page.screenshot({ path: EVID + 'et3-音频-高级设置-真开.png' });
        const 后面板 = await page.evaluate(() => {
          const 命中 = [...document.querySelectorAll('body *')].filter(e => (e.innerText || '').includes('高级设置'));
          return 命中.slice(0, 4).map(e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return { tag: e.tagName, cls: String(e.className).slice(0, 44), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 70), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], pos: cs.position, z: cs.zIndex, op: cs.opacity, vis: cs.visibility }; });
        });
        记(`　⭐ 面板里含「高级设置」的元素 ${后面板.length} 个：`);
        for (const p of 后面板) 记(`　　<${p.tag}> box=${JSON.stringify(p.box)} pos=${p.pos} z=${p.z} op=${p.op} vis=${p.vis} cls=${p.cls} 文字=${JSON.stringify(p.文字)}`);
        全.高级设置元素 = 后面板;
        const 已开 = await 扫滑杆v2(page, '音频-已打开');
        记(`　★ **点开之后**：滑杆 ${已开.length} 个，其中**可信** ${已开.filter(x => x.可信).length} 个`);
        for (const s of 已开) 记(`　　<${s.tag} ${s.role || s.type}> 标签=${JSON.stringify(s.标签)} 可信=${s.可信} 指针能点到=${s.指针能点到} aria=[${s.ariaMin}~${s.ariaMax}] now=${s.ariaNow}｜input 原生[${s.原生min}~${s.原生max}] value=${s.原生value}`);
        全.音频已开 = 已开;
        全.提示条.已打开 = await 数提示条(page);
        记(`　　「新功能」此刻：innerText 命中=${全.提示条.已打开.全页innerText含新功能} 最内=${JSON.stringify(全.提示条.已打开.最内元素)}`);
        await page.keyboard.press('Escape'); await page.waitForTimeout(1300);
        const 已关 = await 扫滑杆v2(page, '音频-再关掉');
        记(`　★ **再按 Esc 关掉**：滑杆 ${已关.length} 个，其中**可信** ${已关.filter(x => x.可信).length} 个`);
        for (const s of 已开) { const y = 已关.find(z => z.box.join() === s.box.join() && z.tag === s.tag); if (y) 记(`　　对照 ${s.tag} 标签=${JSON.stringify(s.标签)} 打开时 now=${s.ariaNow}/value=${s.原生value} → 关掉后 now=${y.ariaNow}/value=${y.原生value} 可信=${y.可信}`); }
        全.音频已关 = 已关;
        全.提示条.已关掉 = await 数提示条(page);
        记(`　　「新功能」此刻：innerText 命中=${全.提示条.已关掉.全页innerText含新功能} 最内=${JSON.stringify(全.提示条.已关掉.最内元素)}`);
      }
    }
  }

  // ③ 视频参数面板：ⓘ 精确悬停（阳性对照：滑块手柄 EQ 验过会出气泡）
  记('\n════ ③ 视频参数面板：ⓘ 精确悬停 + 滑块手柄做阳性对照 ════');
  记(`　平移视频节点：${await 平移到左上(page, 'v-v2hlWY4Br3')}`);
  const 落2 = await 安全点(page, 'v-v2hlWY4Br3');
  if (落2) {
    await page.mouse.click(落2[0], 落2[1]);
    await page.waitForTimeout(2400);
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
      await page.screenshot({ path: EVID + 'et3-视频-面板.png' });
      const 问号 = await page.evaluate(() => [...document.querySelectorAll('.cursor-help')].map(e => { const r = e.getBoundingClientRect(); return { box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], cls: String(e.className).slice(0, 50), 父cls: String(e.parentElement && e.parentElement.className).slice(0, 44), 父文字: (e.parentElement ? (e.parentElement.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) : null), 父title: e.parentElement && e.parentElement.getAttribute('title'), 自身title: e.getAttribute('title'), 文本: (e.innerText || '').trim() }; }));
      记(`　　全页 .cursor-help 元素 ${问号.length} 个：${JSON.stringify(问号)}`);
      全.问号 = 问号;
      if (问号.length) {
        const b = 问号[0].box;
        全.悬停问号 = await 测悬停(page, [b[0] + Math.round(b[2] / 2), b[1] + Math.round(b[3] / 2)], '问号图标');
      }
      const 手柄 = await page.evaluate(() => {
        const s = document.querySelector('[role="slider"]');
        if (!s) return null;
        const r = s.getBoundingClientRect();
        return { box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], cls: String(s.className).slice(0, 50) };
      });
      记(`　　滑块手柄（阳性对照）= ${JSON.stringify(手柄)}`);
      if (手柄) 全.悬停手柄 = await 测悬停(page, [手柄.box[0] + Math.round(手柄.box[2] / 2), 手柄.box[1] + Math.round(手柄.box[3] / 2)], '视频时长手柄');
      全.提示条.视频面板 = await 数提示条(page);
      记(`　　「新功能」此刻：innerText 命中=${全.提示条.视频面板.全页innerText含新功能} 最内=${JSON.stringify(全.提示条.视频面板.最内元素)}`);
      await page.keyboard.press('Escape'); await page.waitForTimeout(1300);
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
  console.log('\n=== 已写 tools/batchET3.json ===');
}
