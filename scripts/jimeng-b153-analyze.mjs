import fs from 'node:fs';
const j = JSON.parse(fs.readFileSync('scripts/_tmp-b153.json', 'utf8'));
const 两个 = (j.替换媒体 || {}).file输入 || [];
const 左栏 = 两个.find((f) => !f.节点内);
const 节点内 = 两个.find((f) => f.节点内);
console.log('DOM 里 input[type=file] 恒有 ' + 两个.length + ' 个：');
console.log('  #1 节点内（替换媒体）节点aria=' + JSON.stringify(节点内 && 节点内.节点aria) + ' multiple=' + (节点内 && 节点内.multiple));
console.log('  #2 左栏（canvas-fixed-toolbar）multiple=' + (左栏 && 左栏.multiple));
if (!左栏) process.exit(1);

const 项 = 左栏.accept.split(',').map((s) => s.trim()).filter(Boolean);
console.log('\n🔑 左栏白名单 accept 共 ' + 项.length + ' 项（页面记「111 条 / 48 个扩展名 / 4 类」）');

const 扩展 = 项.filter((s) => s.startsWith('.'));
const 非扩展 = 项.filter((s) => !s.startsWith('.'));
console.log('  其中 `.ext` 形式 ' + 扩展.length + ' 个 | MIME 形式 ' + 非扩展.length + ' 个');
const 唯一扩展 = [...new Set(扩展.map((s) => s.slice(1).toLowerCase()))];
console.log('  去重后的扩展名 ' + 唯一扩展.length + ' 个：' + 唯一扩展.join(' '));

const 类 = { 图片: /image\//, 视频: /video\//, 音频: /audio\//, 文档: /^(text\/markdown|text\/x-markdown|text\/plain)$/, 其他: /application\// };
const 计数 = {};
for (const k of Object.keys(类)) 计数[k] = 项.filter((s) => 类[k].test(s)).length;
console.log('  按 MIME 前缀分：' + JSON.stringify(计数));
console.log('  👉 页面记的「4 类」= 图片/视频/音频/文档；`application/*` 那几条被页面归进各自族（acc/wmv/mxf 是真实文件扩展名）');

const 页面扩展 = {
  图片: ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tif', 'tiff', 'gif', 'heif', 'heic'],
  视频: ['mp4', 'm4v', 'webm', 'mov', 'flv', 'mkv', 'avi', 'wmv', 'rm', 'rmvb', '3gp', 'm2ts', 'mt2s', 'm2t', 'ts', 'mxf', 'mpg', 'mpeg', 'mpe'],
  音频: ['mp3', 'mpa', 'mp2', 'wav', 'm4a', 'flac', 'aac', 'acc', 'oga', 'ogg', 'wma', 'amr', 'aif', 'aiff', 'ac3', 'ape', 'mac'],
  文档: ['md', 'txt'],
};
const 页面全 = [...页面扩展.图片, ...页面扩展.视频, ...页面扩展.音频, ...页面扩展.文档];
console.log('\n  页面写的扩展名总数 = ' + 页面全.length + '（图片10 + 视频19 + 音频17 + 文档2）');
const 缺 = 页面全.filter((x) => !唯一扩展.includes(x));
const 多 = 唯一扩展.filter((x) => !页面全.includes(x));
console.log('  🔑 页面写了但实测没有的：' + JSON.stringify(缺));
console.log('  🔑 实测有但页面没写的：' + JSON.stringify(多));

console.log('\n=== 节点内「替换媒体」白名单 ===');
const 节点项 = 节点内.accept.split(',').map((s) => s.trim()).filter(Boolean);
const 节点扩展 = [...new Set(节点项.filter((s) => s.startsWith('.')).map((s) => s.slice(1).toLowerCase()))];
console.log('  共 ' + 节点项.length + ' 项 | 去重扩展名 ' + 节点扩展.length + ' 个：' + 节点扩展.join(' '));
console.log('  页面记「23 条 / 10 个扩展名 / 只有图片」→ 条数 ' + 节点项.length + (节点项.length === 23 ? ' ✅' : ' ❌') +
  ' / 扩展名 ' + 节点扩展.length + (节点扩展.length === 10 ? ' ✅' : ' ❌'));
const 全是图 = 节点项.every((s) => s.startsWith('.') || /^image\//.test(s));
console.log('  是否全部为图片：' + (全是图 ? '✅' : '❌'));
console.log('  multiple：' + 节点内.multiple + '（页面记「❌ 单选」）' + (节点内.multiple === false ? ' ✅' : ' ❌'));
