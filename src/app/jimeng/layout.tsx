import "../jimeng-canvas.css";

export default function JimengLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  // 即梦画布全屏工作区；字体栈来自源站 body 计算样式 (SOURCE_FACT)
  return (
    <div
      className="jimeng-app"
      style={{ width: "100vw", height: "100vh", overflow: "hidden" }}
    >
      {children}
    </div>
  );
}
