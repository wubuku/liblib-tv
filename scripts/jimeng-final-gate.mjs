// 即梦画布手册 —— 一条命令跑完全部收尾质量门。
//
// 背景（2026-10-01 批次 30–48 的来历）：
//   ① 批次 39/43 两次事故都源于「守卫判据写漏了一种输入面」→ 已固化为
//      scripts/jimeng-safe-keys.mjs；本脚本调它。
//   ② 批次 48 发现 6 个节点的**位置**被移动，而我历来的收尾核对清单
//      **只覆盖内容与标题**，位移在上面完全隐形 → 本脚本做位置比对。
//   ③ 批次 48 发现 4 处 U+FFFD 乱码，而 6 道机械门**都不校验字符编码** → 第 7 道门。
//   ④ 批次 48 还发生过「把上一轮的 build 退出码当成这一轮的」→ 本脚本每次
//      现场重跑，不沿用任何历史读数。
//
// 用法：node scripts/jimeng-final-gate.mjs
// 退出码：0 = 全部通过；1 = 有门失败；2 = 环境问题（找不到画布 / 视口被污染）
import { execFileSync, spawnSync } from 'node:child_process';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, resolve, dirname, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '..');
const MANUAL = join(ROOT, 'docs/user-manual/jimeng-canvas');
const BASELINE = join(HERE, 'jimeng-baseline-nodes.json');
const LEDGER = join(HERE, 'jimeng-ephemeral-ledger.json');
/** 本任务创建过的临时节点 id（读不到就当空集，此时 leftover 恒空 ⇒ 判负能力退化但不误报） */
function readLedger() {
  try { return JSON.parse(readFileSync(LEDGER, 'utf8')); }
  catch { return { ids: [] }; }
}
const PORT = 9444;

const results = [];
const record = (name, ok, detail) => {
  results.push({ name, ok, detail });
  console.log(`\n${ok ? '✅' : '❌'} ${name}\n   ${String(detail).replace(/\n/g, '\n   ')}`);
};
const run = (label, cmd, args) => {
  try {
    const out = execFileSync(cmd, args, { cwd: ROOT, encoding: 'utf8', maxBuffer: 32 * 1024 * 1024 });
    return { ok: true, out };
  } catch (e) {
    return { ok: false, out: `${e.stdout || ''}${e.stderr || e.message}` };
  }
};

// ---------- 1. alt 审计 ----------
{
  const r = run('alt', process.execPath, [join('scripts', 'jimeng-alt-audit.mjs')]);
  record('1/9 截图 alt 审计', r.ok, (r.out.match(/截图总数.*|无冲突|无问题/g) || [r.out.trim().split('\n').pop()]).join(' / '));
}
// ---------- 2. 交叉一致性（批次 66 起：不再是纯扫读器） ----------
// 🔧 **批次 66 把这道门从「恒绿」改成「会红」**。
// 旧版只跑 jimeng-crosscheck.mjs：它列出「可疑命中 N 处」供人工判读，
// 退出码**恒为 0** ⇒ 无论命中多少都打 ✅（批次 58 已在记录行里写明这点）。
//
// 现在跑 **jimeng-crosscheck-gate.mjs**（双向不变式）：
//   ① 命中台账（AUDIT/SOURCE_OBSERVATIONS/PROGRESS/FINAL-REPORT）→ 只计数，不失败
//   ② 命中正文/概念/排障页 → 必须在白名单里且**逐字**对得上，否则 FAIL
//   ③ 白名单里对不上任何命中的条目 → FAIL（防「删掉条目就安静了」）
// 另附 v2 扫读器（递归，覆盖 164 个 .md）的汇总，作为信息行保留。
{
  const r = run('crosscheck-gate', process.execPath, [join('scripts', 'jimeng-crosscheck-gate.mjs')]);
  const scan = run('crosscheck2', process.execPath, [join('scripts', 'jimeng-crosscheck2.mjs')]);
  const mGate = r.out.match(/扫描 \d+ 个 Markdown，命中 \d+ 处/) || [];
  const mUser = r.out.match(/正文\/概念\/排障（受管）：\d+ 处，白名单 \d+ 条/) || [];
  const mLed = r.out.match(/台账（豁免，只计数）：\d+ 处/) || [];
  const mVerdict = r.out.match(/(✅ 交叉一致性双向门通过[^\n]*|🔴 双向门不通过)/) || [];
  const mScan = scan.out.match(/v2 覆盖 \d+ 个文件 → \d+ 处命中/) || [];
  record('2/9 交叉一致性双向门（未判读命中 0 且白名单无陈旧条目才算通过）', r.ok,
    [mGate[0], mLed[0], mUser[0], `v2 扫读器：${mScan[0] || '?'}`, mVerdict[0]].filter(Boolean).join(' ｜ '));
}
// ---------- 3/4. gate-a 与 final ----------
for (const [idx, phase] of [[3, 'gate-a'], [4, 'final']]) {
  const r = run(phase, 'python3', ['.agents/skills/web-studio-user-manual/scripts/audit_manual.py', 'docs/user-manual/jimeng-canvas', '--phase', phase]);
  const m = r.out.match(/OK \((?:gate-a|final)\).*/);
  record(`${idx}/9 ${phase}`, r.ok, m ? m[0] : r.out.trim().split('\n').slice(0, 2).join(' '));
}
// ---------- 5. 死链（独立扫描，排除 node_modules/dist/site） ----------
{
  const SKIP = new Set(['node_modules', 'dist', 'site', '.git', '.vitepress']);
  const md = [];
  (function walk(dir) {
    for (const e of readdirSync(dir)) {
      if (SKIP.has(e)) continue;
      const p = join(dir, e);
      if (statSync(p).isDirectory()) walk(p);
      else if (e.endsWith('.md')) md.push(p);
    }
  })(MANUAL);
  const re = /!?\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g;
  let total = 0; const dead = [];
  for (const f of md) {
    const txt = readFileSync(f, 'utf8');
    for (const m of txt.matchAll(re)) {
      const u = m[1].trim();
      if (/^(https?:|mailto:|#)/.test(u)) continue;
      total++;
      const target = normalize(join(dirname(f), u.split('#')[0]));
      if (u.split('#')[0] && !statSync(target, { throwIfNoEntry: false })) dead.push(`${f} -> ${u}`);
    }
  }
  record('5/9 死链扫描', dead.length === 0, `扫描 ${md.length} 个 Markdown，链接 ${total} 条，死链 ${dead.length}${dead.length ? '\n' + dead.join('\n') : ''}`);
}
// ---------- 6. U+FFFD 乱码（第 7 道门，批次 48 新增） ----------
{
  const SKIP = new Set(['node_modules', 'dist', 'site', '.git', '.vitepress']);
  const md = [];
  (function walk(dir) {
    for (const e of readdirSync(dir)) {
      if (SKIP.has(e)) continue;
      const p = join(dir, e);
      if (statSync(p).isDirectory()) walk(p);
      else if (e.endsWith('.md')) md.push(p);
    }
  })(MANUAL);
  const hits = md.filter((f) => readFileSync(f, 'utf8').includes('�'));
  record('6/9 乱码扫描（U+FFFD）', hits.length === 0,
    hits.length === 0 ? `${md.length} 个 Markdown 全部无替换字符` : `命中 ${hits.length} 个文件：\n${hits.join('\n')}`);
}
// ---------- 7. 站点构建 ----------
{
  const r = spawnSync('bash', [join('docs/user-manual/jimeng-canvas/build-site.sh')], { cwd: ROOT, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  const out = `${r.stdout || ''}${r.stderr || ''}`;
  const m = out.match(/dist 页面数: \d+[\s\S]*?示意图 alt 与正文引用逐字一致/);
  record('7/9 站点构建', r.status === 0, r.status === 0 ? (m ? m[0].replace(/\x1b\[[0-9;]*m/g, '') : '退出码 0') : `退出码 ${r.status}\n${out.split('\n').slice(-8).join('\n')}`);
}
// ---------- 8. 订正回填门（批次 75 新增） ----------
{
  const r = run('backfill-gate', process.execPath, [join('scripts', 'jimeng-backfill-gate.mjs')]);
  const mScan = r.out.match(/扫描 .*命中 \d+ 处/) || [];
  const mVerdict = r.out.match(/(✅ 订正回填门通过[^\n]*|🔴 订正回填门不通过)/) || [];
  const mBad = r.out.match(/⛔ [^\n]*/g) || [];
  record('8/9 订正回填门（被推翻的结论，原始记录处必须带内联订正标记）', r.ok,
    [mScan[0], mVerdict[0], ...mBad.slice(0, 4)].filter(Boolean).join(' ｜ '));
}
// ---------- 8. 画布：焦点守卫 + 节点位置比对（第 9 道，批次 48 新增） ----------
{
  let b;
  try {
    b = await chromium.connectOverCDP(`http://127.0.0.1:${PORT}`);
  } catch (e) {
    record('9/9 画布焦点守卫 + 位置比对', false, `无法连接 CDP ${PORT}：${e.message}`);
    b = null;
  }
  if (b) {
    const page = b.contexts()[0].pages().find((p) => p.url().includes('ai-canvas'));
    if (!page) {
      record('9/9 画布焦点守卫 + 位置比对', false, '找不到画布页面');
    } else {
      const { keyGuard, canvasBaseline, diffNodePositions, pinViewport } = await import('./jimeng-safe-keys.mjs');
      let vp = null, vErr = null;
      try { vp = await pinViewport(page); } catch (e) { vErr = e.message; }
      if (vErr) {
        record('9/9 画布焦点守卫 + 位置比对', false, vErr);
      } else {
        const g = await keyGuard(page);
        const base = JSON.parse(readFileSync(BASELINE, 'utf8'));
        const cur = await canvasBaseline(page);
        const bad = await diffNodePositions(page, base.nodes, 1.5);
        // 批次 73：区分「**我没删干净**」与「**别人新建了节点**」。
        // 为什么必须分：共享画布上有并行 session 在不停新建节点（批次 72 观察到音频 1/2/3/4），
        // 旧逻辑把「画布上出现基线以外的 id」一律判负 ⇒ 红灯原因**不在本任务**，
        // 而一道会因外部改动变红的门，训练出的行为是「忽略它」（批次 66 的教训反过来用）。
        // 现在：**本任务创建过的 id 仍在画布上 = 真失败**；其余外部 id = 如实计数并列出。
        const led = readLedger();
        const curIds = cur.nodes.map((n) => n.id);
        const leftover = curIds.filter((id) => led.ids.includes(id));
        const extReg = base._external_nodes || {};
        const suspectCopies = cur.nodes.filter((n) => /\s\(\d+\)\s*$/.test(n.title || '')
          && !(n.id in base.nodes) && !(n.id in extReg) && !led.ids.includes(n.id)).map((n) => `${n.id}(${n.title})`);
        const external = curIds.filter((id) => !(id in base.nodes) && !led.ids.includes(id));
        const knownExt = external.filter((id) => id in extReg);
        const newExt = external.filter((id) => !(id in extReg));
        const extra = curIds.filter((id) => !(id in base.nodes));
        const missing = Object.keys(base.nodes).filter((id) => !cur.nodes.some((n) => n.id === id));
        const titleBad = cur.nodes.filter((n) => base.nodes[n.id] && n.title !== base.nodes[n.id].title)
          .map((n) => `${n.id} 标题 ${JSON.stringify(n.title)} ≠ 基线 ${JSON.stringify(base.nodes[n.id].title)}`);
        // 状态行里与节点数无关的描述部分（节点数会因他人新建而变，edges/selected 才是本任务的责任）
        const descOf = (s) => String(s || '').replace(/^[\d]+ nodes?, [\d]+ edges?, [\d]+ selected\s*/, '').trim();
        const cntOf = (s, k) => { const m = new RegExp(`[\\d]+ ${k}`).exec(String(s || '')); return m ? m[0] : '?'; };
        const statusDescOk = descOf(cur.status) === descOf(base.status);
        // 状态行形如 `10 nodes, 0 edges, 0 selected. Editable. …`
        const zeroOk = /\b0 edges\b/.test(cur.status) && /\b0 selected\b/.test(cur.status);
        // ⚠️ 判负条件里**没有** extra（= 基线以外的全部 id）：外部新建不算本任务的失败，
        //    只有 **leftover**（本任务建过却没删）才判负。
        const ok = g.safe && !bad.length && !missing.length && !titleBad.length && !leftover.length
          && cur.credit === base.credit && statusDescOk && zeroOk;
        const lines = [
          `视口 ${vp.w}×${vp.h} @dpr2`,
          `焦点守卫 ${g.safe ? '✅ 可按字母键' : '⛔ 不可'} (${g.where})`,
          `状态行 ${cur.status}`,
          `积分 ${cur.credit}（基线 ${base.credit}）`,
          `节点位置偏离 ${bad.length} 个${bad.length ? '：' + bad.join(', ') : ''}`,
          `本任务遗留节点 ${leftover.length} 个${leftover.length ? '：' + leftover.join(', ') : ''}${leftover.length ? ' ⛔ 必须删干净' : ' ✅'}`,
          `外部（他人新建）节点 ${external.length} 个：已登记 ${knownExt.length}${knownExt.length ? '（' + knownExt.join(', ') + '）' : ''}／本轮新出现 ${newExt.length}${newExt.length ? '（' + newExt.join(', ') + '）' : ''} ⚠️ 只计数，不判负`,
          `多余节点合计 ${extra.length} 个`,
          `缺失节点 ${missing.length} 个${missing.length ? '：' + missing.join(', ') : ''}`,
          `标题不符 ${titleBad.length} 处${titleBad.length ? '：' + titleBad.join('; ') : ''}`,
          `状态行描述部分 ${statusDescOk ? '✅ 一致' : '⛔ 不一致'}｜edges/selected ${zeroOk ? '✅ 为 0' : '⛔ 非 0'}（${cntOf(cur.status, 'edges')} / ${cntOf(cur.status, 'selected')}）`,
          // 批次 77 盲区补丁：ledger 只记「我新建的节点」，**不记 ⌘D 派生的副本**。
          // 一版脚本中止时留下的「文本 4 (2)」孤儿因此既不在 ledger 也不在基线，
          // 被当成「外部节点」只计数 ⇒ 门是绿的、画布是脏的。
          // 这里补一条**信息性**提示：标题形如 `xxx (2)` 且未登记的节点。
          `疑似未登记副本 ${suspectCopies.length} 个${suspectCopies.length ? '：' + suspectCopies.join(', ') : ''}${suspectCopies.length ? ' ⚠️ 只提示不判负（他人测 ⌘D 也会这样）' : ''}`,
          `节点 canvas 坐标：`,
          ...cur.nodes.map((n) => `    ${n.id}  [${n.canvas ? n.canvas.join(', ') : '?'}]  ${JSON.stringify(n.title)}`),
        ];
        record('9/9 画布焦点守卫 + 位置比对', ok, lines.join('\n'));
      }
    }
    await b.close();
  }
}

console.log('\n' + '='.repeat(64));
const failed = results.filter((r) => !r.ok);
console.log(`收尾质量门：${results.length - failed.length}/${results.length} 通过`);
results.forEach((r) => console.log(`  ${r.ok ? '✅' : '❌'} ${r.name}`));
if (failed.length) { console.log('\n未通过：'); failed.forEach((r) => console.log(`  - ${r.name}`)); }
console.log('='.repeat(64));
process.exit(failed.length ? 1 : 0);
