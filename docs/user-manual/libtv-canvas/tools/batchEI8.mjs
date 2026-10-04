// Batch EI-8：⭐ 用真值表验 canStoryboardGroup（>=2 且 <=25 且全是图片）——
//   纯观察，不点「合并分镜组」，不改任何画布状态。
//   另：点一次「批量下载」确认「当前选区无可下载的资源」这句提示是真的（应该什么也不发生）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI8.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
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
  await page.waitForTimeout(1800);

  const 节点类型 = await page.evaluate(() => {
    const o = {};
    for (const n of document.querySelectorAll('.react-flow__node')) {
      const r = n.getBoundingClientRect();
      const cls = n.className.toString();
      o[n.getAttribute('data-id')] = { 类型: (cls.match(/react-flow__node-([a-zA-Z]+)/) || [, '?'])[1], box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
    }
    return o;
  });
  结果.读数.节点类型 = 节点类型;
  记(`节点类型：${JSON.stringify(Object.entries(节点类型).map(([k, v]) => k + '=' + v.类型))}`);

  // 用「点选 + Shift 加选」构造选区（单击不移动，不会拖动节点）
  const 选这些 = async (ids) => {
    await page.keyboard.press('Escape');
    await page.mouse.click(1300, 780);                    // 点空白先清空
    await page.waitForTimeout(700);
    for (let i = 0; i < ids.length; i++) {
      const box = 节点类型[ids[i]].box;
      const cx = Math.round(box[0] + box[2] / 2), cy = Math.round(box[1] + box[3] / 2);
      if (i === 0) await page.mouse.click(cx, cy);
      else await page.keyboard.down('Shift'), await page.mouse.click(cx, cy), await page.keyboard.up('Shift');
      await page.waitForTimeout(650);
    }
    await page.waitForTimeout(1400);
    return page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  };

  // 打开「打组」下拉，把两项的视觉态读出来（纯读）
  const 读下拉 = async () => {
    const 打组 = await page.evaluate(() => {
      const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim().startsWith('打组') && x.getBoundingClientRect().top < 140);
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
    });
    if (!打组) return { 错: '工具条上没有「打组」' };
    await page.mouse.click(打组[0], 打组[1]);
    await page.waitForTimeout(1300);
    const m = await page.evaluate(() => {
      const all = [...document.querySelectorAll('body *')].filter(e => /合并分镜组/.test(e.innerText || '') && e.getBoundingClientRect().width > 0);
      if (!all.length) return { 错: '菜单没开' };
      all.sort((p, q) => p.getBoundingClientRect().width * p.getBoundingClientRect().height - q.getBoundingClientRect().width * q.getBoundingClientRect().height);
      let 宿主 = all[0]; for (let i = 0; i < 3; i++) { if (宿主.querySelectorAll('button').length >= 2) break; 宿主 = 宿主.parentElement; }
      return [...宿主.querySelectorAll('button')].map(e => {
        const cs = getComputedStyle(e);
        return { 文本: (e.innerText || '').trim().slice(0, 12), opacity: cs.opacity, cursor: cs.cursor, disabled: e.disabled === true, ariaDis: e.getAttribute('aria-disabled') };
      });
    });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(700);
    return m;
  };

  // ---- 四种选区，构成真值表
  const 用例 = [
    { 名: 'A 两个图片节点', ids: ['i-9nlG6HdjK2', 'i-sODTbgLUm1'] },
    { 名: 'B 一个图片 + 一个文本', ids: ['i-9nlG6HdjK2', 't-2AK3Ukyxj3'] },
    { 名: 'C 只选一个图片节点', ids: ['i-9nlG6HdjK2'] },
    { 名: 'D 全部（阳性对照：应为灰）', ids: [] },       // 空 = 用框选
  ];
  结果.读数.真值表 = [];
  for (const u of 用例) {
    let 选中;
    if (!u.ids.length) {
      const box = (id) => 节点类型[id].box;
      const 位置 = ['i-9nlG6HdjK2', 'i-sODTbgLUm1', 'v-eMpqKtiLlx', 'a-GgqvrVz0pw', 'a-THmbuJXQj4'].map(box);
      const x1 = Math.min(...位置.map(p => p[0])) - 20, y1 = Math.min(...位置.map(p => p[1])) - 10;
      const x2 = Math.max(...位置.map(p => p[0] + p[2])) + 20, y2 = Math.max(...位置.map(p => p[1] + p[3])) + 20;
      await page.mouse.move(1300, 780); await page.mouse.click(1300, 780); await page.waitForTimeout(600);
      await page.mouse.move(x1, y1); await page.mouse.down();
      await page.mouse.move((x1 + x2) / 2, (y1 + y2) / 2, { steps: 10 });
      await page.mouse.move(x2, y2, { steps: 10 });
      await page.waitForTimeout(300); await page.mouse.up();
      await page.mouse.move(700, 760);
      await page.waitForTimeout(1600);
      选中 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
    } else {
      选中 = await 选这些(u.ids);
    }
    const 类型表 = 选中.map(id => 节点类型[id] ? 节点类型[id].类型 : '?');
    const 下拉 = await 读下拉();
    记(`\n【${u.名}】选中 ${选中.length} 个：${JSON.stringify(选中)}`);
    记(`　类型：${JSON.stringify(类型表)}`);
    记(`　下拉：${JSON.stringify(下拉)}`);
    结果.读数.真值表.push({ 用例: u.名, 选中, 类型: 类型表, 下拉 });
    落盘(结果);
  }

  // ---- 阳性对照用截图：两个图片节点被选中时的下拉
  await 选这些(['i-9nlG6HdjK2', 'i-sODTbgLUm1']);
  const c = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim().startsWith('打组') && x.getBoundingClientRect().top < 140);
    const r = b.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
  });
  await page.mouse.click(c[0], c[1]);
  await page.waitForTimeout(1400);
  await page.screenshot({ path: EVID + 'ei8-两个图片-下拉-亮.png', clip: { x: 520, y: 60, width: 320, height: 220 } });
  记('✅ 已拍「两个图片节点」时的下拉（阳性对照图）');
  await page.keyboard.press('Escape');
  await page.waitForTimeout(800);

  // ---- 点一次「批量下载」：应该什么也不发生（无下载、无提示、无弹窗）
  const 下载前 = await page.evaluate(() => document.querySelectorAll('[role="dialog"]').length);
  const dl = await page.evaluate(() => {
    const 在条上 = (el) => { const r = el.getBoundingClientRect(); return r.top > 70 && r.top < 130 && r.left > 250 && r.left < 1000; };
    const b = [...document.querySelectorAll('button')].filter(x => !x.closest('.react-flow__node') && 在条上(x) && x.getBoundingClientRect().width === 32)[0];
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
  });
  if (dl) {
    await page.mouse.click(dl[0], dl[1]);
    await page.waitForTimeout(2200);
    const 后 = await page.evaluate(() => ({
      弹窗: [...document.querySelectorAll('[role="dialog"]')].map(e => (e.innerText || '').trim().slice(0, 40)),
      toast: [...document.querySelectorAll('body *')].filter(e => e.children.length === 0 && /下载|失败|成功|无可下载/.test(e.innerText || '') && e.getBoundingClientRect().width > 0).map(e => e.innerText.trim().slice(0, 30)),
      toast类: [...document.querySelectorAll('[class*="toast"],[class*="Toast"],[class*="notification"],[class*="Notification"]')].map(e => (e.innerText || '').trim().slice(0, 40)).filter(Boolean).slice(0, 3),
    }));
    记(`⭐ 点「批量下载」后：弹窗=${JSON.stringify(后.弹窗)} 短文案=${JSON.stringify(后.toast.slice(0, 5))} toast类=${JSON.stringify(后.toast类)}`);
    结果.读数.点批量下载 = { 前弹窗数: 下载前, 后: 后 };
    await page.screenshot({ path: EVID + 'ei8-点批量下载之后.png' });
  }
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI8.json ===');
}
