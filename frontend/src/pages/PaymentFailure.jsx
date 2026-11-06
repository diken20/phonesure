import { Link } from "react-router-dom";

export default function PaymentFailure() {
  return (
    <div className="card center">
      <h1 className="h3">Payment cancelled or failed</h1>
      <p className="muted">No money was taken for this order. Your phones are still in your cart.</p>
      <Link className="btn" to="/cart">Back to cart</Link>
    </div>
  );
}
