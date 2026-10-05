/* probe-a16.js —— M256 单点核 A16：节点是否真的画在连线的「上面」
 *
 * A16 的限定词是「节点画在连线的上面」，而正文那句是「一条连线只要整段压在某个节点底下，
 * 在它中间点右键，命中的永远是那个节点」。**要验的是层叠顺序，不是 DOM 顺序**——
 * DOM 里连线写在前面、节点写在后面，只能说明作者是后写的那个，不能说明谁盖谁。
 *
 * 判据：问布局引擎「这一格归谁」（elementFromPoint）。
 *   · 落点是连接 → 这一段没被盖住
 *   · 落点是节点 → 这一段被盖住了
 * 阳性对照：同一条连线上必须**同时**存在被盖与没被盖两种段，否则「落点是节点」
 * 只说明连线没画在那儿。
 *
 * ── ⚠️ 当前状态：本探针**跑不出 A16-② 那一段**，如实记为未实测 ──────────
 * 本机几张画布**一条连线都没有**（`data-connection-id` 计数为 0），而建连线的拖拽**连试四次都没成功**。
 * ★ 四次各自学到的东西都留在这个文件里，因为**它们是同一类错的四次复发**：
 *   ① 把**同一个节点**的输入口与输出口配成了一对 → 不成线；
 *   ② 按数组下标取端口，四个节点各 4 个口，**下标 0 全是输入口** → 输入口拖输入口不成线；
 *   ③ 用 `cursor: crosshair` 找端口 —— **找对了元素，却没悬停节点**，
 *      而 `components/canvas/canvas-node.tsx:1107` 的端口带 `visible` 开关，
 *      不可见时是 `pointer-events-none opacity-0`，**不悬停就拖不动**；
 *   ④ 补上悬停（`pointer-events` 实测变 `auto`、透明度变 1）→ 仍然没成线，原因未定。
 * ★ **四次都是「按位置/顺序取一个看起来像的东西」，而正确的判据是产品自己写出来的属性**
 *   （`data-port-direction` / `pointer-events`）。**这正是台账 F75 的第三次复发。**
 * ★ 在 A16-② 拿到读数之前，§14 里 A16 的复核结论只标为**源码级**，不拿源码顶运行时读数。
 */
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');
const OUT = (...a) => process.stdout.write(a.join(' ') + '\n');

const IDS = () => Array.from(document.querySelectorAll('[data-node-id]')).map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-node-id'), cx: r.x + r.width / 2, cy: r.y + r.height / 2, y: r.y, h: r.height };
});

/** 沿一条连线逐点问「这一格归谁」 */
const TRACE = () => {
  const conn = document.querySelector('[data-connection-id]');
  if (!conn) return { err: '没有连线' };
  const cr = conn.getBoundingClientRect();
  const out = [];
  for (let t = 0.05; t <= 0.95; t += 0.05) {
    const x = cr.left + cr.width * t;
    const y = cr.top + cr.height * t;
    const e = document.elementFromPoint(x, y);
    const c = e && e.closest('[data-connection-id]');
    const n = e && e.closest('[data-node-id]');
    out.push({ t: +t.toFixed(2), 归: c ? '连线' : n ? '节点 ' + n.getAttribute('data-node-id').slice(0, 12) : (e ? e.tagName : 'null') });
  }
  return {
    连线数: document.querySelectorAll('[data-connection-id]').length,
    落连接: out.filter((o) => o.归 === '连线').length,
    落节点: out.filter((o) => o.归.startsWith('节点')).length,
    明细: out,
  };
};

const LAYER = () => {
  const node = document.querySelector('[data-node-id]');
  const conn = document.querySelector('[data-connection-id]');
  const svg = conn && (conn.closest('svg') || conn.ownerSVGElement);
  const all = Array.from(document.querySelectorAll('body *'));
  return {
    连接层: svg ? svg.tagName : null,
    连接层_z: svg ? getComputedStyle(svg).zIndex : null,
    节点_z: getComputedStyle(node).zIndex,
    节点类里的z: String(node.className).match(/z-\S+/)?.[0] || null,
    文档序_节点在前: all.indexOf(node) < (svg ? all.indexOf(svg) : -1),
  };
};

(async () => {
  const ctx = await chromium.launchPersistentContext(process.env.PROFILE || '/tmp/m244-profile', { headless: true, viewport: { width: 1600, height: 1000 } });
  const page = ctx.pages()[0] || await ctx.newPage();
  let madeLink = false;
  try {
    await page.goto((process.env.APP_URL || 'http://localhost:3000') + (process.env.CANVAS_URL || '/canvas/H4UgDBdT3NxvK_C5MLMq5'), { waitUntil: 'networkidle' });
    await page.waitForTimeout(2200);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);

    if (!(await page.$('[data-connection-id]'))) {
      // 从一个节点的输出端口拖到另一个节点的输入端口
      // ★ 端口必须用 `data-port-direction` 精确取：源取 output、目标取 input。
      //   前两版分别栽在「同一个节点的口口相配」和「按数组下标取、全是输入口」上——
      //   ★ **两次都是「按位置/顺序取一个看起来像的东西」，而正确的判据是产品自己写出来的属性。**
      const probe = await page.evaluate(() => {
        const byNode = new Map();
        document.querySelectorAll('[data-port-direction]').forEach((e) => {
          const host = e.closest('[data-node-id]');
          if (!host) return;
          const r = e.getBoundingClientRect();
          const id = host.getAttribute('data-node-id');
          if (!byNode.has(id)) byNode.set(id, { out: [], in: [] });
          byNode.get(id)[e.getAttribute('data-port-direction') === 'output' ? 'out' : 'in']
            .push({ x: r.x + r.width / 2, y: r.y + r.height / 2 });
        });
        return Array.from(byNode.entries()).map(([id, p]) => ({ id, ...p }));
      });
      OUT('[按节点分组的端口]', JSON.stringify(probe.map((g) => ({ id: g.id, out: g.out.length, in: g.in.length }))));
      const srcN = probe.find((g) => g.out.length);
      const dstN = probe.find((g) => g.in.length && g.id !== (srcN && srcN.id));
      if (srcN && dstN) {
        const src = srcN.out[0], dst = dstN.in[0];
        OUT('[拖拽]', JSON.stringify({ 源: srcN.id, 目标: dstN.id }));
        // ★ 端口带 `visible` 开关（canvas-node.tsx:1107）：
        //   不可见时是 `pointer-events-none opacity-0`——**不悬停就拖不动**。
        //   这一条是第三版才补上的，前两版的「点了没反应」都栽在这里。
        await page.mouse.move(srcN.out[0].x, (srcN.out[0].y), { steps: 4 });
        await page.waitForTimeout(200);
        const nodeBox = await page.evaluate((id) => {
          const n = document.querySelector('[data-node-id="' + id + '"]');
          const r = n.getBoundingClientRect();
          return { x: r.x + r.width / 2, y: r.y + 10 };
        }, srcN.id);
        await page.mouse.move(nodeBox.x, nodeBox.y, { steps: 6 });
        await page.waitForTimeout(500);
        const vis = await page.evaluate((id) => {
          const p = document.querySelector('[data-node-id="' + id + '"] [data-port-direction="output"]');
          if (!p) return null;
          const s = getComputedStyle(p);
          return { pe: s.pointerEvents, op: s.opacity, r: JSON.stringify(p.getBoundingClientRect().toJSON()).slice(0, 80) };
        }, srcN.id);
        OUT('[悬停后源端口]', JSON.stringify(vis));
        const s2 = await page.evaluate((id) => {
          const p = document.querySelector('[data-node-id="' + id + '"] [data-port-direction="output"]');
          const r = p.getBoundingClientRect();
          return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
        }, srcN.id);
        await page.mouse.move(s2.x, s2.y);
        await page.mouse.down();
        await page.waitForTimeout(300);
        await page.mouse.move((s2.x + dst.x) / 2, (s2.y + dst.y) / 2, { steps: 10 });
        await page.waitForTimeout(300);
        await page.mouse.move(dst.x, dst.y, { steps: 10 });
        await page.waitForTimeout(400);
        await page.mouse.up();
        await page.waitForTimeout(1200);
        madeLink = !!(await page.$('[data-connection-id]'));
        OUT('[连线] 建成 =', madeLink);
      } else {
        OUT('[连线] 没有同时具备 output 与 input 的两个节点，跳过');
      }
    }

    OUT('\n===== A16-① 层叠参数 =====');
    OUT(JSON.stringify(await page.evaluate(LAYER), null, 1));
    OUT('\n===== A16-② 沿连线逐点问「这一格归谁」 =====');
    const tr = await page.evaluate(TRACE);
    OUT(JSON.stringify(tr, null, 1));
  } catch (e) { OUT('[异常]', e && e.stack ? e.stack.split('\n').slice(0, 3).join(' | ') : e); }
  finally {
    if (madeLink) {
      try {
        // 走产品自己的路径删掉这条线：点选它 → Delete
        const p = await page.evaluate(() => {
          const c = document.querySelector('[data-connection-id]');
          const r = c.getBoundingClientRect();
          return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
        });
        const hit = await page.evaluate(([x, y]) => {
          const e = document.elementFromPoint(x, y);
          return e && e.closest('[data-connection-id]') ? '连线' : (e ? e.tagName : 'null');
        }, [p.x, p.y]);
        if (hit === '连线') {
          await page.mouse.click(p.x, p.y);
          await page.waitForTimeout(500);
          await page.keyboard.press('Delete');
          await page.waitForTimeout(800);
          OUT('\n[还原] 还剩连线 =', await page.evaluate(() => document.querySelectorAll('[data-connection-id]').length));
        } else {
          OUT('\n[还原] 落点是 ' + hit + ' 不是连线——不按 Delete，人工确认');
        }
      } catch (e) { OUT('[还原失败]', e); }
    }
    await ctx.close();
  }
})();
