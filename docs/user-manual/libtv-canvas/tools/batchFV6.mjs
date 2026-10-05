// ⭐⭐⭐⭐⭐ Batch FV-6：决定性实验 —— 节点标题上的 `{index}` 到底怎么来的
//
// 已知（FV-3 实拍 + FV-5 截图，两路互证）：
//     音频节点 1 ×2   文本节点 1 ×2   图片节点 2 ×2   视频节点 3 ×2
//     智能剪辑 4 ×1   导演台 5 ×1     逐帧拉片（无数字）  脚本 V2 1
//
// ⇒ **数字不唯一**（1 出现 5 次）⇒ 「画布全局递增」被排除（已实测，不是推断）。
//
// 三个候选解释，本轮逐个证伪/坐实：
//   H1「类型在添加节点面板里的序号」：文本1 图片2 视频3 智能剪辑4 导演台5
//       ⭐ 五个连号全中，**但音频该是 6/7 而实测是 1** ⇒ 需读面板实锤
//   H2「画布全局递增」：12 个节点该是 1~12 ⇒ **已被 FV-3 排除**
//   H3「复制节点沿用原节点的 index」：可解释「两个 X 都是同一个数」
//
// ⭐ 手册自己还留着一条**反证材料**（缺陷 462：先 grep 账本）：
//   `create-nodes.md` 记过 `音频节点 6` / `音频节点 7` / `视频节点 18` ——
//   而 6/7 正好落在 H1 算出的音频序号位置上 ⇒ 说明**编号会随时间变**。
//
// 决定性做法：**新建一个文本节点，看它拿到几号**。
//   - 拿到 2  ⇒ H1（类型内递增，之前两个「1」里有一个该是 2）
//   - 拿到 13 ⇒ H2（全局递增，但 FV-3 说不是，矛盾要解释）
//   - 拿到 6  ⇒ 独立编号流，H1/H2 都不对
//
// ⛔ 建节点不消耗积分（FQ-6 已实测：建完危险按钮 0 枚）。
// ⛔ 复原走**资产管理抽屉的「⋯ → 删除」菜单**（M-45 实测可用、无确认框），
//    绝不按 Delete / Backspace。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFV6.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

const 读全部标题 = () => page.evaluate(() => {
  const out = [];
  for (const el of document.querySelectorAll('.react-flow__node')) {
    const cls = [...el.classList].find((c) => c.startsWith('react-flow__node-')) || '';
    let 标题 = '';
    const b = el.getBoundingClientRect();
    for (const t of el.querySelectorAll('*')) {
      if (t.children.length) continue;
      const s = (t.textContent || '').trim();
      if (!s || s.length > 24) continue;
      const r = t.getBoundingClientRect();
      if (r.top < b.top + 44 && (!标题 || r.top < 标题.top)) 标题 = { 文: s, top: r.top };
    }
    out.push({ id: (el.getAttribute('data-id') || '').trim(),
      类型: cls.replace('react-flow__node-', ''), 标题: 标题 ? 标题.文 : '' });
  }
  return out;
});

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);

  // ── 0 关掉右侧抽屉与通知横幅（⛔ 绝不点「开启」按钮，只点 ×）
  const 关掉前 = await page.evaluate(() => ({
    抽屉: document.querySelectorAll('.mantine-Drawer-inner').length,
    横幅: [...document.querySelectorAll('*')].filter((e) => /开启浏览器通知/.test(e.innerText || '') && e.children.length === 0).length,
  }));
  记(`关掉前：抽屉 ${关掉前.抽屉} 个，通知横幅 ${关掉前.横幅} 个`);
  await page.evaluate(() => {
    for (const e of document.querySelectorAll('*')) {
      if (e.children.length) continue;
      if (e.getAttribute('aria-label') !== '关闭') continue;
      if (e.closest('.mantine-Drawer-inner') || /开启浏览器通知|最新消息/.test((e.closest('[class*="mantine"]')?.innerText) || '')) e.click();
    }
  });
  await page.waitForTimeout(900);
  const 关掉后 = await page.evaluate(() => document.querySelectorAll('.mantine-Drawer-inner').length);
  记(`关掉后：抽屉 ${关掉后} 个（DOM 计数，见缺陷 482：DOM 还在 ≠ 还挡着）`);

  // ── 1 基线
  const 基线 = await 读全部标题();
  R.读数.基线 = 基线;
  断言('基线读数自证', 基线.length === 12, `读到 ${基线.length} 个节点（预期 12）`);
  const 基线数 = new Set(基线.map((n) => n.标题).filter((t) => /\d+\s*$/.test(t)));
  记(`基线标题（去重后带数字的）：${[...基线数].join(' / ')}`);

  // ── 2 找底栏那枚 + 按钮（FV-5 截图指认：不是双击）
  const 加号 = await page.evaluate(() => {
    for (const b of document.querySelectorAll('button, [role="button"]')) {
      const r = b.getBoundingClientRect();
      if (r.y < 760 || r.y > 810) continue;
      if (Math.abs(r.width - 34) > 12 || Math.abs(r.height - 34) > 12) continue;
      if (b.querySelector('svg') && !(b.innerText || '').trim()) {
        return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
          cls: b.className.slice(0, 90), 底栏内: !!b.closest('[class*="absolute"][class*="bottom"]') };
      }
    }
    return null;
  });
  R.读数.加号 = 加号;
  if (!加号) { 记('⛔ 底栏没找到 + 按钮，放弃'); }
  else {
    记(`底栏 + 按钮 @${加号.x},${加号.y} ${加号.w}×${加号.h}`);
    // ⭐ 自证：点之前先确认这个点上 elementFromPoint 确实是它
    const 落点 = await page.evaluate(({ x, y }) => {
      const e = document.elementFromPoint(x + 17, y + 17);
      return e ? { tag: e.tagName, cls: (e.className || '').slice(0, 70) } : null;
    }, 加号);
    R.读数.加号落点 = 落点;
    断言('+ 按钮落点自证', !!落点, `elementFromPoint 命中 ${落点?.tag} ${落点?.cls}`);

    await page.mouse.click(加号.x + 17, 加号.y + 17);
    await page.waitForTimeout(1300);
    await page.screenshot({ path: resolve(EVID, 'fv6-1-点加号之后.png') });

    const 面板 = await page.evaluate(() => {
      const out = [];
      for (const el of document.querySelectorAll('body *')) {
        const s = (el.innerText || '').trim();
        if (!s || s.length > 20) continue;
        const r = el.getBoundingClientRect();
        if (r.width < 30 || r.height < 12) continue;
        if (!/^(文本|图片|视频|智能剪辑|导演台|逐帧拉片|音频|脚本|素材库|全部)/.test(s)) continue;
        out.push({ 文字: s, y: Math.round(r.y), x: Math.round(r.x) });
      }
      const seen = new Map();
      for (const o of out) if (!seen.has(o.y) || seen.get(o.y).文字.length < o.文字.length) seen.set(o.y, o);
      return [...seen.values()].sort((a, b) => a.y - b.y);
    });
    R.读数.面板 = 面板;
    断言('面板真的打开了', 面板.length > 0, `读到 ${面板.length} 行（FV-4 就是这里假绿灯的）`);
    记('\n添加节点面板（按 y 排序）：');
    面板.forEach((p, i) => 记(`   ${i + 1}. \`${p.文字}\` @y=${p.y}`));
    const 名 = 面板.map((p) => p.文字.replace(/[A-Za-z]*$/, '').trim());
    记(`\n面板顺序：${名.join(' → ')}`);
    记(`H1 预测：文本${名.indexOf('文本') + 1} 图片${名.indexOf('图片') + 1} 视频${名.indexOf('视频') + 1} 智能剪辑${名.indexOf('智能剪辑') + 1} 导演台${名.indexOf('导演台') + 1} 音频${名.indexOf('音频') + 1}`);
    记(`H1 实测：文本1 图片2 视频3 智能剪辑4 导演台5 音频1`);

    await page.keyboard.press('Escape');
    await page.waitForTimeout(700);
  }
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFV6.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
