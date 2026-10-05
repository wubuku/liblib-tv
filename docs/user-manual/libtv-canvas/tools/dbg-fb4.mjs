// ⭐⭐⭐ 诊断导演台为什么「-1px 连拖 30 轮纹丝不动」
//
// FB-3 结束时导演台停在 [-1222.84, 370.975]，基线是 [-1225.03, 370.975]，差 2.19 画布单位 = 1 屏 px。
// restore-any 在**新会话**里试了 30 轮 -1px，每次都「拖拽成功」但位置零变化。
//   ⇒ 排除「吸附钉住」：新会话的吸附是关的。
//   ⇒ 剩下的解释是**那个落点上没有可发起拖拽的东西**（`.nodrag` 后代 / 内部滚动容器）。
//
// 本脚本：
//   ① 把导演台节点里所有 `.nodrag` 后代连屏幕框全倒出来
//   ② 在导演台框内**扫 9×9 网格**，逐格用 elementFromPoint 找「落点属于导演台且最近 .nodrag 祖先为 null」的可拖区
//   ③ 在找到的可拖区上试 -1px
//   ④ 顺便测：普通文本节点 t-UtVx3lZmrV 能不能 +5px（阳性对照）
//   ⑤ 试键盘方向键（不依赖落点，最安全）
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const ID = process.argv[2] || 'n-56F19pXVB4';
const HERE = new URL('.', import.meta.url).pathname;
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'dbg-fb4.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

const 读 = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return {
    画布: t ? [Number(t[1]), Number(t[2])] : null,
    框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
    中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
    class: n.getAttribute('class'),
    全部属性: Object.fromEntries([...n.attributes].map((a) => [a.name, a.value])),
  };
}, id);

const 拖点 = async (id, x, y, dx, dy) => {
  await page.mouse.move(x, y); await page.waitForTimeout(320);
  const v = await page.evaluate((p) => {
    const e = document.elementFromPoint(p[0], p[1]);
    if (!e) return { null: true };
    const n = e.closest('.react-flow__node');
    const nodrag = e.closest('.nodrag');
    return {
      标签: e.tagName, class: (e.getAttribute('class') || '').slice(0, 100),
      节点id: n ? n.getAttribute('data-id') : null,
      最近nodrag: nodrag ? (nodrag.getAttribute('class') || '').slice(0, 80) : null,
    };
  }, [x, y]);
  if (v.节点id !== id) return { 错: '落点不属于本节点', 落点: v };
  await page.mouse.down(); await page.waitForTimeout(150);
  await page.mouse.move(x + dx, y + dy, { steps: 5 });
  await page.waitForTimeout(280);
  await page.mouse.up(); await page.waitForTimeout(560);
  await page.mouse.move(720, 170); await page.waitForTimeout(260);
  return { 成功: true, 落点: v };
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  const s0 = await 读(ID);
  记(`${ID}｜基线 ${JSON.stringify(坐标[ID])}｜现 ${JSON.stringify(s0.画布)}｜框 ${JSON.stringify(s0.框)}`);
  记('节点 class = ' + s0.class);
  记('节点全部属性 = ' + JSON.stringify(s0.全部属性));
  R.读数.节点 = s0;

  // ① nodrag 后代
  const nd = await page.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!n) return null;
    return [...n.querySelectorAll('.nodrag')].map((e) => {
      const r = e.getBoundingClientRect();
      return { 标签: e.tagName, class: (e.getAttribute('class') || '').slice(0, 90), 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
    });
  }, ID);
  记(`① .nodrag 后代 ${nd ? nd.length : 'null'} 个`);
  if (nd) for (const e of nd.slice(0, 12)) 记(`    <${e.标签} class="${e.class}"> 框 ${JSON.stringify(e.框)}`);
  R.读数.nodrag = nd;

  // ② 扫 9×9
  const [L, T, W, H] = s0.框;
  const 可拖 = [];
  for (let r = 0; r < 9; r++) {
    for (let c = 0; c < 9; c++) {
      const x = L + Math.round(W * (c + 0.5) / 9);
      const y = T + Math.round(H * (r + 0.5) / 9);
      const v = await page.evaluate((p) => {
        const e = document.elementFromPoint(p[0], p[1]);
        if (!e) return null;
        const n = e.closest('.react-flow__node');
        return { 属本节点: n ? n.getAttribute('data-id') : null, 有nodrag: !!e.closest('.nodrag'), 标签: e.tagName };
      }, [x, y]);
      if (v && v.属本节点 === ID) 可拖.push({ x, y, 有nodrag: v.有nodrag, 标签: v.标签 });
    }
  }
  const 净 = 可拖.filter((p) => !p.有nodrag);
  记(`② 9×9 扫 ${可拖.length}/81 格落在本节点；其中**无 nodrag 祖先**的 ${净.length} 格`);
  if (净.length) {
    const 样本 = 净.slice(0, 12);
    记('   样本：' + JSON.stringify(样本.map((p) => [p.x, p.y, p.标签])));
    const 前 = (await 读(ID)).画布;
    const r = await 拖点(ID, 净[0].x, 净[0].y, -1, 0);
    记(`③ 在 (${净[0].x},${净[0].y}) 拖 -1px：${JSON.stringify(r.落点)}`);
    const 后 = (await 读(ID)).画布;
    记(`   ${JSON.stringify(前)} → ${JSON.stringify(后)}｜位移 ${(后[0] - 前[0]).toFixed(4)}`);
    R.读数.净拖区 = 净;
  } else {
    记('⛔ 本节点框内**没有**无 nodrag 的落点');
  }

  // ④ 阳性对照：普通文本节点
  const 控 = 't-UtVx3lZmrV';
  const c0 = (await 读(控));
  const r4 = await 拖点(控, c0.中心[0], c0.中心[1], 5, 0);
  const c1 = (await 读(控));
  记(`④ 阳性对照 ${控} 中心 +5px：${JSON.stringify(c0.画布)} → ${JSON.stringify(c1.画布)}｜位移 ${(c1.画布[0] - c0.画布[0]).toFixed(4)}`);
  // 复原对照节点
  for (let 轮 = 0; 轮 < 12; 轮++) {
    const n = (await 读(控)).画布;
    const dx = 坐标[控][0] - n[0];
    if (Math.abs(dx) < 0.5) break;
    const px_ = Math.max(-8, Math.min(8, Math.round(dx * 0.458621)));
    if (!px_) break;
    await 拖点(控, (await 读(控)).中心[0], (await 读(控)).中心[1], px_, 0);
  }
  记(`   对照节点复原到 ${JSON.stringify((await 读(控)).画布)}`);

  // ⑤ 方向键
  const 前5 = (await 读(ID)).画布;
  await page.mouse.move(s0.中心[0], s0.中心[1]);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(700);
  const sel = await page.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    return n ? n.classList.contains('selected') : null;
  }, ID);
  记(`⑤ 点选后 selected=${sel}`);
  for (const k of ['ArrowLeft', 'ArrowLeft']) {
    await page.keyboard.press(k); await page.waitForTimeout(500);
    记(`   按 ${k} 之后 ${JSON.stringify((await 读(ID)).画布)}`);
  }
  const 后5 = (await 读(ID)).画布;
  记(`   两次方向键合计位移 ${Number((后5[0] - 前5[0]).toFixed(4))}（目标 -2.19）`);
} catch (e) {
  R.错误 = String((e && e.stack) || e);
  记('❌ ' + e.message);
} finally {
  const 终 = await 读(ID);
  记(`终态 ${ID} = ${JSON.stringify(终.画布)}｜基线 ${JSON.stringify(坐标[ID])}`);
  await 浏览器.browser.close();
}
