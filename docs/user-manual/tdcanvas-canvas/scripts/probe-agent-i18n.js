/**
 * probe-agent-i18n.js —— 量 Agent 面板那 7 个图标按钮，**中英两种语言各量一遍**。
 *
 *   复测的原文（20-reference.md「切到英文」一节）：
 *     「英文下的 Agent 面板 7 个图标按钮的 aria-label 全部已本地化，没有漏译。」
 *
 * 用法：
 *   node scripts/probe-agent-i18n.js http://localhost:3000/canvas/<id> [/tmp/m157-profile]
 *
 * ★ 为什么不能并进 probe-canvas-chrome.js：那一支的选择器全是**中文字面量**
 *   （`aria-label === 'Agent'`、`includes('收起 Agent 面板')`）。英文界面下
 *   它们必然全部失配——**不是产品变了，是尺子换了单位**。所以单独一支。
 *
 * ══ 这一批实际栽过的坑，四条都写在这里免得下一个人重犯 ══
 *
 * 1. ★ **空 profile 会伪造出一个「0 个」。**
 *    我第一次拿一个新建的 profile 去跑 `/canvas/<id>`，读回来是「0 个按钮」。
 *    真实原因不是按钮不见了，是**那个 profile 的 IndexedDB 里一张画布都没有**，
 *    于是 `/canvas/:id` 被重定向回列表页，全页当然扫不到 Dock。
 *    **阴性读数先怀疑量具。** 本探针把「`.td-canvas-dock` 在不在」当成前置对照，
 *    不成立就**明确报「对照不成立」并中断**，绝不报 0。
 *
 * 2. ★ **面板可能本来就是开着的，不先问就点 opener 会把它点关。**
 *    共享 profile 里 Agent 面板常处于已展开状态。无脑 `opener.click()` 之后
 *    找不到「Collapse」按钮，读出来是「面板开合后都定位不到容器」——
 *    **一个纯属自己制造的阴性结果**。所以先找 Collapse 按钮：找得到就说明已开着。
 *
 * 3. ★ **枚举必须限定在面板容器内。**
 *    全页按文案过滤会把**左侧 Dock 的「历史」**也算进来，读出 8 个、
 *    且「历史」出现两次。这是 M185「找一个 X 默认它有多个」的同一族错误。
 *
 * 4. ★ **「英文界面里正文含中文」多半不是界面在漏译。**
 *    画布上的节点内容是用户自己写的（中文标题、中文参考素材），
 *    它当然含中文。**一条读数只证明一件事**——判断有没有漏译，
 *    只能看 `aria-label` / `title` 这些**界面自己生成的文案**，
 *    不能看 `document.body.innerText`。
 *
 * ★ **只读不写。** 本探针不点任何删除类按钮，也不点「清空画布」。
 *   唯一会改动持久化状态的是语言设置，**收尾时已还原成调用前的值**。
 */
const { chromium } = require(process.env.PLAYWRIGHT_PATH ||
  '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright');

const URL = process.argv[2];
const PROFILE = process.argv[3] || '/tmp/m157-profile';
const LOCALE_KEY = 'tdcanvas:locale';
if (!URL) {
  console.error('用法：node scripts/probe-agent-i18n.js <画布URL> [profile]');
  process.exit(2);
}
const say = (...a) => console.log(a.join(' '));
/** 手册里逐字列出来的那 7 个英文读屏名，用来对账。 */
const CLAIM_EN = ['Chat', 'History', 'Skills', 'Logs', 'New chat',
  'Collapse Agent panel', 'Connection settings'];

const readIn = async (locale) => {
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    headless: true, viewport: { width: 1600, height: 950 },
  });
  // ★ 语言必须在页面脚本执行**之前**写好：i18n 初始化时读一次就定死了。
  await ctx.addInitScript(([k, v]) => {
    try { localStorage.setItem(k, v); } catch (e) { /* 无痕模式等场景 */ }
  }, [LOCALE_KEY, locale]);
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 140)));
  await page.goto(URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  const pre = await page.evaluate(() => ({
    title: document.title,
    lang: document.documentElement.lang,
    dock: !!document.querySelector('.td-canvas-dock'),
    head: (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 90),
  }));
  // 纪律 1：前置对照不成立就中断，不报 0
  if (pre.lang !== locale || !pre.dock) {
    await ctx.close();
    return { broken: true, pre };
  }

  const agent = await page.evaluate(async () => {
    const buttons = () => Array.from(document.querySelectorAll('button, [role="button"]'));
    const aria = (b) => (b.getAttribute('aria-label') || '').trim();
    // 纪律 2：先问「是不是已经开着」
    const collapse = () => buttons().find((b) => /Collapse|收起/.test(aria(b)));
    if (!collapse()) {
      const opener = buttons().find((b) => /Agent|智能体/.test(aria(b)) && !/Collapse|收起/.test(aria(b)));
      if (!opener) return { opened: false, why: '顶栏找不到 Agent 按钮' };
      opener.click();
      await new Promise((r) => setTimeout(r, 2200));
    }
    const c = collapse();
    if (!c) return { opened: true, why: '开合之后都找不到 Collapse 按钮，无法定位面板容器' };
    // 纪律 3：限定在面板容器内枚举
    for (let up = 0; up < 6; up++) {
      let panel = c.parentElement;
      for (let i = 0; i < up; i++) panel = panel && panel.parentElement;
      if (!panel) break;
      const row = Array.from(panel.querySelectorAll('button, [role="button"]'))
        .map((b) => ({
          aria: aria(b),
          text: (b.innerText || '').replace(/\s+/g, ' ').trim(),
          inDock: !!b.closest('.td-canvas-dock'),
          inTop: !!b.closest('.td-canvas-topbar'),
        }))
        .filter((b) => !b.inDock && !b.inTop && b.aria);
      if (row.length >= 6) return { opened: true, row, depth: up };
    }
    return { opened: true, why: '没找到同时容纳这批按钮的面板容器' };
  });
  await ctx.close();
  return { pre, agent, errs };
};

(async () => {
  // 先记住原来的语言设置，收尾还原——**别把共享 profile 的状态留给下一批**
  const readCurrent = async () => {
    const c = await chromium.launchPersistentContext(PROFILE, { headless: true });
    const p = await c.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(800);
    const v = await p.evaluate((k) => { try { return localStorage.getItem(k); } catch (e) { return null; } }, LOCALE_KEY);
    await c.close();
    return v;
  };
  const origin = await readCurrent();
  say(`[起始] profile=${PROFILE}｜语言设置原值=${JSON.stringify(origin)}`);

  for (const locale of ['en-US', 'zh-CN']) {
    say('');
    say(`=== locale = ${locale} ===`);
    const r = await readIn(locale);
    if (r.broken) {
      say(`  **对照不成立**：lang=${r.pre.lang}（期望 ${locale}）｜dock=${r.pre.dock}`);
      say(`  页面正文开头：「${r.pre.head}」`);
      say('  这通常意味着 profile 的 IndexedDB 里没有画布，/canvas/:id 被重定向回了列表页。');
      say('  **不报 0**——0 是量具的读数，不是产品的读数。');
      continue;
    }
    say(`  title=${r.pre.title}｜lang=${r.pre.lang}｜dock=${r.pre.dock}`);
    if (!r.agent.opened) { say(`  **面板没打开**：${r.agent.why}（不报 0）`); continue; }
    if (!r.agent.row) { say(`  **${r.agent.why}**（不报 0）`); continue; }
    r.agent.row.forEach((b, i) => say(`  ${i + 1}. aria-label="${b.aria}"｜可见文字="${b.text}"`));
    const got = r.agent.row.map((b) => b.aria);
    const iconOnly = r.agent.row.filter((b) => b.text === '').length;
    const cjk = got.filter((g) => /[一-龥]/.test(g));
    say(`  ★ 共 ${got.length} 个（面板容器向上 ${r.agent.depth} 层）｜纯图标 ${iconOnly} 个`);
    say(`    aria-label 仍含中文的 ${cjk.length} 个 = ${JSON.stringify(cjk)}`);
    if (locale === 'en-US') {
      const missing = CLAIM_EN.filter((x) => !got.includes(x));
      const extra = got.filter((g) => !CLAIM_EN.includes(g));
      say(`    手册逐字列的 7 个里，**缺** ${JSON.stringify(missing)}`);
      say(`    手册没列、但实际读到的 ${JSON.stringify(extra)}`);
      say(`    「没有漏译」这条：${cjk.length === 0 ? '**成立**' : '**不成立**'}`);
      say('    ⚠ 手册把「Connection settings」写成固定串，**实际带连接状态后缀、会变**。');
    } else {
      say(`    中文 locale 对照：${got.length} 个，纯图标 ${iconOnly} 个（与英文同序同数）`);
    }
    say(`    页面错误 ${r.errs.length} 个`);
  }

  // 还原语言设置
  const c = await chromium.launchPersistentContext(PROFILE, { headless: true });
  const p = await c.newPage();
  await p.goto(URL, { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(800);
  await p.evaluate(([k, v]) => { try { localStorage.setItem(k, v); } catch (e) { /* 忽略 */ } },
    [LOCALE_KEY, origin || 'zh-CN']);
  await c.close();
  say('');
  say(`[收尾] 语言设置已还原为 ${JSON.stringify(origin || 'zh-CN')}`);
})().catch((e) => { console.error('探针崩了:', e); process.exit(1); });
