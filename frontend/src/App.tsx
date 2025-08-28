import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import ClientChat from "./pages/ClientChat";
import AdminLogin from "./pages/AdminLogin";
import AdminBranding from "./pages/AdminBranding";

export default function App() {
  return (
    <BrowserRouter>
      <nav className="p-3 border-b flex gap-3 text-sm">
        <Link to="/">Chat</Link>
        <Link to="/admin/login">Admin Login</Link>
        <Link to="/admin/branding">Branding</Link>
      </nav>
      <Routes>
        <Route path="/" element={<ClientChat />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="/admin/branding" element={<AdminBranding />} />
      </Routes>
    </BrowserRouter>
  );
}