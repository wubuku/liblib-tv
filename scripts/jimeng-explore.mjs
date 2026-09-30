// 即梦画布取证工具：只读快照 + 受控点击 + 高亮截图。
// 计费边界：绝不点击 生成/发送/局部重拍/智能超清/视频编辑/补帧/智能改图/配音 等
// 会提交按积分计费任务的按钮。BLOCKED 列表在点击前硬拦截。
// 用法：node scripts/jimeng-explore.mjs <command> [args]
import { chromium } from 'playwright';

const CDP = 'http://127.0.0.1:9444';
const CANVAS =
  'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';

// 计费边界：命中即拒绝点击
const BLOCKED = [
  '生成', '发送', '局部重拍', '智能超清', '视频编辑', '补帧', '深度动作捕捉',
  '提示词反推', '智能改图', '配音', '音频生成', '立即创作', '确认生成',
];

const browser = await chromium.connectOverCDP(CDP);
const ctx = browser.contexts()[0];
const page = ctx.pages().find((p) => p.url().includes('jimeng.jianying.com')) || ctx.pages()[0];

function assertSafe(text) {
  for (const b of BLOCKED) {
    if (text && text.includes(b)) {
      throw new Error(`拒绝点击：命中计费边界关键词「${b}」（原文：${text}）`);
    }
  }
}

const cmd = process.argv[2];

if (cmd === 'snapshot') {
  const s = await page.evaluate(() => {
    const nodes = Array.from(document.querySelectorAll('.react-flow__node'));
    return {
      url: location.href,
      status: document.body.innerText.match(/[\d]+ nodes,[\s\S]{0,80}/)?.[0]?.replace(/\s+/g, ' '),
      nodeCount: nodes.length,
      nodes: nodes.map((n) => ({
        id: (n.getAttribute('data-id') || '').slice(0, 28),
        cls: n.className,
        rect: (({ x, y, width, height }) => ({ x: Math.round(x), y: Math.round(y), w: Math.round(width), h: Math.round(height) }))(n.getBoundingClientRect()),
        text: n.innerText.replace(/\s+/g, ' ').slice(0, 90),
      })),
      handles: document.querySelectorAll('.react-flow__handle').length,
      edges: document.querySelectorAll('.react-flow__edge').length,
      toolbar: document.querySelector('.react-flow__node-toolbar')?.innerText.replace(/\s+/g, ' ') || null,
    };
  });
  console.log(JSON.stringify(s, null, 2));
} else if (cmd === 'rail') {
  // 列出左栏入口的 aria-label（只读）
  const rails = await page.evaluate(() =>
    Array.from(document.querySelectorAll('[aria-label]'))
      .map((e) => e.getAttribute('aria-label'))
      .filter((l) => l && l.length < 12)
      .filter((l, i, a) => a.indexOf(l) === i)
  );
  console.log(JSON.stringify(rails));
} else if (cmd === 'click') {
  const label = process.argv[3];
  assertSafe(label);
  const ok = await page.evaluate((l) => {
    const el = Array.from(document.querySelectorAll('button,[role="button"],[aria-label]'))
      .find((e) => (e.getAttribute('aria-label') || e.innerText || '').trim() === l);
    if (!el) return false;
    el.click();
    return true;
  }, label);
  console.log(ok ? `clicked: ${label}` : `NOT FOUND: ${label}`);
  await page.waitForTimeout(1500);
} else if (cmd === 'shot') {
  const out = process.argv[3];
  await page.screenshot({ path: out });
  console.log('saved', out);
}

await browser.close();
