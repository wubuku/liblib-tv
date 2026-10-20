// 无头 + 独立 profile 对**活站点**做只读取证，产出稳定结构的 JSON。
// 纪律：绝不点击生成/发送/购买/充值；只读 DOM，不改任何状态。
// 输出路径可用 JIMENG_FORENSICS_OUT 覆盖（默认 /tmp/b1031-live-fresh.json）。
import pw from '/Users/yangjiefeng/node_modules/playwright/index.js';
const fs = await import('node:fs');
const { chromium } = pw;

const PROFILE = process.env.JIMENG_PROFILE || '/tmp/jimeng-manual-profile';
// ⭐⭐⭐⭐⭐ 1032-①：登录态的**真源**现在有两个形态，只认 persistent profile 会**静默降级**：
//   · persistent profile（`/tmp/jimeng-manual-profile`）—— `/tmp` 会被清空 ⇒ 常常凭空消失
//   · storageState（`~/.jimeng-automation/state.json`，chmod 600）—— `scripts/jimeng_auth.py`
//     里的 `STATE`，由 `scripts/jimeng_login_capture.py` 捕获，且**当场用无头 Chrome 验证过可用**
//   ⇒ 之前只认前者 ⇒ profile 一被清空，探针就**记 null 降级**（而不是报「没登录」），
//     而 1015 那种跑法只看 rc ⇒ **「没测到」被当成「测过没红」**。
//   ⇒ 现在两者都认，且**优先 storageState**（它不在 /tmp，不会被清）。
const STATE_JSON = process.env.JIMENG_STATE_JSON
  || (await import('node:os')).homedir() + '/.jimeng-automation/state.json';
const USE_STATE = fs.existsSync(STATE_JSON);
const URL = process.env.JIMENG_CANVAS_URL ||
  'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create';
const OUT = process.env.JIMENG_FORENSICS_OUT || '/tmp/b1031-live-fresh.json';

const LAUNCH = {
  headless: true, viewport: { width: 1600, height: 1000 },
  locale: 'zh-CN', timezoneId: 'Asia/Shanghai',
};
// ⚠️ 两条通路的**登录态等价性**已由 `jimeng_login_capture.py` 用无头 Chrome 验过
//   （`headless logged_in : True`）⇒ 这里用它不算「换了测量仪器」。
let _browser = null;
const ctx = USE_STATE
  ? await ((_browser = await chromium.launch(LAUNCH)),
           _browser.newContext({ ...LAUNCH, storageState: STATE_JSON }))
  : await chromium.launchPersistentContext(PROFILE, LAUNCH);
console.error(`[forensics] 登录态来源: ${USE_STATE ? 'storageState ' + STATE_JSON : 'persistent profile ' + PROFILE}`);
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
// ⭐⭐⭐⭐⭐ 1032-①：storageState 通路用的是 `chromium.launch()` + `newContext()`，
//   **只关 context 不关 browser ⇒ Node 的事件循环不会空 ⇒ 进程不退出**
//   ⇒ 上游 1031 探针的 `subprocess.run(timeout=300)` 会**超时**，
//   而**产物其实早就写好了** ⇒ 症状是「探针崩了」，真相是「探针挂住了」。
//   ⚠️ 这正是「量错了 ≠ 产品坏了」的又一种形态：**仪器自己没退出，被读成被测对象失败**。
//   ⇒ persistent profile 通路没有这个问题（`launchPersistentContext` 返回的就是 browser）。
if (_browser) await _browser.close();
console.log('HEADLESS_CLOSED');