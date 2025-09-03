import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function AdminLogin() {
  const [user, setUser] = useState("admin");
  const [pass, setPass] = useState("");
  const nav = useNavigate();

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const token = btoa(`${user}:${pass}`);
    localStorage.setItem("adminAuth", token);
    nav("/admin/branding");
  }

  return (
    <div className="min-h-screen grid place-items-center bg-zinc-100">
      <form
        onSubmit={submit}
        className="w-[360px] bg-white rounded-2xl p-6 shadow"
      >
        <h1 className="text-lg font-semibold mb-4">Admin Login</h1>
        <label className="block text-sm mb-1">Username</label>
        <input className="w-full border rounded px-3 py-2 mb-3" value={user} onChange={e=>setUser(e.target.value)} />
        <label className="block text-sm mb-1">Password</label>
        <input type="password" className="w-full border rounded px-3 py-2 mb-4" value={pass} onChange={e=>setPass(e.target.value)} />
        <button className="w-full rounded-lg bg-black text-white py-2" type="submit">Continue</button>
      </form>
    </div>
  );
}