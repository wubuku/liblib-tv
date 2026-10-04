import fs from 'node:fs';
// 裁剪后自检：确认每份证据的**关键读数**一个没丢
const 查 = (文件, 取) => { const j = JSON.parse(fs.readFileSync(文件, 'utf8')); return { 文件, ...取(j) }; };

const a = 查('scripts/_tmp-b151.json', (j) => ({
  族数: j.族.length,
  每族量_静息态: j.族.map((f) => (f.量_静息态 || []).length).join(','),
  每族量_选中态: j.族.map((f) => (f.量_选中态 || []).length).join(','),
  缩放档数: (j.缩放档 && j.缩放档.档 || []).length,
  同态真不一致条数: (j.同态真不一致 || []).length,
  断言全过: j.断言全过,
  收尾: j.收尾,
  标题文字齐全: j.族.every((f) => (f.量_静息态 || []).every((m) => m.元素 && m.元素['flow-node-title'] && m.元素['flow-node-title'].文字)),
  标签文字齐全: j.族.every((f) => (f.量_静息态 || []).every((m) => m.元素 && m.元素['flow-node-selected-tag'] && Array.isArray(m.元素['flow-node-selected-tag'].css))),
}));
const c = 查('scripts/_tmp-b151c.json', (j) => ({
  档数: (j.档 || []).length,
  每档新建3: (j.档 || []).every((d) => (d.新建组 || []).length === 3),
  每档原有3: (j.档 || []).every((d) => (d.原有组 || []).length === 3),
  建前文本节点: (j.建前文本节点 || []).map((x) => x.aria),
  新建k取值: [...new Set(j.表.map((r) => r.新k标签))],
  原有k取值: [...new Set(j.表.map((r) => r.原k标签))],
  断言全过: j.断言全过,
  收尾: j.收尾,
  原有删除: (j.删除 || []).map((d) => (d.消失 || []).join('|')),
}));
const b = 查('scripts/_tmp-b151b.json', (j) => ({
  档数: (j.档 || []).length, 断言全过: j.断言全过, 收尾: j.收尾,
  注: 'b 轮的作用域是错的（量到了原有节点），它留下的线索由 c 轮按 id 重测收口 —— 证据保留是因为它记录了「k_标题 全为 null」这个事实',
}));
console.log(JSON.stringify({ a, b, c }, null, 1));

const ok = a.族数 === 4 && a.每族量_静息态 === '3,3,3,3' && a.缩放档数 === 3 && a.标题文字齐全 && a.标签文字齐全 &&
  c.档数 === 6 && c.每档新建3 && c.每档原有3 &&
  JSON.stringify(c.新建k取值) === JSON.stringify([1.6667, 2]) && JSON.stringify(c.原有k取值) === JSON.stringify([2]);
console.log(ok ? '\n✅ 关键读数一个没丢' : '\n🔴 关键读数有丢失');
process.exit(ok ? 0 : 1);
