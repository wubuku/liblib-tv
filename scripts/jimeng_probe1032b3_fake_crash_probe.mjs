/**
 * 一个**故意崩溃**的探针 —— 只给 `jimeng_probe1032b3_crash_selftest.py` 用。
 *
 * 它模拟「仪器故障」：打印崩溃标记并以**独立退出码 2** 退出
 * （2 = 仪器崩了；1 = 数据有问题；0 = 全绿）。
 */
const CRASH_EXIT_CODE = 2;
const CRASH_MARKER = 'INSTRUMENT_CRASH';
console.log('INSTRUMENT_CRASH :: 模拟的仪器故障（自检用）');
process.exit(CRASH_EXIT_CODE);
