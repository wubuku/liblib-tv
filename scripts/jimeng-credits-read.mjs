/**
 * 只读探针：读画布页上的**积分显示**与资源行，用来核对「收尾时积分是否变化」这条纪律。
 *
 * 📌 **为什么要单独写这个**（批次 248 收尾时发现的）：
 *   `scripts/jimeng-headless.mjs` 的启动日志报 `Credits: 725 · 基础会员`，
 *   而 PROGRESS.md 里连续十几个批次记的都是「**积分 813**」。
 *   ⇒ **这是一个真实的读数变化，不能当成噪声，也不能默认是我这批消耗的**
 *   （本批全程只做「搜索定位 + 缩放按键」，**未触发生成**）。
 *   ⇒ 本探针**只读、连开两页各读一次**，用来区分「稳定读数」与「偶发串台」。
 *
 * 🔴 纪律：只读。**不点任何按钮**、不新建、不删除、不上传、不触发生成、
 *   不进入扣费/购买页、不点「保存到主体库」、不分享。每读完一页就关掉。
 *
 * 用法：node scripts/jimeng-credits-read.mjs
 */
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (let i = 1; i <= 2; i++) {
  const p = await ctx.newPage();
  try {
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(8000);
    const r = await p.evaluate(() => {
      const t = document.body.innerText || '';
      // 🔴 积分显示**不一定落在 innerText 里**（首次读数返回 null），
      //   所以这里从整棵 DOM 的文本节点里正则捞，并**同时**记下捞到它的元素
      const 全树文本 = (document.documentElement.innerText || '') + '\n' +
        Array.from(document.querySelectorAll('*'))
          .filter((e) => e.children.length === 0)
          .map((e) => e.textContent || '')
          .join('\n');
      const 积分 = (全树文本.match(/Credits:\s*\d+[^一-鿿\n]*/) || [])[0] || null;
      // 🔴 第二次读数发现：**积分值只在 aria-label 里，文本流里根本没有**
      //   ⇒ 只扫 innerText 会永远读到 null，这本身就是一条该记的取数纪律
      const aria积分 = Array.from(document.querySelectorAll('[aria-label]'))
        .map((e) => e.getAttribute('aria-label') || '')
        .filter((a) => /Credits/.test(a));
      return {
        积分文本节点: 积分,
        积分aria: aria积分,
        积分: (aria积分[0] || 积分),
        状态行: (t.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
        节点数: document.querySelectorAll('.react-flow__node').length,
        资源行: (t.match(/\d+ resource[^\n]*/) || [])[0] || null,
      };
    });
    console.log(`读数 ${i}:`, JSON.stringify(r));
  } catch (e) {
    console.log(`读数 ${i} 出错:`, e.message);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
  }
}
await b.close();
