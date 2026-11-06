import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, generalError, money } from "../api";
import { useCart } from "../CartContext.jsx";
import { FormError } from "../components/Field.jsx";

export default function PaymentSuccess() {
  const [params] = useSearchParams();
  const { refresh } = useCart();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState(null);
  const started = useRef(false); // React StrictMode runs effects twice in development

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const data = params.get("data");
    if (!data) return setError("No payment details were received from eSewa.");
    // The browser only tells us eSewa sent it back. The SERVER checks the signature and amount.
    api("/orders/esewa/verify/", { method: "POST", body: { data } })
      .then((o) => { setOrder(o); refresh(); })
      .catch((err) => setError(generalError(err) || err.data?.detail || "We could not confirm your payment."));
  }, [params, refresh]);

  if (error) {
    return (
      <div className="card center">
        <h1 className="h3">Payment not confirmed</h1>
        <FormError message={error} />
        <p className="muted">If money was taken from your eSewa account, contact support with your eSewa receipt.</p>
        <Link className="btn" to="/cart">Back to cart</Link>
      </div>
    );
  }
  if (!order) return <p className="muted">Confirming your payment with eSewa...</p>;

  return (
    <div className="card center">
      {order.status === "paid" ? (
        <>
          <h1 className="h3">Payment received</h1>
          <p>Thank you! You paid <b>{money(order.total)}</b>.</p>
          <p className="muted small">eSewa reference: {order.esewa_code}</p>
          <p className="muted">Your receipt has a QR code. Scan it any time to report a problem with the phone.</p>
          <Link className="btn" to={`/orders/${order.id}`}>View receipt and QR code</Link>
        </>
      ) : (
        <>
          <h1 className="h3">Payment received, phone unavailable</h1>
          <p className="muted">Another buyer completed the purchase of a phone in your order first. Your payment of {money(order.total)} has been flagged and will be refunded to your eSewa account.</p>
          <Link className="btn" to="/marketplace">Back to marketplace</Link>
        </>
      )}
    </div>
  );
}
