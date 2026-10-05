// ⭐⭐⭐⭐⭐ Batch FZ-2：命名框里点「确定」，把新画布真正建出来
//
// FZ-1 的读数已经把机制查清了（缺陷 499 的答案）：
//   点 `aria="新建画布"` 的加号 ⇒ **弹出命名对话框**，
//   而对话框里那个输入框的 `value` **已经是 `画布 64`** —— 也就是说
//   ⭐ **新画布在点加号的那一刻就已经建出来了**（拿到了下一个编号 64），
//   命名框只是让你**改个名并确认**；不点「确定」，这次创建就不落地。
//   ⇒ 所以 FY-6「点了没反应」的真正原因是：
//      **它弹了一个框，而我只等了 5 秒就去读 URL** —— 读的还是旧 URL。
//
// 本轮：命名框里点「确定」，然后在新画布上探新手引导。
// ⛔ 建画布属 CRUD，允许。⛔ 命名用默认的「画布 64」，不乱改。
// ⛔ 建完只读引导，不建节点、不点生成。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFZ2.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

const 探引导 = () => page.evaluate(() => {
  const 词 = ['第1/4步', '第2/4步', '第3/4步', '第4/4步', '跟着做，快速上手',
    '双击或右键创建新节点', '图片上方工具栏有高清', '拖拽一个或多个节点',
    '把多个作品打组', '先跟着引导完成这一步', '知道了', '跳过', '下一步', '上一步'];
  const 找到 = [];
  for (const w of 词) {
    for (const e of document.querySelectorAll('*')) {
      if (e.children.length) continue;
      const t = (e.innerText || '').trim();
      if (!t.includes(w)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      if (r.x < -200 || r.y < -200 || r.x > 2000 || r.y > 1200) continue;
      找到.push({ 词: w, x: Math.round(r.x), y: Math.round(r.y),
        w: Math.round(r.width), h: Math.round(r.height) });
      break;
    }
  }
  return 找到;
});

const 数画布 = () => page.evaluate(() => {
  const 名 = new Set();
  for (const e of document.querySelectorAll('*')) {
    if (e.children.length) continue;
    const t = (e.innerText || '').trim();
    if (!/^画布 \d+$|^手册/.test(t) || t.length > 20) continue;
    const r = e.getBoundingClientRect();
    if (r.x < 100 || r.x > 500) continue;
    名.add(t);
  }
  return [...名];
});

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(主画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6000);
  await closePromos(page);
  await page.waitForTimeout(4000);

  // ① 打开下拉
  记('--- ① 打开下拉 ---');
  await page.mouse.click(200, 24);
  await page.waitForTimeout(1700);
  const 前 = await 数画布();
  记(`  建前 ${前.length} 项，最大编号 ${Math.max(...前.filter((x) => /^画布 \d+$/.test(x)).map((x) => +x.replace('画布 ', '')))}`);

  // ② 点加号 → 命名框
  记('\n--- ② 点加号，等命名框 ---');
  const 按钮 = await page.evaluate(() => {
    const b = document.querySelector('[aria-label="新建画布"]');
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  断言('找到加号', !!按钮, JSON.stringify(按钮));
  await page.mouse.click(按钮[0], 按钮[1]);
  await page.waitForTimeout(2000);

  // ③ 把命名框读全（这是本轮要弄清的东西）
  记('\n--- ③ 命名框逐字读全 ---');
  const 框 = await page.evaluate(() => {
    const o = { 弹窗: [], 输入: [], 按钮: [] };
    for (const d of document.querySelectorAll('[role="dialog"]')) {
      const t = (d.innerText || '').trim();
      o.弹窗.push({ 文: t, 框: (() => { const r = d.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() });
    }
    for (const i of document.querySelectorAll('input')) {
      const r = i.getBoundingClientRect();
      if (r.width < 4) continue;
      o.输入.push({ v: i.value, ph: i.placeholder, aria: i.getAttribute('aria-label'),
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
    }
    for (const b of document.querySelectorAll('[role="dialog"] button, [role="dialog"] [role="button"]')) {
      const r = b.getBoundingClientRect();
      if (r.width < 8) continue;
      o.按钮.push({ 文: (b.innerText || '').trim(), aria: b.getAttribute('aria-label'),
        disabled: b.disabled, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] });
    }
    return o;
  });
  R.读数.命名框 = 框;
  记(`  弹窗 ${框.弹窗.length} 个：${框.弹窗.map((d) => `「${d.文.replace(/\n/g, ' / ')}」@${d.框.join(',')}`).join(' ｜ ')}`);
  记(`  输入框：${JSON.stringify(框.输入)}`);
  记(`  按钮：${框.按钮.map((b) => `「${b.文}」aria=${b.aria} disabled=${b.disabled} @${b.框.join(',')}`).join(' ｜ ') || '（无）'}`);
  await page.screenshot({ path: resolve(EVID, 'fz2-1-命名框.png') });

  // ④ 点确定
  const 确认 = 框.按钮.find((b) => /^(确定|创建|确认|保存|完成)$/.test(b.文)) || 框.按钮.find((b) => !b.disabled && b.文);
  if (!确认) { 记('  ⛔ 命名框里没找到确认按钮，停下不猜'); }
  else {
    记(`\n--- ④ 点「${确认.文}」@${确认.中心.join(',')} ---`);
    await page.mouse.click(确认.中心[0], 确认.中心[1]);
    await page.waitForTimeout(6000);
    const URL = page.url();
    R.读数.新URL = URL;
    记(`  URL：${URL}`);
    断言('切到了新画布', URL !== 主画布, `${URL.slice(-40)}`);
    await page.screenshot({ path: resolve(EVID, 'fz2-2-建好之后.png') });

    // 等节点数稳定（缺陷 491）
    let 上 = -1, 稳 = 0;
    for (let i = 0; i < 20; i++) {
      const n = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
      if (n === 上) { 稳++; if (稳 >= 3) { 记(`  节点数稳定在 ${n}`); break; } } else 稳 = 0;
      上 = n; await page.waitForTimeout(1200);
    }
    await closePromos(page);
    await page.waitForTimeout(2500);

    // ⑤ 探引导
    记('\n--- ⑤ 新画布上探新手引导 ---');
    const G = await 探引导();
    R.读数.引导 = G;
    断言('新画布上出现引导', G.length > 0, G.length ? G.map((g) => `「${g.词}」@${g.x},${g.y} ${g.w}×${g.h}`).join(' / ') : '0 条');
    await page.screenshot({ path: resolve(EVID, 'fz2-3-新画布全屏.png') });
    if (G.length) {
      const 详情 = await page.evaluate(() => {
        const o = [];
        for (const e of document.querySelectorAll('*')) {
          const t = (e.innerText || '').trim();
          if (!/第\d\/4步|跟着做/.test(t)) continue;
          const r = e.getBoundingClientRect();
          if (r.width < 40) continue;
          o.push({ tag: e.tagName, cls: (e.className || '').toString().slice(0, 70),
            框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 文: t.slice(0, 140) });
        }
        return o;
      });
      R.读数.引导层 = 详情;
      详情.forEach((d) => 记(`   <${d.tag}> ${d.框.join(',')} cls=${d.cls}\n     文「${d.文}」`));
    }

    // ⑥ 建后下拉里多了几项
    记('\n--- ⑥ 建后下拉 ---');
    await page.mouse.click(200, 24);
    await page.waitForTimeout(1800);
    const 后 = await 数画布();
    R.读数.建后 = 后;
    记(`  建后 ${后.length} 项；新出现：${后.filter((x) => !前.includes(x)).join(' / ') || '（无）'}`);
    await page.screenshot({ path: resolve(EVID, 'fz2-4-建后下拉.png') });
  }
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFZ2.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
