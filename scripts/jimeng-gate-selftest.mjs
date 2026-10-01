// 即梦画布手册 · **收尾质量门自身的阳性对照自测**
//
// 🔴 为什么需要它（2026-10-01 批次 57 的来历）：
//   批次 57 发现第 8 道门的「位置比对」**恒真** —— 传错基线形状，
//   `Math.abs(x - undefined)` = `NaN`，而 `NaN > tol` 恒为 false，
//   于是「节点位置偏离 0 个」**无论节点偏了多少都照打**。
//   批次 48 正是靠这道门抓到过位置事故 —— 事故修好了，
//   **检查项本身却从此再也没被验证过**。
//
//   🔑 一道「从不失败」的检查 = 没有这道检查。
//      而「8/8 通过」这句话本身也需要被证明，而不只是被打印出来。
//
// 本脚本做什么：
//   对每一道**断言型**门，**故意注入一个缺陷**，跑整条收尾门，
//   **断言对应的那道门变成 ❌**，然后**逐字节还原**注入的文件。
//   任何一道门在注入缺陷后仍然 ✅，就说明它是恒真的 —— 退出码 3。
//
// 注入目标固定为 `10-tasks/connect-nodes.md`（本任务自有、已提交、对 HEAD 干净）。
// 还原方式：**用注入前读到的字节写回**，不用 `git checkout --` / `stash` ——
// 那两个在本仓库被明令禁用（会干扰其他开发者的暂存区）。
// 每次还原后都断言 `git diff --quiet HEAD -- <file>`，字节对不上就报错退出。
//
// 用法：
//   node scripts/jimeng-gate-selftest.mjs            # 全量（跑 5 次整条门，约 3–5 分钟）
//   node scripts/jimeng-gate-selftest.mjs --list     # 只列出用例，不执行
import { execFileSync, spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '..');
const TARGET = 'docs/user-manual/jimeng-canvas/10-tasks/connect-nodes.md';
const LIST_ONLY = process.argv.includes('--list');

const sha = (s) => createHash('sha256').update(s).digest('hex');

// ---- 缺陷用例：每个都只改 TARGET 一个文件 ----
const CASES = [
  {
    id: 'alt-mismatch',
    gates: ['1/9'],
    why: '把正文里 99 号截图的 alt 改一个字，与 manifest.yml 登记的 alt 不再逐字一致',
    expect: (out) => out.includes('❌ 1/9'),
    inject: (t) => t.replace('文本节点是 7 种类型里唯一不与卡片顶边齐平的', '文本节点是 7 种类型里唯一不与卡片顶边齐平'),
    mustChange: true,
  },
  {
    id: 'dead-link',
    gates: ['3/9', '4/9', '5/9'],
    why: '插一条指向不存在文件的死链（批次 57 真实发生过一次，属实的意外阳性对照）',
    expect: (out) => out.includes('❌ 3/9') && out.includes('❌ 4/9') && out.includes('❌ 5/9'),
    inject: (t) => `${t}\n\n<!-- 门自测注入 -->\n[指向不存在](__gate_selftest_no_such__.md)\n`,
  },
  {
    id: 'ufffd',
    gates: ['6/9'],
    why: '注入一个 U+FFFD 替换字符（批次 57 我自己手误打进过一处，肉眼发现）',
    expect: (out) => out.includes('❌ 6/9'),
    inject: (t) => `${t}\n\n<!-- 门自测注入：乱码 -->\n替换字符：�\n`,
  },
  {
    id: 'missing-shot',
    gates: ['7/9'],
    why: '引用一张不存在的截图，构建器的「截图数与源一致」应当报不一致',
    expect: (out) => out.includes('❌ 7/9'),
    inject: (t) => `${t}\n\n![门自测注入的不存在截图](../screenshots/__gate_selftest_no_such__.png)\n`,
  },
  {
    id: 'backfill-unmarked',
    gates: ['8/9'],
    why: '在正文里复述一条**已被推翻**的措辞、且**不带任何订正标记** —— 正是批次 74 抓到的那一类（改了结论没回填）',
    expect: (out) => out.includes('❌ 8/9'),
    // ⚠️ 注入文本里绝不能出现标记词（订正/推翻/已被/口径/机制…），否则门会判它「已标记」
    inject: (t) => `${t}\n\n- 时间线/主体可连\n`,
  },
];

const runGate = () => {
  const r = spawnSync(process.execPath, [join('scripts', 'jimeng-final-gate.mjs')],
    { cwd: ROOT, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, timeout: 300000 });
  return { code: r.status, out: `${r.stdout || ''}${r.stderr || ''}` };
};

const restore = (abs, bytes, digest) => {
  writeFileSync(abs, bytes);
  const now = readFileSync(abs, 'utf8');
  if (sha(now) !== digest) throw new Error(`还原后 sha256 不一致：${abs}`);
  const q = spawnSync('git', ['diff', '--quiet', 'HEAD', '--', TARGET], { cwd: ROOT });
  if (q.status !== 0) throw new Error(`还原后该文件与 HEAD 不一致（请人工检查）：${TARGET}`);
};

if (LIST_ONLY) {
  console.log(`收尾门阳性对照自测 —— 共 ${CASES.length} 个用例（注入目标：${TARGET}）\n`);
  for (const c of CASES) console.log(`  ${c.id.padEnd(16)} 期望这几道门变红: ${c.gates.join(' / ')}\n      ${c.why}`);
  process.exit(0);
}

console.log('=== 收尾门 · 阳性对照自测 ===');
console.log('原则：一道从不失败的检查等于没有这道检查。\n');

const abs = join(ROOT, TARGET);
const pristine = readFileSync(abs, 'utf8');
const pristineSha = sha(pristine);
console.log(`注入目标 ${TARGET}`);
console.log(`原始 sha256 ${pristineSha}\n`);

const results = [];
let broken = 0;
for (const c of CASES) {
  let injected = null;
  try {
    injected = c.inject(pristine);
    if (injected === pristine) throw new Error('注入没有改变文件内容 —— 用例本身写错了');
    writeFileSync(abs, injected);
    console.log(`▶ ${c.id}：${c.why}`);
    const { code, out } = runGate();
    const ok = c.expect(out);
    const failed = code !== 0;
    console.log(`  收尾门退出码 ${code}（${failed ? '非 0，符合预期' : '**是 0** —— 门没拦住'}）`);
    if (!ok) { broken++; console.log('  ⛔ 期望的门没有变红 —— 这道门可能是恒真的'); }
    else console.log(`  ✅ 期望的门如期变红：${c.gates.join(' / ')}`);
    for (const g of ['1/8', '2/8', '3/8', '4/8', '5/8', '6/8', '7/8', '8/8']) {
      const m = out.match(new RegExp(`^[✅❌] ${g.replace('/', '\\/')}[^\\n]*`, 'm'));
      if (m) console.log(`     ${m[0]}`);
    }
    results.push({ id: c.id, ok, code, gates: c.gates });
  } catch (e) {
    broken++;
    console.log(`  ⛔ 用例执行出错：${e.message}`);
    results.push({ id: c.id, ok: false, err: e.message, gates: c.gates });
  } finally {
    try { restore(abs, pristine, pristineSha); console.log('  ↩︎ 已逐字节还原并断言与 HEAD 一致\n'); }
    catch (e) { broken++; console.log(`  ⛔ 还原失败：${e.message}\n`); }
  }
}

console.log('================ 结论 ================');
for (const r of results) console.log(`  ${r.ok ? '✅' : '⛔'} ${r.id.padEnd(16)} 期望变红: ${r.gates.join(' / ')}`);
console.log(`\n${broken ? `⛔ ${broken} 个用例未达预期 —— 有恒真的门，或用例写错了` : '✅ 全部用例达预期：被测的每一道门都会失败，因此它们的 ✅ 有意义'}`);
console.log('ℹ️ 第 2 道「交叉一致性」不在本自测内：它是**扫读器**不是断言门');
console.log('   （只报「可疑命中 N 处」、退出码恒 0，✅ 只表示脚本跑通了）。');
process.exit(broken ? 3 : 0);
