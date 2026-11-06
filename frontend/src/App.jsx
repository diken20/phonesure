import { Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Calculator from "./pages/Calculator.jsx";
import PhoneList from "./pages/PhoneList.jsx";
import PhoneForm from "./pages/PhoneForm.jsx";
import Marketplace from "./pages/Marketplace.jsx";
import ListingDetail from "./pages/ListingDetail.jsx";
import Cart from "./pages/Cart.jsx";
import PaymentSuccess from "./pages/PaymentSuccess.jsx";
import PaymentFailure from "./pages/PaymentFailure.jsx";
import Orders from "./pages/Orders.jsx";
import OrderDetail from "./pages/OrderDetail.jsx";
import ReportProblem from "./pages/ReportProblem.jsx";
import Problems from "./pages/Problems.jsx";
import AdminDashboard from "./pages/admin/AdminDashboard.jsx";
import AdminListings from "./pages/admin/AdminListings.jsx";
import AdminUsers from "./pages/admin/AdminUsers.jsx";
import AdminPrices from "./pages/admin/AdminPrices.jsx";
import AdminOrders from "./pages/admin/AdminOrders.jsx";
import AdminProblems from "./pages/admin/AdminProblems.jsx";

export default function App() {
  return (
    <>
      <Navbar />
      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/valuation" element={<Calculator />} />
          <Route path="/marketplace" element={<ProtectedRoute><Marketplace /></ProtectedRoute>} />
          <Route path="/marketplace/:id" element={<ProtectedRoute><ListingDetail /></ProtectedRoute>} />
          <Route path="/phones" element={<ProtectedRoute sellerOnly><PhoneList /></ProtectedRoute>} />
          <Route path="/phones/add" element={<ProtectedRoute sellerOnly><PhoneForm /></ProtectedRoute>} />
          <Route path="/phones/:id/edit" element={<ProtectedRoute sellerOnly><PhoneForm /></ProtectedRoute>} />
          <Route path="/cart" element={<ProtectedRoute buyerOnly><Cart /></ProtectedRoute>} />
          <Route path="/payment/success" element={<ProtectedRoute buyerOnly><PaymentSuccess /></ProtectedRoute>} />
          <Route path="/payment/failure" element={<ProtectedRoute buyerOnly><PaymentFailure /></ProtectedRoute>} />
          <Route path="/orders" element={<ProtectedRoute buyerOnly><Orders /></ProtectedRoute>} />
          <Route path="/orders/:id" element={<ProtectedRoute buyerOnly><OrderDetail /></ProtectedRoute>} />
          <Route path="/report-problem/:publicId" element={<ProtectedRoute buyerOnly><ReportProblem /></ProtectedRoute>} />
          <Route path="/report-listing/:listingId" element={<ProtectedRoute buyerOnly><ReportProblem listingReport /></ProtectedRoute>} />
          <Route path="/problems" element={<ProtectedRoute><Problems /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute adminOnly><AdminDashboard /></ProtectedRoute>} />
          <Route path="/admin/listings" element={<ProtectedRoute adminOnly><AdminListings /></ProtectedRoute>} />
          <Route path="/admin/users" element={<ProtectedRoute adminOnly><AdminUsers /></ProtectedRoute>} />
          <Route path="/admin/prices" element={<ProtectedRoute adminOnly><AdminPrices /></ProtectedRoute>} />
          <Route path="/admin/orders" element={<ProtectedRoute adminOnly><AdminOrders /></ProtectedRoute>} />
          <Route path="/admin/problems" element={<ProtectedRoute adminOnly><AdminProblems /></ProtectedRoute>} />
          <Route path="*" element={<div className="card">Page not found.</div>} />
        </Routes>
      </main>
    </>
  );
}
