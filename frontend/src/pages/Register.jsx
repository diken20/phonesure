import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { generalError } from "../api";
import { useAuth } from "../AuthContext.jsx";
import { Field, FormError } from "../components/Field.jsx";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", email: "", password: "", role: "seller" });
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);

  const set = (name) => (e) => setForm({ ...form, [name]: e.target.value });

  async function handleSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    try {
      await register(form);
      navigate(form.role === "seller" ? "/phones" : "/marketplace");
    } catch (err) {
      setErrors(err.data?.detail ? { general: err.data.detail } : { ...err.data, general: generalError(err) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card center">
      <h1 className="h3">Create your account</h1>
      <form onSubmit={handleSubmit}>
        <FormError message={errors.general} />
        <Field label="Username" htmlFor="username" error={errors.username}>
          <input id="username" value={form.username} onChange={set("username")} autoComplete="username" required />
        </Field>
        <Field label="Email" htmlFor="email" error={errors.email}>
          <input id="email" type="email" value={form.email} onChange={set("email")} autoComplete="email" required />
        </Field>
        <Field label="Password" htmlFor="password" error={errors.password} help="At least 8 characters, not a common password.">
          <input id="password" type="password" value={form.password} onChange={set("password")} autoComplete="new-password" required />
        </Field>
        <Field label="I am a" htmlFor="role" error={errors.role}>
          <select id="role" value={form.role} onChange={set("role")}>
            <option value="seller">I want to sell phones</option>
            <option value="buyer">I want to buy or check prices</option>
          </select>
        </Field>
        <button className="btn btn-block" disabled={busy}>{busy ? "Creating..." : "Register"}</button>
      </form>
      <p className="muted">Already registered? <Link to="/login">Sign in</Link></p>
    </div>
  );
}
