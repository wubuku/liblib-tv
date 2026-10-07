/**
 * 只验活，不登录、不打印任何凭证内容。
 * 权威判据：同源 fetch /passport/account/info/v2/ —— 未登录稳定返回 user_id=0。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const API = '/passport/account/info/v2/?aid=513695&account_sdk_source=web&sdk_version=2.2.6';

console.log('state.json 存在 =', fs.existsSync(STATE));
const st = JSON.parse(fs.readFileSync(STATE, 'utf8'));
console.log('cookie 条数 =', (st.cookies || []).length, '｜origin 条数 =', (st.origins || []).length);

const b = await chromium.launch({ headless: true });
const ctx = await b.newContext({ storageState: STATE, viewport: { width: 1280, height: 720 } });
const p = await ctx.newPage();
await p.goto('https://jimeng.jianying.com/', { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForTimeout(3000);
const 判据 = await p.evaluate(async (api) => {
  try {
    const r = await fetch(api, { credentials: 'include' });
    const j = await r.json();
    return { http: r.status, user_id: j?.data?.user_id ?? null, error_code: j?.data?.error_code ?? null, description: j?.data?.description ?? null, 昵称: j?.data?.nickname ?? null };
  } catch (e) { return { 错误: String(e) }; }
}, API);
console.log('账户判据 =', JSON.stringify(判据));

await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForTimeout(18000);
const 画布 = await p.evaluate(() => ({
  节点数: document.querySelectorAll('.react-flow__node').length,
  正文前200: (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 200),
  积分: (document.querySelector('[data-testid="canvas-commerce-entry"]') || {}).textContent || null,
}));
console.log('画布 =', JSON.stringify(画布));
await ctx.close();
await b.close();
process.exit(0);
