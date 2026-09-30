import { Outlet } from "react-router";

export default function App() {
  return (
    <div className="min-h-screen bg-slate-100">
      <Outlet />
    </div>
  );
}