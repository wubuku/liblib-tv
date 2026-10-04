// 批次 157 靶子筛选 —— 纯静态，不连浏览器。
//
// 目的：找出**当前还写着「未验证 / 仍未验证 / 未获授权 / 无法确认 / 未能复现 / 没找到路径」**
//       的陈述，按「过期程度」排序，挑出下一批最值得验的那一条。
//
// 🔑 判「过期」不看字面年龄，看**阻塞理由是否还成立**：
//   2026-10-04 新授权解除了「不执行真实生图/生视频前提下可执行 CRUD 副作用」，
//   于是「需单独授权」「未获授权」这类理由**大面积过期**；
//   而「素材限制」「扣费边界」「无删除入口」这类理由**仍然成立**，不该重排。
import fs from 'node:fs';
import path from 'node:path';

const ROOT = new URL('../docs/user-manual/jimeng-canvas/', import.meta.url).pathname;
const 过期理由 = [
  '未获单独授权', '需单独授权', '没有单独授权', '在未获授权', '需授权', '本手册不执行',
  '没有点', '没有点击', '只读不点', '未执行', '没测', '未测', '未验证', '仍未验证',
  '没法干净', '无从比对', '无从做', '未复现', '没有找到', '找不到路径', '不给出行内',
];
const 仍成立理由 = ['扣费边界', '素材限制', '属扣费', '永久不在本手册范围', '无删除入口'];

const walk = (d, out = []) => {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    if (e.name === '.vitepress' || e.name === 'node_modules') continue;
    const f = path.join(d, e.name);
    if (e.isDirectory()) walk(f, out);
    else if (e.name.endsWith('.md')) out.push(f);
  }
  return out;
};

const files = walk(ROOT).filter((f) => !/SOURCE_OBSERVATIONS|PROGRESS|AUDIT|FINAL-REPORT/.test(f));
const 计 = {};
const 细 = [];

for (const f of files) {
  const rel = path.relative(ROOT, f);
  const lines = fs.readFileSync(f, 'utf8').split('\n');
  for (let i = 0; i < lines.length; i++) {
    const ln = lines[i];
    const 命 = 过期理由.filter((k) => ln.includes(k));
    if (!命.length) continue;
    // 已带订正标记的行不再计入（订正是闭环的）
    const 已订正 = /~~|已被推翻|订正|已关闭|不成立/.test(ln);
    if (已订正) continue;
    const 挡 = 仍成立理由.filter((k) => ln.includes(k));
    const key = rel;
    计[key] = (计[key] || 0) + 1;
    细.push({ 文件: rel, 行: i + 1, 理由仍成立: 挡.length > 0, 片段: ln.trim().slice(0, 130) });
  }
}

const 排序 = Object.entries(计).sort((a, b) => b[1] - a[1]);
console.log('=== 未订正的「未验证 / 未授权」陈述，按文件计数 ===');
for (const [f, n] of 排序) console.log(String(n).padStart(3), f);
console.log('\n合计', 细.length, '处 ｜ 扫描', files.length, '个页面 md\n');

const 可动手 = 细.filter((d) => !d.理由仍成立);
console.log('=== 其中「理由可能已过期」的（阻塞理由不含扣费/素材限制/无删除入口）', 可动手.length, '处 ===');
for (const d of 可动手) console.log(`${d.文件}:${d.行}  ${d.片段}`);
