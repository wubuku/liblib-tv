// 批次 165-f —— 静态产物：把源站 CSS 里**所有与视口相关的尺寸声明**导出成清单。
//
// 🔑 165-e 的副产品（也是本轮最值钱的一条方法论）：
//   模态尺寸是 **Tailwind 任意值类名**（`w-[min(801px,calc(100vw-32px))]`），
//   全部写死在一个 CSS 文件里 ⇒ **「某模态在多分辨率下多大」不必开浏览器**。
//   页面内读不到（3 张样式表全是 lf3-lv-buz.vlabstatic.com 跨域：cssRules 抛、fetch 被 CORS 挡），
//   但**在 Node 里 curl 同一个 URL 是通的** ⇒ 静态这条路走得通。
//
// 🔴 165-e 首版正则的教训（自身失误 2）：
//   我按 `.\[ … \]{…}` 去匹配，结果 **0 条**。原因是 Tailwind 把类名里的特殊字符转义了：
//     逗号 → `\2c `、右方括号 → `\]`、圆括号 → `\(` `\)`
//   ⇒ 「类名以字面 `]` 结尾」这个假设不成立。正解：**从声明侧倒着抓**
//     （凡是声明里含 vw/vh/% 的规则块，把它的选择器一并带出来），再反转义。
//
// 📌 用法：`node scripts/jimeng-b165f-inventory.mjs` → 落 `scripts/_tmp-b165f.json`。
import fs from 'node:fs';
import { execSync } from 'node:child_process';

const CSS_URL = 'https://lf3-lv-buz.vlabstatic.com/obj/image-lvweb-buz/ies/lvweb/octo_web/static/css/main.94b57a0e55.css';
const CSS_LOCAL = '/tmp/jimeng-main.94b57a0e55.css';
const OUT = new URL('./_tmp-b165f.json', import.meta.url);

if (!fs.existsSync(CSS_LOCAL)) {
  console.log('下载源站 CSS …');
  execSync(`curl -s -m 40 -o ${CSS_LOCAL} ${CSS_URL}`);
}
const css = fs.readFileSync(CSS_LOCAL, 'utf8');
const rec = { 产物: 'b165f', 目的: '源站 CSS 中所有视口相关的宽高声明清单', css字节: css.length, css来源: CSS_URL, 清单: [] };

// 反转义：Tailwind 类名里的 `\2c ` → `,`、`\]` → `]`、`\(`→`(`、`\)`→`)`、`\.`→`.`
const 解转义 = (s) => s.replace(/\\2c\s?/g, ',').replace(/\\\]/g, ']').replace(/\\\(/g, '(').replace(/\\\)/g, ')').replace(/\\\//g, '/');

const 尺寸属性 = /^(max-)?(min-)?(width|height)$/;
for (const m of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
  const 选择器 = m[1], 声明 = m[2];
  if (!/\b(?:max-|min-)?(?:width|height)\s*:/.test(声明)) continue;
  if (!/(?:v[w|h]|\d+%)/.test(声明)) continue;                     // 只留跟视口/百分比挂钩的
  for (const one of 选择器.split(',')) {
    const sel = one.trim();
    if (!/^\.[\w\\]/.test(sel)) continue;                          // 只要类选择器
    const 类名 = 解转义(sel.slice(1));
    for (const d of 声明.split(';')) {
      const [prop, ...v] = d.split(':');
      if (!prop) continue;
      const p = prop.trim();
      if (!尺寸属性.test(p)) continue;
      rec.清单.push({ 类名: '.' + 类名, 属性: p, 值: v.join(':').trim() });
    }
  }
}
const 去重 = []; const 见过 = new Set();
for (const z of rec.清单) { const k = z.类名 + '|' + z.属性; if (!见过.has(k)) { 见过.add(k); 去重.push(z); } }
rec.清单 = 去重;
rec.条数 = 去重.length;
rec.其中min = 去重.filter((z) => /min\(/.test(z.值));
rec.其中max = 去重.filter((z) => /^max-/.test(z.属性));

console.log(`CSS ${rec.css字节} 字节 ｜ 视口相关尺寸声明 ${rec.条数} 条（其中 min() ${rec.其中min.length} 条、max-* ${rec.其中max.length} 条）`);
console.log('\n--- 含 min() 的（= 「固定上限 + 视口余量」型模态）---');
for (const z of rec.其中min) console.log(`  ${z.类名}  →  ${z.属性}: ${z.值}`);
console.log('\n--- max-* 型 ---');
for (const z of rec.其中max.slice(0, 25)) console.log(`  ${z.类名}  →  ${z.属性}: ${z.值}`);
fs.writeFileSync(OUT, JSON.stringify(rec, null, 1));
console.log(`\n已落盘 ${OUT.pathname}（${rec.条数} 条）`);
