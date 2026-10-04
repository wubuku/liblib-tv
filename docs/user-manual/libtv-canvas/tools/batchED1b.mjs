// Batch ED-1b：先诊断画布状态，ED-1 那轮只读到 1 个 4976×2800 的巨组、且在视口外。
//
// ED-1 的失败原因不明 ⇒ 先查：
//   ① 有没有「单画布单编辑者保护」遮罩（lib.mjs 里有 isEditorLocked）
//   ② 真实节点数、每层的 class（排除巨型组容器）
//   ③ 它们在视口里的位置，节点是不是真的没渲染
import { launch, open, closePromos, isEditorLocked, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchED1b.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = {};

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6000 });
  await closePromos(page);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1500);

  结果.是否被锁 = await isEditorLocked(page);
  console.log('是否命中单画布锁遮罩:', 结果.是否被锁);

  const 诊断 = await page.evaluate(() => {
    const W = window.innerWidth, H = window.innerHeight;
    const nodes = [...document.querySelectorAll('.react-flow__node')].map(n => {
      const r = n.getBoundingClientRect();
      const inView = r.right > 0 && r.bottom > 0 && r.left < W && r.top < H;
      return {
        id: n.getAttribute('data-id'),
        cls: n.className.toString().split(' ').filter(c => c.startsWith('react-flow__node-')).join(','),
        rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        在视口内: inView,
      };
    });
    const edges = [...document.querySelectorAll('.react-flow__edge')].length;
    const vp = document.querySelector('.react-flow__viewport');
    return {
      视口: [W, H],
      节点总数: nodes.length,
      在视口内节点数: nodes.filter(n => n.在视口内).length,
      连线数: edges,
      viewportTransform: vp ? getComputedStyle(vp).transform : null,
      正文片段: document.body.innerText.slice(0, 200),
      节点: nodes,
    };
  });
  结果.诊断 = 诊断;
  console.log('\n═══ 诊断 ═══');
  console.log('  节点总数:', 诊断.节点总数, '| 在视口内:', 诊断.在视口内节点数, '| 连线:', 诊断.连线数);
  console.log('  viewport transform:', 诊断.viewportTransform);
  console.log('  正文前 200 字:', JSON.stringify(诊断.正文片段));
  console.log('\n  节点明细:');
  for (const n of 诊断.节点) console.log(`    ${n.id}  ${n.cls}  rect=${JSON.stringify(n.rect)}  在视口内=${n.在视口内}`);
  落盘(结果);
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchED1b.json ===');
}
