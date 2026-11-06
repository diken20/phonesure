import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api, generalError, money, number } from "../api";
import { FormError } from "../components/Field.jsx";

const STATUS_BADGE = {
  draft: ["Draft", "badge-warn"],
  pending: ["Waiting for approval", "badge-warn"],
  listed: ["Live for buyers", ""],
  rejected: ["Rejected", "badge-danger"],
  sold: ["Sold", ""],
};

const VERDICT_BADGE = {
  within: ["Fair price", ""],
  above: ["Above range", "badge-warn"],
  below: ["Below range", "badge-warn"],
};

export default function PhoneList() {
  const location = useLocation();
  const [phones, setPhones] = useState(null);
  const [error, setError] = useState(null);
  const [flash, setFlash] = useState(location.state?.flash || null);
  const [toDelete, setToDelete] = useState(null);

  useEffect(() => {
    api("/phones/").then(setPhones).catch((err) => setError(generalError(err) || "Could not load phones."));
  }, []);

  async function confirmDelete() {
    try {
      await api(`/phones/${toDelete.id}/`, { method: "DELETE" });
      setPhones(phones.filter((p) => p.id !== toDelete.id));
      setFlash("Phone deleted.");
    } catch (err) {
      setError(generalError(err) || "Could not delete the phone.");
    } finally {
      setToDelete(null);
    }
  }

  return (
    <>
      <div className="between" style={{ marginBottom: "1.5rem" }}>
        <h1 className="h3" style={{ margin: 0 }}>My Phones</h1>
        <Link className="btn" to="/phones/add">Add new phone</Link>
      </div>
      <FormError message={error} />
      {flash && <div className="alert alert-success">{flash}</div>}

      <div className="card" style={{ padding: 0 }}>
        {phones === null ? (
          <p className="muted" style={{ padding: "2rem" }}>Loading...</p>
        ) : phones.length === 0 ? (
          <p className="muted" style={{ padding: "2rem", textAlign: "center" }}>You have not added any phones yet.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Phone</th><th>Asking</th><th>Fair range</th><th>Trust</th><th>Price check</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {phones.map((p) => {
                  const [label, cls] = VERDICT_BADGE[p.price_verdict];
                  return (
                    <tr key={p.id}>
                      <td>
                        <b>{p.reference_label}</b>
                        <div className="muted" style={{ fontSize: ".85rem" }}>{p.condition}, {p.battery_health}% battery</div>
                      </td>
                      <td>{money(p.asking_price)}</td>
                      <td>{number(p.valuation.low)} - {number(p.valuation.high)}</td>
                      <td>{p.trust_score}/100</td>
                      <td><span className={`badge ${cls}`}>{label}</span></td>
                      <td>
                        <span className={`badge ${STATUS_BADGE[p.status][1]}`}>{STATUS_BADGE[p.status][0]}</span>
                        {p.status === "rejected" && p.review_note && <div className="error small" style={{ maxWidth: 220, marginTop: ".35rem" }}>{p.review_note}</div>}
                      </td>
                      <td>
                        {p.status === "sold" ? <span className="muted small">Sold - locked</span> : (
                          <div className="row">
                            <Link className="btn btn-outline btn-small" to={`/phones/${p.id}/edit`}>Edit</Link>
                            <button className="btn btn-outline btn-small" onClick={() => setToDelete(p)}>Delete</button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {toDelete && (
        <div className="overlay" onClick={() => setToDelete(null)}>
          <div className="modal" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
            <h2 className="h5">Delete this phone?</h2>
            <p className="muted"><b>{toDelete.reference_label}</b> will be removed permanently.</p>
            <div className="row">
              <button className="btn btn-danger" onClick={confirmDelete}>Yes, delete</button>
              <button className="btn btn-outline" onClick={() => setToDelete(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
