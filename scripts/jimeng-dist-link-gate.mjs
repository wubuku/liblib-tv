/**
 * 产物级死链门（批次 227 新增）：扫描**构建产物** `.vitepress/dist` 里的 HTML，
 * 要求每一条站内链接在 dist 里**真的打得开**。
 *
 * 🔴 为什么源级死链门（第 5 项）不够 —— 它有一个**结构性盲区**，批次 227 实测到 5 条：
 *   源级门看的是手册目录下所有 .md 里的相对链接，
 *   只要**源文件存在**就算通过。可是构建之后有两类链接会凭空断掉，而源级门看不见：
 *
 *   ① **指向 `srcExclude` 里被排除的页面**：
 *      `.vitepress/config.mjs` 的 `srcExclude` 明确把 `SOURCE_OBSERVATIONS.md`、
 *      `AUDIT.md`、`PROGRESS.md`、`PUBLISH.md` 等工作账本排除出站点
 *      （注释原文：「Agent 工作账本与构建/发布文档不进站点」），
 *      于是 dist 里**根本没有** `SOURCE_OBSERVATIONS.html`，
 *      而正文里 `[…](SOURCE_OBSERVATIONS.md)` 会被 VitePress 改写成
 *      `SOURCE_OBSERVATIONS.html` ⇒ 读者一点就是 404。
 *      而 `ignoreDeadLinks: true` **让它连构建期都不报错**（`PUBLISH.md` §排障早就记过这个坑，
 *      说明它**以前修过、但只修在了首页/README，没有机制防复发**）。
 *
 *   ② **普通链接指向被哈希化的资源**：VitePress 只改写 `![](…)` 图片语法的 src，
 *      不会改写 `[文字](../screenshots/x.png)` 这种**链接**语法。
 *      而同一个文件被 `![]()` 引用时会被搬进 `assets/` 并加哈希
 *      （本例 `assets/74-zoom-input-typing.BODS_9iu.png`），
 *      于是那个普通链接指向的 `dist/screenshots/x.png` 永远不存在。
 *
 * 两类都在**源级门全绿**的情况下让产物带病 ⇒ 这道门不是重复劳动，是补一个真实的洞。
 *
 * 解析规则（照抄站点真实行为，别凭直觉）：
 *   - `/` 开头 = 站点根绝对路径 ⇒ 相对 **dist 根**解析（这一条是批次 227 自己踩过的坑：
 *     第一次自检脚本按「相对所在页目录」解析，`/` 开头的 880 条全被误判成断链）
 *   - 其余 = 相对**所在页所在目录**解析
 *   - 去掉 `?query` 与 `#hash`
 *   - 跳过外链协议与纯锚点
 *   - 以 `/` 结尾按目录处理，查其下的 `index.html`
 *
 * 用法：
 *   node scripts/jimeng-dist-link-gate.mjs            正常门
 *   node scripts/jimeng-dist-link-gate.mjs --probe    自检：注入坏链探针，验证这道门会红
 */
import { readdirSync, statSync, readFileSync, writeFileSync, unlinkSync, existsSync } from 'node:fs';
import { join, dirname, normalize, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const DIST = join(ROOT, 'docs/user-manual/jimeng-canvas/.vitepress/dist');
const PROBE = join(DIST, 'dist-link-selfcheck-probe.html');
const SKIP = new Set(['node_modules', 'cache']);

const SKIP_SCHEME = /^(https?:|mailto:|tel:|data:|javascript:|#|\/\/)/i;
const ATTR = /(?:href|src)="([^"]*)"/g;

function walk(dir, acc = []) {
  for (const e of readdirSync(dir)) {
    if (SKIP.has(e)) continue;
    const p = join(dir, e);
    if (statSync(p).isDirectory()) walk(p, acc);
    else acc.push(p);
  }
  return acc;
}

/** 扫描 dist，返回 { pages, total, dead }。dist 不存在时抛错（**不许**当成通过）。 */
export function scanDist(dist = DIST) {
  if (!existsSync(dist)) throw new Error(`产物目录不存在：${dist} —— 先跑 docs/user-manual/jimeng-canvas/build-site.sh`);
  const pages = walk(dist).filter((p) => p.endsWith('.html'));
  let total = 0;
  const dead = [];
  for (const f of pages) {
    const html = readFileSync(f, 'utf8');
    for (const m of html.matchAll(ATTR)) {
      const raw = m[1].trim();
      if (!raw || SKIP_SCHEME.test(raw)) continue;
      const u = raw.split('#')[0].split('?')[0];
      if (!u) continue;
      total += 1;
      const target = u.startsWith('/')
        ? normalize(join(dist, decodeURIComponent(u).slice(1)))
        : normalize(join(dirname(f), decodeURIComponent(u)));
      // 以 / 结尾 ⇒ 目录，查 index.html
      const ok = u.endsWith('/')
        ? existsSync(join(target, 'index.html'))
        : statSync(target, { throwIfNoEntry: false });
      if (!ok) dead.push(`${relative(dist, f)} -> ${raw}`);
    }
  }
  return { pages: pages.length, total, dead };
}

// ---------- 自检模式 ----------
if (process.argv.includes('--probe')) {
  let ok = false;
  try {
    writeFileSync(PROBE, '<!doctype html><a href="./绝对不存在的产物探针.html">探针</a>\n');
    const r = scanDist();
    const caught = r.dead.some((d) => d.includes('绝对不存在的产物探针'));
    ok = caught;
    console.log(`自检：产物页 ${r.pages}，站内链 ${r.total}，断链 ${r.dead.length}`);
    r.dead.forEach((d) => console.log('  抓到 ' + d));
    console.log(ok
      ? '✅ 产物级死链门会红：注入的坏链被抓到了'
      : '⛔ 产物级死链门抓不到自己注入的坏链 ⇒ 这道门恒绿，不可采信');
  } finally {
    try { unlinkSync(PROBE); console.log('探针已删除'); } catch (e) { console.log('⚠️ 探针删除失败', e.message); }
  }
  process.exit(ok ? 0 : 1);
}

// ---------- 正常门 ----------
try {
  const r = scanDist();
  if (r.dead.length) {
    console.log(`🔴 产物级死链门不通过：产物 ${r.pages} 页，站内链 ${r.total} 条，断链 ${r.dead.length} 条`);
    r.dead.forEach((d) => console.log('  ⛔ ' + d));
    console.log('（站点的 ignoreDeadLinks: true 让构建期不报错，这类断链只有这道门看得见）');
    process.exit(1);
  }
  console.log(`✅ 产物级死链门通过：产物 ${r.pages} 页，站内链 ${r.total} 条，断链 0`);
} catch (e) {
  console.log(`⛔ 产物级死链门无法判定：${e.message}`);
  process.exit(1);
}