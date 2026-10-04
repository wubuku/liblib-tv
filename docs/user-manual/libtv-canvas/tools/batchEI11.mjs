// Batch EI-11：把 EI-10 挖出来的源码结论一条条落地验。
//   ① 最左那枚无名图标 = 排列菜单（源码：F.Icons.LayoutPanelTop + onLayoutChange）⇒ 点开读菜单项
//   ② 真值表：把选区收敛到「只有 2 个图片节点」，看「合并分镜组」是否由灰变亮
//      （关键：必须**保留框选产生的选区**——用 Shift 点选把多余的取消掉，不能重新点选）
//   ③ 蓝点（n5 = libtv.canvas.multiSelect.groupMenuNewDotDismissed）只在**点菜单项**时消 ⇒
//      点一次「打组」真的成组，看 localStorage 写入 + 蓝点消失，再 ⌘⇧G 解组复原
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI11.json';
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

  const 节点 = await page.evaluate(() => { const o = {}; for (const n of document.querySelectorAll('.react-flow__node')) { const r = n.getBoundingClientRect(); o[n.getAttribute('data-id')] = { 类型: (n.className.toString().match(/react-flow__node-([a-zA-Z]+)/) || [, '?'])[1], box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }; } return o; });
  结果.读数.节点 = 节点;

  const 找工具条 = () => page.evaluate(() => {
    const all = [...document.querySelectorAll('div')].filter(e => /保存到资产/.test(e.innerText || '') && e.getBoundingClientRect().width > 300 && e.getBoundingClientRect().height > 0);
    if (!all.length) return { 找到: false };
    all.sort((p, q) => p.getBoundingClientRect().width - q.getBoundingClientRect().width);
    const c = all[0]; const r = c.getBoundingClientRect();
    return { 找到: true, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 按钮: [...c.querySelectorAll('button')].map(b => { const rb = b.getBoundingClientRect(); return { 文字: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 12) || (b.getAttribute('aria-label') || '(无名)'), aria: b.getAttribute('aria-label') || '', box: [Math.round(rb.left), Math.round(rb.top), Math.round(rb.width), Math.round(rb.height)] }; }) };
  });
  const 当前选中 = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  const 节点总数 = () => page.evaluate(() => document.querySelectorAll('.react-flow__node').length);

  // 框选（复现「工具条只在框选后出现」）
  const 框选 = async () => {
    const ids = ['i-9nlG6HdjK2', 'i-sODTbgLUm1', 'v-eMpqKtiLlx', 'a-GgqvrVz0pw', 'a-THmbuJXQj4'];
    const ps = ids.map(i => 节点[i].box);
    const x1 = Math.min(...ps.map(p => p[0])) - 20, y1 = Math.min(...ps.map(p => p[1])) - 10;
    const x2 = Math.max(...ps.map(p => p[0] + p[2])) + 20, y2 = Math.max(...ps.map(p => p[1] + p[3])) + 20;
    await page.mouse.move(1250, 800); await page.mouse.click(1250, 800); await page.waitForTimeout(700);
    await page.mouse.move(x1, y1); await page.mouse.down();
    await page.mouse.move((x1 + x2) / 2, (y1 + y2) / 2, { steps: 10 });
    await page.mouse.move(x2, y2, { steps: 10 });
    await page.waitForTimeout(300); await page.mouse.up();
    await page.mouse.move(1250, 800);
    await page.waitForTimeout(1800);
  };

  // ---- ① 排列菜单（最左那枚无名按钮）
  await 框选();
  记(`框选后选中 ${JSON.stringify(await 当前选中())}`);
  let 条 = await 找工具条();
  const 最左 = 条.按钮 && 条.按钮[0];
  记(`最左按钮：${JSON.stringify(最左)}（aria=${最左 ? 最左.aria || '无' : '?'}）`);
  if (最左) {
    await page.mouse.click(Math.round(最左.box[0] + 最左.box[2] / 2), Math.round(最左.box[1] + 最左.box[3] / 2));
    await page.waitForTimeout(1500);
    const 菜单 = await page.evaluate(() => {
      // ⭐ 枚举工具条下方 260px 内所有可见浮层里的按钮文字
      const 出 = [];
      for (const b of document.querySelectorAll('button')) {
        const r = b.getBoundingClientRect();
        const t = (b.innerText || '').trim().replace(/\s+/g, ' ');
        if (r.width === 0 || !t) continue;
        if (/宫格|水平|垂直|排列/.test(t)) 出.push({ 文本: t.slice(0, 14), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], opacity: getComputedStyle(b).opacity });
      }
      return 出;
    });
    记(`⭐ 排列菜单项：${JSON.stringify(菜单)}`);
    结果.读数.排列菜单 = 菜单;
    await page.screenshot({ path: EVID + 'ei11-排列菜单.png' });
    await page.screenshot({ path: EVID + 'ei11-排列菜单裁图.png', clip: { x: 250, y: 60, width: 500, height: 320 } });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(900);
  }

  // ---- ② 真值表：Shift 点掉 3 个非图片节点，保留「框选产生的选区」
  for (const id of ['a-GgqvrVz0pw', 'a-THmbuJXQj4', 'v-eMpqKtiLlx']) {
    const b = 节点[id].box;
    await page.keyboard.down('Shift');
    await page.mouse.click(b[0] + 14, b[1] + 14);          // 左上角：避开播放键/预览
    await page.keyboard.up('Shift');
    await page.waitForTimeout(800);
  }
  await page.mouse.move(1250, 800);
  await page.waitForTimeout(1500);
  const 选2 = await 当前选中();
  条 = await 找工具条();
  记(`\n⭐ Shift 点掉 3 个后：选中 ${JSON.stringify(选2)}（${选2.length} 个）；工具条 ${条.找到 ? '仍在' : '消失'}`);
  结果.读数.收敛后 = { 选中: 选2, 工具条还在: 条.找到 };
  await page.screenshot({ path: EVID + 'ei11-只剩两图.png' });

  if (条.找到) {
    const 打 = 条.按钮.find(b => b.文字.startsWith('打组'));
    await page.mouse.click(Math.round(打.box[0] + 打.box[2] / 2), Math.round(打.box[1] + 打.box[3] / 2));
    await page.waitForTimeout(1500);
    const 项 = await page.evaluate(() => {
      const all = [...document.querySelectorAll('body *')].filter(e => /合并分镜组/.test(e.innerText || '') && e.getBoundingClientRect().width > 0);
      if (!all.length) return { 错: '菜单没开' };
      all.sort((p, q) => p.getBoundingClientRect().width * p.getBoundingClientRect().height - q.getBoundingClientRect().width * q.getBoundingClientRect().height);
      let h = all[0]; for (let i = 0; i < 3; i++) { if (h.querySelectorAll('button').length >= 2) break; h = h.parentElement; }
      return [...h.querySelectorAll('button')].map(e => { const cs = getComputedStyle(e); return { 文本: (e.innerText || '').trim().slice(0, 12), opacity: cs.opacity, cursor: cs.cursor }; });
    });
    记(`⭐【真值表】只剩 2 个图片节点时，下拉：${JSON.stringify(项)}`);
    结果.读数.真值表_两图 = 项;
    await page.screenshot({ path: EVID + 'ei11-两图下拉.png', clip: { x: 500, y: 60, width: 360, height: 240 } });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(900);
  }

  // ---- ③ 蓝点：点一次菜单里的「打组」⇒ 看 localStorage 与蓝点，然后 ⌘⇧G 复原
  const 前 = await page.evaluate(() => ({
    节点数: document.querySelectorAll('.react-flow__node').length,
    键: localStorage.getItem('libtv.canvas.multiSelect.groupMenuNewDotDismissed'),
  }));
  记(`\n成组前：节点数=${前.节点数}，提示点键=${JSON.stringify(前.键)}`);
  结果.读数.成组前 = 前;

  条 = await 找工具条();
  if (条.找到) {
    const 打 = 条.按钮.find(b => b.文字.startsWith('打组'));
    await page.mouse.click(Math.round(打.box[0] + 打.box[2] / 2), Math.round(打.box[1] + 打.box[3] / 2));
    await page.waitForTimeout(1400);
    const 打项 = await page.evaluate(() => {
      const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === '打组' && x.getBoundingClientRect().top > 140);
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
    });
    记(`菜单里「打组」项：${JSON.stringify(打项)}`);
    if (打项) {
      await page.mouse.click(打项[0], 打项[1]);
      await page.waitForTimeout(2200);
      const 后 = await page.evaluate(() => {
        const btn = [...document.querySelectorAll('button')].find(x => (x.getAttribute('aria-label') || '') === '打组菜单');
        const dot = btn ? [...btn.querySelectorAll('span')].map(s => { const r = s.getBoundingClientRect(); return { 尺寸: [Math.round(r.width), Math.round(r.height)], 背景: getComputedStyle(s).backgroundColor }; }).filter(x => x.尺寸[0] > 0 && x.尺寸[0] <= 6) : '按钮不见了';
        return { 节点数: document.querySelectorAll('.react-flow__node').length, 组: [...document.querySelectorAll('.react-flow__node')].map(n => (n.className.toString().match(/react-flow__node-([a-zA-Z]+)/) || [, '?'])[1]).filter(t => t !== 'image' && t !== 'text' && t !== 'video' && t !== 'audio' && t !== 'director' && t !== 'shot'), 蓝点: dot, 键: localStorage.getItem('libtv.canvas.multiSelect.groupMenuNewDotDismissed') };
      });
      记(`⭐ 点「打组」后：节点数=${后.节点数}，蓝点=${JSON.stringify(后.蓝点)}，提示点键=${JSON.stringify(后.键)}，疑似组节点类型=${JSON.stringify(后.组)}`);
      结果.读数.成组后 = 后;
      await page.screenshot({ path: EVID + 'ei11-已成组.png' });

      // ⭐ 复原：⌘⇧G 解组
      await page.keyboard.press('Escape');
      await page.waitForTimeout(700);
      await page.keyboard.press('Meta+Shift+g');
      await page.waitForTimeout(2200);
      const 复 = await page.evaluate(() => ({
        节点数: document.querySelectorAll('.react-flow__node').length,
        选中: [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')),
      }));
      记(`⌘⇧G 后：节点数=${复.节点数}，选中 ${JSON.stringify(复.选中)}`);
      结果.读数.解组后 = 复;
      await page.screenshot({ path: EVID + 'ei11-已解组.png' });
    }
  }
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI11.json ===');
}
