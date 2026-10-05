// 探针脚本的**机械闸门**（批次 214 立）
//
// 为什么存在：本会话在批次 212/213/214 里**三次**因为「中文标识符以数字开头」
// （`26档变体` / `50变体` / `变体26` 写反）导致脚本在**运行期**才炸，
// 而 `node --check` 在其中两次**没有**拦住它 ⇒ 光靠 --check 不够。
//
// 本脚本查三件事：
//   ① 属性访问里以数字开头的：`对象.26档` —— JS 词法直接判非法
//   ② 对象字面量的**未加引号**的键以数字开头：`{ 26档: x }`
//   ③ 变量/函数声明名以数字开头：`const 26x = 1`
//
// 用法：node scripts/jimeng-probe-lint.mjs scripts/jimeng-b214a.mjs [...]
import fs from 'node:fs';

const 文件 = process.argv.slice(2);
if (!文件.length) { console.error('用法：node scripts/jimeng-probe-lint.mjs <文件...>'); process.exit(2); }

let 错数 = 0;
for (const f of 文件) {
  const 行 = fs.readFileSync(f, 'utf8').split('\n');
  行.forEach((ln, i) => {
    const 报 = (码, 说明) => { 错数++; console.error(`⛔ ${f}:${i + 1} [${码}] ${说明}\n    ${ln.trim().slice(0, 120)}`); };
    // ① 属性访问 .数字（排除浮点数里的 .5 / 1.5 —— 那种前面是数字不是标识符）
    for (const m of ln.matchAll(/(^|[^\w$])\.(\d[^\d\s]*)/g)) {
      if (/^\.\d/.test(m[0].trim()) === false) continue;
      报('属性以数字开头', `\`${m[0].trim()}\` 不是合法的 JS 标识符`);
    }
    // ② 对象字面量键以数字开头且未加引号
    for (const m of ln.matchAll(/[{,]\s*(\d[^\s:]*)\s*:/g)) 报('键以数字开头且未加引号', `\`${m[1]}\` 需要写成 \`"${m[1]}": ...\``);
    // ③ 声明名以数字开头
    for (const m of ln.matchAll(/\b(?:const|let|var|function)\s+(\d[^\s(=]*)/g)) 报('声明名以数字开头', `\`${m[1]}\` 不是合法标识符`);
  });
}
if (错数) { console.error(`\n🔴 探针闸门不通过：${错数} 处`); process.exit(1); }
console.log(`✅ 探针闸门通过：${文件.length} 个文件，0 处「中文/数字标识符」问题`);
