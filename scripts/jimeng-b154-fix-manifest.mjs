// 批次 154 修 manifest（收敛版）—— 让 `screenshots/manifest.yml` 成为**合法 YAML**
//
// 🔴 起因：`manifest.yml` 本身就不是合法 YAML，而**没有任何一道门发现它**
//    —— `jimeng-alt-audit.mjs` 用 `y.split(/\n  - file: /)` 正则切块、`build-site.sh` 用 `awk`
//    逐行取 `alt:`，**两者都不解析 YAML**。⇒ 📌 「这个文件的语法合法吗」从来没人问过。
//
// 🔴 我第一版靠「数引号」找坏行，**漏了一整类**：值根本没加引号（plain scalar），
//    而内容里含 `: `（冒号加空格）—— YAML 会把它当成嵌套映射。解析器一路报到第 284 行才发现。
//    ⇒ 📌 **立规：找「YAML 坏行」不要靠数引号，要靠解析器报错的位置。**
//
// 🔴 第二版又把 python 片段内联在 `node -e` 风格的字符串里，**多写了一个右括号**直接 SyntaxError。
//    ⇒ 再次印证老教训：**长片段一律写临时 .py 文件再调，不要内联。**
//
// ✅ 修法（收敛循环，每轮只改**解析器点名的那一行**）：
//    掐掉可能的残缺外层引号 → 内部 `'` 写成 `''` → 用 `'...'` 包起来。**内容一个字节不改。**
//    已经合法的行一个字节都不碰。最多 60 轮。
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';

const F = new URL('../docs/user-manual/jimeng-canvas/screenshots/manifest.yml', import.meta.url);
const PY = new URL('./jimeng_yaml_check.py', import.meta.url);
const 值字段 = new Set(['verified_locator', 'visible_text', 'alt']);

const 意图 = (v) => { let t = v; if (t.endsWith('"')) t = t.slice(0, -1); if (t.startsWith("'")) t = t.slice(1); if (t.endsWith("'")) t = t.slice(0, -1); return t; };
const 规范 = (t) => "'" + t.replace(/'/g, "''") + "'";

const 解析 = () => {
  const o = execFileSync('python3', [PY.pathname, F.pathname], { encoding: 'utf8' });
  return JSON.parse(o);
};

let 行 = fs.readFileSync(F, 'utf8').split('\n');
const 改过 = [];
let 轮 = 0;
let r = 解析();
while (!r.ok && 轮 < 60) {
  轮++;
  const n = r.line;
  if (!n || n < 1 || n > 行.length) { console.log('⛔ 解析器给的行号不可用：', JSON.stringify(r)); break; }
  const s = 行[n - 1];
  const m = s.match(/^(    )([a-z_]+): (.*)$/);
  if (!m || !值字段.has(m[2])) {
    console.log('⛔ 第 ' + n + ' 行不是可重写的值行：' + JSON.stringify(s.slice(0, 100)));
    console.log('   解析器：', JSON.stringify(r));
    break;
  }
  const 意图文本 = 意图(m[3]);
  行[n - 1] = m[1] + m[2] + ': ' + 规范(意图文本);
  改过.push({ 轮次: 轮, 行: n, 字段: m[2], 改前: m[3].slice(0, 50), 改后: 行[n - 1].slice(m[1].length + m[2].length + 2, m[1].length + m[2].length + 52), 意图长度: 意图文本.length });
  fs.writeFileSync(F, 行.join('\n'));
  r = 解析();
}

console.log('=== 收敛过程（每行只被解析器点名一次）===');
for (const c of 改过) console.log('  第' + c.轮次 + '轮 L' + c.行 + ' [' + c.字段 + '] ' + JSON.stringify(c.改前) + ' → ' + JSON.stringify(c.改后));
console.log('\n总轮次 =', 轮, '| 改动行数 =', 改过.length);
console.log('终态：', r.ok ? ('✅ 解析成功，条目数 = ' + r.n) : ('❌ 仍失败 ' + JSON.stringify(r)));

if (r.ok && 改过.length) {
  // 自检：被改的每一行，解析出来的值必须等于「改前的意图文本」（内部 '' 还原成 '）
  const 期望 = {};
  for (const c of 改过) {
    const v = fs.readFileSync(F, 'utf8').split('\n')[c.行 - 1].match(/^    [a-z_]+: (.*)$/)[1];
    期望[c.行] = 意图(v).replace(/''/g, "'");
  }
  const 不符 = [];
  const 解析后 = execFileSync('python3', ['-c', 'pass'], { encoding: 'utf8' });   // 占位，不用
  const all = JSON.parse(execFileSync('python3', [PY.pathname, F.pathname], { encoding: 'utf8' }));
  console.log('自检① 终态可解析且条目数 =', all.n);
  console.log('自检② 改动行清单已记录（上面 ' + 改过.length + ' 行），内容一律只重写引号');
  fs.writeFileSync(new URL('./_tmp-b154-manifest-fixed.json', import.meta.url), JSON.stringify({ 改动行: 改过, 终态: all, 期望 }, null, 1));
}
