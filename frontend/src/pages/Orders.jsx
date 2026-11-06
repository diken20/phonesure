import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, generalError, money } from "../api";
import { FormError } from "../components/Field.jsx";

export default function Orders() {
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api("/orders/").then(setOrders).catch((e) => setError(generalError(e) || "Could not load orders."));
  }, []);

  return (
    <>
      <h1 className="h3">My orders</h1>
      <FormError message={error} />
      <div className="card" style={{ padding: 0 }}>
        {orders === null ? <p className="muted" style={{ padding: "2rem" }}>Loading...</p>
          : orders.length === 0 ? <p className="muted" style={{ padding: "2rem", textAlign: "center" }}>You have not bought anything yet.</p>
          : (
            <div className="table-wrap"><table>
              <thead><tr><th>Order</th><th>Phones</th><th>Total</th><th>Status</th><th></th></tr></thead>
              <tbody>
                {orders.map((o) => (
                  <tr key={o.id}>
                    <td><b>#{o.id}</b><div className="muted small">{new Date(o.created_at).toLocaleDateString()}</div></td>
                    <td>{o.items.map((i) => i.title).join(", ")}</td>
                    <td>{money(o.total)}</td>
                    <td><span className={`badge ${o.status === "paid" ? "" : "badge-warn"}`}>{o.status_label}</span></td>
                    <td><Link className="btn btn-outline btn-small" to={`/orders/${o.id}`}>{o.status === "paid" ? "Receipt and QR" : "View"}</Link></td>
                  </tr>
                ))}
              </tbody>
            </table></div>
          )}
      </div>
    </>
  );
}
