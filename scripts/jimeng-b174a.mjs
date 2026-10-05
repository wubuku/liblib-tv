// 批次 174 a 轮：画布持久化面的**纯静态侦察**（只读，不改任何状态）。
//
// 手册现状（自我降级，立规 34）：
//   持久化只被**顺带**记过 4 处，没有成体系的覆盖 ——
//     canvas-context.md:622 「顶栏 已保存 常驻显示保存状态；改动后自动保存。」
//     canvas-context.md:623 「内容跨刷新持久（实测）：刷新页面后节点与连线完好。」
//     30-concepts.md:118-119 同上 + 撤销历史不跨刷新
//     90-troubleshooting.md:664 一条排障
//   ⇒ 用户真正会问的三个问题**一个都没答**：
//     ①「保存」到底在保存什么？顶栏那个指示器有哪几种状态？
//     ② 换台电脑 / 关掉浏览器再打开，还找得到这份画布吗？
//     ③ 画布 id 在 URL 里，是本地缓存还是账号级数据？
//
// 本轮只做「读得到什么」，不点保存、不导航、不新建。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '174a' };

// ---------------------------------------------------------------- 0. 页面身份
rec.url = p.url();
rec.canvasId = (p.url().match(/ai-canvas\/([0-9a-f-]{36})/) || [])[1] || null;
rec.标题 = await p.title();
rec.页签数 = b.contexts()[0].pages().length;
rec.所有页签URL = await Promise.all(b.contexts()[0].pages().map((x) => x.url()));

// ------------------------------------------------- 1. 顶栏保存指示器：DOM 全貌
// 手册只写了「已保存」三个字。这里把**含「保存」二字的每一个元素**连同
// 祖先链、class、testid、可见性一起打出来 —— 先确认它到底是几个元素、
// 哪几个是同一个指示器的不同态。
rec.保存指示器 = await p.evaluate(() => {
  const 命中 = [];
  for (const e of document.querySelectorAll('body *')) {
    const t = (e.textContent || '').trim();
    if (t !== '已保存' && t !== '保存中' && t !== '未保存' && t !== '保存失败') continue;
    // 只留**最深**的那个（textContent 逐字相等的最小元素）
    if (Array.from(e.children).some((c) => (c.textContent || '').trim() === t)) continue;
    const r = e.getBoundingClientRect();
    const 链 = [];
    for (let n = e; n && n !== document.body; n = n.parentElement) {
      链.push(n.tagName.toLowerCase() +
        (n.getAttribute('data-testid') ? `[testid=${n.getAttribute('data-testid')}]` : '') +
        (n.getAttribute('role') ? `[role=${n.getAttribute('role')}]` : '') +
        (n.className && typeof n.className === 'string' ? `.${n.className.trim().split(/\s+/).join('.')}` : ''));
    }
    命中.push({
      文本: t,
      可见: r.width > 0 && r.height > 0,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      aria: e.getAttribute('aria-label'),
      testid: e.getAttribute('data-testid'),
      title: e.getAttribute('title'),
      自身class: typeof e.className === 'string' ? e.className : null,
      祖先链: 链.slice(0, 6),
    });
  }
  return 命中;
});

// ------------------------------------------- 2. 顶栏全貌：到底有哪些可点的东西
// 「画布列表 / 分享 / 导出 / 重命名」这些入口如果不在顶栏，就得在别处找。
rec.顶栏 = await p.evaluate(() => {
  const 头 = document.querySelector('header,[data-testid*=header],[data-testid*=top-bar],[data-testid*=topbar]');
  const 根 = 头 || document.querySelector('[data-testid="canvas-display-toggle-minimap"]')?.closest('div');
  if (!根) return { 失败: '没找到顶栏容器' };
  const 按钮 = Array.from(根.querySelectorAll('button,a,[role=button],[role=menuitem]')).map((e) => {
    const r = e.getBoundingClientRect();
    return { tag: e.tagName.toLowerCase(), aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
      testid: e.getAttribute('data-testid'), 文本: (e.textContent || '').trim().slice(0, 24),
      禁用: e.disabled === true || e.getAttribute('aria-disabled') === 'true',
      可见: r.width > 0 && r.height > 0, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
  return { 容器: 根.tagName.toLowerCase() + (根.dataset?.testid ? `[testid=${根.dataset.testid}]` : ''),
    容器文字: (根.innerText || '').slice(0, 400), 按钮数: 按钮.length, 按钮 };
});

// -------------------------------------------- 3. 左侧栏/全局导航：画布列表入口
rec.侧栏与导航 = await p.evaluate(() => {
  const 侧 = Array.from(document.querySelectorAll('aside,nav,[role=navigation]')).map((e) => {
    const r = e.getBoundingClientRect();
    return { 可见: r.width > 0, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      文字: (e.innerText || '').replace(/\n+/g, ' | ').slice(0, 300),
      aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid') };
  });
  // 全页搜「画布 / 最近 / 我的」这类导航词。
  // ⚠️ v1 写成「每个词各扫一遍全文档的 textContent」= O(n²)，在 76 节点的画布上**卡死**
  //    （textContent 会遍历整棵子树，76 个节点 ⇒ 十万量级子树重算）。改成**单遍**：
  //    每���元素只算一次 textContent，再一次性比对所有词。
  const 词 = new Set(['我的画布', '画布列表', '最近', '全部画布', '新建画布', '分享', '导出', '画布设置']);
  const 命中 = {};
  for (const e of document.querySelectorAll('button,a,[role=button],[role=menuitem],span,div')) {
    const aria = e.getAttribute('aria-label') || '';
    if (!词.has(aria)) continue;                       // 先按 aria 过滤，绝大多数元素在这里就被丢掉
    const t = (e.textContent || '').trim();
    if (!词.has(t)) continue;
    (命中[aria] ||= []).push(e.tagName.toLowerCase() + '「' + t + '」');
  }
  return { 侧栏: 侧, 导航词: 命中 };
});

// ------------------------------------------------- 4. 存储面：local/session 键
// ⚠️ 只列键名 + 类型 + 长度，**不打印值**（可能有 token 之类的东西）。
rec.存储 = await p.evaluate(() => {
  const 列 = (s) => { const o = {}; try { for (let i = 0; i < s.length; i++) { const k = s.key(i); o[k] = `${s.getItem(k) == null ? 'null' : typeof s.getItem(k)} len=${(s.getItem(k) || '').length}`; } } catch (e) { o['__err'] = String(e); } return o; };
  return { localStorage: 列(localStorage), sessionStorage: 列(sessionStorage),
    cookie名: document.cookie.split(';').map((c) => c.split('=')[0].trim()).filter(Boolean) };
});

// ------------------------------------ 5. 画布状态在 URL / 路由里吗（路由学）
rec.路由线索 = await p.evaluate(() => ({
  href全量: Array.from(document.querySelectorAll('a[href]')).map((a) => a.getAttribute('href')).filter((h) => h && h !== '#'),
  全部testid: Array.from(new Set(Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid'))))
    .filter((t) => /save|share|export|canvas|doc|title|name|menu|header|top|back|home/i.test(t)),
}));

// -------------------------------------------------------------- 6. 基线读数
rec.基线 = { 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom() };

console.log(JSON.stringify(rec, null, 1));

process.exit(0);
