import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../AuthContext.jsx";

export default function ProtectedRoute({ children, sellerOnly = false, buyerOnly = false, adminOnly = false }) {
  const { user, loading, isSeller } = useAuth();
  const location = useLocation();

  if (loading) return null;
  if (!user) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  if (sellerOnly && !isSeller) {
    return <div className="card"><h1 className="h3">Sellers only</h1><p className="muted">Register a seller account to add and manage phones.</p></div>;
  }
  if (adminOnly && user.role !== "admin") {
    return <div className="card"><h1 className="h3">Admins only</h1><p className="muted">This area is for the PhoneSure admin team.</p></div>;
  }
  if (buyerOnly && user.role !== "buyer") {
    return <div className="card"><h1 className="h3">Buyers only</h1><p className="muted">Sign in with a buyer account to use this page.</p></div>;
  }
  return children;
}
