import { useEffect, useState } from "react";
import { api, generalError } from "../api";
import { useAuth } from "../AuthContext.jsx";
import { FormError } from "../components/Field.jsx";

export default function Problems() {
  const { user } = useAuth();
  const [reports, setReports] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api("/problems/").then(setReports).catch((e) => setError(generalError(e) || "Could not load reports."));
  }, []);

  return (
    <>
      <h1 className="h3">{user.role === "buyer" ? "My problem reports" : "Problems reported on phones you sold"}</h1>
      <FormError message={error} />
      <div className="card" style={{ padding: 0 }}>
        {reports === null ? <p className="muted" style={{ padding: "2rem" }}>Loading...</p>
          : reports.length === 0 ? <p className="muted" style={{ padding: "2rem", textAlign: "center" }}>No reports yet.</p>
          : (
            <div className="table-wrap"><table>
              <thead><tr><th>Phone</th><th>Problem</th><th>Details</th><th>Status</th><th>Date</th></tr></thead>
              <tbody>
                {reports.map((r) => (
                  <tr key={r.id}>
                    <td><b>{r.item_title}</b></td>
                    <td>{r.category_label}</td>
                    <td style={{ maxWidth: 320 }}>{r.description}{r.admin_note && <div className="muted small">Team note: {r.admin_note}</div>}</td>
                    <td><span className={`badge ${r.status === "open" ? "badge-warn" : ""}`}>{r.status_label}</span></td>
                    <td>{new Date(r.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table></div>
          )}
      </div>
    </>
  );
}
