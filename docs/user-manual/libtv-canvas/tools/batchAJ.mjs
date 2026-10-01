// Batch AJ —— 故事板模式里仅剩的两枚没点过的控件。
//
// batchS/T/U 只把故事板的**静态样子**拍下来了：
//   · 视频列列头右上角一个「全部」筛选下拉
//   · 视频节点行尾一枚「对话」按钮
// 两枚都只被写进了表格，一个都没点。
//
// 要问的：
//   AJ1 「全部」下拉里有什么、选了之后视频列怎么变？
//       ⚠️ **视频节点没生成过东西**，筛选要拿什么来筛？先看选项再说。
//   AJ2 「对话」点开会是什么？
//       ⚠️ 名字像是要跟这个节点对话，可能触发 Agent。规则同 batchY：
//          出现「发送 / 提交 / 派发 / 运行 / 消耗」立刻停手，只读 DOM。
//
// 另外故事板还有一个没验的机制：batchT 发现「点故事板会把 TV Director 面板拉出来跟着你」，
// 这次顺带确认那个面板在**每一列**上的行为是不是一致。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAJ';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodeList = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}));
const floating = () => page.evaluate(() => [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"],[class*="Dropdown-dropdown"]')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { cls: (e.className || '').toString().slice(0, 36), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 240),
      items: [...e.querySelectorAll('[role="menuitem"],[role="option"],button,li,label,div')].filter((c) => {
        const cr = c.getBoundingClientRect();
        return cr.width > 24 && cr.height > 8 && cr.height < 46 && (c.innerText || '').trim().length <= 24 && !c.querySelector('div[style]');
      }).map((c) => { const cr = c.getBoundingClientRect();
        return { t: (c.innerText || '').trim(), aria: c.getAttribute('aria-label'), cx: Math.round(cr.x + cr.width / 2), cy: Math.round(cr.y + cr.height / 2) }; })
        .filter((x, i, a) => a.findIndex((y) => y.t === x.t && y.cy === x.cy) === i) }; }));
/** 故事板三列的完整读数：列头 + 每列主体。不预设 class，按位置切。 */
const board = () => page.evaluate(() => {
  const cols = [...document.querySelectorAll('*')].filter((e) => {
    const r = e.getBoundingClientRect();
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    return r.width > 380 && r.width < 620 && r.height > 300 && /^(文本|图片|视频)/.test(t)
      && ![...e.children].some((c) => /^文本|^图片|^视频/.test((c.innerText || '').trim()));
  });
  const pick = cols.slice(-3);
  return {
    colCount: pick.length,
    cols: pick.map((c) => { const r = c.getBoundingClientRect();
      const btns = [...c.querySelectorAll('button,[role="button"],[role="tab"]')].map((b) => { const br = b.getBoundingClientRect();
        return { t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14), aria: b.getAttribute('aria-label'),
          cx: Math.round(br.x + br.width / 2), cy: Math.round(br.y + br.height / 2), rect: [Math.round(br.width), Math.round(br.height)] }; });
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        head: (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120), buttons: btns }; }),
    modeBar: (() => { const e = [...document.querySelectorAll('*')].find((x) => /故事板.*跟随|正在跟随/.test((x.innerText || '').replace(/\s+/g, ' ')));
      return e ? (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120) : null; })(),
    tvPanel: !!document.querySelector('.mantine-Drawer-inner'),
  };
});
const toasts = () => page.evaluate(() => [...document.querySelectorAll('[role="alert"],[class*="toast"]')]
  .filter((t) => t.getBoundingClientRect().width > 0).map((t) => (t.innerText || '').replace(/\s+/g, ' ').slice(0, 140)));

async function freeSpot() {
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(450);
  const ns = await nodeList();
  if (!ns.length) return [760, 320];
  const right = Math.max(...ns.map((n) => n.rect[0] + n.rect[2]));
  const bottom = Math.max(...ns.map((n) => n.rect[1] + n.rect[3]));
  for (const [x, y] of [[Math.min(right + 360, 1370), 260], [Math.min(right + 360, 1370), 540],
    [700, Math.min(bottom + 280, 720)], [1150, Math.min(bottom + 280, 720)], [430, Math.min(bottom + 280, 720)]]) {
    if (!ns.some((n) => x > n.rect[0] - 40 && x < n.rect[0] + n.rect[2] + 40 && y > n.rect[1] - 40 && y < n.rect[1] + n.rect[3] + 40)
        && x > 400 && y > 140 && y < 740) return [x, y];
  }
  return null;
}
async function addNode(item) {
  for (let r = 0; r < 3; r += 1) {
    const spot = await freeSpot();
    if (!spot) return false;
    await page.mouse.dblclick(spot[0], spot[1]); await page.waitForTimeout(1100);
    const it = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
      .getByText(item, { exact: false }).first();
    if (await it.count().catch(() => 0)) {
      const b = await N();
      await it.click({ timeout: 4000 }).catch(() => {}); await page.waitForTimeout(2300);
      if (await N() > b) return true;
    }
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(700);
  }
  return false;
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '故事板「全部」筛选 + 「对话」按钮' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  for (const item of ['文本', '图片', '视频']) console.log(`建 ${item}:`, await addNode(item), await N());

  // 切故事板
  const tab = page.getByRole('button', { name: '故事板', exact: true }).first();
  await tab.click({ timeout: 6000 }); await page.waitForTimeout(3000);
  const b0 = await board();
  await shot(page, 'M-87-故事板-三列读数.png');
  console.log('AJ0:', JSON.stringify(b0).slice(0, 2200));
  await logStep(B, { id: 'AJ0-board', title: '故事板三列的列头与全部按钮（按位置切列，不预设 class）',
    target: '切到故事板后把三列的框、列头文案、每列所有按钮连 aria 一起 dump',
    evidence: b0,
    visible_text: `切到故事板后识别到 ${b0.colCount} 列：${JSON.stringify(b0.cols.map((c) => ({ 位置: c.rect, 列头: c.head, 按钮: c.buttons.map((x) => x.t || x.aria) })))}。` +
      `底部状态条 ${JSON.stringify(b0.modeBar)}；TV Director 面板在场：${b0.tvPanel}`,
    shot: 'M-87-故事板-三列读数.png' });

  // ── AJ1 视频列的「全部」筛选
  try {
    const videoCol = b0.cols.find((c) => /视频/.test(c.head)) || b0.cols[2];
    const filterBtn = videoCol?.buttons.find((x) => x.t === '全部' || /全部/.test(x.aria || ''));
    if (!filterBtn) throw new Error('视频列里找不到「全部」按钮；该列按钮=' + JSON.stringify(videoCol?.buttons.map((x) => x.t || x.aria)));
    await page.mouse.click(filterBtn.cx, filterBtn.cy); await page.waitForTimeout(1800);
    const pop = await floating();
    await shot(page, 'M-88-故事板-全部筛选下拉.png');
    const items = pop?.[0]?.items || [];
    let picked = null;
    const opt = items.find((i) => i.t && i.t !== '全部');
    if (opt) {
      const bBefore = await board();
      await page.mouse.click(opt.cx, opt.cy); await page.waitForTimeout(1900);
      const bAfter = await board();
      picked = { opt: opt.t, videoBefore: bBefore.cols.find((c) => /视频/.test(c.head))?.head,
        videoAfter: bAfter.cols.find((c) => /视频/.test(c.head))?.head,
        btnAfter: bAfter.cols.find((c) => /视频/.test(c.head))?.buttons.map((x) => x.t || x.aria) };
      await shot(page, 'M-89-故事板-筛选选中之后.png');
    }
    await logStep(B, { id: 'AJ1-filter', title: '故事板视频列的「全部」筛选里有什么',
      target: `点视频列列头的「全部」按钮 (${filterBtn.cx},${filterBtn.cy})，读浮层`,
      evidence: { filterBtn, pop, picked },
      visible_text: `按钮位置 ${JSON.stringify(filterBtn)}。点开后浮层 ${JSON.stringify(pop)}，共 ${items.length} 个选项。` +
        (picked ? `选「${picked.opt}」：视频列列头「${picked.videoBefore}」→「${picked.videoAfter}」，列头按钮变成 ${JSON.stringify(picked.btnAfter)}。` :
          '**没有可点的选项**（浮层是空的或只有当前项）。') +
        `⚠️ 这张画布上**没生成过任何视频**，所以筛不出内容差异。`,
      shot: 'M-88-故事板-全部筛选下拉.png' });
    console.log('AJ1:', JSON.stringify({ pop, picked }).slice(0, 1800));
  } catch (e) { await logStep(B, { id: 'AJ1-filter', title: '故事板「全部」筛选', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AJ1 失败', String(e).slice(0, 250)); }

  // ── AJ2 视频节点行尾的「对话」按钮
  try {
    const b = await board();
    const videoCol = b.cols.find((c) => /视频/.test(c.head)) || b.cols[2];
    const talk = videoCol?.buttons.find((x) => x.t === '对话' || /对话/.test(x.aria || ''));
    if (!talk) throw new Error('视频列里找不到「对话」按钮；该列按钮=' + JSON.stringify(videoCol?.buttons.map((x) => x.t || x.aria)));
    const nBefore = await N();
    await page.mouse.click(talk.cx, talk.cy); await page.waitForTimeout(2600);
    const detail = await page.evaluate(() => {
      const panel = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
        .find((x) => x.getBoundingClientRect().x > 500);
      const buttons = panel ? [...panel.querySelectorAll('button')].map((x) => ({
        t: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), aria: x.getAttribute('aria-label'),
        title: x.getAttribute('title'), disabled: x.disabled === true || getComputedStyle(x).opacity < 0.45 })) : [];
      return {
        panelFound: !!panel,
        panelText: panel ? (panel.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300) : null,
        buttons: buttons.slice(0, 22),
        danger: buttons.filter((x) => /发送|提交|派发|运行|开始生成|消耗|Send/.test(`${x.t}${x.aria || ''}${x.title || ''}`)),
        stillWelcome: !!document.querySelector('.chat-welcome-root'),
        chatEditor: (() => { const e = panel?.querySelector('.ChatRichInput-editor,[contenteditable="true"]');
          if (!e) return null; const r = e.getBoundingClientRect();
          return { text: (e.innerText || '').replace(/\s+/g, ' ').trim(), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })(),
      };
    });
    await shot(page, 'M-90-故事板-点对话之后.png');
    const danger = detail.danger.length > 0;
    await logStep(B, { id: 'AJ2-dialog', title: '故事板节点行尾的「对话」点开是什么',
      target: `点视频列里的「对话」按钮 (${talk.cx},${talk.cy})，之后**只读 DOM，不点任何发送控件**`,
      evidence: { talk, nodeCountBefore: nBefore, nodeCountAfter: await N(), detail },
      visible_text: `点之前画布 ${nBefore} 个节点，点之后 ${await N()} 个。` +
        `右侧面板 ${detail.panelFound ? '出现了' : '没出现'}；文案「${(detail.panelText || '').slice(0, 180)}」。` +
        `面板按钮 ${JSON.stringify(detail.buttons.map((x) => x.t || x.aria))}；` +
        `**发送类按钮 ${JSON.stringify(detail.danger)}**${danger ? '（**已停手，一个都没点**）' : ''}；` +
        `输入编辑区 ${JSON.stringify(detail.chatEditor)}；仍停在欢迎页（=没自动发送）：**${detail.stillWelcome ? '是' : '否'}**`,
      shot: 'M-90-故事板-点对话之后.png' });
    console.log('AJ2:', JSON.stringify(detail).slice(0, 2000));
  } catch (e) { await logStep(B, { id: 'AJ2-dialog', title: '故事板「对话」按钮', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AJ2 失败', String(e).slice(0, 250)); }

  console.log('提示:', JSON.stringify(await toasts()));
  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
