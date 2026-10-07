/**
 * 批次 281：「点不动」到底是**被挡住**，还是**应用自己不响应**？
 *
 * 📌 起意（批次 280 留下的第一条尾巴）：
 *   280 已钉死阈值 `H ≥ 249` 生效 / `H ≤ 248` 点不动，并排除了三件事：
 *   **不是时序**（连点两遍，中间隔 5 秒，没有一臂是第二遍才生效）、
 *   **不是几何**（结果行在 `H=241…250` 上逐字相同：`304×64`、顶 `152`、底 `216`、中心 `[168,184]`）、
 *   **不是搜不到**（`H=180/200/220` 上结果数都是 `1`）。
 *   ⇒ 剩下两种解释，**用户看到的现象一样，但处置办法完全不同**：
 *     H1 **被挡住**（有东西盖在结果行上 / `pointer-events` 被关掉 / 命中测试落到别的元素上）
 *     H2 **应用自己不响应**（命中测试落在结果行上，应用收到事件后拒绝执行）
 *
 * 📌 **怎么分开**（三个互相独立的探针）：
 *   探针① **`document.elementFromPoint(行中心)`** —— 命中测试到底落在谁身上？
 *          落在别的元素 ⇒ H1；落在结果行本身 ⇒ 不是遮挡。
 *   探针② **样式三连**：`pointer-events` / `visibility` / `display`，外加行与面板的 `z-index`。
 *   探针③ 🔴 **程序化点击** `元素.click()` —— 它**绕过命中测试**、直接派发事件。
 *          🔴 **这一步是关键**：鼠标点不行而 `element.click()` 行 ⇒ 一定是命中/遮挡问题（H1）；
 *          **两者都不行 ⇒ 应用收到了事件却不执行**（H2）。
 *
 * 📌 **预测先写死**（立规 129/130）：
 *   P1 **H1 被挡住**：探针① 在 `H ≤ 248` 时返回的**不是**结果行；
 *   P2 **H2 应用拒绝**：探针① 在所有高度都返回结果行，探针③ 的程序化点击**在 `H ≥ 249` 成功、`H ≤ 248` 仍失败**。
 *   🔴 **P1 与 P2 的处置完全不同**：P1 可以建议用户换个点法；P2 只能建议「把窗口拉高」。
 *
 * 📌 **三条前提**：
 *   ① **轴向自检**：`innerW/innerH` 逐字等于设定值；
 *   ② **命中测试的自检**：在 `H ≥ 249`（已知生效）上探针①必须返回结果行 ——
 *      否则「探针① 在 `H ≤ 248` 返回别的东西」这句话没有意义（判据本身在正例上要会响，立规 160）；
 *   ③ **程序化点击的自检**：同 ②，程序化点击必须在 `H ≥ 249` 上成功过一次。
 *
 * 📌 **纪律**：只读（不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**）；
 *   每臂开新页；末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b281.mjs      （落盘 /tmp/b281.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B281_OUT || '/tmp/b281.json';
const 宽 = 460;
const 高度组 = [246, 247, 248, 249, 250, 252];
const 节点 = { id: 'node_236ctpehgg', 名: '视频 1', 备用名: ['视频 1', '视频'] };

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b281',
  问: '「点不动」是被挡住，还是应用自己不响应？',
  预测: {
    P1_H1_被挡住: '命中测试在 H≤248 时返回的不是结果行',
    P2_H2_应用拒绝: '命中测试在所有高度都返回结果行；程序化点击在 H≥249 成功、H≤248 仍失败',
  },
  宽, 高度组, 节点, 臂: [], 收尾: {},
};

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 读选中 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));

for (const 高 of 高度组) {
  const p = await ctx.newPage();
  const 记 = { 高, 宽 };
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);

    // 前提①：轴向自检
    const 实际 = await p.evaluate(() => ({ w: window.innerWidth, h: window.innerHeight }));
    if (实际.w !== 宽 || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${宽}×${高}，实测 ${实际.w}×${实际.h}`);
    记.实际视口 = 实际;

    // 开面板 + 找结果行
    const 钮 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('button, [role="button"]')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 在视口内: r.y >= 0 && r.bottom <= innerHeight };
    });
    if (!钮 || !钮.在视口内) throw new Error('搜索钮不在视口内');
    await p.mouse.click(钮.中心[0], 钮.中心[1]);
    await p.waitForTimeout(1600);
    if (!await p.evaluate(() => !!document.querySelector('[data-testid="canvas-search-panel"]'))) throw new Error('搜索面板没打开');

    const 短名 = 节点.id.replace(/^node_/, '');
    let 行 = null;
    for (const 名 of 节点.备用名) {
      await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
      await p.keyboard.type(名, { delay: 80 });
      await p.waitForTimeout(2000);
      行 = await p.evaluate((nid) => {
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 盒: [Math.round(r.width), Math.round(r.height)], 顶: Math.round(r.y), 底: Math.round(r.bottom) };
      }, 短名);
      if (行) break;
    }
    if (!行) throw new Error('搜不到结果行');
    记.行 = 行;

    // 探针①：命中测试落在谁身上（连同它整条祖先链上的 testid）
    记.探针1_命中测试 = await p.evaluate(({ x, y, nid }) => {
      const el = document.elementFromPoint(x, y);
      const 描述 = (e) => {
        if (!e) return null;
        const t = e.getAttribute('data-testid');
        return {
          tag: e.tagName,
          testid: t || null,
          aria: e.getAttribute('aria-label') || null,
          role: e.getAttribute('role') || null,
          是结果行: (t || '') === `canvas-search-result-node_${nid}`,
        };
      };
      const 链 = [];
      for (let e = el; e && 链.length < 6; e = e.parentElement) 链.push(描述(e));
      return { 命中: 描述(el), 祖先链: 链 };
    }, { x: 行.中心[0], y: 行.中心[1], nid: 短名 });

    // 探针②：样式三连 + z-index
    记.探针2_样式 = await p.evaluate((nid) => {
      const row = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
      const pn = document.querySelector('[data-testid="canvas-search-panel"]');
      const 取 = (e) => {
        if (!e) return null;
        const cs = getComputedStyle(e);
        return { pointerEvents: cs.pointerEvents, visibility: cs.visibility, display: cs.display, zIndex: cs.zIndex, position: cs.position };
      };
      return { 行: 取(row), 面板: 取(pn), body: 取(document.body) };
    }, 短名);

    // 先做一次「鼠标点击」，记录结果（批次 280 的结论作对照）
    await p.mouse.click(行.中心[0], 行.中心[1]);
    await p.waitForTimeout(5000);
    记.鼠标点击后选中 = await 读选中(p);

    // 探针③：程序化点击（绕过命中测试）
    // 🔴 先确认结果行还在（面板可能已被关掉）
    const 还在 = await p.evaluate((nid) => !!document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`), 短名);
    记.程序化点击前行还在 = 还在;
    if (还在) {
      记.程序化点击已派发 = await p.evaluate((nid) => {
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
        if (!e) return false;
        e.click();          // 绕过命中测试，直接派发
        return true;
      }, 短名);
      await p.waitForTimeout(5000);
      记.程序化点击后选中 = await 读选中(p);
    } else {
      // 面板已被关掉 ⇒ 重开再试
      await p.keyboard.press('Escape'); await p.waitForTimeout(700);
      await p.keyboard.press('Escape'); await p.waitForTimeout(900);
      const 钮2 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('button, [role="button"]')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 在视口内: r.y >= 0 && r.bottom <= innerHeight };
      });
      if (钮2?.在视口内) {
        await p.mouse.click(钮2.中心[0], 钮2.中心[1]);
        await p.waitForTimeout(1600);
        await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
        await p.keyboard.type(节点.名, { delay: 80 });
        await p.waitForTimeout(2200);
        记.程序化点击已派发 = await p.evaluate((nid) => {
          const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
          if (!e) return false;
          e.click();
          return true;
        }, 短名);
        await p.waitForTimeout(5000);
        记.程序化点击后选中 = await 读选中(p);
      }
    }

    记.鼠标点击生效 = (记.鼠标点击后选中 || []).includes(节点.id);
    记.程序化点击生效 = (记.程序化点击后选中 || []).includes(节点.id);
    记.命中测试落在结果行 = 记.探针1_命中测试?.命中?.是结果行 === true;
    log(`H=${高}｜行中心 [${行.中心}]｜命中测试落在结果行 ${记.命中测试落在结果行 ? '✅' : '🔴 落在 ' + (记.探针1_命中测试?.命中?.tag + '/' + (记.探针1_命中测试?.命中?.testid || '无 testid'))}`);
    log(`    行样式 pointerEvents=${记.探针2_样式?.行?.pointerEvents} visibility=${记.探针2_样式?.行?.visibility} zIndex=${记.探针2_样式?.行?.zIndex}｜面板 zIndex=${记.探针2_样式?.面板?.zIndex}`);
    log(`    鼠标点击生效 ${记.鼠标点击生效 ? '✅' : '🔴'}｜程序化点击 ${记.程序化点击已派发 ? '已派发' : '未派发'}、生效 ${记.程序化点击生效 ? '✅' : '🔴'}`);
  } catch (e) { 记.错误 = e.message; log(`H=${高} 🔴 ${e.message}`); }
  finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ═══ 判定 ═══
const 生效H = out.臂.filter((a) => a.鼠标点击生效).map((a) => a.高);
const 不生效H = out.臂.filter((a) => a.鼠标点击生效 === false).map((a) => a.高);
const 命中行H = out.臂.filter((a) => a.命中测试落在结果行).map((a) => a.高);
const 命中别物H = out.臂.filter((a) => a.命中测试落在结果行 === false).map((a) => a.高);
const 程序化生效H = out.臂.filter((a) => a.程序化点击生效).map((a) => a.高);
const 报错H = out.臂.filter((a) => a.错误).map((a) => a.高);

out.判定 = {
  鼠标点击生效的高度: 生效H, 鼠标点击不生效的高度: 不生效H,
  命中测试落在结果行的高度: 命中行H, 命中测试落在别处的高度: 命中别物H,
  程序化点击生效的高度: 程序化生效H, 报错的高度: 报错H,
  结论: 报错H.length
    ? `🔴 ${JSON.stringify(报错H)} 报错，无法判定`
    : 命中别物H.length
      ? `P1 ✅ H1「被挡住」：${JSON.stringify(命中别物H)} 的命中测试没落在结果行上`
      : 程序化生效H.length && 程序化生效H.length !== 生效H.length
        ? `P2 ✅ H2「应用拒绝」：命中测试在所有高度都落在结果行；程序化点击在 ${JSON.stringify(程序化生效H)} 生效，在 ${JSON.stringify(生效H.filter((h) => !程序化生效H.includes(h)))} 仍失败`
        : '🔴 三种探针给出互相矛盾的结果，需要再看原始读数',
};
log(`\n════ 判定 ════\n${out.判定.结论}`);
log(`鼠标点击生效：${JSON.stringify(生效H)}\n鼠标点击不生效：${JSON.stringify(不生效H)}`);
log(`命中落在结果行：${JSON.stringify(命中行H)}\n命中落在别处：${JSON.stringify(命中别物H)}`);
log(`程序化点击生效：${JSON.stringify(程序化生效H)}\n报错：${JSON.stringify(报错H)}`);

// 末态独立复查（立规 140）
{
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 1280, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    out.收尾.节点数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    out.收尾.状态行 = await p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
    out.收尾.通过 = out.收尾.节点数 === 76 && /0 selected/.test(out.收尾.状态行 || '');
    log(`\n末态独立复查：节点 ${out.收尾.节点数}｜${out.收尾.状态行} ⇒ ${out.收尾.通过 ? '✅' : '🔴'}`);
  } catch (e) { out.收尾.错误 = e.message; } finally { try { await p.close(); } catch (e) { /* 忽略 */ } }
}

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`\n写入 ${OUT}`);
process.exit(0);