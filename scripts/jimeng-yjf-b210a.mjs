// 会话 mvs_fb62b78 · 批次 210 a 轮：在 1200~1280 之间密集取点，钉出「取景后 ty」那个断点的确切位置。
//
// ⚠️ 文件名带 yjf 前缀是**为了不和别的会话撞名**：本仓库同时有 3 个会话在写这一本手册
//   （批次 165~203 / 288 / 1005）。批次 201 已经记过一次「我明明关掉了怎么还在」，
//   同一个病在**协作面**上复发了一次：我曾用 write 工具覆盖掉别人已提交的
//   `scripts/jimeng-b202a.mjs`。⇒ 立规 81（见 PROGRESS）：
//   **写任何文件之前先确认它不属于别人**（`git log -- <path>` + `ls`），
//   文件名带上本会话唯一的标识，绝不复用别人批次里的序号。
//
// 靶子（批次 200 PROGRESS 明写「⚠️ 仍未测 · 断点的确切位置」）：
//   批次 200 把 ty 拟合成 ty ≈ 0.504 × 视口高 + C，发现 C 分成两支：
//     1000 / 1200 宽 → C = −407.435（两档逐字相同）
//     1280×3 档 + 1600 → C = −508 那一支
//   ⇒ 断点落在 1200 与 1280 之间，但只知道区间。
//
// 本轮设计（逐条对着已经吃过的亏）：
//  ① **一个页签复用**（批次 199：只开一个页签并复用 ⇒ 共享页签跑前跑后都未被污染；
//     批次 201：逐档 ctx.newPage() 会往屏幕上蹦标签）。所以这里**只 newPage 一次**。
//  ② 🔴 **臂有效性断言**（立规 78）：点之前必须读得到那一行；读不到就写成
//     `{ 无效: 原因 }` 显式字段，**不参与统计**，收尾**把无效臂条数一并报出**。
//  ③ **6 帧去重**（立规 76）：最后一帧有可能落在取景动画的中间态上 ⇒ 只读去重后的值。
//  ④ **固定 testid**（批次 200）：固定对象，排除「点的对象变了」这个变量。
//  ⑤ **不按 Esc 清场**（批次 200 a 轮 18 臂全废的根因）：Esc 只在**每臂开头**用来清场，
//     点完结果行之后**一个键都不按**，连采 6 帧。
//  ⑥ **读数的那一刻顺手读缩放**（立规 33）。
//  ⑦ **每臂 finally 落盘**：崩了也不丢先前的读数。
//
// ⚠️ 本轮测的量是**取景之后**的 ty（批次 200 的口径），
//    不是批次 199 测过的**初始** translate（立规 79：否证的对象和现象不是一回事）。
import fs from 'node:fs';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 搜索词 = '音频';
const 目标 = 'canvas-search-result-node_tadm1nyykc';
const H = 720;
// 密集取点：1190~1290 步长 10，两侧各留一档当护栏
const 宽度集 = [1190, 1200, 1210, 1220, 1230, 1240, 1250, 1260, 1270, 1280, 1290];
const log = (...a) => console.log(a.join(' '));
const OUT = '/tmp/b210a.json';
const out = {
  轮次: 'b210a', 测的量: '取景之后的 .react-flow__viewport translate/ty',
  口径警示: '与批次 199 测的「初始 translate」不是同一个量（立规 79）',
  目标testid: 目标, 高度固定: H, 宽度集, 无效臂: 0, 档: {},
};

const { chromium } = await import('playwright');
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const 共享页 = ctx.pages().find((x) => x.url().includes('ai-canvas'));
if (!共享页) throw new Error('找不到共享画布页');
out.共享页_前 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);
log('共享页跑前：', JSON.stringify(out.共享页_前));

// 🔵 只开一个页签，全部臂复用它（批次 199 的做法）
const p = await ctx.newPage();
try {
  await p.setViewportSize({ width: 1280, height: H });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(4500);

  for (const w of 宽度集) {
    try {
      // ① 改宽度 → 等布局稳定
      await p.setViewportSize({ width: w, height: H });
      await p.waitForTimeout(1800);

      // ② 清场只在这一步按 Esc（点完结果行之后绝不按 —— 批次 200 a 轮 18 臂全废于此）
      await p.keyboard.press('Escape');
      await p.waitForTimeout(400);

      // ③ 打开搜索并输入
      const 搜索钮 = await p.evaluate(() => {
        const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
          || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      });
      if (!搜索钮) { out.档[w] = { 无效: '找不到搜索钮' }; out.无效臂++; log(w, '⛔ 无效臂：找不到搜索钮'); continue; }
      await p.mouse.click(搜索钮[0], 搜索钮[1]);
      await p.waitForTimeout(1200);
      await p.evaluate(() => {
        const e = document.querySelector('input[aria-label*="搜索"],input[type="text"]');
        if (e) {
          Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(e, '');
          e.dispatchEvent(new Event('input', { bubbles: true }));
        }
      });
      await p.keyboard.type(搜索词, { delay: 90 });
      await p.waitForTimeout(2000);

      // ④ 臂有效性断言（立规 78）：点之前必须读得到目标行
      const 前置 = await p.evaluate((tid) => {
        const e = document.querySelector(`[data-testid="${tid}"]`);
        if (!e) {
          return { 存在: false, 现存前5: Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).slice(0, 5).map((x) => x.getAttribute('data-testid')) };
        }
        const r = e.getBoundingClientRect();
        return {
          存在: true,
          点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
          aria: e.getAttribute('aria-label'),
          总条数: document.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length,
        };
      }, 目标);
      if (!前置.存在) {
        out.档[w] = { 无效: '目标行不在这一页', 前置 };
        out.无效臂++;
        log(w, '⛔ 无效臂：目标行不在（现存前5 =', JSON.stringify(前置.现存前5) + '）');
        continue;
      }

      // 点之前先确认**画布上那个节点元素真的在**（第一版漏了这步 ⇒ 点了个寂寞还照样出数）
      const 节点前置 = await p.evaluate((tid) => {
        const id = tid.replace('canvas-search-result-node_', 'node_');
        return { 目标id: id, 节点在: !!document.querySelector(`.react-flow__node[data-id="${id}"]`) };
      }, 目标);
      if (!节点前置.节点在) {
        out.档[w] = { 无效: '画布上找不到目标节点元素', 前置, 节点前置 };
        out.无效臂++;
        log(w, '⛔ 无效臂：画布上找不到', 节点前置.目标id);
        continue;
      }

      // ⑤ 点目标行 → 连采 6 帧（不按任何键）
      await p.mouse.click(前置.点[0], 前置.点[1]);
      const 帧 = [];
      for (let k = 0; k < 6; k++) {
        帧.push(await p.evaluate((tid) => {
          // 🔴 第一版这里写成 'canvas-search-result-node-node_' —— 那个前缀**根本不存在**
          //   （真实前缀是 'canvas-search-result-node_'）⇒ 11 臂的读数**全是 null**，
          //   而「去重后只剩 1 个值」这条断言在 `[null]` 上**照样通过**。
          //   ⇒ 立规 82（见 PROGRESS）：**去重断言必须先确认读数本身不是空的**，
          //     否则「1 个值」既可能是「真的收敛了」，也可能是「从头到尾没读到数」。
          const id = tid.replace('canvas-search-result-node_', 'node_');
          const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
          if (!n) return { 找不到: true };
          const vp = document.querySelector('.react-flow__viewport');
          const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
          const cm = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
          const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
          return {
            画布: cm ? [Number(cm[1]), Number(cm[2])] : null,
            vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null,
            // 立规 33：读数的那一刻顺手把缩放读出来
            zoom: z ? z.getAttribute('aria-label') : null,
          };
        }, 目标));
        await p.waitForTimeout(600);
      }

      const ty集合 = [...new Set(帧.map((f) => f.vp && f.vp[1]))];
      const tx集合 = [...new Set(帧.map((f) => f.vp && f.vp[0]))];
      const sc集合 = [...new Set(帧.map((f) => f.vp && f.vp[2]))];
      const 画布集合 = [...new Set(帧.map((f) => f.画布 && JSON.stringify(f.画布)))];
      // 🔴 立规 82：先判「读到数了吗」，再判「收敛了吗」。
      const 有效帧 = 帧.filter((f) => f.vp && f.vp.length === 3 && Number.isFinite(f.vp[1]));
      if (有效帧.length === 0) {
        out.档[w] = { 无效: '6 帧里一帧都没读到 viewport 读数', 前置, 节点前置, 帧 };
        out.无效臂++;
        log(w, '⛔ 无效臂：6 帧全空', JSON.stringify(帧.slice(0, 2)));
        continue;
      }
      // 布局地标：贴右边缘、宽 ≥150、竖长的元素（批次 199 的扫法）
      const 地标 = await p.evaluate(() => Array.from(document.querySelectorAll('body *')).filter((e) => {
        const r = e.getBoundingClientRect();
        return r.height >= 300 && r.width >= 150 && r.right >= innerWidth - 2;
      }).slice(0, 14).map((e) => {
        const r = e.getBoundingClientRect();
        return [e.tagName + (e.getAttribute('data-testid') ? '#' + e.getAttribute('data-testid') : ''),
          Math.round(r.x), Math.round(r.width), Math.round(r.height)];
      }));

      out.档[w] = {
        前置, 节点前置, 帧, 末: 帧[帧.length - 1], 有效帧数: 有效帧.length,
        tx取值: tx集合, ty取值: ty集合, scale取值: sc集合, 画布取值: 画布集合,
        地标,
        断言: {
          判据: '先要求 6 帧里至少 1 帧读到数值（立规 82），再要求 ty 去重后只剩 1 个值',
          读到数了: 有效帧.length > 0,
          ty收敛: ty集合.length === 1,
          画布恒定: 画布集合.length === 1,
        },
      };
      log(w, '| 条数', 前置.总条数, '| ty', JSON.stringify(ty集合), '| tx', JSON.stringify(tx集合),
        '| scale', JSON.stringify(sc集合), '| 画布', JSON.stringify(画布集合),
        '| ty收敛', ty集合.length === 1);
    } catch (e) {
      out.档[w] = { 出错: e.message };
      out.无效臂++;
      log(w, '🔴 出错：', e.message);
    } finally {
      // ⑦ 每臂 finally 落盘
      fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
    }
  }
} finally {
  try { await p.close(); } catch {}
}

out.共享页_后 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);
log('\n共享页 前/后：', JSON.stringify(out.共享页_前), '→', JSON.stringify(out.共享页_后));
log('无效臂条数：', out.无效臂, '/', 宽度集.length);
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
await b.close();
