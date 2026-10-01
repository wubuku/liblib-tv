// 探针 04 —— 只读：把首页/项目页上那个挡住操作促销模态的 DOM 结构原样打印出来，
// 目的是找出真实可点的关闭控件（aria / role / 位置），而不是猜。
import { launch, open, ORIGIN } from './lib.mjs';

const { browser, page } = await launch();

try {
  await open(page, `${ORIGIN}/project`, { settle: 2500 });
  const dump = await page.evaluate(() => {
    const root = document.querySelector('.mantine-Modal-root') || document.querySelector('.mantine-Modal-overlay');
    if (!root) return { found: false };
    const out = [];
    root.querySelectorAll('*').forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) return;
      const label = el.getAttribute('aria-label');
      const text = (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 30);
      if (!label && !text) return;
      out.push({
        tag: el.tagName,
        role: el.getAttribute('role'),
        aria: label,
        cls: (el.className || '').toString().slice(0, 60),
        text,
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        clickable: getComputedStyle(el).pointerEvents,
      });
    });
    return {
      found: true,
      modalRootHtml: root.outerHTML.slice(0, 400),
      nodes: out.filter((n) => n.role || n.aria || n.tag === 'BUTTON' || n.tag === 'A').slice(0, 40),
    };
  });
  console.log(JSON.stringify(dump, null, 1));
} finally {
  await browser.close();
}
