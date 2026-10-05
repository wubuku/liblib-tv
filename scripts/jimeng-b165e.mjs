// 批次 165-e —— 把「行为测出来的定律」和「样式表里逐字的声明」**接上**。
//
// 🔑 165-a~d 全靠黑盒量法，得出两条定律：
//     宽 = min(801, 视口宽 − 32)   门槛 833/832
//     高 = min(620, 视口高 − 32)   门槛 652/651
//   165-d 用「改根字号」排除了 rem（20px 根字号下钳位纹丝不动）。
//   本轮把源站的 CSS 直接抓下来（curl，**不是页面内 fetch —— 页面内 3 张样式表全是
//   lf3-lv-buz.vlabstatic.com 跨域，cssRules 抛异常、fetch 也被 CORS 挡掉，同源 0 张），
//   于是拿到了**逐字声明**：
//     .w-[min(801px,calc(100vw-32px))]{width:min(801px,calc(100vw - 32px))}
//     .h-[min(620px,calc(100vh-32px))]{height:min(620px,calc(100vh - 32px))}
//   ⇒ 行为定律与声明**逐字吻合**，且「32 是 px 不是 rem」得到第二次独立确认。
//
// 🔴 本轮真正值钱的副产品：**这些模态尺寸是 Tailwind 任意值类名，全部写在那一个 CSS 文件里**
//   ⇒ 「某个模态在什么分辨率下是什么尺寸」从此**不必开浏览器**，
//   可以把源站 CSS 抓下来 grep 一次就得到**全站模态尺寸清单**。
//   本轮顺手把该文件里所有 min(...)/max-h/min(...) 尺寸声明导出，作为下一批的输入。
//
// ⛔ 只读：共享页签上只开一次「资产库」模态读 className，立刻 Esc；不改任何画布数据。
import fs from 'node:fs';
import { execSync } from 'node:child_process';
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';

const CSS_URL = 'https://lf3-lv-buz.vlabstatic.com/obj/image-lvweb-buz/ies/lvweb/octo_web/static/css/main.94b57a0e55.css';
const CSS_LOCAL = '/tmp/jimeng-main.94b57a0e55.css';
const rec = { 批次: '165e', 目的: '把运行时 class 与源站 CSS 里的尺寸声明对上，并导出全站模态尺寸清单' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' → ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b165e.json', import.meta.url), JSON.stringify(rec, null, 1));

// ---- ① 静态：导出源站 CSS 里所有「响应式尺寸」声明 ----
try {
  if (!fs.existsSync(CSS_LOCAL)) execSync(`curl -s -m 30 -o ${CSS_LOCAL} ${CSS_URL}`);
} catch (e) { rec.css抓取异常 = String(e).slice(0, 200); }
const css = fs.existsSync(CSS_LOCAL) ? fs.readFileSync(CSS_LOCAL, 'utf8') : '';
rec.css字节 = css.length;
const 全部尺寸类 = [];
const re = /\.((?:max-)?[wh])-\[([^\]]+?\]\]|h-\[min\\\([^\]]+)\{([^}]+)\}/g;
// 逐条扫描 `.<prop>-[<value>]{<declaration>}` 形式（类名里的 ] 已被转义成 \]）
for (const m of css.matchAll(/\.((?:max-)?[wh]|size)-(\[(?:\\.|[^\]])*?\])\{([^}]+)\}/g)) {
  const 值 = m[2].replace(/\\\]/g, ']');
  if (!/vw|vh|%/.test(值)) continue;                    // 只留与视口/百分比相关的
  全部尺寸类.push({ 类名: '.' + m[1] + '-' + 值, 声明: m[3] });
}
const 去重 = []; const 见过类 = new Set();
for (const z of 全部尺寸类) { if (!见过类.has(z.类名)) { 见过类.add(z.类名); 去重.push(z); } }
rec.尺寸类总数 = 全部尺寸类.length;
rec.唯一尺寸类 = 去重.length;
rec.含min的尺寸类 = 去重.filter((z) => /min\(/.test(z.声明));
console.log(`CSS ${rec.css字节} 字节 ｜ 视口相关尺寸声明 ${rec.尺寸类总数} 条 ／ 去重 ${rec.唯一尺寸类} 条 ／ 其中 min() ${rec.含min的尺寸类.length} 条`);
for (const z of rec.含min的尺寸类) console.log('   ' + z.声明);
落盘();

// ---- ② 运行时：读对话框的完整 class，逐字对上面的声明 ----
const { b, p } = await openCanvas();
const R = readers(p);
try {
  const 起点 = { 状态行: await R.status(), 节点数: (await R.ids()).length, 积分: await R.credits() };
  rec.起点 = 起点;
  const 钮 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button,[role=button]'))
    .find((x) => (x.getAttribute('aria-label') || '') === '资产库'); if (!e) return null;
    const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  断言('⓪ 左栏找得到「资产库」按钮', !!钮, { 钮 });
  if (钮) {
    await p.mouse.click(钮[0], 钮[1]);
    let d = null;
    for (let k = 0; k < 8 && !d; k++) { await p.waitForTimeout(650); d = await p.evaluate(() => document.querySelector('[data-testid="canvas-asset-library-dialog"]') || null); }
    if (d) {
      rec.对话框 = await p.evaluate(() => {
        const e = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
        const r = e.getBoundingClientRect();
        const 层 = ['canvas-asset-library-surface', 'canvas-asset-library-operation-area', 'canvas-asset-library-viewport', 'canvas-asset-library-footer']
          .map((t) => { const x = document.querySelector(`[data-testid="${t}"]`); const q = x.getBoundingClientRect();
            return { testid: t, 盒: [Math.round(q.width), Math.round(q.height)], 尺寸类: (x.className || '').split(/\s+/).filter((c) => /^(w|h|max-w|max-h|min-w|min-h)-/.test(c)) }; });
        return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
          classList: (e.className || '').split(/\s+/),
          尺寸类: (e.className || '').split(/\s+/).filter((c) => /^(w|h|max-w|max-h|min-w|min-h)-/.test(c)), 层 };
      });
      console.log('对话框尺寸类 =', JSON.stringify(rec.对话框.尺寸类));
      console.log('四层尺寸类 =', JSON.stringify(rec.对话框.层.map((z) => z.尺寸类)));
      const W = rec.对话框.尺寸类.find((c) => c.startsWith('w-[') && /801/.test(c));
      const H = rec.对话框.尺寸类.find((c) => c.startsWith('h-[') && /620/.test(c));
      rec.对上类名 = { W, H };
      断言('① 运行时 class 里带着 `w-[min(801px,calc(100vw-32px))]`', !!W, rec.对话框.尺寸类);
      断言('② 运行时 class 里带着 `h-[min(620px,calc(100vh-32px))]`', !!H, rec.对话框.尺寸类);
      // 那条声明在 CSS 里必须逐字存在（把 CSS 证据与运行时连起来）
      const css有W = new RegExp('width:\\s*min\\(801px\\s*,\\s*calc\\(100vw - 32px\\)\\)').test(css);
      const css有H = new RegExp('height:\\s*min\\(620px\\s*,\\s*calc\\(100vh - 32px\\)\\)').test(css);
      rec.css逐字 = { css有W, css有H };
      断言('③ 源站 CSS 里逐字存在这两条声明', css有W && css有H, rec.css逐字);
      落盘();
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 800); console.log('异常', rec.异常); }
finally {
  for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
  try { await settle(p, R); } catch (e) {}
  const 收尾 = { 状态行: await R.status(), 节点数: (await R.ids()).length, 选中: await R.selCount(), 浮层: await R.overlays(), 积分: await R.credits() };
  rec.收尾 = 收尾;
  console.log('收尾', JSON.stringify(收尾));
  断言('④ 收尾回到起点（76 节点 / 0 选中 / 浮层 0 / 积分不变）',
    收尾.节点数 === 76 && 收尾.选中 === 0 && 收尾.浮层 === 0 && String(收尾.积分) === String(rec.起点 && rec.起点.积分), { 起点: rec.起点, 收尾 });
  rec.断言全过 = 断言过; 落盘();
  console.log('\n断言全过 =', 断言过);
}
process.exit(0);
