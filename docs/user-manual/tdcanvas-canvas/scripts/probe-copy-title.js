#!/usr/bin/env node
/**
 * 副本标题探针（M212 建立）
 *
 * **为什么要有这个探针**：`shortcuts-help.md` 写「副本标题是在现标题后面追加一个英文的
 * ` Copy`」「**连点复制就会叠加出一长串 Copy**」。这句话是在**右键「复制」**那一步实测出来的。
 * 但源码里有**两条互不相同的复制路径**，追加规则不一样：
 *
 *   - `duplicateNode()`      —— 右键「复制」：无条件 `${title} Copy`，位置 +36/+36
 *   - `pasteCopiedNodes()`   —— `Ctrl/Cmd+V` 与画布右键「粘贴」：
 *                              `title.endsWith(" Copy") ? title : \`${title} Copy\``
 *
 * 也就是说**快捷键那条路径不叠加**。而同一页恰恰在教读者「多选要用 `Ctrl/Cmd + C/V` 一次复制全部」。
 * ★ M210 的教训：**查到一个函数 ≠ 就是文档描述的那条路径**——所以这支探针不去核函数，
 *   它**在真实画布上按真实按键走一遍**，把两条路径各自的标题结果读出来。
 *
 * **它问的问题只有一句**：同一个节点，用右键复制和用快捷键复制，副本标题是不是同一种规律。
 *
 * 判据纪律（沿用 probe-toolbar-states.js 的前七条，此处只补本探针特有的）：
 *
 * 8. **★ 阳性对照必须先成立，否则整支探针作废**
 *    第 1 步（右键复制）**必须**先读出 `文本` → `文本 Copy`。
 *    这一步证明「这个环境确实能产出 ` Copy` 标题」；它不成立时，
 *    第 2/3 步读到的任何「没叠加」都可能是**探针根本没点到菜单**，
 *    而不是产品行为。**先证明量具会响，再拿它说某个东西没响。**
 *
 * 9. **★ 判别读数只有一个：第 3 步**
 *    第 1 步与第 2 步两条路径**都会**追加一次 ` Copy`，分不出彼此；
 *    只有**对一个已经叫「…Copy」的标题再复制一次**（第 3 步），
 *    两种规则才给出不同结果：叠加 → `…Copy Copy`，不叠加 → `…Copy`（与原件重名）。
 *
 * 10. **★ 标题从 IndexedDB 读，不从屏幕上抄**
 *     页面上有左侧节点列表，但那可能是**截断显示**；存储里的是真值。
 *     每一步都**重读存储**（M211 纪律：改完先读库确认）。
 *
 * 11. **★ 只新建画布，不碰既有画布**
 *     探针会**清掉自己建的那张画布**（列表页删除），但**绝不**动 `/tmp/m157-profile`
 *     里原本就有的画布——那些是别的批次取证时留下的现场。
 *
 * 用法（Node 18+）：
 *
 *     node scripts/probe-copy-title.js --profile /tmp/m157-profile
 *
 * 退出码：0 = 探针跑完（**不代表断言通过，判读在报告里**）；非 0 = 探针自身失败。
 */

const path = require('path');
const PW = '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright/index.js';
const { chromium } = require(PW);

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

const PROFILE = arg('profile', '/tmp/m157-profile');
const BASE = arg('base', 'http://localhost:3000');
const REPORT = arg('out', path.join('/tmp', 'm212-copy-title.json'));
/** 跑完是否删掉自己建的画布（默认删） */
const KEEP = process.argv.includes('--keep');

/** 从 IndexedDB 读当前画布的节点。参数用第二个 argument 传，不引用 Node 作用域变量。 */
async function readNodes(page) {
  return await page.evaluate(async () => {
    const db = await new Promise((res, rej) => {
      const r = indexedDB.open('tdcanvas');
      r.onsuccess = () => res(r.result);
      r.onerror = () => rej(r.error);
    });
    const rec = await new Promise((res, rej) => {
      const tx = db.transaction('app_state', 'readonly');
      const rq = tx.objectStore('app_state').get('tdcanvas:canvas_store');
      rq.onsuccess = () => res(rq.result);
      rq.onerror = () => rej(rq.error);
    });
    const parsed = typeof rec === 'string' ? JSON.parse(rec) : rec;
    const projects = (parsed && parsed.state && parsed.state.projects) || [];
    const m = /\/canvas\/([A-Za-z0-9_-]{6,})/.test(location.pathname) ? location.pathname.match(/\/canvas\/([A-Za-z0-9_-]{6,})/)[1] : null;
    const byId = projects.find((p) => p.id === m);
    const proj = byId || projects.find((p) => Array.isArray(p.nodes) && p.nodes.length) || projects[0];
    if (!proj) return { error: '存储里没有任何画布', nodes: [] };
    return {
      id: proj.id,
      matchedByUrl: !!byId,
      count: Array.isArray(proj.nodes) ? proj.nodes.length : null,
      // id、标题、**坐标**一起返回：后面按 id 定位节点，不拿标题去猜 DOM；
      // 坐标用来量「副本落在哪」——两条路径的位置规则不同，这也是手册要写的一格。
      nodes: (proj.nodes || []).map((n) => ({
        id: n.id, title: n.title, type: n.type,
        x: Math.round((n.position && n.position.x) * 10) / 10,
        y: Math.round((n.position && n.position.y) * 10) / 10,
      })),
      titles: (proj.nodes || []).map((n) => n.title),
    };
  });
}

/** 取某个节点在屏幕上的中心点（锚点从源码现算，见 clickNodeById 的注释）。 */
async function nodeCenter(page, nodeId) {
  return await page.evaluate((id) => {
    const el = document.querySelector(`[data-node-id="${id}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return null;
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
  }, nodeId);
}

/**
 * 按 `data-node-id` 定位并点一个节点。
 * 锚点是**从源码现算**的（`canvas-node.tsx:310` 的 `data-node-id={data.id}`），
 * 不是按 class 猜的——猜出来的选择器在这类改版里经常悄悄匹配到 0 个。
 */
async function clickNodeById(page, nodeId, button) {
  const pt = await nodeCenter(page, nodeId);
  if (!pt) return false;
  await page.mouse.click(pt.x, pt.y, button ? { button } : undefined);
  await page.waitForTimeout(600);
  return true;
}

/** 在页面里按可见文字找一个菜单项，返回它的中心点。找不到返回 null。 */
async function findByText(page, text, sel) {
  return await page.evaluate(
    ({ t, s }) => {
      const el = Array.from(document.querySelectorAll(s || 'button, a, [role="menuitem"], li, div'))
        .find((x) => (x.textContent || '').replace(/\s+/g, ' ').trim() === t);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) return null;
      return { x: r.x + r.width / 2, y: r.y + r.height / 2, tag: el.tagName, cls: (el.className || '').toString().slice(0, 80) };
    },
    { t: text, s: sel }
  );
}

(async () => {
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    headless: true,
    viewport: { width: 1600, height: 950 },
  });
  const page = ctx.pages()[0] || (await ctx.newPage());
  const report = { profile: PROFILE, steps: [], notes: [] };
  const say = (s) => console.log(s);
  const step = (name, data) => { report.steps.push({ step: name, ...data }); say(`  · ${name}：${JSON.stringify(data.titles)}`); };

  try {
    // —— 0. 新建一张空白画布（不碰 profile 里原有的画布）
    await page.goto(`${BASE}/canvas`, { waitUntil: 'networkidle' });
    // ★ 坑（第一次跑就栽了）：首页那个「新建画布」按钮带 `disabled={!hydrated}`
    //   （`web/src/pages/canvas/index.tsx`）。networkidle 之后它**仍然是 disabled**，
    //   点下去毫无反应，页面当然不会跳转——**看起来像「点了没反应」，其实是还没 enable**。
    //   所以这里等的是「按钮 enabled」，不是「页面加载完」。
    const newBtn = await page.waitForFunction(() => {
      const b = Array.from(document.querySelectorAll('button'))
        .find((x) => (x.textContent || '').replace(/\s+/g, ' ').trim() === '新建画布');
      if (!b || b.disabled) return false;
      const r = b.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) return false;
      return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
    }, null, { timeout: 20000 }).then((h) => h.jsonValue()).catch(() => null);
    if (!newBtn) { say('[探针失败] 列表页找不到 enabled 的「新建画布」按钮（可能一直没水合）'); process.exit(2); }
    await page.mouse.click(newBtn.x, newBtn.y);
    let canvasUrl = null;
    for (let i = 0; i < 20; i++) {
      if (/\/canvas\/[A-Za-z0-9_-]{6,}/.test(new URL(page.url()).pathname)) { canvasUrl = page.url(); break; }
      await page.waitForTimeout(500);
    }
    if (!canvasUrl) { say('[探针失败] 新建后没跳到画布页'); process.exit(2); }
    const canvasId = canvasUrl.match(/\/canvas\/([A-Za-z0-9_-]{6,})/)[1];
    report.canvas = canvasId;
    say(`[已新建画布] ${canvasId}`);
    await page.waitForTimeout(2000);

    // —— 1. 建一个文本节点
    //    ★ 按钮文字是 `canvas.emptyGuide.text` = **「文字创作」**，不是「文本」。
    //    第一次跑写成「文本」直接匹配 0 个——**又一个猜出来的锚点**。
    const quick = await page.evaluate(() => {
      const g = document.querySelector('[data-canvas-empty-guide]');
      if (!g) return { err: '空画布引导 data-canvas-empty-guide 不在' };
      const btns = Array.from(g.querySelectorAll('button')).map((b) => (b.textContent || '').trim());
      const b = Array.from(g.querySelectorAll('button')).find((x) => (x.textContent || '').trim() === '文字创作');
      if (!b) return { err: '引导里没有「文字创作」', btns };
      const r = b.getBoundingClientRect();
      return { x: r.x + r.width / 2, y: r.y + r.height / 2, btns };
    });
    if (!quick || quick.err) { say('[探针失败] ' + (quick && quick.err) + '｜实际按钮：' + JSON.stringify(quick && quick.btns)); process.exit(2); }
    report.emptyGuideButtons = quick.btns;
    await page.mouse.click(quick.x, quick.y);
    await page.waitForTimeout(1500);
    const s0 = await readNodes(page);
    step('建好首个文本节点', s0);
    if (!s0.nodes || s0.nodes.length !== 1) {
      say('[探针失败] 建节点后存储里不是 1 个节点：' + JSON.stringify(s0.titles));
      process.exit(2);
    }
    const rootId = s0.nodes[0].id;

    // —— 2. 路径 A（右键「复制」）：连按两次，看标题是否一路叠加
    //    这是**阳性对照**：先证明这个环境能产出 ` Copy`、且能一路叠下去。
    if (!await clickNodeById(page, rootId, 'right')) {
      say('[探针失败] 按 data-node-id 找不到根节点（锚点形状变了？）');
      process.exit(2);
    }
    await page.waitForTimeout(800);
    const dup = await findByText(page, '复制');
    if (!dup) { say('[探针失败] 右键菜单里找不到「复制」——阳性对照不成立，探针停在这里'); process.exit(2); }
    await page.mouse.click(dup.x, dup.y);
    await page.waitForTimeout(1500);
    const s1 = await readNodes(page);
    step('路径 A：右键「复制」第一次', s1);
    const controlOK = s1.titles.includes('文本 Copy') && s1.titles.length === 2;
    report.controlOK = controlOK;
    if (!controlOK) {
      say('★ 阳性对照不成立：右键复制没有产出预期的「文本 Copy」。');
      say('  后面任何「快捷键不叠加」的读数都不能作为结论——先查环境。');
      process.exit(3);
    }
    say('  ✔ 阳性对照成立：右键复制确实追加了一次 ` Copy`。');

    // A 第二次：复制刚出来那个「文本 Copy」——按源码应得「文本 Copy Copy」
    const copyA1 = s1.nodes.find((n) => n.title === '文本 Copy');
    if (!copyA1) { say('[探针失败] 存储里没有名为「文本 Copy」的节点'); process.exit(2); }
    if (!await clickNodeById(page, copyA1.id, 'right')) { say('[探针失败] 右键点不到副本'); process.exit(2); }
    await page.waitForTimeout(800);
    const dup2 = await findByText(page, '复制');
    if (!dup2) { say('[探针失败] 第二次右键菜单里找不到「复制」'); process.exit(2); }
    await page.mouse.click(dup2.x, dup2.y);
    await page.waitForTimeout(1500);
    const s2 = await readNodes(page);
    step('路径 A：右键「复制」第二次', s2);
    const aCascade = s2.titles.includes('文本 Copy Copy');
    report.aCascade = aCascade;
    if (!aCascade) {
      say('★ 阳性对照不成立：右键复制第二次没有叠成「文本 Copy Copy」，后面全部作废。');
      process.exit(3);
    }
    say('  ✔ 右键路径确实一路叠加：文本 → 文本 Copy → 文本 Copy Copy');

    // —— 3. ★ 判别读数：**拿路径 A 刚叠出来的那个「文本 Copy Copy」**，
    //    改走快捷键 Ctrl/Cmd + C / V。两条路径作用在**同一个节点**上，差别才干净。
    const target = s2.nodes.find((n) => n.title === '文本 Copy Copy');
    if (!await clickNodeById(page, target.id)) { say('[探针失败] 点不到「文本 Copy Copy」'); process.exit(2); }
    await page.keyboard.press('Meta+c');
    await page.waitForTimeout(400);
    await page.keyboard.press('Meta+v');
    await page.waitForTimeout(1500);
    const s3 = await readNodes(page);
    step('★ 判别步：同一个「文本 Copy Copy」改走 Ctrl/Cmd+C/V', s3);

    // ★ 判据**不写死标题字符串**，改成通用地数「有几位标题重复」。
    //   上一版把期望写死成 '文本 Copy Copy'，结果实际标题是 '文本 Copy'，
    //   判据当场失配、探针拒绝下结论——那是判据写错了，不是产品行为。
    //   通用判据不依赖我事先猜到的那个字符串。
    const tally = {};
    for (const t of s3.titles) tally[t] = (tally[t] || 0) + 1;
    const dupes = Object.keys(tally).filter((t) => tally[t] > 1).map((t) => `${t} ×${tally[t]}`);
    const bCascade = s3.titles.includes('文本 Copy Copy Copy');
    report.bCascade = bCascade;
    report.duplicateTitles = dupes;
    report.titles = s3.titles;
    // 位置差：右键两次的每级偏移 vs 快捷键那一次的偏移
    const at = (arr, title, nth) => arr.filter((n) => n.title === title)[nth] || null;
    const a0 = s2.nodes[s2.nodes.length - 3], a1 = s2.nodes[s2.nodes.length - 2], a2 = s2.nodes[s2.nodes.length - 1];
    const b3 = s3.nodes[s3.nodes.length - 1];
    const d = (p, q) => (p && q ? { dx: Math.round((q.x - p.x) * 10) / 10, dy: Math.round((q.y - p.y) * 10) / 10 } : null);
    report.offsets = {
      a_first: d(a0, a1), a_second: d(a1, a2), b_paste: d(a2, b3),
    };

    say('');
    say('★ 判读（判读在报告里，退出码不代表结论）：');
    say(`  阳性对照（右键复制连按两次）：${controlOK && aCascade ? '通过' : '未通过'}`);
    say(`  路径 A 右键复制之后：${JSON.stringify(s2.titles)}`);
    say(`  同一节点改走 Ctrl/Cmd+C/V：${JSON.stringify(s3.titles)}`);
    say(`  快捷键路径是否继续叠加（出现「文本 Copy Copy Copy」）：${bCascade ? '是' : '否'}`);
    say(`  画布上重名的标题：${dupes.length ? dupes.join('、') : '（无）'}`);
    say(`  位置差：右键第一次 ${JSON.stringify(report.offsets.a_first)}｜右键第二次 ${JSON.stringify(report.offsets.a_second)}｜快捷键粘贴 ${JSON.stringify(report.offsets.b_paste)}`);
    if (aCascade && !bCascade && dupes.length) {
      say('  → 结论：**同一个节点，右键复制会叠加、`Ctrl/Cmd+C/V` 不叠加**。');
      say('    两条复制路径的标题规则不一致——手册「连点复制就会叠加出一长串 Copy」只对前者成立。');
    } else if (aCascade && bCascade) {
      say('  → 结论：两条路径都叠加，手册原话成立。');
    } else {
      say('  → 结论：**判据不成立**——别急着改手册，先怀疑探针没选中节点 / 焦点不在画布。');
    }
  } catch (e) {
    say('[探针失败] ' + (e && e.stack ? e.stack : e));
    report.error = String(e && e.message ? e.message : e);
  } finally {
    require('fs').writeFileSync(REPORT, JSON.stringify(report, null, 2));
    say('\n[报告] ' + REPORT);
    if (KEEP || report.error) {
      say('[保留画布] ' + (report.canvas || '(未知)') + '——探针失败或传了 --keep，请到 /canvas 列表页自行处理。');
    } else if (report.canvas) {
      // 删掉自己建的那张画布。
      // ★ **走产品自己的 UI 删除，不直写 IndexedDB。**
      //   直写过两条，都不稳：(1) 页面 evaluate 里写会撞上应用水合的客户端路由替换，
      //   报 "Execution context was destroyed"，重试 6 次全挂；
      //   (2) 挂到 addInitScript 里删，写进去又被应用从内存回写覆盖，核对发现原封不动。
      //   删数据这件事上，**走产品自己的路径比绕过去改库更可靠**。
      try {
        await page.goto(`${BASE}/canvas`, { waitUntil: 'networkidle' });
        await page.waitForFunction(() => Array.from(document.querySelectorAll('button'))
          .some((x) => (x.textContent || '').replace(/\s+/g, ' ').trim() === '新建画布' && !x.disabled),
          null, { timeout: 20000 }).catch(() => null);

        const hit = await page.evaluate((id) => {
          const card = document.querySelector(`[data-canvas-project-card="${id}"]`);
          if (!card) return { err: '卡片不在' };
          const b = card.querySelector('button[title="删除"]');
          if (!b) return { err: '卡片里没有 title=删除 的按钮' };
          const r = b.getBoundingClientRect();
          return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
        }, report.canvas);
        if (hit.err) throw new Error(hit.err);
        await page.mouse.move(hit.x, hit.y);          // 操作按钮默认隐藏，先悬停
        await page.waitForTimeout(200);
        await page.mouse.click(hit.x, hit.y);
        await page.waitForTimeout(800);

        const dlg = await page.evaluate(() => {
          const m = document.querySelector('.ant-modal-confirm, .ant-modal');
          if (!m) return { err: '确认弹窗没出现' };
          // ★ antd 的 `ant-btn` 会在**两个汉字之间插一个空格**：源码写的是「删除」，
          //   渲染出来 textContent 却是「删 除」。按字面精确匹配会**永远匹配 0 个**。
          const ok = Array.from(m.querySelectorAll('button'))
            .find((b) => (b.textContent || '').replace(/\s+/g, '') === '删除');
          if (!ok) return { err: '弹窗里没有文字为「删除」的按钮' };
          const r = ok.getBoundingClientRect();
          return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
        });
        if (dlg.err) throw new Error(dlg.err);
        await page.mouse.click(dlg.x, dlg.y);
        await page.waitForTimeout(1200);

        // ★ 改完**重新读一遍**确认（改了先读库确认）——「已点删除」只等于「已点」。
        await page.reload({ waitUntil: 'networkidle' });
        await page.waitForFunction(() => Array.from(document.querySelectorAll('button'))
          .some((x) => (x.textContent || '').replace(/\s+/g, ' ').trim() === '新建画布' && !x.disabled),
          null, { timeout: 20000 }).catch(() => null);
        const still = await page.evaluate(async (id) => {
          const db = await new Promise((res, rej) => {
            const r = indexedDB.open('tdcanvas');
            r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error);
          });
          const rec = await new Promise((res, rej) => {
            const tx = db.transaction('app_state', 'readonly');
            const rq = tx.objectStore('app_state').get('tdcanvas:canvas_store');
            rq.onsuccess = () => res(rq.result); rq.onerror = () => rej(rq.error);
          });
          const p = typeof rec === 'string' ? JSON.parse(rec) : rec;
          const st = (p && p.state) || {};
          return { total: (st.projects || []).length, remains: (st.projects || []).some((x) => x.id === id) };
        }, report.canvas);
        say('[清理核对] 画布 ' + report.canvas + ' 仍存在：' + (still.remains ? '是（没删掉）' : '否') + '｜库中画布总数 ' + still.total);
        if (still.remains) say('  ⚠️ 还没删掉，请到 /canvas 列表页手动处理。');
      } catch (e) {
        say('[清理失败] ' + e + '——画布 ' + report.canvas + ' 请到 /canvas 列表页手动删除。');
      }
    }
    await ctx.close();
  }
  process.exit(report.error ? 2 : 0);
})();
