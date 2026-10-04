// 批次 158：两处订正。
// 🔑 **锚点从文件里按行号读出来**，不在脚本里手抄 —— 手抄的模板字面量一旦差一个空格
//    （本轮就差了：手抄版 `s.split(从).length-1 === 0`，而原文明明在屏幕上），
//    报错信息只有一句「锚点出现 0 次」，不会告诉你是哪个字符差。
import fs from 'node:fs';
const B = new URL('../docs/user-manual/jimeng-canvas/', import.meta.url);
const 取 = (名, 起, 止) => {
  const L = fs.readFileSync(new URL(名, B), 'utf8').split('\n');
  return L.slice(起 - 1, 止).join('\n');   // 1 闭
};
const 改 = (名, 从, 到) => {
  const p = new URL(名, B);
  const s = fs.readFileSync(p, 'utf8');
  const n = s.split(从).length - 1;
  if (n !== 1) { console.log('❌ ' + 名 + '：锚点出现 ' + n + ' 次'); process.exit(1); }
  fs.writeFileSync(p, s.replace(从, 到));
  console.log('✅ ' + 名 + '：替换 1 处（' + 从.split('\n').length + ' 行 → ' + 到.split('\n').length + ' 行）');
};

// ---- ① media-playback.md 第 386–391 行 ----
const 锚1 = 取('10-tasks/media-playback.md', 386, 391);
if (锚1.indexOf('仍未验证') < 0) { console.log('❌ 行号漂了，第 386 行是：', JSON.stringify(锚1.slice(0, 40))); process.exit(1); }
const 新1 = fs.readFileSync(new URL('./_tmp-b158-mp-new.md', import.meta.url), 'utf8').replace(/\n$/, '');
改('10-tasks/media-playback.md', 锚1, 新1);

// ---- ② 20-reference.md：CDN 那一条的前面插入新读数 ----
const 锚2 = '- 同一素材的请求会在**多个 CDN 节点**之间跳（`v3-dreamina-de` / `v26-dreamina-de`），';
const 新2 = fs.readFileSync(new URL('./_tmp-b158-ref-new.md', import.meta.url), 'utf8').replace(/\n$/, '') + '\n' + 锚2;
改('20-reference.md', 锚2, 新2);

console.log('✅ 两处订正全部落盘');
