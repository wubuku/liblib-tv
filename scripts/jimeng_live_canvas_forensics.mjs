// 无头 + 独立 profile 对**活站点**做只读取证，产出稳定结构的 JSON。
// 纪律：绝不点击生成/发送/购买/充值；只读 DOM，不改任何状态。
// 输出路径可用 JIMENG_FORENSICS_OUT 覆盖（默认 /tmp/b1031-live-fresh.json）。
import pw from '/Users/yangjiefeng/node_modules/playwright/index.js';
const fs = await import('node:fs');
const { chromium } = pw;

const PROFILE = process.env.JIMENG_PROFILE || '/tmp/jimeng-manual-profile';
const URL = process.env.JIMENG_CANVAS_URL ||
  'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create';
const OUT = process.env.JIMENG_FORENSICS_OUT || '/tmp/b1031-live-fresh.json';

const ctx = await chromium.launchPersistentContext(PROFILE, {
  headless: true, viewport: { width: 1600, height: 1000 },
  locale: 'zh-CN', timezoneId: 'Asia/Shanghai',
});
const page = ctx.pages()[0] || await ctx.newPage();
await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(9000);

const body = await page.evaluate(() => document.body ? document.body.innerText : '');
const clickables = await page.evaluate(() => {
  const vis = (el) => {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && st.visibility !== 'hidden' && st.display !== 'none';
  };
  const bag = [];
  for (const el of document.querySelectorAll('button,[role=button],a,input,textarea,select,[tabindex],[contenteditable=true]')) {
    if (!vis(el)) continue;
    const tid = el.getAttribute('data-testid') || '';
    const cls = (el.className && typeof el.className === 'string')
      ? '.' + el.className.trim().split(/\s+/).slice(0, 3).join('.') : '';
    bag.push({
      tag: el.tagName.toLowerCase(),
      sel: el.tagName.toLowerCase() + (tid ? `[data-testid="${tid}"]` : '') + cls,
      text: (el.innerText || el.value || '').trim().slice(0, 40),
      aria: el.getAttribute('aria-label') || '',
      role: el.getAttribute('role') || '',
      disabled: el.disabled === true || el.getAttribute('aria-disabled') === 'true',
    });
  }
  return bag;
});

const doc = {
  title: await page.title(),
  url: page.url(),
  body_head: body.slice(0, 3000),
  clickables,
  has_engine: await page.evaluate(() =>
    !!document.querySelector('.react-flow,[class*="react-flow"]')),
  node_counts: await page.evaluate(() => {
    const g = {};
    for (const s of ['[data-node-id]', '[class*="node"]', 'canvas', 'svg']) {
      g[s] = document.querySelectorAll(s).length;
    }
    return g;
  }),
};
fs.writeFileSync(OUT, JSON.stringify(doc, null, 1));
console.log('WROTE ' + OUT + ' title=' + doc.title + ' n_clickables=' + clickables.length);
await ctx.close();
console.log('HEADLESS_CLOSED');