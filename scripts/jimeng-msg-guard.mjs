// 提交信息守卫：在 `git commit -F` 之前扫掉替换字符（U+FFFD）。
//
// 为什么需要：收尾质量门第 6 道只扫 **Markdown 文件**，
// **提交信息不在任何一道门的覆盖范围内** —— 批次 55 的提交
// （`1b0f7d63`）信息里就混进了 3 个 U+FFFD，门是 8/8 通过的。
// 共享分支上**不能**用 amend + force-push 去改已推送的历史，
// 所以只能在提交**之前**挡住。
//
// 用法：
//   node scripts/jimeng-msg-guard.mjs /tmp/msg.txt
//   git commit -F /tmp/msg.txt -- <paths>
import { readFileSync } from 'node:fs';

const file = process.argv[2];
if (!file) { console.error('用法：node scripts/jimeng-msg-guard.mjs <提交信息文件>'); process.exit(1); }
let s;
try { s = readFileSync(file, 'utf8'); } catch (e) { console.error('读不到文件：', file, e.message); process.exit(1); }

const bad = [];
for (let i = 0; i < s.length; i++) if (s[i] === '�') bad.push(i);
if (!bad.length) {
  console.log(`✅ 提交信息干净：${file}（${s.length} 字符，U+FFFD 0 个）`);
  process.exit(0);
}
console.error(`⛔ 提交信息含 ${bad.length} 个替换字符（U+FFFD），已中止提交：`);
for (const i of bad) console.error(`   位置 ${i}：${JSON.stringify(s.slice(Math.max(0, i - 20), i + 20))}`);
console.error('提示：把该处改成正确的汉字/标点后重写信息文件再提交。');
process.exit(1);
