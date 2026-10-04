// 批次 158 文档手术 —— 三处定位**全部用行首/行尾锚**，不手抄原文
import fs from 'node:fs';

const 读 = (p) => fs.readFileSync(p, 'utf8').replace(/\n+$/, '').split('\n');
const 基 = 'docs/user-manual/jimeng-canvas/';
let 坏 = 0;
const 校验 = (名, ok, 详情) => { if (!ok) { 坏++; console.log('  ❌ ' + 名 + ' ' + JSON.stringify(详情)); } else console.log('  ✅ ' + 名); };

// ---------- 1. media-playback.md：整段替换 ----------
{
  const P = 基 + '10-tasks/media-playback.md';
  const L = 读(P);
  const s = L.findIndex((x) => x.trim().startsWith('~~资源失效后的「重试播放」与空载态'));
  const e = L.findIndex((x) => x.includes('上方「重试播放的两个分支」那节的读数'));
  校验('media 段起锚', s >= 0, { s });
  校验('media 段止锚', e > s, { e });
  console.log('  段范围', s + 1, '..', e + 1, '共', e - s + 1, '行');
  const 新 = 读('/tmp/b158-mp-block.md');
  L.splice(s, e - s + 1, ...新);

  // ---------- 2. media-playback.md：往「重试播放的两个分支」里插补注 ----------
  const a = L.findIndex((x) => x.startsWith('- **并且关掉浏览器缓存**'));
  校验('补注锚点', a >= 0, { a });
  console.log('  补注插在第', a + 1, '行后');
  L.splice(a + 1, 0, ...读('/tmp/b158-mp-note.md'), '');
  fs.writeFileSync(P, L.join('\n') + '\n');
  console.log('  → 写回', P, '共', L.length, '行');
}

// ---------- 3. 20-reference.md：先摘掉插错位置的块，再插到列表末尾 ----------
{
  const P = 基 + '20-reference.md';
  const L = 读(P);
  const s = L.findIndex((x) => x.trim().startsWith('- 🆕 **2026-10-05 批次 158 补一条：路径里有两个会变的段'));
  const e = L.findIndex((x) => x.includes('不据此改写上面的「两个分支」那节'));
  校验('ref 旧块起锚', s >= 0, { s });
  校验('ref 旧块止锚', e > s, { e });
  console.log('  旧块范围', s + 1, '..', e + 1, '共', e - s + 1, '行');
  L.splice(s, e - s + 1);

  const a = L.findIndex((x) => x.startsWith('- 资源账**不会**因为取流失败而变'));
  校验('ref 新块锚点', a >= 0, { a });
  console.log('  新块插在第', a + 1, '行后');
  L.splice(a + 1, 0, '', ...读('/tmp/b158-ref-block.md'));
  fs.writeFileSync(P, L.join('\n') + '\n');
  console.log('  → 写回', P, '共', L.length, '行');
}

console.log(坏 === 0 ? '\n✅ 手术全部锚定成功' : '\n❌ 有 ' + 坏 + ' 处锚点失败，**未写回该文件**');
process.exit(坏 === 0 ? 0 : 1);
