import { NavLink } from "react-router-dom";

export default function AdminTabs() {
  return (
    <div className="tabs">
      <NavLink to="/admin" end>Dashboard</NavLink>
      <NavLink to="/admin/listings">Listings</NavLink>
      <NavLink to="/admin/users">Users</NavLink>
      <NavLink to="/admin/prices">Reference prices</NavLink>
      <NavLink to="/admin/orders">Orders</NavLink>
      <NavLink to="/admin/problems">Problems</NavLink>
    </div>
  );
}
