import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { generalError } from "../api";
import { useAuth } from "../AuthContext.jsx";
import { Field, FormError } from "../components/Field.jsx";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const set = (name) => (e) => setForm({ ...form, [name]: e.target.value });

  async function handleSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const user = await login(form.username, form.password);
      const home = { buyer: "/marketplace", seller: "/phones", admin: "/admin" }[user.role];
      navigate(location.state?.from || home, { replace: true });
    } catch (err) {
      setError(generalError(err) || "Please fill in both fields.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card center">
      <h1 className="h3">Sign in</h1>
      <form onSubmit={handleSubmit}>
        <FormError message={error} />
        <Field label="Username" htmlFor="username">
          <input id="username" value={form.username} onChange={set("username")} autoComplete="username" required />
        </Field>
        <Field label="Password" htmlFor="password">
          <input id="password" type="password" value={form.password} onChange={set("password")} autoComplete="current-password" required />
        </Field>
        <button className="btn btn-block" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
      </form>
      <p className="muted">New here? <Link to="/register">Create an account</Link></p>
    </div>
  );
}
