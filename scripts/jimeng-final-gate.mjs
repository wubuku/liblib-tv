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
  record('1/8 截图 alt 审计', r.ok, (r.out.match(/截图总数.*|无冲突|无问题/g) || [r.out.trim().split('\n').pop()]).join(' / '));
}
// ---------- 2. 交叉一致性 ----------
{
  const r = run('crosscheck', process.execPath, [join('scripts', 'jimeng-crosscheck.mjs')]);
  const m = r.out.match(/可疑命中 \d+ 处/);
  record('2/8 交叉一致性', r.ok, m ? m[0] : r.out.trim().split('\n').pop());
}
// ---------- 3/4. gate-a 与 final ----------
for (const [idx, phase] of [[3, 'gate-a'], [4, 'final']]) {
  const r = run(phase, 'python3', ['.agents/skills/web-studio-user-manual/scripts/audit_manual.py', 'docs/user-manual/jimeng-canvas', '--phase', phase]);
  const m = r.out.match(/OK \((?:gate-a|final)\).*/);
  record(`${idx}/8 ${phase}`, r.ok, m ? m[0] : r.out.trim().split('\n').slice(0, 2).join(' '));
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
  record('5/8 死链扫描', dead.length === 0, `扫描 ${md.length} 个 Markdown，链接 ${total} 条，死链 ${dead.length}${dead.length ? '\n' + dead.join('\n') : ''}`);
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
  record('6/8 乱码扫描（U+FFFD）', hits.length === 0,
    hits.length === 0 ? `${md.length} 个 Markdown 全部无替换字符` : `命中 ${hits.length} 个文件：\n${hits.join('\n')}`);
}
// ---------- 7. 站点构建 ----------
{
  const r = spawnSync('bash', [join('docs/user-manual/jimeng-canvas/build-site.sh')], { cwd: ROOT, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  const out = `${r.stdout || ''}${r.stderr || ''}`;
  const m = out.match(/dist 页面数: \d+[\s\S]*?示意图 alt 与正文引用逐字一致/);
  record('7/8 站点构建', r.status === 0, r.status === 0 ? (m ? m[0].replace(/\x1b\[[0-9;]*m/g, '') : '退出码 0') : `退出码 ${r.status}\n${out.split('\n').slice(-8).join('\n')}`);
}
// ---------- 8. 画布：焦点守卫 + 节点位置比对（批次 48 新增） ----------
{
  let b;
  try {
    b = await chromium.connectOverCDP(`http://127.0.0.1:${PORT}`);
  } catch (e) {
    record('8/8 画布焦点守卫 + 位置比对', false, `无法连接 CDP ${PORT}：${e.message}`);
    b = null;
  }
  if (b) {
    const page = b.contexts()[0].pages().find((p) => p.url().includes('ai-canvas'));
    if (!page) {
      record('8/8 画布焦点守卫 + 位置比对', false, '找不到画布页面');
    } else {
      const { keyGuard, canvasBaseline, diffNodePositions, pinViewport } = await import('./jimeng-safe-keys.mjs');
      let vp = null, vErr = null;
      try { vp = await pinViewport(page); } catch (e) { vErr = e.message; }
      if (vErr) {
        record('8/8 画布焦点守卫 + 位置比对', false, vErr);
      } else {
        const g = await keyGuard(page);
        const base = JSON.parse(readFileSync(BASELINE, 'utf8'));
        const cur = await canvasBaseline(page);
        const bad = await diffNodePositions(page, base.nodes, 1.5);
        const extra = cur.nodes.map((n) => n.id).filter((id) => !(id in base.nodes));
        const missing = Object.keys(base.nodes).filter((id) => !cur.nodes.some((n) => n.id === id));
        const titleBad = cur.nodes.filter((n) => base.nodes[n.id] && n.title !== base.nodes[n.id].title)
          .map((n) => `${n.id} 标题 ${JSON.stringify(n.title)} ≠ 基线 ${JSON.stringify(base.nodes[n.id].title)}`);
        const ok = g.safe && !bad.length && !extra.length && !missing.length && !titleBad.length
          && cur.status === base.status && cur.credit === base.credit;
        const lines = [
          `视口 ${vp.w}×${vp.h} @dpr2`,
          `焦点守卫 ${g.safe ? '✅ 可按字母键' : '⛔ 不可'} (${g.where})`,
          `状态行 ${cur.status}`,
          `积分 ${cur.credit}（基线 ${base.credit}）`,
          `节点位置偏离 ${bad.length} 个${bad.length ? '：' + bad.join(', ') : ''}`,
          `多余节点 ${extra.length} 个${extra.length ? '：' + extra.join(', ') : ''}`,
          `缺失节点 ${missing.length} 个${missing.length ? '：' + missing.join(', ') : ''}`,
          `标题不符 ${titleBad.length} 处${titleBad.length ? '：' + titleBad.join('; ') : ''}`,
          `节点 canvas 坐标：`,
          ...cur.nodes.map((n) => `    ${n.id}  [${n.canvas ? n.canvas.join(', ') : '?'}]  ${JSON.stringify(n.title)}`),
        ];
        record('8/8 画布焦点守卫 + 位置比对', ok, lines.join('\n'));
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
