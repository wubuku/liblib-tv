// ⭐⭐⭐⭐⭐ Batch FW-1：拍底栏与左下角工具行 —— FV-7 交了实名，这一批补图
//
// FV-7 读全了 12 枚按钮的 aria，但**一张图都没有**。
// 手册规矩：图文并茂 ⇒ 凡是正文里列了成排控件的位置，都要有图。
//
// 拍两张：
//   ① 底部中央七枚（添加节点 / 移动 / 素材库 / 角色造型室 / 生成历史 / 快捷键 / 教程）
//   ② 左下角五枚（整理画布 / 切换小地图 / 隐藏节点连线 / 网格吸附 / 缩放选项）
//
// ⛔ 悬停读 tooltip（只读，不触发任何动作），⛔ 不点任何生成/危险按钮。
// ⛔ 每张都做 elementFromPoint 遮挡采样（缺陷 482）。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFW1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6000);
  await closePromos(page);
  await page.waitForTimeout(4000);

  // ⭐ 等画布节点数稳定（缺陷 491）
  let 上次 = -1, 稳 = 0;
  for (let i = 0; i < 25; i++) {
    const n = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    if (n === 上次) { 稳++; if (稳 >= 3) { 记(`画布稳定在 ${n} 个节点`); break; } } else 稳 = 0;
    上次 = n; await page.waitForTimeout(1200);
  }

  // 关掉右侧抽屉（⛔ 只点 aria 恰为「关闭」的那枚，绝不点「开启浏览器通知」）
  const 关 = await page.evaluate(() => {
    const o = [];
    for (const b of document.querySelectorAll('.mantine-Drawer-inner [aria-label="关闭"], .mantine-Drawer-close')) {
      const r = b.getBoundingClientRect();
      if (r.width < 8) continue;
      o.push([Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]);
    }
    return o;
  });
  记(`抽屉关闭按钮 ${关.length} 枚`);
  for (const c of 关) { await page.mouse.click(c[0], c[1]); await page.waitForTimeout(700); }
  // 关掉通知横幅的 ×（⛔ 不点「开启」）
  const 关x = await page.evaluate(() => {
    for (const e of document.querySelectorAll('[aria-label="关闭"], button')) {
      const p = e.parentElement;
      if (!p) continue;
      if (!/开启浏览器通知/.test(p.innerText || '')) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 8) continue;
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    }
    return null;
  });
  if (关x) { await page.mouse.click(关x[0], 关x[1]); await page.waitForTimeout(700); 记('已关通知横幅的 ×'); }

  // 读两排按钮的框
  const 排 = await page.evaluate(() => {
    const g = (sel, x0, x1) => {
      const o = [];
      for (const b of document.querySelectorAll('[aria-label]')) {
        const r = b.getBoundingClientRect();
        if (r.y < 750 || r.y > 800) continue;
        if (r.x < x0 || r.x > x1) continue;
        o.push({ aria: b.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y),
          w: Math.round(r.width), h: Math.round(r.height),
          中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
          文字: (b.innerText || '').trim() });
      }
      return o.sort((a, b) => a.x - b.x);
    };
    return { 底中: g('', 400, 1000), 左下: g('', 0, 400) };
  });
  R.读数.排 = 排;
  记(`\n底部中央 ${排.底中.length} 枚：`);
  排.底中.forEach((b, i) => 记(`   ${i + 1}. \`${b.aria}\` @${b.x},${b.y} ${b.w}×${b.h}`));
  记(`左下角 ${排.左下.length} 枚：`);
  排.左下.forEach((b, i) => 记(`   ${i + 1}. \`${b.aria}\` @${b.x},${b.y} ${b.w}×${b.h}`));

  // 逐枚悬停读 tooltip（只读）
  const tips = {};
  for (const 组 of [排.底中, 排.左下]) {
    for (const b of 组) {
      await page.mouse.move(b.中心[0], b.中心[1]);
      await page.waitForTimeout(750);
      const t = await page.evaluate(() => {
        const o = [];
        for (const e of document.querySelectorAll('[role="tooltip"], [class*="Tooltip"]')) {
          const s = (e.innerText || '').trim();
          if (s && s.length < 60) o.push(s);
        }
        return o;
      });
      tips[b.aria] = t;
      记(`   \`${b.aria}\` 悬停 → ${t.length ? t.join(' / ') : '（无 tooltip）'}`);
    }
  }
  R.读数.tooltip = tips;
  await page.mouse.move(700, 400);
  await page.waitForTimeout(600);

  // 遮挡采样（缺陷 482）
  const 采样 = (组, 名) => {
    const pts = [];
    for (const b of 组) pts.push(b.中心);
    return page.evaluate(({ pts, 名 }) => {
      const 挡 = [];
      for (const [x, y] of pts) {
        const e = document.elementFromPoint(x, y);
        const inDrawer = !!(e && e.closest('.mantine-Drawer-inner'));
        挡.push({ x, y, tag: e?.tagName, inDrawer });
      }
      return { 名, 挡 };
    }, { pts, 名 });
  };
  const s1 = await 采样(排.底中, '底部中央');
  const s2 = await 采样(排.左下, '左下角');
  R.读数.采样 = [s1, s2];
  断言('底部中央无遮挡', s1.挡.every((p) => !p.inDrawer), `${s1.挡.filter((p) => p.inDrawer).length} 个被抽屉挡`);
  断言('左下角无遮挡', s2.挡.every((p) => !p.inDrawer), `${s2.挡.filter((p) => p.inDrawer).length} 个被抽屉挡`);

  // 拍图
  const clipOf = (组, pad = 14) => {
    const x0 = Math.max(0, Math.min(...组.map((b) => b.x)) - pad);
    const x1 = Math.max(...组.map((b) => b.x + b.w)) + pad;
    const y0 = Math.max(0, Math.min(...组.map((b) => b.y)) - pad);
    const y1 = Math.max(...组.map((b) => b.y + b.h)) + pad;
    return { x: x0, y: y0, width: x1 - x0, height: y1 - y0 };
  };
  if (排.底中.length) {
    const c = clipOf(排.底中);
    await page.screenshot({ path: resolve(EVID, 'fw1-0-底部中央七枚.png'), clip: c });
    记(`拍底部中央：clip ${JSON.stringify(c)}`);
    R.读数.底部中央clip = c;
  }
  if (排.左下.length) {
    const c = clipOf(排.左下);
    await page.screenshot({ path: resolve(EVID, 'fw1-1-左下角五枚.png'), clip: c });
    记(`拍左下角：clip ${JSON.stringify(c)}`);
    R.读数.左下角clip = c;
  }
  // 再拍一张带 tooltip 的（悬停在「移动」上，证明它就是整理画布）
  const 移动 = 排.底中.find((b) => b.aria === '移动');
  if (移动) {
    await page.mouse.move(移动.中心[0], 移动.中心[1]);
    await page.waitForTimeout(900);
    const c = { x: 移动.x - 120, y: 移动.y - 90, width: 240 + 移动.w, height: 90 + 移动.h };
    await page.screenshot({ path: resolve(EVID, 'fw1-2-移动悬停出提示.png'), clip: c });
    记('拍「移动」悬停');
  }
  await page.screenshot({ path: resolve(EVID, 'fw1-3-整屏.png') });
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFW1.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
