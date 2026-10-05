/* probe-toolbar-offset.js —— 同一条悬浮工具条，偏移量随「节点类型」变不变（M255 建立）
 *
 * 用法：
 *   CANVAS_URL=/canvas/<id> node scripts/probe-toolbar-offset.js
 *
 * ── 这条探针为什么存在 ────────────────────────────────────────────
 * R105：手册写「顶边在节点顶边上方 104px（100% 缩放）」，并给出 `48×缩放 + 56`。
 * 源码 `lib/canvas/canvas-node-toolbar-position.ts` 的完整写法是
 *   `const titleClearance = (isNativeWorkbench ? 48 : 36) * viewport.k + 8`
 * 而 `isNativeWorkbench` 只认 Image / Video / Audio / Text。
 * **36 那支是不是死代码？** `project.tsx:634` 的 `toolbarNode` 是
 * 「`selectedNodeIds.size === 1` 的那个节点」，**不按类型过滤**——所以不是。
 * ★ 本探针负责把「不是死代码」这句从源码推断变成**屏幕像素读数**。
 *
 * ── 判据 ──────────────────────────────────────────────────────────
 * 量 `offset = 节点顶边 − 工具条顶边`（屏幕像素）。
 * ★ **不把节点拖到画布顶端**：那样量的是被顶栏裁剪后的值，不是布局值。
 *   偏移量与节点位置无关，所以这个约束是白拿的。
 * ★ 工具条渲染在画布变换层**之外**，它自己那 48px 不随缩放变；
 *   节点 rect 是屏幕坐标。**两边同在屏幕坐标系，直接相减。**
 *
 * ── 两条必须自己长出来的纪律 ──────────────────────────────────────
 * ① **组节点要现建现删**。判据用类名 `z-[5]`（`components/canvas/canvas-node.tsx:311` 只在 `isGroup` 时加它）。
 * ② ★ **按 Delete 之前必须验落点**（台账 F72，本条就是被它咬过一次才写进来的）：
 *    组节点建在画布正中，**会压在原有节点上面**。
 *    `elementFromPoint(...).closest('[data-node-id]')` 拿到的 id
 *    **不等于**要删的 id 就不许按 Delete——本探针的收尾就卡在这一步。
 * ③ ★ **别用「位置」认节点，用「工具条的按钮签名」认**（台账 F75）：
 *    组建在画布正中会压住文本节点，于是「点组 → 弹出的是文本节点的工具条」，
 *    而按位置配对的那个判据照样能配出一个节点——**它配出的是那个压着的节点**。
 *    签名是自证的：组 = 2 个按钮（查看节点信息 / 移除节点），图片 = 13 个。
 *    ★ 而且**根元素的类名根本认不出选中态**：`components/canvas/canvas-node.tsx:311` 是三目运算、
 *    **`isGroup` 排在最前**，所以组节点即使被选中，类名也还是 `z-[5]` 而不是 `z-50`。
 */
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');

const APP = process.env.APP_URL || 'http://localhost:3000';
const CANVAS = process.env.CANVAS_URL || '';
const PROFILE = process.env.PROFILE || '/tmp/m244-profile';
const OUT = (...a) => process.stdout.write(a.join(' ') + '\n');

/** 组的按钮签名 / 媒体节点的按钮签名——用来证明量到的是「我要量的那个」 */
const SIG = { group: 2, media: 13 };

const INSPECT = () => Array.from(document.querySelectorAll('[data-node-id]')).map((n) => {
  const r = n.getBoundingClientRect();
  return {
    id: n.getAttribute('data-node-id'),
    isGroup: /z-\[5\]/.test(n.className || ''),   // components/canvas/canvas-node.tsx:311
    media: (n.querySelector('img,video,audio') || {}).tagName?.toLowerCase() || null,
    left: r.left, right: r.right, top: r.top, bottom: r.bottom,
    cx: r.x + r.width / 2, cy: r.y + Math.min(24, r.height / 2),
  };
});

/** 量当前那条工具条 —— 不猜它属于谁，只报它自己的签名，让调用方对账 */
const MEASURE = () => {
  const tb = document.querySelector('[data-canvas-node-hover-toolbar]');
  if (!tb) return { ok: false, why: '没有悬浮工具条' };
  const tr = tb.getBoundingClientRect();
  const btns = Array.from(tb.querySelectorAll('button'))
    .map((b) => b.getAttribute('aria-label') || (b.textContent || '').trim().slice(0, 8));
  return {
    ok: true,
    top: +tr.y.toFixed(1),
    tbW: Math.round(tr.width), tbH: +tr.height.toFixed(1),
    btns,
  };
};

/** ★ F75：找出「这个节点独占、点下去只会选中它」的一个点——沿右缘往内逐个试
 *  ★ 必须自包含：`page.evaluate` 把它整个序列化到页内执行，
 *    **在里面调本文件的另一个函数会 ReferenceError**（本条就撞过一次）。 */
const EXCLUSIVE_POINT = (id) => {
  const g = Array.from(document.querySelectorAll('[data-node-id]'))
    .find((n) => n.getAttribute('data-node-id') === id);
  if (!g) return null;
  const r = g.getBoundingClientRect();
  for (let fy = 0.5; fy <= 0.9; fy += 0.1) {
    for (const inset of [16, 30, 50, 8]) {
      const x = r.right - inset;
      const y = r.top + r.height * fy;
      if (y > window.innerHeight - 20 || y < 70) continue;
      const e = document.elementFromPoint(x, y);
      const n = e && e.closest('[data-node-id]');
      if (n && n.getAttribute('data-node-id') === id) return { x, y };
    }
  }
  return null;
};

const SET_ZOOM = (pct) => {
  const inp = document.querySelector('input[type="range"][aria-label]');
  if (!inp) return null;
  Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(inp, String(pct));
  inp.dispatchEvent(new Event('input', { bubbles: true }));
  inp.dispatchEvent(new Event('change', { bubbles: true }));
  return inp.value;
};

/** ★ F72：这一步返回的 id 不等于 expect，就说明落点不是它 */
const HIT_ID = ([x, y]) => {
  const e = document.elementFromPoint(x, y);
  const n = e && e.closest('[data-node-id]');
  return n ? n.getAttribute('data-node-id') : null;
};

(async () => {
  const ctx = await chromium.launchPersistentContext(PROFILE, { headless: true, viewport: { width: 1600, height: 1000 } });
  const page = ctx.pages()[0] || await ctx.newPage();
  let created = null;
  try {
    await page.goto(APP + CANVAS, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2200);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);

    // 左侧节点面板默认开着，会把 Dock 的新建飞层整块盖住（R106）——先收起
    if (await page.evaluate(() => !!document.querySelector('aside.td-canvas-side-panel'))) {
      const sb = await page.$('button[data-canvas-tool="tool-search"]');
      if (sb) { await sb.click({ force: true }); await page.waitForTimeout(800); }
    }
    OUT('[前置] 节点面板开着吗 =', await page.evaluate(() => !!document.querySelector('aside.td-canvas-side-panel')));

    let nodes = await page.evaluate(INSPECT);
    let group = nodes.find((n) => n.isGroup);
    if (group) {
      // ★ 上一次异常退出留下的组节点**不是本探针建的**，所以收尾不会删它——
      //   「不删不是我建的」这条边界必须让它自己喊出来，不然下次跑的人以为画布是干净的。
      OUT('[注意] 画布上**本来就有**组节点 ' + group.id + '，本探针不删它；收尾只删自己建的那个');
    }
    if (!group) {
      const before = new Set(nodes.map((n) => n.id));
      await page.click('button[data-canvas-tool="tool-create"]');
      await page.waitForTimeout(800);
      const item = await page.evaluateHandle(() => {
        const fly = document.querySelector('.td-canvas-flyout');
        return fly ? Array.from(fly.querySelectorAll('button')).find((b) => (b.textContent || '').trim() === '组') : null;
      });
      const el = item.asElement();
      OUT('[建组] 找到「组」菜单项 =', !!el);
      if (el) {
        // 阳性对照：先证明这一格收得到指针的确实是菜单项，否则「点了没反应」会被读成产品坏了
        const box = await el.boundingBox();
        const top = await page.evaluate(([x, y]) => {
          const e = document.elementFromPoint(x, y);
          return e ? e.tagName + '.' + String(e.className || '').split(' ')[0] : null;
        }, [box.x + box.width / 2, box.y + box.height / 2]);
        OUT('[阳性对照] 菜单项中点落点 =', top);
        await el.click({ force: true });
        await page.waitForTimeout(1400);
        nodes = await page.evaluate(INSPECT);
        const fresh = nodes.filter((n) => !before.has(n.id) && n.isGroup);
        group = fresh[0] || null;
        created = group ? group.id : null;
        OUT('[建组] 新增组节点 =', created || '(没建成)');
      }
    }
    const native = nodes.find((n) => !n.isGroup && n.media);
    OUT('组 =', group ? group.id : '(无)', ' 原生 =', native ? native.id + ' ' + native.media : '(无)');

    for (const pct of [100, 50]) {
      OUT('\n########## 缩放 ' + pct + '% ##########');
      OUT('[滑杆]', await page.evaluate(SET_ZOOM, pct));
      await page.waitForTimeout(900);
      for (const [label, n, want] of [['原生', native, SIG.media], ['组  ', group, SIG.group]]) {
        if (!n) { OUT('  [' + label + '] 跳过（节点不存在）'); continue; }
        await page.keyboard.press('Escape');
        await page.waitForTimeout(300);
        // ★ 组可能被别的节点压着，必须点一个「只有它」的点（F75）
        const pt = n.isGroup
          ? await page.evaluate(EXCLUSIVE_POINT, n.id)
          : await page.evaluate((id) => {
              const e = document.querySelector('[data-node-id="' + id + '"]');
              const r = e.getBoundingClientRect();
              return { x: r.x + r.width / 2, y: r.y + Math.min(24, r.height / 2) };
            }, n.id);
        if (!pt) { OUT('  [' + label + '] 找不到独占点，跳过'); continue; }
        await page.mouse.click(pt.x, pt.y);
        await page.waitForTimeout(900);
        const m = await page.evaluate(MEASURE);
        if (!m.ok) { OUT('  [' + label + '] ' + m.why); continue; }
        // ★ 对账：按钮数不是该类型的签名，说明点到的不是它，这行读数作废
        const sig = m.btns.length === SIG.group ? 'group' : m.btns.length === SIG.media ? 'media' : '其他';
        const ok = sig === (n.isGroup ? 'group' : 'media');
        const node = (await page.evaluate(INSPECT)).find((x) => x.id === n.id);
        const offset = node ? +(node.top - m.top).toFixed(1) : null;
        OUT('  [' + label + '] ' + (ok ? '✓' : '✗ 签名=' + sig + ' 不符，这行作废')
            + '  offset=' + offset + '  工具条 ' + m.tbW + '×' + m.tbH + '  按钮 ' + m.btns.length + ' 个');
        if (pct === 100) OUT('        ' + JSON.stringify(m.btns));
      }
    }

    OUT('\n===== 公式对照 =====');
    OUT('  原生 48k+56：100%→104  50%→ 80');
    OUT('  组   36k+56：100%→ 92  50%→ 74');
  } catch (e) {
    OUT('[异常]', e && e.stack ? e.stack.split('\n').slice(0, 3).join(' | ') : e);
    process.exitCode = 1;
  } finally {
    // 还原：★ 先验落点、再验签名，两道都对才按 Delete（F72 + F75），最后缩放复位
    try {
      if (created) {
        const pt = await page.evaluate(EXCLUSIVE_POINT, created);
        const hit = pt ? await page.evaluate(HIT_ID, [pt.x, pt.y]) : null;
        if (pt && hit === created) {
          await page.mouse.click(pt.x, pt.y);
          await page.waitForTimeout(600);
          // ★ 落点对不等于选中的是它——再用工具条签名确认一次
          const tb = await page.evaluate(MEASURE);
          if (tb.ok && tb.btns.length === SIG.group) {
            await page.keyboard.press('Delete');
            await page.waitForTimeout(1000);
            OUT('\n[还原] 删掉组节点，剩 =', (await page.evaluate(INSPECT)).map((n) => n.id).join(', '));
          } else {
            OUT('\n[还原] 工具条签名不是组（' + ((tb.btns || []).length) + ' 个按钮）——**不按 Delete**，人工确认');
          }
        } else {
          OUT('\n[还原] 落点是 ' + hit + ' 而不是 ' + created + '——**不按 Delete**，人工确认');
        }
      }
      await page.evaluate(SET_ZOOM, 100);
    } catch (e) { OUT('[还原失败]', e); }
    await ctx.close();
  }
})();
