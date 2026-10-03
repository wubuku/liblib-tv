// Batch DT-4：只 hover、不点击，一次拿到两样东西。
//
// ⛔ DT-2 / DT-3 为什么连着失败（都栽在「要开浮层」这条路上）：
//   DT-2：一屏一屏滚 + 读视口卡名定位 ⇒ 滚动后 DOM 里的短文本**对不上接口映射**
//          （虚拟滚动回收重建，112 → 35 个名字全变），只测到 1 张。
//   DT-3：改用搜索框定位（对的方向）⇒ 点的那枚 button **不是 ⤢ 详情按钮**，
//          浮层没出现；随后广场状态被带偏，第二个卡连搜索框都找不到了。
//   ⇒ **开浮层这条路对「连续多张卡」不稳定**，不划算。
//
// ⭐ 本轮换目标（对读者更有价值，且**零风险：只 hover，绝不点击**）：
//   ① **卡面左上角模型徽标的模型名并集** —— 手册 M-346 记过「徽标带文字、
//      悬停出气泡，气泡文字就是模型名」，但**从没系统读过一遍**。
//   ② ⭐ **`当前使用`（currentlyInUse）的界面实测** —— 它在 i18n 表里一直标 ⛔，
//      源码上它有**两个**渲染点：
//        · 卡面一枚**白底黑字**徽标（`bg-white` + `CurrentUseCheck` 图标 + 黑字）
//        · 「全部适配模型」下拉里**当前那一行右侧的对勾**（带同一个 tooltip）
//      两者都是纯展示，**hover 就能读到**。
//
// ⛔ 安全边界：全程只 `mouse.move`，**不 click、不 fill、不 press**（末页除外）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 只读: true, 徽标: [], 模型并集: [], 下拉: [], 命中: null };
const SAVE = () => writeFileSync(new URL('./batchDT4.json', import.meta.url), JSON.stringify(out, null, 2));

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
await page.waitForTimeout(1500);
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2800);
for (let i = 0; i < 3; i += 1) {
  const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(600);
}
const pk = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
  if (!b) return null; const r = b.getBoundingClientRect();
  return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
});
if (pk) { await page.mouse.click(pk[0], pk[1]); await page.waitForTimeout(1200); }
await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(5000);
const 分类 = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].filter((x) => /^(推荐|平面设计|风格插画|文创周边)$/.test((x.innerText || '').trim()));
  const on = b.filter((x) => { const c = getComputedStyle(x).backgroundColor; return c && c !== 'rgba(0, 0, 0, 0)'; });
  return on.length ? (on[0].innerText || '').trim() : '?';
});
LOG(`当前分类: ${分类}`);
out.分类 = 分类;

// ---- 枚举首屏所有卡片 ----
const 卡片 = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width >= 150 && r.width <= 340 && r.height >= 180 && r.height <= 460 && s.visibility !== 'hidden'; };
  // 卡片 = 满足尺寸、且内部含一个 <img> 或背景图的容器；用「内部有 2 个以上可点元素」筛
  const 全 = [...document.querySelectorAll('div')].filter(vis);
  const seen = new Set(); const 卡 = [];
  for (const e of 全) {
    const r = e.getBoundingClientRect();
    // 卡片的特征：内部有 button，且自身文本不多
    const btns = e.querySelectorAll('button').length;
    if (btns < 2) continue;
    if (e.parentElement && seen.has(e.parentElement)) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (t.length > 120) continue;
    seen.add(e);
    卡.push({ 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 尺寸: [Math.round(r.width), Math.round(r.height)], 文本: t.slice(0, 60), button数: btns });
  }
  return 卡;
});
LOG(`首屏识别到 ${卡片.length} 张卡片`);
out.卡片数 = 卡片.length;

// ---- 逐张 hover，读左上角徽标 ----
for (const [i, c] of 卡片.entries()) {
  await page.mouse.move(c.中心[0], c.中心[1]);
  await page.waitForTimeout(650);
  const 读 = await page.evaluate((盒) => {
    // ⛔ DT-4 第一版用「距卡片中心 ±40」找徽标 ⇒ 0 枚（坐标系搞错了，徽标在卡片**左上角**）。
    //   正解：**先定位卡片盒子**，再在盒子内部找 button。
    const 卡 = [...document.querySelectorAll('div')].find((e) => {
      const r = e.getBoundingClientRect();
      return Math.abs((r.x + r.width / 2) - 盒[0]) < 4 && Math.abs((r.y + r.height / 2) - 盒[1]) < 4
        && r.width >= 150 && r.width <= 340 && r.height >= 180 && r.height <= 460;
    });
    if (!卡) return { 有徽标: false, 原因: '找不到卡片盒子' };
    const 徽 = [...卡.querySelectorAll('button')].filter((b) => {
      const r = b.getBoundingClientRect();
      return r.width >= 18 && r.width <= 40 && r.height >= 18 && r.height <= 40;
    });
    if (!徽.length) return { 有徽标: false, 卡内button数: 卡.querySelectorAll('button').length };
    return 徽.map((b) => {
      const img = b.querySelector('img');
      const r = b.getBoundingClientRect();
      return {
        aria: b.getAttribute('aria-label') || '', title: b.getAttribute('title') || '',
        文字: (b.innerText || '').replace(/\s+/g, ' ').trim(),
        imgAlt: img ? img.getAttribute('alt') : null,
        尺寸: [Math.round(r.width), Math.round(r.height)],
        html: (b.innerHTML || '').slice(0, 160),
      };
    });
  }, c.中心);
  if (读.length) {
    for (const m of 读) {
      const 名 = m.文字 || m.imgAlt || '';
      out.徽标.push({ 卡: i, 卡文本: c.文本, 名, aria: m.aria, title: m.title, imgAlt: m.imgAlt, 尺寸: m.尺寸 });
      if (名) out.模型并集.push(名);
    }
  }
  if ((i + 1) % 10 === 0) LOG(`  已扫 ${i + 1} 张，累计徽标 ${out.徽标.length} 枚`);
}
out.模型并集 = [...new Set(out.模型并集)];
LOG(`\n⭐ 徽标枚数 ${out.徽标.length} / 模型名并集 ${out.模型并集.length} 个: ${JSON.stringify(out.模型并集)}`);

// ---- ⭐ 第二目标：找「✧」入口，hover 出「全部适配模型」下拉，读 `当前使用` ----
// ✧ 入口的源码特征：24×24 button、无文字无 aria/title。hover 才显形。
const 找X = async () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0.3; };
  const 全部 = [...document.querySelectorAll('button')].filter((b) => {
    const r = b.getBoundingClientRect();
    return r.width >= 22 && r.width <= 26 && r.height >= 22 && r.height <= 26 && (b.innerText || '').trim() === '' && !b.getAttribute('aria-label') && !b.getAttribute('title') && !b.querySelector('img');
  });
  return 全部.map((b) => { const r = b.getBoundingClientRect(); return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 位置: [Math.round(r.x), Math.round(r.y)] }; });
});
const Xs = await 找X();
LOG(`\n「✧」形候选（24×24 无字无 aria 的 button）: ${Xs.length} 个`);
out.找到X = Xs.length;
for (const [i, x] of Xs.slice(0, 6).entries()) {
  await page.mouse.move(x.中心[0], x.中心[1]);
  await page.waitForTimeout(1400);
  const 下拉 = await page.evaluate(() => {
    const 浮 = [...document.querySelectorAll('div')].filter((e) => {
      const t = (e.innerText || '').replace(/\s+/g, ' ');
      const s = getComputedStyle(e);
      return /全部适配模型/.test(t) && t.length < 200 && s.visibility !== 'hidden' && +s.opacity > 0.5;
    });
    if (!浮.length) return null;
    // ⭐⭐ DT-4 第一版挑「innerText 最短」的那个 ⇒ 挑中了**标题 div 本身**，
    //   读出来只有「全部适配模型」，而截图里明明有 General image V2 / General image Pro 两行。
    //   ⇒ 正解：**挑最大的那个**（含标题 + 全部模型行）。
    const 详 = 浮.sort((a, b) => (b.innerText || '').length - (a.innerText || '').length)[0];
    const 行 = [...详.querySelectorAll('div')].filter((e) => (e.innerText || '').replace(/\s+/g, ' ').trim() && e.children.length === 0)
      .map((e) => { const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return { 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), x: Math.round(r.x), y: Math.round(r.y), 颜色: c.color }; });
    return { 全文: (详.innerText || '').replace(/\n+/g, ' | '), 行 };
  });
  if (下拉) {
    out.下拉.push(下拉);
    LOG(`  第 ${i + 1} 个 ✧ 悬停出下拉: ${下拉.全文}`);
    LOG(`     ⭐ 含「当前使用」? ${/当前使用/.test(下拉.全文) ? '✅ 有' : '⛔ 没有'}`);
    if (i === 0) { await shot(page, 'DT-a-全部适配模型下拉.png'); LOG('     📸 DT-a'); }
  } else {
    LOG(`  第 ${i + 1} 个 ✧ 悬停没出下拉`);
  }
}
out.命中 = { 下拉几次: out.下拉.length, 有当前使用: out.下拉.filter((d) => /当前使用/.test(d.全文)).length };
LOG(`\n══════ 汇总 ══════`);
LOG(`  下拉出现 ${out.命中.下拉几次} 次，其中含「当前使用」的 ${out.命中.有当前使用} 次`);
out.最终节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDT4.json ===');
