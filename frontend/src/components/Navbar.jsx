import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext.jsx";
import { useCart } from "../CartContext.jsx";

export default function Navbar() {
  const { user, logout } = useAuth();
  const { cart } = useCart();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  return (
    <nav className="nav">
      <Link to="/" className="brand">PhoneSure</Link>
      <div className="nav-links">
        <NavLink to="/valuation">Valuation</NavLink>
        <NavLink to="/marketplace">Marketplace</NavLink>
        {user?.role === "seller" && <NavLink to="/phones">My Phones</NavLink>}
        {user?.role === "admin" && <NavLink to="/admin">Admin portal</NavLink>}
        {user?.role === "buyer" && <NavLink to="/cart">Cart{cart.count > 0 && <span className="badge" style={{ marginLeft: ".35rem" }}>{cart.count}</span>}</NavLink>}
        {user?.role === "buyer" && <NavLink to="/orders">My Orders</NavLink>}
        {user && <NavLink to="/problems">Problems</NavLink>}
      </div>
      <div className="nav-actions">
        {user ? (
          <>
            <span>{user.username} <span className="badge">{user.role}</span></span>
            <button className="btn btn-outline" onClick={handleLogout}>Log out</button>
          </>
        ) : (
          <>
            <Link className="btn btn-outline" to="/register">Register</Link>
            <Link className="btn" to="/login">Sign in</Link>
          </>
        )}
      </div>
    </nav>
  );
}
