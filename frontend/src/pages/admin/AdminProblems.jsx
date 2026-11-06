import { useCallback, useEffect, useState } from "react";
import { api, generalError } from "../../api";
import AdminTabs from "../../components/AdminTabs.jsx";
import { FormError } from "../../components/Field.jsx";

function ProblemRow({ report, onSave }) {
  const [status, setStatus] = useState(report.status);
  const [note, setNote] = useState(report.admin_note);
  const changed = status !== report.status || note !== report.admin_note;
  return (
    <tr>
      <td><b>{report.item_title}</b><div className="muted small">Order #{report.order_id} &middot; seller {report.seller}</div></td>
      <td>{report.category_label}<div className="muted small">by {report.reporter_name}</div></td>
      <td style={{ maxWidth: 280 }}>{report.description}</td>
      <td>
        <select className="input" value={status} aria-label="Status" onChange={(e) => setStatus(e.target.value)}>
          <option value="open">Open</option><option value="resolved">Resolved</option>
        </select>
      </td>
      <td><input className="input" value={note} placeholder="Note for buyer and seller" aria-label="Admin note" onChange={(e) => setNote(e.target.value)} /></td>
      <td><button className="btn btn-small" disabled={!changed} onClick={() => onSave(report, { status, admin_note: note })}>Save</button></td>
    </tr>
  );
}

export default function AdminProblems() {
  const [reports, setReports] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    api("/admin/problems/").then(setReports).catch((e) => setError(generalError(e) || "Could not load reports."));
  }, []);
  useEffect(load, [load]);

  async function save(report, body) {
    setError(null);
    try { await api(`/admin/problems/${report.id}/`, { method: "PATCH", body }); load(); }
    catch (e) { setError(generalError(e) || "Could not save."); }
  }

  return (
    <>
      <h1 className="h3">Admin portal</h1>
      <AdminTabs />
      <FormError message={error} />
      <div className="card" style={{ padding: 0 }}>
        {reports === null ? <p className="muted" style={{ padding: "2rem" }}>Loading...</p>
          : reports.length === 0 ? <p className="muted" style={{ padding: "2rem", textAlign: "center" }}>No problem reports.</p> : (
          <div className="table-wrap"><table>
            <thead><tr><th>Phone</th><th>Problem</th><th>Details</th><th>Status</th><th>Note</th><th></th></tr></thead>
            <tbody>{reports.map((r) => <ProblemRow key={`${r.id}-${r.status}-${r.admin_note}`} report={r} onSave={save} />)}</tbody>
          </table></div>
        )}
      </div>
    </>
  );
}
