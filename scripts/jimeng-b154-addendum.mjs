// 批次 154 收尾补录：把最后两个发现写进 SOURCE_OBSERVATIONS §4.77.6 与 AUDIT.md
// 🔑 正文片段一律从 .md 文件读入，**不在 JS 里用模板串拼反引号**（会被 bash/node 吃掉）。
import fs from 'node:fs';

const DIR = new URL('../docs/user-manual/jimeng-canvas/', import.meta.url);
const 读 = (p) => fs.readFileSync(new URL(p, DIR), 'utf8');
const 存 = (p, s) => fs.writeFileSync(new URL(p, DIR), s);
let 失败 = 0;

const 改 = (p, 锚, 新, 名) => {
  const s = 读(p);
  const n = s.split(锚).length - 1;
  if (n !== 1) { console.log('❌ ' + 名 + ' 命中 ' + n + ' 次'); 失败++; return; }
  const t = s.replace(锚, 锚 + 新);
  if (t === s) { console.log('❌ ' + 名 + ' 未生效'); 失败++; return; }
  if (t.split(锚).length - 1 !== 1) { console.log('❌ ' + 名 + ' 锚点重复'); 失败++; return; }
  存(p, t);
  console.log('✅ ' + 名 + '（+' + 新.length + ' 字符）');
};

const 附 = fs.readFileSync('/tmp/b154-addendum.md', 'utf8');
const 行 = fs.readFileSync('/tmp/b154-audit-rows.md', 'utf8');
if (附.includes('�') || 行.includes('�')) { console.log('⛔ 片段含 U+FFFD'); process.exit(1); }

改('SOURCE_OBSERVATIONS.md',
  '📌 **这 8 条必须一次修干净**：否则就是批次 66 说的「一道长期红的门等于没有门」。',
  附, '§4.77.6 追加两条');

改('AUDIT.md',
  '| ⛔ **零副作用** | 正面 |',
  行, 'AUDIT 追加两行');

console.log(失败 ? '\n⛔ ' + 失败 + ' 处失败' : '\n✅ 补录完成');
process.exit(失败 ? 1 : 0);
