// Batch EX-1：⭐⭐⭐ **细粒度全量悬停扫描** —— 出一张「画布上哪些地方会出气泡」的完整表。
//
// EW-5 已经证明这条路的价值：用 56px 网格扫全视口，一次扫出
//   3 枚真·悬停气泡（添加节点 / 移动 / 手动生成）+ 1 枚常驻气泡（新功能：支持真人），
//   并顺手把「谁是真悬停、谁是常开」分辨了出来。
//
// ⛔ 但 56px 的网格**太粗** —— 底栏那些按钮只有 28×28，网格点完全可能落在按钮之间的缝里，
//   于是「扫不到」会被误读成「没有气泡」。
//   手册里早就吃过这个亏：20-reference 记着「连续两轮把 画布小地图 / 缩放选项 /
//   隐藏节点连线 / 网格吸附 全读成没有气泡」。
//
// 本轮改成**分区细扫**，步长按控件密度给：
//   · 底栏那一排（y 750~810）→ **8px**（比最窄的 28px 按钮还密）
//   · 参数面板区域（选中时）→ **16px**
//   · 其余画布 → **40px**
// ⇒ 覆盖密度远高于任何控件尺寸，**「扫不到」才真的等于「没有」**。
//
// ⭐ 每一枚气泡都记：文案、气泡框、触发控件的框 + aria + class、扫中它的点数。
//    点数是自证：**一枚真悬停气泡，命中点数应该等于它所在控件的面积 / 步长²**。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEX1.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

const 读气泡 = (page) => page.evaluate(() => {
  const 出 = [];
  for (const e of document.querySelectorAll('[class*="mantine-Tooltip-tooltip"]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    if (parseFloat(getComputedStyle(e).opacity) < 0.5) continue;
    出.push({ 文字: (e.innerText || '').trim().slice(0, 40), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
  }
  return 出;
});

const 读落点 = (page, x, y) => page.evaluate(([px, py]) => {
  const e = document.elementFromPoint(px, py);
  if (!e) return null;
  const b = e.closest('button,[role="button"],[data-nodeid]') || e;
  const rb = b.getBoundingClientRect();
  return {
    标签: b.tagName,
    aria: b.getAttribute('aria-label'),
    文字: (b.innerText || '').trim().slice(0, 24),
    cls: String(b.className).slice(0, 60),
    box: [Math.round(rb.left), Math.round(rb.top), Math.round(rb.width), Math.round(rb.height)],
  };
}, [x, y]);

/** 分区扫描 */
const 扫 = async (区域, 步长) => {
  const 表 = new Map();      // 文案 -> { 气泡, 触发控件, 命中点数, 点样本 }
  let 总点数 = 0;
  for (const [x0, y0, x1, y1] of 区域) {
    for (let y = y0; y <= y1; y += 步长) {
      for (let x = x0; x <= x1; x += 步长) {
        if (x < 2 || x > 1438 || y < 2 || y > 808) continue;
        总点数 += 1;
        await page.mouse.move(x, y);
        await page.waitForTimeout(45);
        const 泡 = await 读气泡(page);
        if (!泡.length) continue;
        const 落 = await 读落点(page, x, y);
        for (const b of 泡) {
          const k = b.文字;
          if (!表.has(k)) 表.set(k, { 文字: k, 气泡: b.box, 触发: null, 命中点: 0, 样本: [] });
          const h = 表.get(k);
          h.命中点 += 1;
          if (h.样本.length < 8) h.样本.push([x, y]);
          if (!h.触发 && 落) h.触发 = 落;
        }
      }
    }
  }
  return { 表: [...表.values()], 总点数 };
};

try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  // 关掉首访弹窗，免得它们的气泡混进来
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      const t = (b.innerText || '').trim();
      if (t === '知道了' || t === '开启') { try { b.click(); } catch (e) {} }
    }
  });
  await page.waitForTimeout(1500);
  await page.mouse.move(20, 20);
  await page.waitForTimeout(1000);

  // ════════ ① 底栏细扫（8px）—— 不选中任何东西 ════════
  记('① 扫底栏（8px 网格）…');
  const A = await 扫([[0, 748, 1440, 808]], 8);
  记(`   扫了 ${A.总点数} 个点，扫出 ${A.表.length} 种气泡`);
  for (const h of A.表) 记(`   「${h.文字}」 气泡@${JSON.stringify(h.气泡)} 命中${h.命中点}点 触发=${h.触发 ? h.触发.标签 + '/' + (h.触发.aria || h.触发.文字 || '—') + ' ' + JSON.stringify(h.触发.box) : '—'}`);
  结果.读数.底栏细扫 = A;

  // ════════ ② 底栏细扫（8px）—— 选中视频节点（底栏不受影响，阳性对照）════════
  const p = await page.evaluate(() => {
    const el = document.querySelector('.react-flow__node[data-id="v-v2hlWY4Br3"]');
    const r = el.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + 14)];
  });
  const 验 = await page.evaluate(([x, y]) => {
    const n = document.elementFromPoint(x, y)?.closest('.react-flow__node');
    return n ? n.getAttribute('data-id') : null;
  }, p);
  记('落点自证=' + 验);
  await page.mouse.click(p[0], p[1]);
  await page.waitForTimeout(2500);

  // ② 参数面板区域细扫（16px）：面板位置从 DOM 现取
  const 面板区 = await page.evaluate(() => {
    for (const e of document.querySelectorAll('button')) {
      if ((e.innerText || '').trim() !== '参考') continue;
      let p = e.parentElement, 框 = null;
      for (let i = 0; i < 12 && p; i++) {
        const r = p.getBoundingClientRect();
        if (r.width > 240 && r.height > 120) 框 = r;
        p = p.parentElement;
      }
      if (!框) continue;
      return [[Math.max(0, Math.round(框.left) - 30), Math.max(0, Math.round(框.top) - 60),
               Math.min(1440, Math.round(框.right) + 10), Math.min(808, Math.round(框.bottom) + 10)]];
    }
    return null;
  });
  记('面板区域=' + JSON.stringify(面板区));
  if (面板区) {
    记('② 扫参数面板（16px 网格）…');
    const B = await 扫(面板区, 16);
    记(`   扫了 ${B.总点数} 个点，扫出 ${B.表.length} 种气泡`);
    for (const h of B.表) 记(`   「${h.文字}」 气泡@${JSON.stringify(h.气泡)} 命中${h.命中点}点 触发=${h.触发 ? h.触发.标签 + '/' + (h.触发.aria || h.触发.文字 || '—') + ' ' + JSON.stringify(h.触发.box) : '—'}`);
    结果.读数.面板细扫 = B;
  }

  await page.screenshot({ path: EVID + 'ex1-面板全景.png' });
  记('已拍 ex1-面板全景.png');

  // ════════ ③ 其余画布粗扫（40px）—— 补全 ════════
  记('③ 扫其余画布（40px 网格）…');
  const C = await 扫([[0, 40, 1440, 744]], 40);
  记(`   扫了 ${C.总点数} 个点，扫出 ${C.表.length} 种气泡`);
  for (const h of C.表) 记(`   「${h.文字}」 气泡@${JSON.stringify(h.气泡)} 命中${h.命中点}点 触发=${h.触发 ? h.触发.标签 + '/' + (h.触发.aria || h.触发.文字 || '—') : '—'}`);
  结果.读数.画布粗扫 = C;

  // ════════ ④ 底栏再扫一次（此时指针停在画布上）—— 确认常开的那枚 ════════
  await page.mouse.move(200, 400);
  await page.waitForTimeout(1200);
  const D = await 读气泡(page);
  记('④ 指针停在空画布时的气泡：' + JSON.stringify(D));
  结果.读数.常驻 = D;

  await page.mouse.click(40, 700);
  await page.waitForTimeout(1500);
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
  console.log('\n=== 已写 tools/batchEX1.json ===');
}
