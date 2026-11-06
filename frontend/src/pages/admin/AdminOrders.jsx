import { useCallback, useEffect, useState } from "react";
import { api, generalError, money } from "../../api";
import AdminTabs from "../../components/AdminTabs.jsx";
import { FormError } from "../../components/Field.jsx";

export default function AdminOrders() {
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    api("/admin/orders/").then(setOrders).catch((e) => setError(generalError(e) || "Could not load orders."));
  }, []);
  useEffect(load, [load]);

  async function refunded(order) {
    if (!window.confirm(`Confirm that you already refunded order #${order.id} (${money(order.total)}) in the eSewa merchant portal?`)) return;
    try { await api(`/admin/orders/${order.id}/refunded/`, { method: "POST" }); load(); }
    catch (e) { setError(e.data?.detail || generalError(e) || "Could not update the order."); }
  }

  return (
    <>
      <h1 className="h3">Admin portal</h1>
      <AdminTabs />
      <FormError message={error} />
      <div className="card" style={{ padding: 0 }}>
        {orders === null ? <p className="muted" style={{ padding: "2rem" }}>Loading...</p>
          : orders.length === 0 ? <p className="muted" style={{ padding: "2rem", textAlign: "center" }}>No orders yet.</p> : (
          <div className="table-wrap"><table>
            <thead><tr><th>Order</th><th>Buyer</th><th>Phones</th><th>Total</th><th>eSewa ref</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id}>
                  <td><b>#{o.id}</b><div className="muted small">{new Date(o.created_at).toLocaleDateString()}</div></td>
                  <td>{o.buyer}</td>
                  <td>{o.items.map((i) => i.title).join(", ")}</td>
                  <td>{money(o.total)}</td>
                  <td>{o.esewa_code || "-"}</td>
                  <td><span className={`badge ${o.status === "paid" || o.status === "refunded" ? "" : "badge-warn"}`}>{o.status_label}</span></td>
                  <td>{o.status === "review" && <button className="btn btn-small" onClick={() => refunded(o)}>Mark refunded</button>}</td>
                </tr>
              ))}
            </tbody>
          </table></div>
        )}
      </div>
      <p className="muted small">"Needs review" means the buyer paid but the phone was sold to someone else first. Refund it in the eSewa merchant portal, then press "Mark refunded".</p>
    </>
  );
}
