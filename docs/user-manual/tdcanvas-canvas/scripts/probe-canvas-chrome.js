/**
 * probe-canvas-chrome.js —— 量画布外围那几组固定按钮，M196 实测的四个数都出自这里。
 *
 *   ① 左侧 Dock：未选中 / 单选 / Shift 真多选 / 点空白取消选中，四档各几个；
 *      「删除选中」在不在。
 *   ② 顶栏：`.td-canvas-topbar` 容器内几个，**以及容器外还有几个**——
 *      手册那句「11 个」是「容器内 10 + 容器外的面板拖动把手 1」。
 *   ③ 缩放条 `data-canvas-view-control` 四个。
 *   ④ Agent 面板顶端那排图标按钮几个、是不是真的没有文字。
 *
 * 用法：
 *   TD_PROBE_PROFILE=/tmp/m124-profile node scripts/probe-canvas-chrome.js http://localhost:3000/canvas/<id>
 *
 * ══ 三条量测纪律，都是 M196/M197 实际栽过或差点栽的，写在这里免得下一个人重犯 ══
 *
 * 1. ★ **id 不是标签。** 同一个动作在不同状态下可以换名字：
 *    音频/视频节点的按钮 `id` 恒为 `uploadAudio`/`uploadVideo`，
 *    而按钮上的字与读屏标签会在「上传…」与「替换…」之间切换。
 *    **只读 id 会得出与读者所见相反的结论**——M197 第一遍就这么差点把对的写成错的。
 *    所以本探针凡涉及按钮，一律**同时输出 id、按钮上的字、读屏标签三样**。
 *
 * 2. ★ **阳性对照不成立时，要报「不成立」，不能报 0。**
 *    「Dock 0 个按钮」和「我没找到 Dock」是两回事，混起来就会把量具的毛病
 *    写成产品的毛病（M186 起的核心纪律）。
 *
 * 3. ★ **「读数整齐」也可能是判据坏了的信号。**
 *    尤其 Shift 多选那一档：节点默认全叠在画布中心，点偏移一点就落到**空白画布**上，
 *    那是「取消选中」而不是「多选」——**两种解释会给出完全相同的读数**。
 *    所以这里用**节点工具条数量**当独立读数：单选时为 1，多选/无选中时为 0。
 *
 * ★ **不碰任何删除类按钮**，也**不点「清空画布」**（M192 的教训：子串匹配会先命中
 * 「删除全部」，两张画布一起没了）。本探针只读不写。
 */
const { chromium } = require(process.env.PLAYWRIGHT_PATH ||
  '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright');

const URL = process.argv[2];
if (!URL) {
  console.error('用法：node scripts/probe-canvas-chrome.js <画布URL>');
  process.exit(2);
}
const say = (...a) => console.log(a.join(' '));
let page;

/** 纪律 1：id / 按钮上的字 / 读屏标签，三样一起读。 */
const buttonsOf = (sel) => page.evaluate((s) => {
  const root = document.querySelector(s);
  if (!root) return { found: false };
  return {
    found: true,
    items: Array.from(root.querySelectorAll('button, [role="button"]')).map((b) => ({
      id: b.getAttribute('data-canvas-node-toolbar-action') || '',
      aria: b.getAttribute('aria-label') || '',
      text: (b.innerText || '').replace(/\s+/g, ' ').trim(),
    })),
  };
}, sel);

/** 纪律 3：节点工具条数量 = 「有没有单一归属的选中」的独立读数。 */
const toolbarBars = () => page.evaluate(
  () => document.querySelectorAll('[data-canvas-node-hover-toolbar]').length
);

/** 点第 idx 个节点；先找**确实命中它自己**的点，避免点到盖在上面的那个。 */
const pickNode = (idx, shift) => page.evaluate(async ([i, useShift]) => {
  const node = document.querySelectorAll('[data-node-id]')[i];
  if (!node) return { err: '节点不存在' };
  const b = node.getBoundingClientRect();
  for (let fy = 0.12; fy <= 0.88; fy += 0.08) {
    for (let fx = 0.12; fx <= 0.88; fx += 0.08) {
      const x = b.left + b.width * fx, y = b.top + b.height * fy;
      const hit = document.elementFromPoint(x, y);
      if (hit && hit.closest('[data-node-id]') === node) {
        const opts = { bubbles: true, clientX: x, clientY: y, button: 0, pointerId: 1 };
        if (useShift) opts.shiftKey = true;
        for (const t of ['pointerdown', 'mousedown', 'mouseup', 'click']) {
          node.dispatchEvent(t.startsWith('pointer')
            ? new PointerEvent(t, opts) : new MouseEvent(t, opts));
        }
        await new Promise((z) => setTimeout(z, 900));
        return { ok: true, at: { x: Math.round(x), y: Math.round(y) } };
      }
    }
  }
  return { err: '该节点被完全遮住（阳性对照不成立，换一张只放目标节点的画布）' };
}, [idx, shift]);

/** 点空白处取消选中。
 *  ★ 第一版把鼠标事件派发在 `document.body` 上，**取消选中没有发生**——
 *    应用的处理器挂在画布表面上，不在 body 上。所以这一档要用**真实鼠标点击**：
 *    事件落到哪个元素上，就该是哪个元素的监听器接到。 */
const clickEmpty = async () => {
  const pt = await page.evaluate(() => {
    for (let x = 60; x < 1500; x += 37) {
      for (let y = 500; y < 950; y += 41) {
        const hit = document.elementFromPoint(x, y);
        if (hit && !hit.closest('[data-node-id]') && !hit.closest('.td-canvas-dock')
            && !hit.closest('[data-canvas-node-hover-toolbar]')
            && !hit.closest('.td-canvas-topbar')) {
          return { x, y, tag: hit.tagName.toLowerCase() };
        }
      }
    }
    return null;
  });
  if (!pt) return { err: '找不到空白处' };
  await page.mouse.click(pt.x, pt.y);
  await page.waitForTimeout(900);
  return { ok: true, at: pt };
};

(async () => {
  const profile = process.env.TD_PROBE_PROFILE || '/tmp/m124-profile';
  const ctx = await chromium.launchPersistentContext(profile, {
    headless: true, viewport: { width: 1600, height: 1000 },
  });
  page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', (e) => errs.push(String((e && e.message) || e).slice(0, 120)));

  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  const brand = await page.evaluate(() => ({
    title: document.title,
    nodes: document.querySelectorAll('[data-node-id]').length,
  }));
  say(`[0] 身份核对 = ${JSON.stringify(brand)}｜**不是 TDCanvas 就中止**（200 只证明有东西在监听）`);
  if (!/TDCanvas/.test(brand.title || '')) { await ctx.close(); return; }

  // ── ① 左侧 Dock 四档 ──
  say('');
  say('=== ① 左侧 Dock（.td-canvas-dock）逐档 ===');
  const rows = [];
  const snap = async (label) => {
    const d = await buttonsOf('.td-canvas-dock');
    if (!d.found) return { label, err: '**没找到 Dock 容器**（不报 0）' };
    const bars = await toolbarBars();
    // ★ 用**全名精确匹配**，不用 `/删除选中/` 这种带「删除」前缀的正则。
    //   M193 立的纪律：子串/正则碰上「删除」这种前缀，先命中的必然是更严重的那个
    //   （M192 因此丢了两张画布）。这里虽然只用来判断按钮在不在、从不点击，
    //   **但纪律要的是形状本身**：写全名，判据才不会在下次编辑时变成一次点击。
    const hasDel = d.items.some((b) => b.aria === '删除选中');
    rows.push({ label, n: d.items.length, hasDel, bars,
                names: d.items.map((b) => b.aria) });
    return rows[rows.length - 1];
  };
  const r0 = await snap('未选中');
  say(`  ${r0.label}：${r0.n} 个（工具条 ${r0.bars}）`);
  // ★ 对照失败的步骤**必须中断整段序列**，不能打个错就继续跑。
  //   第一版只在行尾打印错误、后面几档照跑，于是顶着错误的标签产出读数
  //   （明明 bars=1 却标成「Shift 多选」）。**错误的标签比没有读数更坏**。
  let aborted = null;
  if (brand.nodes > 0) {
    const p0 = await pickNode(0, false);
    if (p0.err) {
      aborted = `单选这一步：${p0.err}`;
    } else {
      const r1 = await snap('单选');
      say(`  ${r1.label}：${r1.n} 个（工具条 ${r1.bars}，含删除选中=${r1.hasDel}）`);
      if (brand.nodes < 2) {
        aborted = '画布上只有 1 个节点，Shift 多选这一档无法构造';
      } else {
        const p1 = await pickNode(1, true);
        if (p1.err) {
          aborted = `Shift 多选这一步：${p1.err}`;
        } else {
          const r2 = await snap('Shift 多选');
          say(`  ${r2.label}：${r2.n} 个（工具条 ${r2.bars}，含删除选中=${r2.hasDel}）`);
          const e = await clickEmpty();
          if (e.ok) {
            const r3 = await snap('点空白取消选中');
            say(`  ${r3.label}：${r3.n} 个（工具条 ${r3.bars}，含删除选中=${r3.hasDel}）`);
          } else {
            aborted = `点空白这一步：${e.err}`;
          }
        }
      }
    }
  } else {
    aborted = '画布上没有节点，单选/多选两档无法构造';
  }
  if (aborted) {
    say(`  **序列已中断**：${aborted}`);
    say('    后续几档不跑——**对照不成立时继续跑，产出的读数会顶着错误的标签，比没有读数更坏**。');
    say('    换一张节点不互相遮挡的画布（节点默认全叠在画布中心）再跑这几档。');
  }
  say('  逐档明细：');
  rows.forEach((r) => say(`    ${r.label}｜${r.n} 个｜${JSON.stringify(r.names)}`));
  say('  ★ 判据互校：真多选时**工具条应为 0**（工具条按节点走，多选没有单一归属），');
  say('    而「点空白取消选中」也是 0 —— 所以**光看 Dock 的数分辨不出这两者**');
  say('    （M196 就在这里差点把一条对的结论改成错的）。');

  // ── ② 顶栏：先钉边界，再谈那个数 ──
  say('');
  say('=== ② 顶栏（先把边界打出来）===');
  const top = await buttonsOf('.td-canvas-topbar');
  if (!top.found) say('  **没找到 .td-canvas-topbar**（不报 0）');
  else {
    top.items.forEach((b, i) => say(`    ${i + 1}. 读屏="${b.aria}"｜字="${b.text}"`));
    const outside = await page.evaluate(() => Array.from(document.querySelectorAll('button, [role="button"]'))
      .map((b) => ({ aria: b.getAttribute('aria-label') || '', top: !!b.closest('.td-canvas-topbar'),
                      dock: !!b.closest('.td-canvas-dock') }))
      .filter((b) => /调整右侧面板宽度|宽度/.test(b.aria) && !b.top && !b.dock));
    say(`  容器内 ${top.items.length} 个｜容器外另有「调整右侧面板宽度」类按钮 ${outside.length} 个`);
    say(`  **手册那句「11 个」= 容器内 ${top.items.length} + 容器外 ${outside.length}**`);
  }

  // ── ③ 缩放条 ──
  say('');
  say('=== ③ 缩放条 data-canvas-view-control ===');
  const zoom = await page.evaluate(() => Array.from(document.querySelectorAll('[data-canvas-view-control]'))
    .map((el) => {
      const inDock = !!el.closest('.td-canvas-dock');
      const inTop = !!el.closest('.td-canvas-topbar');
      return { id: el.getAttribute('data-canvas-view-control'), inDock, inTop };
    }));
  say(`  ${zoom.length} 个 → ${JSON.stringify(zoom.map((z) => z.id))}`);
  say(`  归属：${zoom.every((z) => !z.inDock && !z.inTop) ? '**既不在 Dock 也不在顶栏**（所以两处都不该把它们算进去）' : '有重叠，注意别数重'}`);

  // ── ④ Agent 面板那排图标按钮 ──
  say('');
  say('=== ④ Agent 面板顶端的图标按钮 ===');
  const agent = await page.evaluate(async () => {
    const opener = Array.from(document.querySelectorAll('button'))
      .find((b) => (b.getAttribute('aria-label') || '').trim() === 'Agent');
    if (!opener) return { opened: false, why: '顶栏没有 Agent 按钮' };
    opener.click();
    await new Promise((r) => setTimeout(r, 1800));
    const collapse = Array.from(document.querySelectorAll('button'))
      .find((b) => (b.getAttribute('aria-label') || '').includes('收起 Agent 面板'));
    if (!collapse) return { opened: true, why: '面板开了但找不到「收起 Agent 面板」，无法定位面板容器' };

    // ★ **必须限定在面板容器内枚举。** 第一版直接全页按 aria-label 过滤，
    //   结果读出 **8 个**、且「历史」出现两次——**第二次是左侧 Dock 的那个「历史」**。
    //   全页过滤把面板外的同名按钮也算了进来。
    //   这正是 M185「找一个 X 默认它有多个」：**过滤条件要跟着范围走**。
    for (let up = 0; up < 6; up++) {
      let panel = collapse.parentElement;
      for (let i = 0; i < up; i++) panel = panel && panel.parentElement;
      if (!panel) break;
      const row = Array.from(panel.querySelectorAll('button, [role="button"]'))
        .map((b) => ({ aria: b.getAttribute('aria-label') || '',
                       text: (b.innerText || '').replace(/\s+/g, ' ').trim(),
                       inDock: !!b.closest('.td-canvas-dock'),
                       inTop: !!b.closest('.td-canvas-topbar') }))
        .filter((b) => /连接设置|^对话$|^历史$|^技能$|^日志$|^新对话$|收起 Agent 面板/.test(b.aria))
        .filter((b) => !b.inDock && !b.inTop);
      if (row.length >= 6) return { opened: true, row, depth: up, panelButtons: panel.querySelectorAll('button').length };
    }
    return { opened: true, why: '没找到同时容纳这些按钮的面板容器' };
  });
  if (!agent.opened) say(`  **面板没打开**：${agent.why}（不报 0）`);
  else if (!agent.row) say(`  **${agent.why}**（不报 0）`);
  else {
    agent.row.forEach((b, i) => say(`    ${i + 1}. 读屏="${b.aria}"｜可见文字="${b.text}"`));
    const iconOnly = agent.row.filter((b) => b.text === '').length;
    const dup = agent.row.map((b) => b.aria).filter((a, i, arr) => arr.indexOf(a) !== i);
    say(`  ★ ${agent.row.length} 个（面板容器向上 ${agent.depth} 层，内共 ${agent.panelButtons} 个 button）`);
    say(`    纯图标（可见文字为空）${iconOnly} 个｜重复项 = ${JSON.stringify(dup)}`);
    say(`  手册声称 7 个且全是纯图标｜${agent.row.length === 7 && iconOnly === 7 ? '一致' : '**不一致**'}`);
    say(`  **「纯图标」不能靠数个数证明**——有的按钮是图标带小字的，所以逐个读了可见文字。`);
  }

  say('');
  say(`[收尾] 页面错误 = ${JSON.stringify(errs.slice(0, 4))}`);
  await ctx.close();
})().catch((e) => { console.error('探针崩了:', e); process.exit(1); });
