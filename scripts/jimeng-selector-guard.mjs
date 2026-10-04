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
      for (const m of L.matchAll(/data-testid\s*=\s*["'`]([^"'`]+)["'`]/g)) {
        const v = m[1].trim();
        if (!v || /[{}]/.test(v)) continue;
        if (!名.has(v)) 名.set(v, []);
        名.get(v).push(`${path.relative(DIR, f)}:${i + 1}`);
      }
    });
  }
  return 名;
}

/**
 * 扫脚本里「按 class 选」的写法。
 * 只认这几种调用形态，避免把普通字符串里的点号误判：
 *   querySelector('.X')  closest('.X')  querySelectorAll('.X')  …
 */
function 扫class用法(源码) {
  const 命中 = [];
  const 调用 = /(querySelectorAll|querySelector|closest|matches|getElementsByClassName)\s*\(\s*(['"])(\.[^'"]*)\2/g;
  let m;
  while ((m = 调用.exec(源码))) {
    const sel = m[3];
    // 把选择器拆成 class token：`.a.b > .c` → a, b, c
    const cls = sel.replace(/>|~|\+|:/g, ' ').split(/\s+/).filter(Boolean)
      .flatMap((t) => (t.startsWith('.') ? t.slice(1).split('.') : []));
    for (const c of cls) if (c) 命中.push({ 位置: 源码.slice(0, m.index).split('\n').length, 写法: m[1], 选择器: sel, class名: c });
  }
  return 命中;
}

function 扫描() {
  const 名 = testid名单();
  const 问题 = [];
  const 扫过 = [];
  for (const f of fs.readdirSync(脚本目录)) {
    if (!f.endsWith('.mjs') && !f.endsWith('.js')) continue;
    if (!前缀.test(f)) continue;
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
  // 用例 5：原样
  const r5 = 扫描();
  results.push(['⑤ 未改动 ⇒ 结果与自测前一致', r5.问题.length === base.问题.length]);

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
