// ⭐⭐⭐⭐⭐ Batch FZ-4：拍空画布上的那排「生成芯片」——手册只有 5 个，这里是 6 个
//
// FZ-3 在**刚建好的空画布**（projectId=59c3c1187a244cfab3c578019f7143e3，节点 0）
// 上读到一整套文字，手册此前**只在旧画布上**记过其中 5 个：
//
//   双击画布 / 自由生成节点 / 图片生成 / 视频生成 / 音频生成
//   ⭐⭐ 剧本生成 / 智能剪辑          ← 这两个本手册没记过「引导芯片」这一形态
//   ⭐⭐ 资产管理
//
// ⭐ 而且这台空画布上还多出两个别处没有的东西：
//   `选择Skill开始创作`（旧画布上是「感知画布开始创作」）
//   `批量创建分镜`    （旧画布上是「批量优化提示词」）
//   `正在跟随 / 取消ESC`
//
// 本轮：把这排芯片逐个实名（框 / 类名 / 点下去是什么），
// 并拍成成品图。⛔ 只读 + 悬停，⛔ 不点任何会生成的东西。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 新画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=59c3c1187a244cfab3c578019f7143e3`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFZ4.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(新画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(7000);
  await closePromos(page);
  await page.waitForTimeout(4000);

  // ① 找那排「生成」芯片
  记('--- ① 定位「生成」芯片组 ---');
  const 芯片 = await page.evaluate(() => {
    const 词 = ['图片生成', '视频生成', '音频生成', '剧本生成', '智能剪辑', '自由生成节点'];
    const o = [];
    for (const w of 词) {
      for (const e of document.querySelectorAll('*')) {
        if (e.children.length) continue;
        if ((e.innerText || '').trim() !== w) continue;
        const r = e.getBoundingClientRect();
        if (r.width < 10 || r.height < 8) continue;
        if (r.x < -100 || r.x > 2000 || r.y < -100 || r.y > 1200) continue;
        o.push({ 词: w, tag: e.tagName, cls: (e.className || '').toString().slice(0, 70),
          框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] });
        break;
      }
    }
    return o;
  });
  R.读数.芯片 = 芯片;
  记(`  找到 ${芯片.length} 枚：`);
  芯片.forEach((c) => 记(`   \`${c.词}\` <${c.tag}> ${c.框.join(',')} cls=${c.cls}`));

  if (芯片.length) {
    // 整组的框（含「双击画布」那一块）
    const 组框 = await page.evaluate((词表) => {
      let x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
      for (const w of 词表) {
        for (const e of document.querySelectorAll('*')) {
          if (e.children.length) continue;
          if ((e.innerText || '').trim() !== w) continue;
          // 往上取整块容器（同一个父）
          let p = e;
          for (let i = 0; i < 4 && p; i++) {
            const r = p.getBoundingClientRect();
            if (r.width > 60 && r.height > 20 && r.height < 160) {
              x0 = Math.min(x0, r.x); y0 = Math.min(y0, r.y);
              x1 = Math.max(x1, r.x + r.width); y1 = Math.max(y1, r.y + r.height);
              break;
            }
            p = p.parentElement;
          }
          break;
        }
      }
      return x1 > 0 ? [Math.round(x0), Math.round(y0), Math.round(x1 - x0), Math.round(y1 - y0)] : null;
    }, 芯片.map((c) => c.词));
    R.读数.组框 = 组框;
    记(`  整组框：${组框 ? 组框.join(',') : '（没算出来）'}`);

    if (组框) {
      // ② 遮挡采样 + 截图
      const 遮 = await page.evaluate((框) => {
        const o = [];
        for (let i = 0; i <= 8; i++) {
          const x = Math.round(框[0] + (框[2] * i) / 8);
          const y = Math.round(框[1] + 框[3] / 2);
          const e = document.elementFromPoint(x, y);
          o.push({ x, y, tag: e?.tagName, inDrawer: !!(e && e.closest('.mantine-Drawer-inner')) });
        }
        return o;
      }, 组框);
      R.读数.遮挡 = 遮;
      断言('整组无遮挡', 遮.every((p) => !p.inDrawer), `${遮.filter((p) => p.inDrawer).length} 个采样点被抽屉挡`);
      const pad = 24;
      const clip = { x: Math.max(0, 组框[0] - pad), y: Math.max(0, 组框[1] - pad),
        width: Math.min(1440, 组框[2] + pad * 2), height: 组框[3] + pad * 2 };
      await page.screenshot({ path: resolve(EVID, 'fz4-1-生成芯片组.png'), clip });
      记(`  已拍：clip ${JSON.stringify(clip)}`);
      R.读数.clip = clip;
    }

    // ③ 逐枚悬停读 tooltip
    记('\n--- ② 逐枚悬停读 tooltip ---');
    const tips = {};
    for (const c of 芯片) {
      await page.mouse.move(c.中心[0], c.中心[1]);
      await page.waitForTimeout(700);
      const t = await page.evaluate(() => {
        const o = [];
        for (const e of document.querySelectorAll('[role="tooltip"],[class*="Tooltip"]')) {
          const s = (e.innerText || '').trim();
          if (s && s.length < 60) o.push(s);
        }
        return o;
      });
      tips[c.词] = t;
      记(`   \`${c.词}\` → ${t.length ? t.join(' / ') : '（无 tooltip）'}`);
    }
    R.读数.tooltip = tips;
    await page.mouse.move(700, 300);
    await page.waitForTimeout(500);
  }

  // ④ 右下角 TV Director 入口的变化（旧画布 4 个，这里不一样）
  记('\n--- ③ 右下角 TV Director 四个入口 ---');
  const 入口 = await page.evaluate(() => {
    const o = [];
    for (const e of document.querySelectorAll('*')) {
      if (e.children.length) continue;
      const t = (e.innerText || '').trim();
      if (!/创作|改编|分镜|提示词/.test(t) || t.length > 18) continue;
      const r = e.getBoundingClientRect();
      if (r.x < 900 || r.width < 30) continue;
      o.push({ 文: t, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
    }
    return o;
  });
  R.读数.导演入口 = 入口;
  记(`  ${入口.length} 个：${入口.map((x) => `「${x.文}」`).join(' / ')}`);

  await page.screenshot({ path: resolve(EVID, 'fz4-2-空画布全屏.png') });
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFZ3.json'.replace('3', '4'), JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
