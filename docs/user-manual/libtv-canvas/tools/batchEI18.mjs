// Batch EI-18：⛔ 只读核查。EI-17 收尾只读到 10 个节点（i-sODTbgLUm1 不见），另有 3 个坐标异常。
// 本脚本**不做任何交互**（不点、不拖、不按键），只打开、读数、截图。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI18.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 标准 = {
  'a-GgqvrVz0pw': [719.388, 1509.13], 'a-THmbuJXQj4': [-1356, 600], 'b-mfkcQNULC3': [636, 300],
  'i-9nlG6HdjK2': [-1764, 900], 'i-sODTbgLUm1': [-168, 900], 'n-56F19pXVB4': [-1225.03, 370.975],
  't-2AK3Ukyxj3': [-1476, 1524], 't-UtVx3lZmrV': [600, 900], 'v-eMpqKtiLlx': [-1787, 900],
  'v-oZNpH99MtM': [132, 300], 'v-v2hlWY4Br3': [-696, 300],
};

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 9000 });
  await page.waitForTimeout(3000);
  const 快照 = async (标签) => {
    const 全部 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => {
      const r = n.getBoundingClientRect();
      const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
      return {
        id: n.getAttribute('data-id'),
        类型: (n.className.toString().match(/react-flow__node-([a-zA-Z]+)/) || [, '?'])[1],
        class: n.className.toString().replace(/selected|dragging|connectable|selectable|animated[^\s]*/g, '').slice(0, 120),
        canvas: m ? [parseFloat(m[1]), parseFloat(m[2])] : null,
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        父: n.parentElement ? (n.parentElement.getAttribute('data-id') || n.parentElement.className.toString().slice(0, 40)) : null,
      };
    }));
    记(`${标签}：共 ${全部.length} 个节点`);
    for (const n of 全部) {
      const std = 标准[n.id];
      const 差 = std && n.canvas ? [Math.round((n.canvas[0] - std[0]) * 10) / 10, Math.round((n.canvas[1] - std[1]) * 10) / 10] : '（无标准）';
      记(`　${n.id.padEnd(16)} ${n.类型.padEnd(9)} canvas=${JSON.stringify(n.canvas)} box=${JSON.stringify(n.box)} 与标准差=${JSON.stringify(差)} 父=${n.父}`);
    }
    const 缺 = Object.keys(标准).filter(id => !全部.some(n => n.id === id));
    记(`　缺失的基线节点：${JSON.stringify(缺)}`);
    return { 全部, 缺 };
  };
  结果.读数.第一次 = await 快照('第一次读数');
  await page.screenshot({ path: EVID + 'ei18-现状.png' });
  await page.waitForTimeout(6000);
  结果.读数.第二次 = await 快照('6 秒后复读');
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI18.json ===');
}
