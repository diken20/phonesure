import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, generalError, money } from "../../api";
import AdminTabs from "../../components/AdminTabs.jsx";
import { FormError } from "../../components/Field.jsx";

function Stat({ label, value, to, alert }) {
  const body = (
    <div className={`card stat ${alert ? "stat-alert" : ""}`}>
      <div className="muted small">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
  return to ? <Link to={to} className="listing-link">{body}</Link> : body;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api("/admin/stats/").then(setStats).catch((e) => setError(generalError(e) || "Could not load statistics."));
  }, []);

  return (
    <>
      <h1 className="h3">Admin portal</h1>
      <AdminTabs />
      <FormError message={error} />
      {stats && (
        <>
          <h2 className="h6 muted">Needs your attention</h2>
          <div className="stats">
            <Stat label="Phones waiting for review" value={stats.phones.pending} to="/admin/listings" alert={stats.phones.pending > 0} />
            <Stat label="Open problem reports" value={stats.open_problems} to="/admin/problems" alert={stats.open_problems > 0} />
            <Stat label="Paid orders to refund" value={stats.orders.review} to="/admin/orders" alert={stats.orders.review > 0} />
          </div>
          <h2 className="h6 muted" style={{ marginTop: "1.5rem" }}>Marketplace</h2>
          <div className="stats">
            <Stat label="Listed phones" value={stats.phones.listed} />
            <Stat label="Sold phones" value={stats.phones.sold} />
            <Stat label="Rejected phones" value={stats.phones.rejected} />
            <Stat label="Revenue (paid orders)" value={money(stats.revenue)} />
          </div>
          <h2 className="h6 muted" style={{ marginTop: "1.5rem" }}>People</h2>
          <div className="stats">
            <Stat label="Sellers" value={stats.users.seller} to="/admin/users" />
            <Stat label="Buyers" value={stats.users.buyer} to="/admin/users" />
            <Stat label="Paid orders" value={stats.orders.paid} to="/admin/orders" />
          </div>
        </>
      )}
    </>
  );
}
