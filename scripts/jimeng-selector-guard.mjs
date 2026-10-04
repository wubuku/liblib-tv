// 守卫「testid 当 class 用」这个错 —— 它已在两个批次里各犯一次。
//
// 🔴 两次实例：
//   批次 146 a 轮：按 `.flow-node-source-handle` 查手柄 —— **恒扑空**，因为它是
//                 **data-testid**。真身要写 `[data-testid="flow-node-source-handle"]`。
//   批次 147 a 轮：按 `.node-toolbar` 查音频面板容器 —— **读出 0 个实例**，差点得出
//                 「音频面板不是 node-toolbar」的错误结论。b 轮走祖先链才发现
//                 L4 是 `class="react-flow__node-toolbar"` + `data-testid="node-toolbar"`。
//
// ⇒ **同一个错跨两个批次各犯一次，说明它不是「粗心」，是缺少机械拦截。** 本脚本就是那道拦截。
//
// 判据：
//   ① 从手册里抽出**全部** `data-testid="X"` 的取值（权威名单，164 个 Markdown）；
//   ② 扫探针脚本里所有「按 class 选」的写法：`.X` / `.X Y` / `.X>` 等
//      （出现位置包括 `querySelector`、`querySelectorAll`、`closest`、`matches`、
//        `getElementsByClassName` 等等）；
//   ③ 凡 `X` **命中 testid 名单** ⇒ 🔴 报错（**class 选择器匹配不到它**）；
//   ④ 反向也查：凡 `X` **是真实的 class 但也被写成 testid 名单里的值**……不查（同名不冲突）。
//
// ⚠️ 白名单：`react-flow__node-toolbar` 这类**真 class** 不在名单里，天然不会命中；
//    但 `node-toolbar` 既是 testid 又长得像 class，所以**必须逐条看**，本脚本只负责指出来。
//
// 🔴 **已知的第三个洞（批次 151 用反向用例 ⑩ 钉死边界）**：
//    选择器**经数组或变量间接传入**时本脚本扫不到，形如
//      `const want = ['.flow-node-title', …]; want.map(s => n.querySelector(s))`
//    —— 字面量不在任何选择器调用的参数位里。要抓它需要做污点追踪，
//    成本与误报都高，本轮**不做**，改成在自测里留一条**反向用例**证明这个洞真实存在，
//    免得以后误以为「已经全覆盖」。
//    ⚠️ 已知实例：`jimeng-b78c.mjs` 的 `want` 数组里仍有 `.flow-node-title` 等
//    **按 class 写的 testid**（它们恰好在同一次 `querySelectorAll('[data-testid], …')`
//    的前半段被兜住了，所以那次没出错）——**这是靠巧合过的门，不是靠机制过的**。
//
// 用法：node scripts/jimeng-selector-guard.mjs [--selftest]
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

const DIR = 'docs/user-manual/jimeng-canvas';
const 脚本目录 = 'scripts';
// 只扫本项目的探针/门脚本，别人的脚本不管
const 前缀 = /^jimeng[-_]/;

const walk = (d, o = [], 后缀 = '.md') => {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const p = path.join(d, e.name);
    if (e.isDirectory()) walk(p, o, 后缀); else if (e.name.endsWith(后缀)) o.push(p);
  }
  return o;
};

/** 手册里全部 data-testid 取值（权威名单）。 */
function testid名单() {
  const 名 = new Map();
  for (const f of walk(DIR)) {
    fs.readFileSync(f, 'utf8').split('\n').forEach((L, i) => {
      // 🔴 批次 151 修法：原来只认**带引号**的 `data-testid="X"`，漏掉了手册里
      //    `data-testid=flow-node-title` 这种**不带引号**的写法（`SOURCE_OBSERVATIONS.md:3486`）。
      //    漏掉的后果很具体：`.flow-node-title` 这个 class 写法因此**过了门**，
      //    而它恒匹配不到元素 —— 正是这道门要拦的那个错。
      //    ⇒ 两种形态都收；收完再把「已收录的名字数」打印出来，改名单时要能一眼看出变化。
      for (const m of L.matchAll(/data-testid\s*=\s*(?:"([^"{}]+)"|'([^'{}]+)'|`([^`{}]+)`|([A-Za-z][A-Za-z0-9_-]*))/g)) {
        const v = (m[1] || m[2] || m[3] || m[4] || '').trim();
        if (!v) continue;
        if (!名.has(v)) 名.set(v, []);
        名.get(v).push(`${path.relative(DIR, f)}:${i + 1}`);
      }
    });
  }
  return 名;
}

/**
 * 扫脚本里「按 class 选」的写法。
 *
 * 🔴 批次 151 补一个洞：原来只认「选择器字符串**以 `.` 开头**」，
 *    于是 `'[data-testid], .flow-node-title'` 这种**逗号列表**整串被跳过
 *    ⇒ 恰恰是「前半段写对了、后半段顺手写成 class」这种最常见的写法溜过去。
 *    现在改成：**取整个字符串，再从里面逐个抠出 `.token`**。
 *
 * 只认这几种调用形态，避免把普通字符串里的点号误判：
 *   querySelector(任意选择器串)  closest(…)  querySelectorAll(…)  matches(…)
 *   getElementsByClassName('X') —— 这一种**不带点**，单独处理。
 */
function 扫class用法(源码) {
  const 命中 = [];
  const 行号 = (i) => 源码.slice(0, i).split('\n').length;
  // ① 接收选择器串的调用
  const 调用 = /(querySelectorAll|querySelector|closest|matches)\s*\(\s*(['"])([^'"]*)\2/g;
  let m;
  while ((m = 调用.exec(源码))) {
    const sel = m[3];
    // 去掉属性选择器内部（`[href=".x"]`）免得把属性值当成 class
    const 净 = sel.replace(/\[[^\]]*\]/g, ' ');
    for (const t of 净.matchAll(/\.(-?[_a-zA-Z][\w-]*)/g))
      命中.push({ 位置: 行号(m.index), 写法: m[1], 选择器: sel, class名: t[1] });
  }
  // ② getElementsByClassName('X') —— 参数是**裸 class 名**
  const 类调用 = /getElementsByClassName\s*\(\s*(['"])([^'"]*)\1\s*\)/g;
  while ((m = 类调用.exec(源码)))
    for (const c of m[2].split(/\s+/).filter(Boolean))
      命中.push({ 位置: 行号(m.index), 写法: 'getElementsByClassName', 选择器: m[2], class名: c });
  return 命中;
}

function 扫描() {
  const 名 = testid名单();
  const 问题 = [];
  const 扫过 = [];
  for (const f of fs.readdirSync(脚本目录)) {
    if (!f.endsWith('.mjs') && !f.endsWith('.js')) continue;
    if (!前缀.test(f)) continue;
    // 🔴 批次 151：本文件**必须排除自己**。
    //    它在注释与自测夹具里**故意**写着 `.X` / `getElementsByClassName('X')` 这类反面写法，
    //    而 `X` 这个占位符名恰好在手册的示例句里以 `data-testid="X"` 出现过
    //    （`AUDIT.md:4122`）⇒ 名单里有 `X` ⇒ 自扫必然把自己报红。
    //    守卫不扫自己，是这类「自检文件」的常规做法。
    if (f === path.basename(new URL(import.meta.url).pathname)) continue;
    const 源码 = fs.readFileSync(path.join(脚本目录, f), 'utf8');
    const 行 = 源码.split('\n');
    for (const h of 扫class用法(源码)) {
      if (名.has(h.class名)) {
        const 文本 = 行[h.位置 - 1] || '';
        const 上一行 = 行[h.位置 - 2] || '';
        // 自查豁免：本行**或紧邻的上一行**在讲「这是错的」（含说明性措辞）。
        // ⚠️ 这是一处**刻意的放宽**：紧挨着的上一行写着「别用 / 错 / 不能」时，
        //    假定作者是在**引用**错误写法（探针脚本经常要演示反面），而不是在用。
        //    代价：确实写错、但上一行恰好有这类词的地方会被放过。选它是因为
        //    「脚本里引用反面写法」比「脚本里写错且上方有解释」常见得多。
        if (/错|误|不能|别|勿|应写|真身|反面|✗|❌/.test(文本 + '\n' + 上一行)) continue;
        问题.push({ 文件: f, 行: h.位置, 写法: h.写法, 选择器: h.选择器, class名: h.class名, 代码: 文本.trim().slice(0, 100) });
      }
    }
    扫过.push(f);
  }
  return { 名, 问题, 扫过 };
}

// ---------- 阳性对照：证明这道门真的会红 ----------
function selftest() {
  const 夹具 = path.join(脚本目录, 'jimeng-_selector-guard-selftest.mjs');
  const 真 = 'flow-node-source-handle';   // 手册里真实存在的 data-testid
  const 假 = 'definitely-not-a-testid-zzz';
  const 写 = (体) => { fs.writeFileSync(夹具, 体); return 扫描(); };
  const 清理 = () => { try { fs.unlinkSync(夹具); } catch {} };
  if (fs.existsSync(夹具)) { console.error('夹具已存在，先清理'); process.exit(9); }

  const base = 扫描();
  const results = [];
  // 用例 1：拿真 testid 当 class 用 ⇒ 必须被抓
  const r1 = 写(`const e = document.querySelectorAll('.${真}');\n`);
  results.push(['① 拿真实 data-testid 当 class 选 ⇒ 门必须红',
    r1.问题.some((q) => q.class名 === 真 && q.文件 === 'jimeng-_selector-guard-selftest.mjs')]);
  清理();
  // 用例 2：拿不存在的名字当 class ⇒ 不该被抓（证明不是无差别报警）
  const r2 = 写(`const e = document.querySelectorAll('.${假}');\n`);
  results.push(['② 拿不存在的名字当 class 选 ⇒ 门不该红（证明不是无差别报警）',
    !r2.问题.some((q) => q.class名 === 假)]);
  清理();
  // 用例 3：正确写法 `[data-testid="X"]` ⇒ 绝不该被抓
  const r3 = 写(`const e = document.querySelectorAll('[data-testid="${真}"]');\n`);
  results.push(['③ 正确写法 [data-testid="X"] ⇒ 门不该红', !r3.问题.some((q) => q.文件 === 'jimeng-_selector-guard-selftest.mjs')]);
  清理();
  // 用例 4：夹具自己行内带「错」字的说明行 ⇒ 豁免机制生效
  const r4 = 写(`// 这是错的写法，别用\nconst e = document.querySelectorAll('.${真}');\n`);
  results.push(['④ 本行自带说明性措辞 ⇒ 豁免生效（不是无差别报警）',
    !r4.问题.some((q) => q.文件 === 'jimeng-_selector-guard-selftest.mjs')]);
  清理();
  // 用例 5：逗号列表 —— 前半段 `[data-testid]` 写对了、后半段顺手把 testid 写成 class
  //   （批次 151 的洞：旧正则要求选择器串**以 `.` 开头**，这种整串被跳过）
  const r5 = 写(`const e = document.querySelectorAll('[data-testid], .${真}');\n`);
  results.push(['⑤ 逗号列表里夹一个 testid 当 class ⇒ 门必须红',
    r5.问题.some((q) => q.class名 === 真 && q.文件 === 'jimeng-_selector-guard-selftest.mjs')]);
  清理();
  // 用例 6：`getElementsByClassName('X')` 传裸 testid 名 ⇒ 也必须红
  const r6 = 写(`const e = document.getElementsByClassName('${真}');\n`);
  results.push(['⑥ getElementsByClassName 传裸 testid 名 ⇒ 门必须红',
    r6.问题.some((q) => q.class名 === 真 && q.文件 === 'jimeng-_selector-guard-selftest.mjs')]);
  清理();
  // 用例 7：属性选择器里**恰好含点**（`[href=".png"]`）不该被当成 class
  const r7 = 写(`const e = document.querySelector('img[src=".${假}.png"]');\n`);
  results.push(['⑦ 属性值里的点号不该被误判成 class（证明不是无差别报警）',
    !r7.问题.some((q) => q.文件 === 'jimeng-_selector-guard-selftest.mjs')]);
  清理();
  // 用例 8：名单**必须**收「不带引号」的 `data-testid=X` 写法
  //   （批次 151 的洞：旧正则只认带引号的，于是 `.flow-node-title` 过了门）
  //   取证方式：`flow-node-title` 在手册里**只**以不带引号的形式出现
  //   （`SOURCE_OBSERVATIONS.md:3486`），它若在名单里就证明这条路径是通的。
  const 名单2 = testid名单();
  results.push(['⑧ 名单收「不带引号」的 data-testid=X（flow-node-title 只以该形态出现）',
    名单2.has('flow-node-title') && (名单2.get('flow-node-title') || [])[0].startsWith('AUDIT.md')]);
  // 用例 9：原样
  const r9 = 扫描();
  results.push(['⑨ 未改动 ⇒ 结果与自测前一致', r9.问题.length === base.问题.length]);
  // 用例 10：**已知的第三个洞** —— 选择器经数组/变量间接传入时，本脚本扫不到。
  //   这里是**反向**用例：断言它抓不到，用来把边界钉死、避免以后误以为「已经全覆盖」。
  //   实例：`jimeng-b78c.mjs` 里 `const want = ['.flow-node-title', …]` 再 `.map(s => n.querySelector(s))`。
  const r10 = 写(`const want = ['.${真}'];\nconst e = n.querySelector(want[0]);\n`);
  results.push(['⑩ 【已知边界·反向】选择器经数组间接传入 ⇒ 本脚本抓不到（用例证明边界真实存在）',
    !r10.问题.some((q) => q.文件 === 'jimeng-_selector-guard-selftest.mjs')]);
  清理();

  console.log('「testid 当 class 用」守卫 · 阳性对照自测：');
  let ok = true;
  for (const [名, 过] of results) { console.log(`  ${过 ? '✅' : '🔴'} ${名}`); if (!过) ok = false; }
  清理();
  const after = 扫描();
  console.log(`  自测后复跑：${after.问题.length === base.问题.length ? '✅ 与自测前一致（未留痕）' : '🔴 被自测污染'}`);
  console.log(ok && after.问题.length === base.问题.length ? '✅ 自测通过：这道门两个方向都会红' : '❌ 自测不通过 —— 门不可信');
  return ok && after.问题.length === base.问题.length;
}

if (process.argv.includes('--selftest')) process.exit(selftest() ? 0 : 1);

const { 名, 问题, 扫过 } = 扫描();
console.log(`手册 testid 名单 ${名.size} 个 × 探针脚本 ${扫过.length} 个 → 可疑写法 ${问题.length} 处`);
if (问题.length) {
  console.log(`\n⛔ ${问题.length} 处**把 data-testid 当 class 选**（这类选择器恒匹配不到任何元素）：`);
  for (const q of 问题) console.log(`  ${q.文件}:${q.行}  .${q.class名}  ←  手册记于 ${(名.get(q.class名) || [])[0]}\n      ${q.代码}`);
  console.log('\n🔴 退出码 1');
  process.exit(1);
}
console.log('\n✅ 选择器守卫通过：没有把 data-testid 当 class 用');
