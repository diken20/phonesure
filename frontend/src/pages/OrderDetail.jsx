import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, generalError, money } from "../api";
import { FormError } from "../components/Field.jsx";

export default function OrderDetail() {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api(`/orders/${id}/`).then(setOrder).catch((e) => setError(e.status === 404 ? "Order not found." : generalError(e) || "Could not load the order."));
  }, [id]);

  if (error) return <><FormError message={error} /><Link to="/orders">Back to orders</Link></>;
  if (!order) return <p className="muted">Loading...</p>;

  return (
    <>
      <p className="no-print"><Link to="/orders">&larr; My orders</Link></p>
      <div className="card receipt">
        <div className="between">
          <h1 className="h3" style={{ margin: 0 }}>Receipt #{order.id}</h1>
          <span className={`badge ${order.status === "paid" ? "" : "badge-warn"}`}>{order.status_label}</span>
        </div>
        <div className="muted small" style={{ margin: ".5rem 0 1.25rem" }}>
          {order.paid_at ? `Paid ${new Date(order.paid_at).toLocaleString()}` : `Created ${new Date(order.created_at).toLocaleString()}`}
          {order.esewa_code && <> &middot; eSewa reference {order.esewa_code}</>}
        </div>

        {order.items.map((item) => (
          <div className="receipt-item" key={item.public_id}>
            <div style={{ flex: 1 }}>
              <b>{item.title}</b>
              <div>{money(item.price)}</div>
              {item.problem_count > 0 && <div className="muted small">{item.problem_count} problem report(s) filed</div>}
              {item.qr && <Link className="btn btn-outline btn-small no-print" style={{ marginTop: ".5rem" }}
                to={`/report-problem/${item.public_id}`}>Report a problem</Link>}
            </div>
            {item.qr && (
              <div className="qr">
                <img src={item.qr} alt={`QR code to report a problem with ${item.title}`} width="130" height="130" />
                <div className="small muted">Scan to report a problem</div>
              </div>
            )}
          </div>
        ))}

        <div className="between" style={{ marginTop: "1rem" }}>
          <b>Total</b><b className="price" style={{ fontSize: "1.3rem" }}>{money(order.total)}</b>
        </div>
        {order.status === "paid" && (
          <button className="btn btn-outline no-print" style={{ marginTop: "1rem" }} onClick={() => window.print()}>Print receipt</button>
        )}
      </div>
    </>
  );
}
