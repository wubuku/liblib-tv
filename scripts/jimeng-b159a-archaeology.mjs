// 批次 159-a —— **纯静态/git 考古**：批次 110 到底拦的哪一段 URL？
//
// 🔑 起因：批次 158 在 `media-playback.md` 就地留了一条补注，说
//    「批次 110 的三步配方**没有记录它当时拦的到底是哪一条 pattern** ——
//      拦整条 CDN 域名？拦 `tos` 桶？拦某个 key？全册查不到。」
//    ⇒ 批次 159 用**仓库里还在的** `jimeng-b110{b,c,d,e}.mjs` 与它们落盘的
//      `scripts/_tmp-b110{b,c,d,e}.json` 把这个缺口**填掉**。
//
// 🔴 结论方向（脚本会自己判）：批次 110 拦的是 **`tos-cn-v-148450/<key>/` 那一段**，
//    也就是 `20-reference.md` 表格里早写着的「**播放取流 key**」；
//    而批次 158 拦的是**第一个 32 位 hex**，那一段批次 110 从没用过。
import fs from 'node:fs';

const rec = { 批次: '159a', 目的: '考古：批次 110 的拦截 pattern 到底是哪一段 URL' };
const 读 = (p) => { try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch (e) { return null; } };

// ---- ① 批次 110 各轮落盘的实际 pattern ----
rec.各轮 = [];
for (const 轮 of ['a', 'b', 'c', 'd', 'e']) {
  const j = 读('scripts/_tmp-b110' + 轮 + '.json');
  if (!j) { rec.各轮.push({ 轮, 缺文件: true }); continue; }
  const 条 = { 轮 };
  for (const k of ['key', 'realKey', 'realKey2', 'blockPattern']) if (j[k] != null) 条[k] = j[k];
  rec.各轮.push(条);
}

// ---- ② 逐条判别：这个 key 属于 URL 的哪一段？----
const 判段 = (key) => {
  if (!key) return { 段: '无', 依据: '该轮没有落盘 key' };
  if (key === 'ooHx1IfRMfIKm8GlcVBdIOFE9UxdJqfdDnCfEL')
    return { 段: '**上传存储 key**', 依据: '逐字等于 `20-reference.md` 表格里「上传存储 key」那一行（tos-d-ct-lf.snssdk.com/upload/…）' };
  if (key === 'oERcOtFfdQDiV1DIHmFBfRExqfYiGndCM8df8E')
    return { 段: '**播放取流 key**', 依据: '由 b110c 的正则 `/tos-cn-v-148450\\/([A-Za-z0-9]+)\\//` 从 `<audio>.src` 抽出' };
  return { 段: '未知', 依据: '与已知的两个 key 都不逐字相同' };
};
rec.判读 = rec.各轮.map((z) => ({ 轮: z.轮, key: z.key || z.realKey || z.realKey2 || null, 判定: 判段(z.key || z.realKey || z.realKey2) }));

// ---- ③ 批次 158 用的那一段，在批次 110 里出现过吗？----
const d = 读('scripts/_tmp-b158d.json');
rec.批次158 = { KEY: d?.KEY || null, pattern: d?.拦截 || null, 结果: '12 帧采样显示音频完整播完 4 秒 ⇒ 拦截没打中' };
rec.批次158落在哪一段 = d?.KEY
  ? (d.KEY === '9b1cc36e5063d367b58d0863f0884010'
      ? 'URL 的**第 1 段**（域名后面紧跟的 32 位 hex）—— 批次 110 的成功配方里**从未出现过这一段**'
      : '未知')
  : '未取到';

// ---- ④ 源码佐证：b110 是哪一行把 pattern 拼出来的 ----
// ⚠️ **不手抄逐字原文当锚**（批次 158 刚踩过：抄漏缩进，报错还不指出是哪个字符）。
//    这里只记「文件 + 行号 + 这行该满足什么形状」，判定交给下面的正则。
const 该含 = { 行: 96, 须匹配: /setBlockedURLs[\s\S]*`\*\$\{/ };
rec.源码佐证 = [
  { 文件: 'scripts/jimeng-b110b.mjs', 行: 96, 须匹配: /`\*\$\{[^}]+\}\*`/, 说明: 'b 轮拼出 pattern `*${KEY}*`，而 KEY 取自 `out.key` = **上传存储 key**' },
  { 文件: 'scripts/jimeng-b110b.mjs', 行: 97, 须匹配: /setBlockedURLs/, 说明: 'b 轮真正发出拦截（urls: [pattern]）' },
  { 文件: 'scripts/jimeng-b110c.mjs', 行: 75, 须匹配: /tos-cn-v-148450/, 说明: 'c 轮：从 `<audio>.src` 用正则抽出**播放取流 key**' },
  { 文件: 'scripts/jimeng-b110c.mjs', 行: 84, 须匹配: /`\*\$\{[^}]+\}\*`/, 说明: 'c 轮拼出 pattern `*${out.realKey}*` —— **这就是成功配方**' },
  { 文件: 'scripts/jimeng-b110c.mjs', 行: 85, 须匹配: /setBlockedURLs/, 说明: 'c 轮真正发出拦截（urls: [blockPattern]）' },
  { 文件: 'scripts/jimeng-b110d.mjs', 行: 116, 须匹配: /setBlockedURLs/, 说明: 'd 轮：`realKey2`（同一个播放取流 key）' },
  { 文件: 'scripts/jimeng-b110e.mjs', 行: 84, 须匹配: /setBlockedURLs/, 说明: 'e 轮：`*${KEY}*`（同一个播放取流 key）' },
];
void 该含;

// ---- ⑤ 自检：那些行是否真的含 setBlockedURLs ----
rec.源码核对 = rec.源码佐证.map((z) => {
  const 全文 = fs.readFileSync(z.文件, 'utf8').split('\n');
  const 实际 = 全文[z.行 - 1] || '';
  return { 文件: z.文件, 行: z.行, 含拦截调用: z.须匹配.test(实际), 实际: 实际.trim().slice(0, 90) };
});

// ---- ⑥ 结论 ----
const 成功段 = rec.判读.filter((z) => /播放取流 key/.test(z.判定.段)).map((z) => z.key);
rec.结论 = {
  批次110成功拦的段: '`tos-cn-v-148450/` 后面那一段 32 位混合大小写 key（即手册早已记的「播放取流 key」）',
  批次110用过的取值: [...new Set(成功段)],
  批次110b拦的段: '**上传存储 key** —— 正是 `20-reference.md` 写着「拿上传日志里的 key 去拦播放会得到假注入」的那一个',
  批次158拦的段: rec.批次158落在哪一段,
  判定: '批次 158 的负结果**根因已定位**：拦错了段。手册的参考页本来就写明了该用哪一段，是本轮自己挑了没被验过的那一段。',
};
rec.源码核对全过 = rec.源码核对.every((z) => z.含拦截调用);
rec.断言 = {
  源码逐行核对全过: rec.源码核对全过,
  批次110存在播放取流key: 成功段.length > 0,
  批次110b拦的是上传存储key: rec.判读.some((z) => z.轮 === 'b' && /上传存储 key/.test(z.判定.段)),
  批次158拦的不是那一段: /第 1 段/.test(rec.批次158落在哪一段),
};
rec.断言全过 = Object.values(rec.断言).every(Boolean);

fs.writeFileSync('scripts/_tmp-b159a.json', JSON.stringify(rec, null, 1));
console.log('各轮 pattern:');
for (const z of rec.判读) console.log('  b110' + z.轮, '→', z.key, '|', z.判定.段);
console.log('\n源码逐行核对:');
for (const z of rec.源码核对) console.log(' ', z.含拦截调用 ? '✅' : '❌', z.文件 + ':' + z.行, z.实际);
console.log('\n结论:', JSON.stringify(rec.结论, null, 1));
console.log('\n断言:', JSON.stringify(rec.断言), '| 全过 =', rec.断言全过);
process.exit(rec.断言全过 ? 0 : 1);
