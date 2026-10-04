// Batch EL-3：真正重验那 2 枚控件。
//   EL-1 作废（点到了被压住的图片节点，实际选中的是盖在它上面的视频节点）。
//   EL-2 诊断确认：i-9nlG6HdjK2 被 v-eMpqKtiLlx 整个盖住，42/42 采样点都归视频；
//   i-sODTbgLUm1 42/42 归自己 ⇒ 改用它当被测对象。
// ⭐ 铁律②：点击前先用 elementFromPoint().closest('.react-flow__node') 复核落点归属。
// ⭐ 铁律③：收尾静置 15s 后用「核对坐标」复核。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEL3.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

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
  await page.waitForTimeout(3500);
  记(`开局坐标偏差：${JSON.stringify(await 核对坐标(page))}`);

  const 被测 = 'i-sODTbgLUm1';
  // ---- ⭐ 铁律②：先找一个 elementFromPoint 确实归属被测节点的点
  const 落点 = await page.evaluate((id) => {
    const 节点 = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!节点) return null;
    const r = 节点.getBoundingClientRect();
    for (let i = 1; i < 10; i++) for (let j = 1; j < 10; j++) {
      const x = Math.round(r.left + r.width * i / 10);
      const y = Math.round(r.top + r.height * j / 10);
      const e = document.elementFromPoint(x, y);
      const 归 = e && e.closest('.react-flow__node');
      if (归 && 归.getAttribute('data-id') === id) return [x, y];
    }
    return null;
  }, 被测);
  记(`铁律②复核：${被测} 的安全落点 = ${JSON.stringify(落点)}`);
  if (!落点) throw new Error('被测节点被完全遮住，本轮放弃');

  await page.mouse.click(落点[0], 落点[1]);
  await page.waitForTimeout(2500);
  const 选中了 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  记(`点击后选中：${JSON.stringify(选中了)} ${选中了.length === 1 && 选中了[0] === 被测 ? '✅' : '❌ 仍不是被测节点'}`);
  if (选中了.length !== 1 || 选中了[0] !== 被测) throw new Error('选中对象不对，终止');
  await page.screenshot({ path: EVID + 'el3-卡片展开.png' });

  // ---- 普查节点内所有小尺寸可点容器 + 全部属性
  const 普查 = await page.evaluate((id) => {
    const 节点 = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!节点) return [];
    const 出 = [], 集 = new Set();
    for (const e of 节点.querySelectorAll('*')) {
      if (集.has(e)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 14 || r.width > 90 || r.height < 14 || r.height > 90) continue;
      const cs = getComputedStyle(e);
      if (cs.borderRadius === '0px' && !/button/.test(e.tagName.toLowerCase())) continue;
      集.add(e);
      const attrs = {};
      for (const a of e.attributes) attrs[a.name] = a.value;
      出.push({
        tag: e.tagName,
        cls: (e.className || '').toString().slice(0, 130),
        attrs,
        文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
        cursor: cs.cursor,
        opacity: cs.opacity,
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
        svg: [...e.querySelectorAll('path')].map(p => (p.getAttribute('d') || '').slice(0, 30))[0] || '',
      });
    }
    return 出;
  }, 被测);
  记(`\n⭐ ${被测} 卡片内小尺寸可点容器 ${普查.length} 个：`);
  for (const b of 普查) {
    const attrKeys = Object.keys(b.attrs).filter(k => k !== 'class').join(',') || '（无）';
    记(`　<${b.tag}> box=${JSON.stringify(b.box)} 文字="${b.文字}" 光标=${b.cursor} 不透明度=${b.opacity}`);
    记(`　　　非 class 属性：${attrKeys}`);
    记(`　　　svg path：${b.svg || '（无 path）'}`);
  }
  结果.读数.普查 = 普查;
  结果.读数.被测 = 被测;

  // ---- 修正后的气泡判据（**不要求叶子节点**）
  const 气泡 = () => page.evaluate(() => {
    const 出 = [], 已 = new Set();
    for (const e of document.querySelectorAll('body *')) {
      const cls = (e.className || '').toString();
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      const r = e.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      if (/Tooltip|tooltip/.test(cls)) {
        const k = 'T|' + t + '|' + Math.round(r.left);
        if (已.has(k)) continue; 已.add(k);
        出.push({ 文本: t.slice(0, 60), cls: cls.slice(0, 46), Tip: true, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
        continue;
      }
      if (t && t.length <= 16 && r.height < 60 && r.width < 300) {
        const k = 'N|' + t + '|' + Math.round(r.left);
        if (已.has(k)) continue; 已.add(k);
        出.push({ 文本: t, cls: cls.slice(0, 46), Tip: false, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
      }
    }
    return 出;
  });

  const 避开 = [20, 800];
  const 试悬停 = async (目标, 标签) => {
    if (!目标) { 记(`\n　[${标签}] 目标不存在，本轮没测到`); return { 标签, 缺失: true, 新: [] }; }
    await page.mouse.move(避开[0], 避开[1]);
    await page.waitForTimeout(1300);
    const 前 = await 气泡();
    await page.mouse.move(目标.中心[0] - 3, 目标.中心[1] - 3);
    await page.waitForTimeout(280);
    await page.mouse.move(目标.中心[0], 目标.中心[1]);
    await page.waitForTimeout(2800);
    const 后 = await 气泡();
    const 新 = 后.filter(y => !前.some(x => x.文本 === y.文本 && Math.abs(x.box[0] - y.box[0]) < 4));
    记(`\n　[${标签}] 悬停 box=${JSON.stringify(目标.box)} → 新出现 ${新.length} 个：`);
    for (const n of 新) 记(`　　　「${n.文本}」 ${JSON.stringify(n.box)} ${n.Tip ? 'Tooltip 容器' : '普通元素'} cls=${n.cls}`);
    const bx = 目标.中心[0], by = 目标.中心[1];
    await page.screenshot({ path: EVID + `el3-悬停-${标签}.png` });
    await page.screenshot({ path: EVID + `el3-悬停-${标签}-近景.png`, clip: { x: Math.max(0, Math.min(1440 - 700, bx - 350)), y: Math.max(0, Math.min(810 - 420, by - 300)), width: 700, height: 420 } });
    return { 标签, box: 目标.box, 新: 新.map(n => n.文本), 新全: 新 };
  };

  // ---- ⭐ 阳性对照：手册明写图片节点上 `翻译提示词` / `预设` 有气泡
  const 阳性目标 = 普查.find(x => /翻译提示词|预设/.test(x.文字)) || 普查.find(x => x.文字 && x.文字.length <= 8);
  记(`\n⭐ 阳性对照目标：${阳性目标 ? `文字="${阳性目标.文字}" box=${JSON.stringify(阳性目标.box)}` : '❌ 没找到'}`);
  结果.读数.阳性对照 = await 试悬停(阳性目标, '阳性对照');

  // ---- ⭐ 正向定位手册点名的两枚
  const 滑块 = 普查.find(x => x.svg.includes('M14 17H5M19 7h-9')) || 普查.find(x => /sliders/.test(x.svg) || /Sliders/.test(x.cls));
  const 箭头 = 普查.find(x => /bg-panel-background/.test(x.cls) && /absolute right-2 top-2/.test(x.cls));
  记(`\n　定位「高级设置滑块」：${滑块 ? JSON.stringify({ tag: 滑块.tag, box: 滑块.box, svg: 滑块.svg }) : '❌ 本轮卡片里没找到'}`);
  记(`　定位「展开/收起箭头」：${箭头 ? JSON.stringify({ tag: 箭头.tag, box: 箭头.box, cls: 箭头.cls.slice(0, 60) }) : '❌ 本轮卡片里没找到'}`);
  for (const [名, t] of [['滑块', 滑块], ['箭头', 箭头]]) {
    if (!t) continue;
    const attrKeys = Object.keys(t.attrs).filter(k => k !== 'class');
    记(`　　${名} 的非 class 属性共 ${attrKeys.length} 个：${attrKeys.length ? attrKeys.map(k => `${k}="${t.attrs[k]}"`).join(' ') : '⛔ 一个都没有'}`);
  }
  结果.读数.滑块 = 滑块 || null;
  结果.读数.箭头 = 箭头 || null;
  结果.读数.滑块悬停 = await 试悬停(滑块, '高级设置滑块');
  结果.读数.箭头悬停 = await 试悬停(箭头, '展开收起箭头');

  记('\n✅ 每枚都已留下全视口截图 + 近景截图（含阴性）');
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  try {
    记('⏳ 静置 15s 后复核坐标（三铁律③）…');
    await page.waitForTimeout(15000);
    记(`⭐ 收尾坐标偏差：${JSON.stringify(await 核对坐标(page))}`);
  } catch (e) { console.error(e); }
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEL3.json ===');
}
