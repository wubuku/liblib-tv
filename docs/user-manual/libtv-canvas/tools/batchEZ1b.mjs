// Batch EZ-1b：找出「图片节点 A 身上真正能点到的那几个像素」
//
// ⭐⭐ 三铁律之二当场立功：EZ-1 第一版要点图 A，
//    `elementFromPoint` 返回的是 **`v-eMpqKtiLlx`（视频节点）**——
//    A 的框 `[76,319,285,161]` 和视频节点的框 `[65,319,285,161]` **几乎完全重合**。
//    这也正是手册记的那个「它们之间正好卡着一个视频节点」的更狠版本：
//    **不是「卡着」，是「盖着」**。
//
// ⇒ 本轮用**扫描**代替「点中心」：在 A 的框里按 6px 网格打 `elementFromPoint`，
//    逐格记归属节点，找出 A 真正暴露在外面的像素。
//    ⭐ 「扫不到才等于没有」——网格要比最窄的缝隙还密。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEZ1b.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  const 扫描 = await page.evaluate(() => {
    const 图A = document.querySelector('.react-flow__node[data-id="i-9nlG6HdjK2"]');
    if (!图A) return null;
    const r = 图A.getBoundingClientRect();
    const S = 6;
    const 命中 = {};
    const 归属 = [];
    for (let x = Math.ceil(r.left); x < r.right; x += S) {
      for (let y = Math.ceil(r.top); y < r.bottom; y += S) {
        const e = document.elementFromPoint(x, y);
        const n = e ? e.closest('.react-flow__node') : null;
        const id = n ? n.getAttribute('data-id') : '(无节点)';
        命中[id] = (命中[id] || 0) + 1;
        归属.push([x, y, id]);
      }
    }
    return {
      图A框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      步长: S, 总格: 归属.length, 命中分布: 命中,
      属于A的格: 归属.filter((g) => g[2] === 'i-9nlG6HdjK2'),
    };
  });

  记('图A 框 ' + JSON.stringify(扫描.图A框) + '，按 ' + 扫描.步长 + 'px 扫了 ' + 扫描.总格 + ' 格');
  记('⭐ 命中分布：' + JSON.stringify(扫描.命中分布));
  const A格 = 扫描.属于A的格;
  记(`⭐⭐ 真正落在图 A 上的格数：${A格.length}`);
  if (A格.length) {
    const xs = A格.map((g) => g[0]), ys = A格.map((g) => g[1]);
    记(`   x ∈ [${Math.min(...xs)}, ${Math.max(...xs)}]，y ∈ [${Math.min(...ys)}, ${Math.max(...ys)}]`);
    const 中心 = [Math.round(A格.reduce((s, g) => s + g[0], 0) / A格.length),
                   Math.round(A格.reduce((s, g) => s + g[1], 0) / A格.length)];
    记('   这片区域的质心 = ' + JSON.stringify(中心) + '（点它应该能选中图 A）');
    结果.读数.建议点击点 = 中心;
    // 再自证一次
    const v = await page.evaluate((p) => {
      const e = document.elementFromPoint(p[0], p[1]);
      const n = e ? e.closest('.react-flow__node') : null;
      return { tag: e && e.tagName, id: n && n.getAttribute('data-id'), cls: e && (e.className || '').toString().slice(0, 50) };
    }, 中心);
    记('   该点 elementFromPoint 自证：' + JSON.stringify(v));
    await page.screenshot({ path: EVID + 'ez1b-图A被视频节点盖住的现场.png', clip: { x: 40, y: 300, width: 700, height: 210 } });
    记('   已拍 ez1b-图A被视频节点盖住的现场.png');
  }
  结果.读数.扫描 = { 图A框: 扫描.图A框, 步长: 扫描.步长, 总格: 扫描.总格, 命中分布: 扫描.命中分布, 属于A的格数: A格.length };
  结果.读数.A格明细 = A格.slice(0, 400);

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差, 已渲染: Object.keys(await 读全部坐标(page)).length };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchEZ1b.json ===');
}
