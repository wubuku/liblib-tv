/**
 * 批次 263 · 收尾专用：**把批次 263 留下的那个主体节点删掉**，让画布回到 `76`。
 *
 * 📌 **为什么单独一个脚本**：`b263` 的收尾用「搜索定位 → 选中 → 按 ⌫」，
 *   结果 **`⌫` 与 `⌘Z` 都没删掉**，画布停在 **`77` 个节点**。
 *   🔴 而这**正是本手册自己写下的坑** ——
 *   `10-tasks/duplicate-delete-history.md:175` 逐字写着
 *   「**从「搜索」面板选中的节点，按 ⌫ 删不掉**」，
 *   修法在 `:198`「**点一下节点的标题行把焦点交回画布，再按 ⌫**」。
 *   ⇒ `b263` 走的**恰好是被警告的那一条路**。📌 立规 141：动手前先查手册有没有写过这个坑。
 *
 * 📌 本脚本按 `:198` 记载的路径走，并把**每一步的 `activeElement`** 读出来，
 *   顺便**验证那条手册警告现在还成立**（它是用户面的排障条目，值得复验）。
 *
 * 🔴 纪律：只删除**这一个**本批新建的主体节点；不碰其他 `76` 个；
 *   不触发生成、不进扣费页、不点「保存到主体库」、不分享。
 *
 * 用法：node scripts/jimeng-b263-clean.mjs      （读数落盘 /tmp/b263-clean.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B263C_OUT || '/tmp/b263-clean.json';
const 宽 = 1280, 高 = 720;

const log = (...a) => console.log(a.join(' '));

const 状态 = () => ({
  选中: (() => { const m = document.body.innerText.match(/(\d+) nodes, \d+ edges, (\d+) selected/); return m ? Number(m[2]) : null; })(),
  个数: document.querySelectorAll('.react-flow__node').length,
  主体: Array.from(document.querySelectorAll('.react-flow__node'))
    .filter((n) => (n.getAttribute('aria-label') || '').startsWith('主体'))
    .map((n) => n.getAttribute('data-id')),
  焦点: (() => {
    const a = document.activeElement;
    if (!a) return null;
    return {
      tag: a.tagName.toLowerCase(),
      testid: a.getAttribute('data-testid'),
      aria: a.getAttribute('aria-label'),
      type: a.getAttribute('type'),
      cls: (typeof a.className === 'string' ? a.className : '').slice(0, 60),
    };
  })(),
});

const out = { 轮次: 'b263-收尾', 步: [], 结果: null };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();
const 记 = (名, s) => { out.步.push({ 步: 名, ...s }); fs.writeFileSync(OUT, JSON.stringify(out, null, 1)); log(`【${名}】${JSON.stringify(s)}`); };

try {
  await p.setViewportSize({ width: 宽, height: 高 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(7000);

  记('起始', await p.evaluate(状态));
  const 主体id = await p.evaluate(() => {
    const n = Array.from(document.querySelectorAll('.react-flow__node'))
      .find((x) => (x.getAttribute('aria-label') || '').startsWith('主体'));
    return n ? n.getAttribute('data-id') : null;
  });
  if (!主体id) {
    out.结果 = '画布上已经没有主体节点 ⇒ 无需收拾';
    log('✅ ' + out.结果);
  } else {
    out.主体id = 主体id;
    log(`待删主体节点：${主体id}`);

    // 🔴 先 `适配画布`，保证它在视口里可点
    const 钮 = await p.evaluate(() => {
      const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
      const r = z.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    });
    await p.mouse.click(钮[0], 钮[1]);
    await p.waitForTimeout(1200);
    const 适位 = await p.evaluate(() => {
      const 面 = document.querySelector('[data-testid="canvas-zoom-menu"]');
      const e = Array.from(面.querySelectorAll('div,button')).find((x) => (x.innerText || '').trim().startsWith('适配画布'));
      const r = e.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    });
    await p.mouse.click(适位[0], 适位[1]);
    await p.waitForTimeout(2200);
    记('适配画布后', await p.evaluate(状态));

    // 📌 **`:198` 记载的修法**：点一下节点的**标题行**把焦点交回画布
    const 位置 = await p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      if (!n) return null;
      const b = n.getBoundingClientRect();
      return { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height) };
    }, 主体id);
    if (!位置) throw new Error('找不到那个主体节点');
    log(`节点视口位置：${JSON.stringify(位置)}`);
    // 📌 标题行 = 节点盒子的**上缘**那一小条
    await p.mouse.click(位置.x + Math.round(位置.w / 2), 位置.y + 8);
    await p.waitForTimeout(1500);
    记('点标题行后', await p.evaluate(状态));

    // 📌 按 Backspace（不是 Delete —— 手册 :167 明确不可互换）
    await p.keyboard.press('Backspace');
    await p.waitForTimeout(2500);
    记('按 Backspace 后', await p.evaluate(状态));

    // 📌 若还不行，走右键菜单里的「删除 ⌫」（手册 :112 记它是可靠路径之一）
    let s = await p.evaluate(状态);
    if (s.个数 !== 76) {
      log('⚠️ Backspace 没删掉，走右键菜单');
      await p.mouse.click(位置.x + Math.round(位置.w / 2), 位置.y + 8, { button: 'right' });
      await p.waitForTimeout(1500);
      const 删项 = await p.evaluate(() => {
        const 面 = document.querySelector('[data-testid="canvas-context-menu"]');
        if (!面) return null;
        const e = Array.from(面.querySelectorAll('div,button,[role="menuitem"]'))
          .find((x) => (x.innerText || '').trim().startsWith('删除'));
        if (!e) return { 找到菜单: true, 有删除项: false, 全部: (面.innerText || '').slice(0, 120) };
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      });
      记('右键菜单', { 删项 });
      if (Array.isArray(删项)) {
        await p.mouse.click(删项[0], 删项[1]);
        await p.waitForTimeout(2500);
        记('右键删除后', await p.evaluate(状态));
      }
    }

    s = await p.evaluate(状态);
    out.结果 = s.个数 === 76 ? '✅ 已回到 76' : `🔴 仍是 ${s.个数} 个`;
    log(out.结果);
  }
} catch (e) {
  out.错误 = e.message;
  log('🔴 ' + e.message);
} finally {
  try { await p.close(); } catch (e) { /* 忽略 */ }
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  log('写入 ' + OUT);
}
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);