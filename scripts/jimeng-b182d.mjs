// 批次 182 d 轮：**给否定读数补最后一道守卫 —— 按键到底能不能改剪贴板。**
//
// c 轮五格一致：按 `Meta+C` 后剪贴板一字未动。v1 那格甚至和批次 178 的做法逐字一样
// （无哨兵、无监听、`readText`），仍然复现不出 178 的 17 字 ⇒ 178 的读数有问题。
//
// 🔴 但**否定读数必须先证明「这个环境里按键能改剪贴板」**，否则下面两种情况分不开：
//   「应用什么都没做」 vs 「这个环境里按键根本改不动剪贴板」。
// c 轮的哨兵是 `navigator.clipboard.writeText()` 写的 —— 那是**页面 API**，
// 它能写**不能**推出「**按键触发的 copy** 能写」。
//
// 本轮做两件事：
//   ① **正向守卫**：在页面上做一个**真实 DOM 文本选区**，按 `Meta+C`，
//      看剪贴板有没有变成那段文字。成了 ⇒ 按键路径在这套环境里是通的，
//      于是 c 轮的「没变」只能解释成「应用没写」。
//   ② 顺带回答一个 c 轮没问的问题：应用的 copy handler 是不是**只在有文本选区时才工作** ——
//      如果①里剪贴板变成的是**选区文字**（原生复制），就说明应用 handler 压根没插手；
//      如果变成的是**别的**东西，那才说明应用接管了。
//
// ⛔ 不生成、不分享、不下载、不点「保存到主体库」。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '182d' };
try {
  const g = await b.contexts()[0].newCDPSession(p);
  await g.send('Browser.grantPermissions', { permissions: ['clipboardReadWrite', 'clipboardSanitizedWrite'], origin: 'https://jimeng.jianying.com' });
  rec.剪贴板权限 = '已授予';
} catch (e) { rec.剪贴板权限 = '授予失败: ' + String(e).slice(0, 80); }
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);

const 读全部 = () => p.evaluate(async () => {
  const 超时 = new Promise((r) => setTimeout(() => r({ 读成功: false, 错误: '2.5 秒没返回' }), 2500));
  const 真读 = (async () => { try { const items = await navigator.clipboard.read(); const out = [];
      for (const it of items) for (const t of it.types) { const o = { type: t, 字节: null, 文本: null };
        try { const b0 = await it.getType(t); o.字节 = b0.size; if (t.startsWith('text/')) o.文本 = (await b0.text()).slice(0, 120); } catch (e) { o.错误 = String(e).slice(0, 60); }
        out.push(o); }
      return { 读成功: true, 明细: out }; } catch (e) { return { 读成功: false, 错误: String(e).slice(0, 100) }; } })();
  return Promise.race([真读, 超时]);
});
const 写哨兵 = (s) => p.evaluate(async (t) => { try { await navigator.clipboard.writeText(t); return '写成功'; } catch (e) { return '写失败: ' + String(e).slice(0, 80); } }, s);

rec.起点 = { 节点数: await p.evaluate(() => document.querySelectorAll('.react-flow__node').length), 积分: await R.credits() };

// ═════════ ① 正向守卫：造一个**内容非空且我能逐字预知**的文本选区，按 Meta+C
rec['①文本选区按MetaC'] = {};
// 📌 d 轮第二次才做对，两次踩到的坑都记在这：
//   ① 标题元素的直接子节点是 `svg` + `SPAN`，**没有直接文本节点** —— 只在 childNodes
//      里找 nodeType===3 一定返回空。必须在**后代**里用 TreeWalker 走树。
//   ③ 即使元素选对了，用 TreeWalker 找文本节点时**必须跳过 `STYLE` / `SCRIPT` 的父节点** ——
//      `<style>` 的内容也是文本节点，TreeWalker 会先撞上它，
//      `selectNodeContents` 到 `<style>` 里之后 `getSelection().toString()` **恒为 ""**
//      （不可见内容不进选区）⇒ 守卫自身变成假阳性。
//   ⇒ 正向守卫的写法必须是：**先断言选区文字非空，再按 ⌘C**。
rec['①文本选区按MetaC'].哨兵 = await 写哨兵('SENTINEL-182D-别选我');
rec['①文本选区按MetaC'].剪贴板前 = await 读全部();

const 造选区 = await p.evaluate(() => {
  const 跳过 = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE']);
  for (const el of Array.from(document.querySelectorAll('div,span,p,section,footer,header'))) {
    const t = (el.textContent || '');
    if (!(t.includes('nodes,') && t.includes('edges,'))) continue;
    if (el.children.length > 4) continue;
    const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null);
    let n; while ((n = w.nextNode())) {
      if (跳过.has(n.parentElement?.tagName)) continue;
      const txt = (n.textContent || '').trim();
      if (txt.length > 15) {
        const r = document.createRange(); r.selectNodeContents(n);
        const s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
        const 选中 = s.toString();
        // 🔴 守卫自身的非空断言：选区空 ⇒ 这次按 ⌘C 说明不了任何事，直接放弃这一格
        if (选中.length > 0) return { 成功: true, 选区文字: 选中, 选区长度: 选中.length, 元素: el.tagName, 父: n.parentElement?.tagName };
      }
    }
  }
  return { 成功: false, 原因: '找不到可选取的、可见且足够长的文本节点' };
});
rec['①文本选区按MetaC'].造选区 = 造选区;
if (造选区.成功) {
  await p.waitForTimeout(300);
  rec['①文本选区按MetaC'].按前选区 = await p.evaluate(() => window.getSelection().toString());
  await p.keyboard.press('Meta+c'); await p.waitForTimeout(2000);
  rec['①文本选区按MetaC'].按后 = await 读全部();
  rec['①文本选区按MetaC'].剪贴板变成了选区文字 =
    rec['①文本选区按MetaC'].按后.读成功 && rec['①文本选区按MetaC'].按后.明细.some((x) => x.文本 === 造选区.选区文字);
  rec['①文本选区按MetaC'].仍然等于哨兵 =
    rec['①文本选区按MetaC'].按后.读成功 && rec['①文本选区按MetaC'].按后.明细.some((x) => (x.文本 || '').includes('SENTINEL-182D'));
  await p.evaluate(() => window.getSelection().removeAllRanges());
}
await p.keyboard.press('Escape'); await p.waitForTimeout(600);

// ═════════ ② 对照：没有选区时按 Meta+C（= c 轮的 V1，但这次在 ① 之后、同一进程）
rec['②无选区按MetaC'] = {};
rec['②无选区按MetaC'].哨兵 = await 写哨兵('SENTINEL-182D-第二次');
rec['②无选区按MetaC'].剪贴板前 = await 读全部();
rec['②无选区按MetaC'].选区数 = await p.evaluate(() => window.getSelection().rangeCount);
await p.keyboard.press('Meta+c'); await p.waitForTimeout(2000);
rec['②无选区按MetaC'].按后 = await 读全部();
rec['②无选区按MetaC'].仍然等于哨兵 =
  rec['②无选区按MetaC'].按后.读成功 && rec['②无选区按MetaC'].按后.明细.some((x) => (x.文本 || '').includes('SENTINEL-182D'));

await p.keyboard.press('Escape'); await p.waitForTimeout(600);
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 40000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(400); }
await p.waitForTimeout(2500);
rec.收尾 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(),
  节点数: await p.evaluate(() => document.querySelectorAll('.react-flow__node').length), 浮层: await R.overlays() };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
