// Batch EZ-1：⭐⭐⭐ 补上手册一直没取到的那个阳性对照
//
// 手册 §「点开 `打组` 的下拉」里挂着一条 📖：
//   「选中 2～25 个节点，且每一个都是图片节点」⇒ `合并分镜组` 应该可用，
//   **但这只是源码条件，没实测过**。
//   当年取不到的原因写得很清楚：**全画布只有 2 个图片节点，
//   而它们之间正好卡着一个视频节点，任何一条框选矩形都必然把它一起圈进来。**
//
// ⭐ 本轮换一个选法：**先点第一个，再 Shift+点第二个**。
//    点选 + 修饰键加选**完全不画矩形**，中间夹着谁都不管。
//    ⇒ 这一条路当年没人试，或者试了没记。
//
// ⛔ 只做点选，绝不拖拽节点；收尾静置 15s 后核对坐标。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEZ1.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

/** 当前渲染出来的节点：id + 屏上框 + 是否选中 */
const 节点 = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return {
    id: n.getAttribute('data-id'),
    cls: n.className,
    box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
    中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
    选中: n.classList.contains('selected'),
    在视口内: r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight,
  };
}));

/** ⭐ 三铁律之二：点之前验落点归属，返回那个点的节点 id */
const 落点 = (p) => page.evaluate(([x, y]) => {
  const e = document.elementFromPoint(x, y);
  if (!e) return { 命中节点: null, tag: null };
  const n = e.closest('.react-flow__node');
  return {
    命中节点: n ? n.getAttribute('data-id') : null,
    tag: e.tagName,
    cls: (e.className || '').toString().slice(0, 40),
  };
}, p);

const 选中集 = async (标签) => {
  const ns = await 节点();
  const s = ns.filter((n) => n.选中);
  记(`  【${标签}】选中 ${s.length} 个：${JSON.stringify(s.map((n) => n.id))}`);
  return s;
};

/** 打组下拉里两项的可用态 —— 判据只用 opacity / cursor（手册已记 disabled 三件套全废） */
const 打组下拉 = () => page.evaluate(() => {
  const 出 = [];
  for (const e of document.querySelectorAll('div,span,li,button')) {
    if (e.children.length) continue;
    const t = (e.innerText || '').trim();
    if (t !== '打组' && t !== '合并分镜组' && t !== '转分镜组') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    const cs = getComputedStyle(e);
    // 往上找两层，看整行的视觉态（文字层本身可能不带 opacity）
    let 节点层 = e, op = cs.opacity, cur = cs.cursor;
    for (let i = 0; i < 2 && 节点层.parentElement; i++) {
      节点层 = 节点层.parentElement;
      const p2 = getComputedStyle(节点层);
      if (parseFloat(p2.opacity) < 1) { op = p2.opacity; cur = p2.cursor; }
    }
    出.push({
      文字: t, tag: e.tagName.toLowerCase(),
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
      自身opacity: cs.opacity, 整行opacity: op, cursor: cur,
      disabled: e.disabled === true,
      ariaDisabled: e.getAttribute('aria-disabled'),
    });
  }
  return 出;
});

/** ⭐ 唯一的点击入口：先 move 回目标 → 自证 → 才 down/up */
const 点击 = async (p, 说明) => {
  await page.mouse.move(p[0], p[1]);
  await page.waitForTimeout(420);
  const v = await 落点(p);
  if (说明 && v.命中节点 !== 说明) throw new Error(`落点自证失败：期望节点 ${说明}，实得 ${v.命中节点}`);
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(900);
  return v;
};

const 开打组下拉 = async () => {
  const b = await page.evaluate(() => {
    const all = [...document.querySelectorAll('div,span,button')]
      .filter((e) => e.children.length === 0 && (e.innerText || '').trim() === '打组')
      .map((e) => e.getBoundingClientRect()).filter((r) => r.width > 10 && r.height > 10);
    if (!all.length) return null;
    const r = all[0];
    return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
  });
  if (!b) throw new Error('找不到「打组」按钮');
  await page.mouse.move(b[0], b[1]); await page.waitForTimeout(420);
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(900);
  return b;
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  const ns = await 节点();
  记(`渲染中 ${ns.length} 个节点：${JSON.stringify(ns.map((n) => [n.id, n.box.join(','), n.选中]))}`);
  const 图A = ns.find((n) => n.id === 'i-9nlG6HdjK2');
  const 图B = ns.find((n) => n.id === 'i-sODTbgLUm1');
  if (!图A || !图B) throw new Error('两个图片节点没同时渲染');
  记(`图A ${图A.id} ${JSON.stringify(图A.box)}｜图B ${图B.id} ${JSON.stringify(图B.box)}`);
  结果.读数.节点 = ns.map((n) => ({ id: n.id, box: n.box }));

  // ---------- 阶段 1：只选图 A ----------
  记('—— 阶段 1：只点图 A ——');
  await 点击(图A.中心, 图A.id);
  await page.mouse.move(700, 400); await page.waitForTimeout(600);
  await 选中集('图A');
  await 开打组下拉();
  const 下拉1 = await 打组下拉();
  记('  下拉读数：' + JSON.stringify(下拉1));
  await page.screenshot({ path: EVID + 'ez1-阶段1-单选一个图片.png' });
  记('  已拍 ez1-阶段1-单选一个图片.png');
  结果.读数.阶段1 = 下拉1;
  await page.keyboard.press('Escape'); await page.waitForTimeout(700);

  // ---------- 阶段 2：Shift 加选图 B → 纯 2 图片 ----------
  记('—— 阶段 2：Shift 加选图 B（纯 2 个图片节点）——');
  await page.keyboard.down('Shift');
  await page.mouse.move(图B.中心[0], 图B.中心[1]);
  await page.waitForTimeout(450);
  const 落点B = await 落点(图B.中心);
  记('  Shift 点击前落点=' + JSON.stringify(落点B));
  if (落点B.命中节点 !== 图B.id) {
    await page.keyboard.up('Shift');
    throw new Error('图 B 落点被别的节点挡住了：' + JSON.stringify(落点B));
  }
  await page.mouse.down(); await page.mouse.up();
  await page.keyboard.up('Shift');
  await page.waitForTimeout(1000);
  await page.mouse.move(700, 400); await page.waitForTimeout(600);
  const 选中2 = await 选中集('图A+图B');
  结果.读数.阶段2选中 = 选中2.map((n) => n.id);

  if (选中2.length !== 2 || !选中2.every((n) => n.id.startsWith('i-'))) {
    记('  ⛔ 选区不是「恰好 2 个纯图片节点」，本轮到此为止');
  } else {
    await 开打组下拉();
    const 下拉2 = await 打组下拉();
    记('  ⭐⭐ 下拉读数：' + JSON.stringify(下拉2));
    结果.读数.阶段2 = 下拉2;
    await page.screenshot({ path: EVID + 'ez1-阶段2-两个图片节点-下拉.png' });
    记('  已拍 ez1-阶段2-两个图片节点-下拉.png');
    const 合 = 下拉2.find((x) => x.文字 === '合并分镜组');
    const 组 = 下拉2.find((x) => x.文字 === '打组');
    if (合 && 组) {
      记(`⭐⭐⭐ 阳性对照结论：选区 = 2 个纯图片节点时`
        + `「合并分镜组」整行 opacity=${合.整行opacity} cursor=${合.cursor}；`
        + `同屏「打组」opacity=${组.整行opacity} cursor=${组.cursor}`);
      记(`  判「变亮」：${parseFloat(合.整行opacity) > 0.9 && 合.cursor === 'pointer' ? '✅ 是' : '⛔ 否'}`);
    }
    await page.keyboard.press('Escape'); await page.waitForTimeout(700);
  }

  // ---------- 阶段 3：阳性/阴性对照 —— 加选一个音频，验证「纯图片」是必要条件 ----------
  记('—— 阶段 3：加选一个音频节点（应重新变灰）——');
  const 音 = ns.find((n) => n.id === 'a-GgqvrVz0pw');
  if (音) {
    await page.keyboard.down('Shift');
    await page.mouse.move(音.中心[0], 音.中心[1]); await page.waitForTimeout(420);
    const 落点音 = await 落点(音.中心);
    记('  音频落点=' + JSON.stringify(落点音));
    if (落点音.命中节点 === 音.id) {
      await page.mouse.down(); await page.mouse.up();
      await page.keyboard.up('Shift');
      await page.waitForTimeout(1000);
      await page.mouse.move(700, 400); await page.waitForTimeout(600);
      const 选中3 = await 选中集('2图片+1音频');
      await 开打组下拉();
      const 下拉3 = await 打组下拉();
      记('  下拉读数：' + JSON.stringify(下拉3));
      结果.读数.阶段3 = 下拉3;
      结果.读数.阶段3选中 = 选中3.map((n) => n.id);
      await page.screenshot({ path: EVID + 'ez1-阶段3-加一个音频之后.png' });
      记('  已拍 ez1-阶段3-加一个音频之后.png');
      await page.keyboard.press('Escape'); await page.waitForTimeout(700);
    } else {
      await page.keyboard.up('Shift');
      记('  ⛔ 音频节点被别的节点挡住（这正是手册记的遮挡事实），阶段 3 跳过');
    }
  }

  // ---------- 收尾：清空选区 ----------
  await page.keyboard.press('Escape');
  await page.waitForTimeout(600);
  await page.mouse.move(720, 640);
  await page.waitForTimeout(400);
  await page.mouse.down(); await page.mouse.up();   // 点空白清选区
  await page.waitForTimeout(1000);
  await page.mouse.move(720, 780); await page.waitForTimeout(500);
  const 末 = await 选中集('收尾');
  记('收尾后仍有选中：' + JSON.stringify(末.map((n) => n.id)));

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差, 已渲染: Object.keys(await 读全部坐标(page)).length, 基线数: BASE.length };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchEZ1.json ===');
}
