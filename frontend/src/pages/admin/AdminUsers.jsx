import { useCallback, useEffect, useState } from "react";
import { api, generalError } from "../../api";
import AdminTabs from "../../components/AdminTabs.jsx";
import { FormError } from "../../components/Field.jsx";

export default function AdminUsers() {
  const [role, setRole] = useState("");
  const [users, setUsers] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    api(`/admin/users/${role ? `?role=${role}` : ""}`).then(setUsers).catch((e) => setError(generalError(e) || "Could not load users."));
  }, [role]);
  useEffect(load, [load]);

  async function toggle(user) {
    setError(null);
    try {
      await api(`/admin/users/${user.id}/`, { method: "PATCH", body: { is_active: !user.is_active } });
      load();
    } catch (e) { setError(e.data?.non_field_errors?.[0] || generalError(e) || "Could not update the user."); }
  }

  return (
    <>
      <h1 className="h3">Admin portal</h1>
      <AdminTabs />
      <div className="row" style={{ marginBottom: "1rem" }}>
        <label htmlFor="role" className="muted small">Show</label>
        <select id="role" className="input" value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="">Everyone</option><option value="seller">Sellers</option><option value="buyer">Buyers</option><option value="admin">Admins</option>
        </select>
      </div>
      <FormError message={error} />
      <div className="card" style={{ padding: 0 }}>
        {users === null ? <p className="muted" style={{ padding: "2rem" }}>Loading...</p> : (
          <div className="table-wrap"><table>
            <thead><tr><th>User</th><th>Role</th><th>Phones</th><th>Orders</th><th>Joined</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td><b>{u.username}</b><div className="muted small">{u.email}</div></td>
                  <td><span className="badge">{u.role}</span></td>
                  <td>{u.phone_count}</td><td>{u.order_count}</td>
                  <td>{new Date(u.date_joined).toLocaleDateString()}</td>
                  <td><span className={`badge ${u.is_active ? "" : "badge-danger"}`}>{u.is_active ? "Active" : "Deactivated"}</span></td>
                  <td>{u.role !== "admin" && (
                    <button className="btn btn-outline btn-small" onClick={() => toggle(u)}>{u.is_active ? "Deactivate" : "Reactivate"}</button>
                  )}</td>
                </tr>
              ))}
            </tbody>
          </table></div>
        )}
      </div>
      <p className="muted small">Deactivating a seller hides their phones from buyers. Deactivated users cannot sign in.</p>
    </>
  );
}
