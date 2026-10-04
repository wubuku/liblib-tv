// Batch EI-19：⛔ 修复 EI-17 造成的数据损伤。
//   损伤：① i-sODTbgLUm1（图片节点 2）被删（11 → 10）② a-THmbuJXQj4 / i-9nlG6HdjK2 / v-eMpqKtiLlx
//        三个统一偏移 (+2320, +412.1)。两者在**新会话**里都稳定复现，不是读数抖动。
//   撤销历史不跨会话 ⇒ 只能直接修：先归位三个，再用底部「+ → 图片」重建缺失的那个并摆回原坐标。
//   每一步都读 transform 验收，最后静置 15s 复核是否真的落盘。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI19.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 标准 = {
  'a-GgqvrVz0pw': [719.388, 1509.13], 'a-THmbuJXQj4': [-1356, 600], 'b-mfkcQNULC3': [636, 300],
  'i-9nlG6HdjK2': [-1764, 900], 'n-56F19pXVB4': [-1225.03, 370.975],
  't-2AK3Ukyxj3': [-1476, 1524], 't-UtVx3lZmrV': [600, 900], 'v-eMpqKtiLlx': [-1787, 900],
  'v-oZNpH99MtM': [132, 300], 'v-v2hlWY4Br3': [-696, 300],
};
const 缺失 = { id: 'i-sODTbgLUm1', 画布: [-168, 900] };

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
  await page.waitForTimeout(3000);

  const 读视口 = () => page.evaluate(() => {
    const el = document.querySelector('.react-flow__viewport');
    const m = el ? /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)[^)]*scale\((-?[\d.]+)\)/.exec(el.style.transform || '') : null;
    return m ? { zoom: parseFloat(m[3]), raw: el.style.transform } : { raw: '(无)' };
  });
  const 读全部 = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => {
    const r = n.getBoundingClientRect();
    const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    return { id: n.getAttribute('data-id'), 类型: (n.className.toString().match(/react-flow__node-([a-zA-Z]+)/) || [, '?'])[1], 标题: (n.innerText || '').split('\n')[0].trim().slice(0, 14), canvas: m ? [parseFloat(m[1]), parseFloat(m[2])] : null, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }));
  const 读一 = (id) => page.evaluate((i) => {
    const el = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(el.style.transform || '');
    return { canvas: m ? [parseFloat(m[1]), parseFloat(m[2])] : null, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }, id);

  const 挪画布 = async (id, 目标) => {
    for (let 轮 = 0; 轮 < 6; 轮++) {
      const v = await 读视口();
      const st = await 读一(id);
      if (!st || !st.canvas) return `${id} 读不到`;
      const dcx = 目标[0] - st.canvas[0], dcy = 目标[1] - st.canvas[1];
      if (Math.abs(dcx) < 1.2 && Math.abs(dcy) < 1.2) return `已到位（残差 ${dcx.toFixed(2)},${dcy.toFixed(2)}）`;
      const z = v.zoom || 0.46;
      const sx = st.box[0] + st.box[2] / 2, sy = st.box[1] + st.box[3] / 2;
      await page.mouse.move(sx, sy);
      await page.mouse.down();
      await page.mouse.move(sx + dcx * z / 2, sy + dcy * z / 2, { steps: 12 });
      await page.mouse.move(sx + dcx * z, sy + dcy * z, { steps: 12 });
      await page.waitForTimeout(450);
      await page.mouse.up();
      await page.waitForTimeout(2000);
      记(`　　${id} 第 ${轮 + 1} 轮画布差 ${dcx.toFixed(1)},${dcy.toFixed(1)}（zoom ${z.toFixed(4)}）`);
    }
    return '多轮后仍有误差';
  };

  // ---- ① 归位偏移的三个
  const 开局 = await 读全部();
  记(`开局 ${开局.length} 个节点`);
  const 要修 = 开局.filter(n => 标准[n.id] && n.canvas && (Math.abs(n.canvas[0] - 标准[n.id][0]) > 1.5 || Math.abs(n.canvas[1] - 标准[n.id][1]) > 1.5));
  记(`要归位：${JSON.stringify(要修.map(n => [n.id, n.canvas, 标准[n.id]]))}`);
  for (const n of 要修) 记(`　${n.id}: ${await 挪画布(n.id, 标准[n.id])}`);

  // ---- ② 重建缺失的图片节点
  const 现有 = await 读全部();
  记(`\n现有图片节点：${JSON.stringify(现有.filter(n => n.类型 === 'image').map(n => [n.id, n.标题, n.canvas]))}`);
  if (!现有.some(n => n.id === 缺失.id)) {
    const 加号 = await page.evaluate(() => {
      const b = [...document.querySelectorAll('button')].find(x => {
        const r = x.getBoundingClientRect();
        return r.width > 0 && r.width < 50 && r.top > 720 && (x.innerText || '').trim() === '' && x.querySelector('svg');
      });
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
    });
    记(`点「+」按钮：${JSON.stringify(加号)}`);
    if (加号) {
      await page.mouse.click(加号[0], 加号[1]);
      await page.waitForTimeout(1500);
      const 菜单项 = await page.evaluate(() => [...document.querySelectorAll('button,[role="menuitem"],li,div')]
        .filter(e => {
          const r = e.getBoundingClientRect();
          return r.width > 0 && r.height > 0 && r.width < 260 && r.height < 60 && /图片|文本|视频|音频/.test(e.innerText || '') && e.children.length <= 2;
        })
        .map(e => { const r = e.getBoundingClientRect(); return { 文本: (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 16), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }; }));
      记(`菜单候选：${JSON.stringify(菜单项.slice(0, 8))}`);
      await page.screenshot({ path: EVID + 'ei19-加号菜单.png' });
      const 图片项 = 菜单项.find(m => /^图片/.test(m.文本));
      if (图片项) {
        await page.mouse.click(图片项.box[0] + 图片项.box[2] / 2, 图片项.box[1] + 图片项.box[3] / 2);
        await page.waitForTimeout(2500);
        const 后 = await 读全部();
        const 新 = 后.filter(n => !开局.some(o => o.id === n.id));
        记(`新增节点：${JSON.stringify(新.map(n => [n.id, n.类型, n.标题, n.canvas]))}`);
        结果.读数.新建 = 新;
        if (新.length) {
          const 新图 = 新.find(n => n.类型 === 'image') || 新[0];
          记(`　把 ${新图.id} 挪到 ${JSON.stringify(缺失.画布)}：${await 挪画布(新图.id, 缺失.画布)}`);
          // 改名成「图片节点 2」以保持手册与画布一致
          const 改名 = await page.evaluate((i) => {
            const el = document.querySelector(`.react-flow__node[data-id="${i}"]`);
            if (!el) return '节点不在';
            const dbl = new MouseEvent('dblclick', { bubbles: true });
            const inp = el.querySelector('input');
            if (inp) { inp.focus(); return '已有 input，直接可改'; }
            el.dispatchEvent(dbl);
            return '已派发双击';
          }, 新图.id);
          await page.waitForTimeout(1200);
          const 改名2 = await page.evaluate((i) => {
            const el = document.querySelector(`.react-flow__node[data-id="${i}"]`);
            if (!el) return '节点不在';
            const inp = el.querySelector('input');
            if (!inp) return '双击后没出现输入框';
            return 'input=' + inp.value;
          }, 新图.id);
          记(`改名尝试：${改名} / ${改名2}`);
          结果.读数.改名 = { 改名, 改名2 };
          await page.screenshot({ path: EVID + 'ei19-新建后.png' });
        }
      } else 记('❌ 菜单里没找到「图片」项');
    }
  }

  // ---- ③ 终检
  记('\n静置 15s 等落盘…');
  await page.waitForTimeout(15000);
  const 终 = await 读全部();
  记(`终检：共 ${终.length} 个节点`);
  for (const n of 终) 记(`　${n.id.padEnd(16)} ${n.类型.padEnd(9)} ${JSON.stringify(n.canvas)} 标题=${n.标题}`);
  结果.读数.终检 = 终;
  await page.screenshot({ path: EVID + 'ei19-终检.png' });
  await page.waitForTimeout(5000);
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI19.json ===');
}
