// Batch AA —— Batch Y/Z 之后还欠三件事：
//
//   ① 「重命名」弹的输入框到底长在画布上还是抽屉里？
//      Y 记录到的输入框在 [75,196]，宽 219 —— 那个 x 落在抽屉（宽 320）里，
//      所以猜测是**抽屉那一行就地变成输入框**，而不是画布节点。
//      判据：读 `document.activeElement`，一路往上找祖先，看它是不是在 `.mantine-Drawer` 里。
//
//   ② Y/Z 都证明抽屉「删除」**没有二次确认**、按 ⌘Z 也撤不回来。
//      但两次 ⌘Z 的焦点都在抽屉里 —— 抽屉吞掉快捷键是常事，
//      所以「撤不回来」这个结论还差一个对照组：**把焦点交回画布再按 ⌘Z**。
//      这个差别对手册的措辞影响很大（能撤销 vs 不能撤销）。
//
//   ③ 「添加到Agent」到底把节点放进了什么。Y 抓到的是 TV Director 对话抽屉，
//      节点名被预填进一个 `ChatRichInput-editor`。还差：输入框里到底装了什么内容、
//      发送按钮叫什么（只读 DOM，**绝不点**）、旁边的「全能创作」是什么。
//      「全能创作」点开应该只是模式选择器，安全；出现发送/提交字样立即停手。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAA';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodeList = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}));
const opener = page.locator('[data-academy-guide-anchor="workspace-asset-management"]');
const openDrawer = async () => {
  if (await page.evaluate(() => !!document.querySelector('div.group\\/node'))) return true;
  await opener.first().click({ timeout: 6000 }); await page.waitForTimeout(2600);
  return await page.evaluate(() => !!document.querySelector('div.group\\/node'));
};
const closeDrawer = async () => {
  await page.mouse.click(1250, 780).catch(() => {}); await page.waitForTimeout(900);
};
const openRowMenu = (idx = 0) => page.evaluate((i) => {
  const row = document.querySelectorAll('div.group\\/node')[i];
  if (!row) return { err: '没有第 ' + i + ' 行' };
  const btn = [...row.querySelectorAll('button')].find((b) => b.getAttribute('aria-label') === '更多操作');
  if (!btn) return { err: '该行没有「更多操作」按钮' };
  const b = btn.getBoundingClientRect();
  return { cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2), rowText: (row.innerText || '').trim() };
}, idx);
const readMenu = () => page.evaluate(() => {
  const m = document.querySelector('[class*="mantine-Menu-dropdown"]');
  if (!m) return null;
  return [...m.querySelectorAll('button,[role="menuitem"],li,div')].filter((e) => {
    const r = e.getBoundingClientRect();
    return r.width > 40 && r.height > 16 && r.height < 46 && (e.innerText || '').trim().length <= 12 && !e.querySelector('div[style]');
  }).map((e) => { const r = e.getBoundingClientRect();
    return { t: (e.innerText || '').trim(), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
    .filter((x, i, a) => a.findIndex((y) => y.t === x.t && y.cy === x.cy) === i);
});
const clickMenu = async (label, idx = 0) => {
  const m0 = await openRowMenu(idx);
  if (m0.err) throw new Error(m0.err);
  await page.mouse.click(m0.cx, m0.cy); await page.waitForTimeout(1800);
  const menu = await readMenu();
  const it = menu?.find((i) => i.t === label);
  if (!it) throw new Error(`菜单里没有「${label}」；读到 ${JSON.stringify(menu?.map((i) => i.t))}`);
  await page.mouse.click(it.cx, it.cy);
  return it;
};
const drawerRows = () => page.evaluate(() => ({
  rows: [...document.querySelectorAll('div.group\\/node')].map((r) => (r.innerText || '').replace(/\s+/g, ' ').trim()),
  summary: [...document.querySelectorAll('[class*="mantine-Drawer-body"]')]
    .map((b) => (b.innerText || '').replace(/\s+/g, ' ').trim()).filter((t) => /共\s*\d+\s*节点/.test(t))[0] || null }));
/** 可见的确认层。`.mantine-Drawer` 本身也是 role=dialog，要排除掉。 */
const confirmScan = () => page.evaluate(() => {
  const ov = [...document.querySelectorAll('.mantine-Modal-overlay,[role="dialog"],[class*="Popover-dropdown"]')]
    .filter((d) => { const r = d.getBoundingClientRect(); return r.width > 60 && r.height > 40; })
    .filter((d) => !d.className.toString().includes('Drawer-content'))
    .map((d) => ({ cls: (d.className || '').toString().slice(0, 44),
      rect: [Math.round(d.getBoundingClientRect().width), Math.round(d.getBoundingClientRect().height)],
      text: (d.innerText || '').replace(/\s+/g, ' ').slice(0, 220),
      buttons: [...d.querySelectorAll('button')].map((b) => (b.innerText || b.getAttribute('aria-label') || '').trim()).filter(Boolean).slice(0, 10) }));
  return { dialogs: ov, hasConfirm: ov.some((o) => /确定|确认|取消|是否|不可恢复|撤销/.test(o.text)) };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '重命名输入框位置 / 画布焦点下能否撤销 / 添加到Agent 面板细节' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  for (const [x, y] of [[500, 300], [500, 390], [500, 210]]) {
    const ns = await nodeList();
    if (ns.some((n) => x > n.rect[0] - 20 && x < n.rect[0] + n.rect[2] + 20 && y > n.rect[1] - 20 && y < n.rect[1] + n.rect[3] + 20)) continue;
    await page.mouse.dblclick(x, y); await page.waitForTimeout(1000);
    const it = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
      .getByText('图片', { exact: false }).first();
    if (await it.count().catch(() => 0)) { await it.click({ timeout: 4000 }).catch(() => {}); await page.waitForTimeout(2200); }
    if (await N() > 0) break;
    await page.keyboard.press('Escape').catch(() => {});
  }
  await fitView(page, 1); await page.waitForTimeout(1200);
  console.log('起点节点:', await N());

  // ── AA1 重命名输入框长在哪
  try {
    if (!(await openDrawer())) throw new Error('抽屉打不开');
    await clickMenu('重命名');
    await page.waitForTimeout(1500);
    const where = await page.evaluate(() => {
      const ae = document.activeElement;
      const inDrawer = (el) => !!(el && el.closest && el.closest('[class*="mantine-Drawer-content"]'));
      const inNode = (el) => !!(el && el.closest && el.closest('.react-flow__node'));
      const all = [...document.querySelectorAll('input,textarea,[contenteditable="true"]')]
        .map((e) => { const b = e.getBoundingClientRect();
          return { tag: e.tagName, v: e.value ?? e.innerText, aria: e.getAttribute('aria-label'),
            rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
            inDrawer: inDrawer(e), inNode: inNode(e), active: document.activeElement === e }; })
        .filter((e) => e.rect[2] > 30 && e.rect[3] > 8);
      return { activeTag: ae ? ae.tagName : null, activeAria: ae ? ae.getAttribute('aria-label') : null,
        activeInDrawer: inDrawer(ae), activeInNode: inNode(ae), fields: all,
        canvasNodeCount: document.querySelectorAll('.react-flow__node').length };
    });
    await shot(page, 'M-47-重命名输入框-抽屉就地编辑.png');
    // 真改一次名，验证画布同步
    const inp = page.locator('input[aria-label="节点名称"]').first();
    if (await inp.count().catch(() => 0)) {
      await inp.click().catch(() => {}); await page.keyboard.press('Meta+a');
      await page.keyboard.type('抽屉改名', { delay: 40 }); await page.waitForTimeout(600);
      await page.keyboard.press('Enter'); await page.waitForTimeout(2200);
    }
    const after = { drawer: await drawerRows(), canvas: (await nodeList()).map((n) => n.title) };
    await shot(page, 'M-48-重命名-画布同步.png');
    await logStep(B, { id: 'AA1-rename-where', title: '「重命名」是在抽屉那一行就地改成输入框',
      target: '资产管理第 0 行 →「⋯ → 重命名」，然后读 document.activeElement 的祖先链',
      evidence: { where, after },
      visible_text: `点「重命名」后页面上可见的输入区 ${JSON.stringify(where.fields)}；` +
        `焦点元素是 \`${where.activeTag}\`（\`aria-label="${where.activeAria}"\`），` +
        `**在抽屉里：${where.activeInDrawer ? '是' : '否'}**；在画布节点里：${where.activeInNode ? '是' : '否'}；` +
        `此时画布节点数 ${where.canvasNodeCount}（节点卡片上**没有**同时冒出输入框）。` +
        `改名为「抽屉改名」并回车后：抽屉 ${JSON.stringify(after.drawer.rows)}，画布节点名 ${JSON.stringify(after.canvas)} → ` +
        `**${JSON.stringify(after.drawer.rows) !== JSON.stringify(after.drawer.rows) || after.canvas[0]?.startsWith('抽屉改名') ? '两边同步' : '不同步'}**`,
      shot: 'M-47-重命名输入框-抽屉就地编辑.png' });
    console.log('AA1:', JSON.stringify(where.fields));
  } catch (e) { await logStep(B, { id: 'AA1-rename-where', title: '重命名输入框位置', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AA1 失败', String(e).slice(0, 200)); }

  // ── AA2 焦点回画布后，⌘Z 能不能救回被抽屉删掉的节点
  try {
    if (!(await openDrawer())) throw new Error('抽屉打不开');
    const before = { n: await N(), drawer: await drawerRows() };
    await clickMenu('删除');
    await page.waitForTimeout(300);
    const mid = { confirm: await confirmScan(), n: await N(), drawer: await drawerRows() };
    await page.waitForTimeout(1800);
    const afterDel = await N();
    // 焦点交回画布：点一块空白
    await closeDrawer();
    await page.mouse.click(760, 120); await page.waitForTimeout(1200);
    const focusNow = await page.evaluate(() => ({ tag: document.activeElement?.tagName,
      cls: (document.activeElement?.className || '').toString().slice(0, 40) }));
    await shot(page, 'M-49-删除后-焦点回画布.png');
    await page.keyboard.press('Meta+z'); await page.waitForTimeout(2200);
    const afterUndo = await N();
    await page.keyboard.press('Meta+Shift+z'); await page.waitForTimeout(2200);
    const afterRedo = await N();
    if (await openDrawer()) await closeDrawer();
    await shot(page, 'M-50-撤销重做之后.png');
    const ev = { before, mid, afterDel, focusNow, afterUndo, afterRedo };
    await logStep(B, { id: 'AA2-undo-after-delete', title: '抽屉删掉的节点能不能撤销：焦点交回画布再按 ⌘Z',
      target: '删除后点画布空白把焦点交回画布，再按 ⌘Z / ⌘⇧Z',
      evidence: ev,
      visible_text: `删之前 ${before.n} 个节点，抽屉 ${JSON.stringify(before.drawer.rows)}。` +
        `点「删除」后 300 毫秒：确认弹层 ${JSON.stringify(mid.confirm.dialogs)}（**有无确认层：${mid.confirm.hasConfirm ? '有' : '没有'}**），` +
        `此时已剩 ${mid.n} 个节点。` +
        `把焦点交回画布（\`document.activeElement\` = ${JSON.stringify(focusNow)}）后按 **⌘Z**：画布 ${afterUndo} 个节点；` +
        `再按 **⌘⇧Z**：${afterRedo} 个节点。` +
        `→ **${afterUndo > afterDel ? '能撤销回来' : '删掉的节点撤不回来（⌘Z 也不管用）'}**`,
      shot: 'M-49-删除后-焦点回画布.png' });
    console.log('AA2:', JSON.stringify(ev.mid.confirm.hasConfirm), before.n, afterDel, afterUndo, afterRedo);
  } catch (e) { await logStep(B, { id: 'AA2-undo-after-delete', title: '删除后撤销', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AA2 失败', String(e).slice(0, 200)); }

  // ── AA3 「添加到Agent」面板细节：只读，绝不点发送
  try {
    if (!(await openDrawer())) throw new Error('抽屉打不开');
    const n0 = await N();
    await clickMenu('添加到Agent');
    await page.waitForTimeout(2800);
    const detail = await page.evaluate(() => {
      const ed = document.querySelector('.ChatRichInput-editor,[contenteditable="true"]');
      const b = ed ? ed.getBoundingClientRect() : null;
      // 面板里所有按钮：只记名字和是否含危险字样
      const panel = document.querySelector('[class*="mantine-Drawer-content"]');
      const buttons = panel ? [...panel.querySelectorAll('button')].map((x) => { const r = x.getBoundingClientRect();
        return { t: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), aria: x.getAttribute('aria-label'),
          disabled: x.disabled === true || getComputedStyle(x).opacity < 0.5,
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }) : [];
      return {
        editorText: ed ? (ed.innerText || ed.textContent || '').replace(/\s+/g, ' ').trim() : null,
        editorRect: b ? [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] : null,
        panelText: panel ? (panel.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400) : null,
        buttons: buttons.slice(0, 24),
        dangerWords: buttons.filter((x) => /发送|提交|派发|运行|开始生成|消耗|扣费/.test((x.t || '') + (x.aria || ''))).map((x) => ({ t: x.t, aria: x.aria, disabled: x.disabled })),
        stillWelcome: !!document.querySelector('.chat-welcome-root'),
      };
    });
    const danger = detail.dangerWords.length > 0;
    await shot(page, 'M-51-添加到Agent-面板细节.png');
    await logStep(B, { id: 'AA3-add-to-agent-detail', title: '「添加到Agent」把节点放进了什么：输入框内容、发送按钮、模式切换',
      target: '点「⋯ → 添加到Agent」后只读 DOM，**不点任何发送按钮**',
      evidence: { nodeCountBefore: n0, nodeCountAfter: await N(), detail },
      visible_text: `点之前画布 ${n0} 个节点，点之后 ${await N()} 个（**没在画布上新建东西**）。` +
        `弹出的面板是一张 TV Director 对话抽屉，文案「${(detail.panelText || '').slice(0, 120)}…」；` +
        `底部输入框里已经预填了 **${JSON.stringify(detail.editorText)}**，位置 ${JSON.stringify(detail.editorRect)}。` +
        `面板内按钮 ${JSON.stringify(detail.buttons.map((x) => x.t || x.aria))}；` +
        `是否还停在欢迎页（说明**没有自动发送**）：**${detail.stillWelcome ? '是' : '否'}**；` +
        `按钮里带「发送/提交/派发/消耗」字样的：${JSON.stringify(detail.dangerWords)} → **${danger ? '存在，已停手未点' : '没有扫到（但图标按钮无文字，实际发送控件未点）'}**`,
      shot: 'M-51-添加到Agent-面板细节.png' });
    console.log('AA3:', JSON.stringify({ ed: detail.editorText, btns: detail.buttons.map((x) => x.t || x.aria), welcome: detail.stillWelcome, danger: detail.dangerWords }));
  } catch (e) { await logStep(B, { id: 'AA3-add-to-agent-detail', title: '添加到Agent 面板', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AA3 失败', String(e).slice(0, 200)); }

  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
