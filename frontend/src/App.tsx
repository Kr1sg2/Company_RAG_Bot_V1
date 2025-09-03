import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import ClientChat from "./pages/ClientChat";
import AdminLogin from "./pages/AdminLogin";
import AdminBranding from "./pages/AdminBranding";

function Navigation() {
  const location = useLocation();
  
  // Only show nav if localhost or __devNav=1 parameter
  const isLocalhost = typeof window !== 'undefined' && window.location.hostname === 'localhost';
  const hasDevNav = new URLSearchParams(location.search).get('__devNav') === '1';
  const shouldShowNav = isLocalhost || hasDevNav;

  if (!shouldShowNav) {
    return null; // Hide navigation for public users
  }

  return (
    <nav className="p-3 border-b flex gap-3 text-sm">
      <Link to="/">Chat</Link>
      <Link to="/admin/login">Admin Login</Link>
      <Link to="/admin/branding">Branding</Link>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Navigation />
      <Routes>
        <Route path="/" element={<ClientChat />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="/admin/branding" element={<AdminBranding />} />
      </Routes>
    </BrowserRouter>
  );
}

