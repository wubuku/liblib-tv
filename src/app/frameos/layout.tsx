import "../frameos-canvas.css";

export default function FrameosLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="frameos-app" style={{ width: "100vw", height: "100vh", overflow: "hidden", background: "#0D0D0D" }}>
      {children}
    </div>
  );
}
