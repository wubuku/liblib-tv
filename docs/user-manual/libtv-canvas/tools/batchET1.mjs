// Batch ET-1：把画布上**所有**滑杆 / 数值框型参数一次读干净。
//
//   ES 的结论：「选中项 = 白边 + 浅底」**只管 <button>**。
//   ⭐ 智能剪辑那块 9 枚按钮只有 2 枚白描边，差的第三段「时长 30」是**滑杆**。
//   ⇒ 面板里有一整类参数**根本不走按钮**，必须另读 —— 而「视频时长」的取值范围一直挂着 📖。
//
//   本批三件事：
//     ① 全视口枚举 `role="slider"` / `input[type=number]` / Mantine Slider/NumberInput，
//        逐个读 `aria-valuemin/max/now`、原生 `min/max/value`、`type`，
//        ⭐ 并**上溯找它属于哪一组**（拿组标题文字）—— 这样才能写成用户看得懂的表。
//     ② 覆盖四个已知的滑杆位置：视频节点参数面板「视频时长」、
//        智能剪辑参数面板「时长」、智能剪辑**大编辑器**里的「时长」、音频 ⚙ 高级设置三根。
//        ⭐ 前两个当**对照组**：视频时长有 EQ 验过的阳性对照（悬停气泡「视频时长 5 s」）。
//     ③ 顺手结清 §121/EQ 留下的「ⓘ 问号图标到底属于谁」—— 这次**不靠悬停**，
//        直接读 DOM 父子与祖先链，看「新功能:」提示条和 ⓘ 在不在同一棵子树里。
//
// ⛔ 只读不拖：不碰任何滑块手柄、不改任何数值。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchET1.json';
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
 * ⭐ 全视口枚举「滑杆 / 数值框」这一类控件，并上溯找出它属于哪一组。
 *   上溯规则：从元素本身往上找**第一个含 ≤ 6 个字文字的祖先**（那就是组标题），
 *   最多上溯 8 层。这是给**读数**配一个「人话标签」，不是用来筛控件的。
 */
const 扫滑杆 = (page, 标签) => page.evaluate((名) => {
  const 候选 = new Set();
  for (const e of document.querySelectorAll('[role="slider"], input[type="number"], input[type="range"], [class*="Slider-thumb"], [class*="NumberInput-input"], [class*="NumberInput-control"], [class*="slider"]')) 候选.add(e);
  const 上溯标题 = (e) => {
    let n = e, 层 = 0;
    while (n && 层 < 8) {
      n = n.parentElement; 层++;
      if (!n) break;
      if (n.closest('.react-flow__node')) break;
      const t = (n.innerText || '').replace(/\s+/g, ' ').trim();
      if (t && t.length <= 12) return { 标题: t, 层数: 层 };
    }
    return { 标题: null, 层数: -1 };
  };
  const 出 = [];
  for (const e of 候选) {
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    if (r.bottom < 0 || r.top > innerHeight) continue;      // 视口外的滑杆这轮不收
    const cls = String(e.className || '');
    出.push({
      场景: 名,
      tag: e.tagName,
      role: e.getAttribute('role'),
      type: e.getAttribute('type'),
      cls: cls.slice(0, 70),
      文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
      ariaNow: e.getAttribute('aria-valuenow'),
      ariaMin: e.getAttribute('aria-valuemin'),
      ariaMax: e.getAttribute('aria-valuemax'),
      ariaText: e.getAttribute('aria-valuetext'),
      原生min: e.getAttribute('min'), 原生max: e.getAttribute('max'),
      原生value: e.value !== undefined ? String(e.value) : null,
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      ...上溯标题(e),
    });
  }
  return 出;
}, 标签);

/** 结清「ⓘ 与新功能提示条」的归属：纯读 DOM 祖先/兄弟链，不做悬停 */
const 查问号 = (page) => page.evaluate(() => {
  const 问号 = [...document.querySelectorAll('body *')].filter(e => {
    const t = (e.innerText || '').trim();
    return (t === 'ⓘ' || t === '?' || t === 'i') && e.children.length === 0 && e.getBoundingClientRect().width > 0 && e.getBoundingClientRect().width < 30;
  });
  const 提示条 = [...document.querySelectorAll('body *')].filter(e => /新功能/.test(e.innerText || '') && e.getBoundingClientRect().width < 600 && e.getBoundingClientRect().width > 100);
  const 祖先链 = (e, n = 6) => { const a = []; let x = e; for (let i = 0; i < n && x; i++) { x = x.parentElement; if (!x) break; a.push({ tag: x.tagName, cls: String(x.className).slice(0, 50), 文字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) }); } return a; };
  const 互含 = (p, q) => { const a = p.getBoundingClientRect(), b = q.getBoundingClientRect(); return a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top; };
  return {
    问号数: 问号.length,
    问号: 问号.slice(0, 6).map(e => {
      const r = e.getBoundingClientRect();
      return { cls: String(e.className).slice(0, 60), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 祖先链: 祖先链(e), 自身title: e.getAttribute('title'), 父title: e.parentElement && e.parentElement.getAttribute('title'), 父aria: e.parentElement && e.parentElement.getAttribute('aria-label') };
    }),
    提示条数: 提示条.length,
    提示条: 提示条.slice(0, 4).map(e => {
      const r = e.getBoundingClientRect();
      return { 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 祖先链: 祖先链(e, 4) };
    }),
    问号与提示条重叠: 问号.length && 提示条.length ? 问号.filter(p => 提示条.some(q => 互含(p, q))).length : null,
  };
});

/** 打开某个节点的参数面板（第二枚带 `·` 的摘要下拉） */
const 开参数面板 = async (page, id, 名) => {
  const 落点 = await page.evaluate((i) => {
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
  if (!落点) return null;
  await page.mouse.click(落点[0], 落点[1]);
  await page.waitForTimeout(2600);
  const 选 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  if (选.length !== 1 || 选[0] !== id) { 记(`　⛔ 点中了 ${JSON.stringify(选)}`); return null; }
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
  }, id);
  if (!下拉) { 记('　⛔ 没有摘要下拉'); return null; }
  await page.mouse.click(下拉.中心[0], 下拉.中心[1]);
  await page.waitForTimeout(2100);
  await page.screenshot({ path: EVID + `et1-${名}-面板.png` });
  return 下拉;
};

const 收起 = async (page) => { await page.keyboard.press('Escape'); await page.waitForTimeout(1200); await page.keyboard.press('Escape'); await page.waitForTimeout(800); };

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

  const 全 = { 滑杆: [], 问号: null };

  // —— ① 基线：什么都没打开时，视口里本来就有几根滑杆？
  记('\n════ ① 基线（什么都没选中）════');
  const 基线 = await 扫滑杆(page, '基线');
  记(`　全视口滑杆/数值框候选 ${基线.length} 个`);
  for (const s of 基线) 记(`　　<${s.tag} role=${s.role} type=${s.type}> 「${s.文字}」 组标题=${JSON.stringify(s.标题)} aria=${s.ariaMin}~${s.ariaMax} now=${s.ariaNow}`);
  全.滑杆.push(...基线);

  // —— ② 视频节点参数面板里的「视频时长」★对照组（EQ 验过悬停气泡「视频时长 5 s」）
  记('\n════ ② 视频节点参数面板（v-v2hlWY4Br3）★对照组 ════');
  if (!(await page.evaluate((id) => !!document.querySelector(`.react-flow__node[data-id="${id}"]`), 'v-v2hlWY4Br3'))) { await page.keyboard.press('Meta+0'); await page.waitForTimeout(2500); }
  if (await 平移到左上(page, 'v-v2hlWY4Br3')) {
    const 下拉 = await 开参数面板(page, 'v-v2hlWY4Br3', '视频');
    if (下拉) {
      记(`　摘要「${下拉.文字}」`);
      const s = await 扫滑杆(page, '视频参数面板');
      for (const x of s) 记(`　　<${x.tag} role=${x.role} type=${x.type} cls=${x.cls.slice(0, 34)}> 组标题=${JSON.stringify(x.标题)} aria=[${x.ariaMin} ~ ${x.ariaMax}] now=${x.ariaNow} valuetext=${JSON.stringify(x.ariaText)} 原生[${x.原生min}~${x.原生max}] value=${x.原生value}`);
      全.滑杆.push(...s);
      全.问号 = await 查问号(page);
      记(`　⭐ 问号图标 ${全.问号.问号数} 枚 / 「新功能」提示条 ${全.问号.提示条数} 条 / 两者矩形重叠 ${全.问号.问号与提示条重叠}`);
      for (const q of 全.问号.问号) 记(`　　ⓘ box=${JSON.stringify(q.box)} 父aria=${JSON.stringify(q.父aria)} 父title=${JSON.stringify(q.父title)} 祖先1=${JSON.stringify(q.祖先链[0])}`);
      for (const t of 全.问号.提示条) 记(`　　提示条「${t.文字}」 box=${JSON.stringify(t.box)}`);
      await 收起(page);
    }
  }

  // —— ③ 智能剪辑参数面板里的「时长」
  记('\n════ ③ 智能剪辑参数面板（v-oZNpH99MtM）════');
  if (await 平移到左上(page, 'v-oZNpH99MtM')) {
    const 下拉 = await 开参数面板(page, 'v-oZNpH99MtM', '智能剪辑');
    if (下拉) {
      记(`　摘要「${下拉.文字}」`);
      const s = await 扫滑杆(page, '智能剪辑参数面板');
      for (const x of s) 记(`　　<${x.tag} role=${x.role} type=${x.type} cls=${x.cls.slice(0, 34)}> 组标题=${JSON.stringify(x.标题)} aria=[${x.ariaMin} ~ ${x.ariaMax}] now=${x.ariaNow} valuetext=${JSON.stringify(x.ariaText)} 原生[${x.原生min}~${x.原生max}] value=${x.原生value}`);
      全.滑杆.push(...s);
      await 收起(page);
    }
  }

  // —— ④ 音频节点 ⚙ 高级设置里的三根（语速/声调/音量）
  记('\n════ ④ 音频节点 ⚙ 高级设置（a-THmbuJXQj4）════');
  if (await 平移到左上(page, 'a-THmbuJXQj4')) {
    const 落点 = await page.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) return null;
      const r = n.getBoundingClientRect();
      for (let a = 1; a < 10; a++) for (let b = 1; b < 10; b++) {
        const x = Math.round(r.left + r.width * a / 10), y = Math.round(r.top + r.height * b / 10);
        if (x < 5 || y < 5 || x > 1435 || y > 805) continue;
        const e = document.elementFromPoint(x, y);
        const g = e && e.closest('.react-flow__node');
        if (g && g.getAttribute('data-id') === id) return [x, y];
      }
      return null;
    }, 'a-THmbuJXQj4');
    if (落点) {
      await page.mouse.click(落点[0], 落点[1]);
      await page.waitForTimeout(2400);
      const 选 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
      if (选.length === 1 && 选[0] === 'a-THmbuJXQj4') {
        const 齿轮 = await page.evaluate((id) => {
          const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
          for (const b of n.querySelectorAll('button')) {
            if (b.innerText.trim()) continue;
            const r = b.getBoundingClientRect();
            if (r.bottom < 0 || r.top > innerHeight) continue;
            return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2), b.getAttribute('aria-label'), b.getAttribute('title'), b.className.slice(0, 50)];
          }
          return null;
        }, 'a-THmbuJXQj4');
        记(`　找到无文字按钮：${JSON.stringify(齿轮)}`);
        if (齿轮) {
          await page.mouse.click(齿轮[0], 齿轮[1]);
          await page.waitForTimeout(1800);
          await page.screenshot({ path: EVID + 'et1-音频-高级设置.png' });
          const 后面板 = await page.evaluate(() => {
            let 最佳 = null;
            for (const e of document.querySelectorAll('body *')) {
              if (e.closest('.react-flow__node')) continue;
              const cs = getComputedStyle(e);
              if (cs.position !== 'absolute' && cs.position !== 'fixed') continue;
              if (+cs.zIndex < 200) continue;
              const r = e.getBoundingClientRect();
              if (r.width < 140 || r.height < 100) continue;
              const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
              if (t.length < 3) continue;
              最佳 = { z: cs.zIndex, 全文: t, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
            }
            return 最佳;
          });
          记(`　高级设置面板：${JSON.stringify(后面板 && 后面板.全文)}`);
          if (后面板) 全.滑杆.push(...await 扫滑杆(page, '音频高级设置'));
          for (const x of 全.滑杆.filter(z => z.场景 === '音频高级设置')) 记(`　　<${x.tag} role=${x.role} type=${x.type}> 组标题=${JSON.stringify(x.标题)} aria=[${x.ariaMin} ~ ${x.ariaMax}] now=${x.ariaNow} 原生[${x.原生min}~${x.原生max}] value=${x.原生value}`);
          await 收起(page);
        }
      } else 记(`　⛔ 点中了 ${JSON.stringify(选)}`);
    }
  }

  结果.读数.全 = 全;
  记(`\n⭐⭐ 滑杆/数值框读数合计 ${全.滑杆.length} 条，按场景：${JSON.stringify(全.滑杆.reduce((a, b) => (a[b.场景] = (a[b.场景] || 0) + 1, a), {}))}`);
  记('\n✅ 完成（未拖任何滑块、未改任何数值）');
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
  console.log('\n=== 已写 tools/batchET1.json ===');
}
