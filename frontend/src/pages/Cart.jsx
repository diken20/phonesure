import { useState } from "react";
import { Link } from "react-router-dom";
import { api, generalError, money } from "../api";
import { useCart } from "../CartContext.jsx";
import { FormError } from "../components/Field.jsx";

// eSewa needs a normal browser form POST, so we build one and submit it.
function postToEsewa({ url, fields }) {
  const form = document.createElement("form");
  form.method = "POST";
  form.action = url;
  Object.entries(fields).forEach(([name, value]) => {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = name;
    input.value = value;
    form.appendChild(input);
  });
  document.body.appendChild(form);
  form.submit();
}

export default function Cart() {
  const { cart, remove, refresh } = useCart();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [problems, setProblems] = useState([]);
  const [paymentMethod, setPaymentMethod] = useState("esewa");

  const unavailable = cart.items.some((i) => !i.available);

  async function handlePay() {
    setBusy(true);
    setError(null);
    setProblems([]);
    try {
      const result = await api("/orders/checkout/", { method: "POST", body: { payment_method: paymentMethod } });
      if (paymentMethod === "esewa") postToEsewa(result.esewa);
      else { refresh(); window.location.href = `/orders/${result.id}`; }
    } catch (err) {
      setError(generalError(err) || err.data?.detail || "Could not start the payment.");
      setProblems(err.data?.problems || []);
      refresh();
      setBusy(false);
    }
  }

  if (cart.items.length === 0) {
    return (
      <div className="card center" style={{ textAlign: "center" }}>
        <h1 className="h3">Your cart is empty</h1>
        <p className="muted">Browse the marketplace and add a phone you like.</p>
        <Link className="btn" to="/marketplace">Browse phones</Link>
      </div>
    );
  }

  return (
    <>
      <h1 className="h3">Your cart</h1>
      <div className="cols">
        <div className="stack">
          {cart.items.map(({ id, phone, available }) => (
            <div className="card cart-row" key={id}>
              <div className="cart-thumb">{phone.photo ? <img src={phone.photo} alt="" /> : "Photo"}</div>
              <div style={{ flex: 1 }}>
                <Link to={`/marketplace/${phone.id}`}><b>{phone.brand} {phone.title}</b></Link>
                <div className="muted small">{phone.condition}, {phone.battery_health}% battery</div>
                {!available && <div className="error">This phone is no longer available. Remove it to continue.</div>}
              </div>
              <div className="price" style={{ fontSize: "1.1rem" }}>{money(phone.asking_price)}</div>
              <button className="btn btn-outline btn-small" onClick={() => remove(id)}>Remove</button>
            </div>
          ))}
        </div>

        <div className="card">
          <h2 className="h6">Order summary</h2>
          <div className="between"><span>{cart.items.length} {cart.items.length === 1 ? "phone" : "phones"}</span><span>{money(cart.total)}</span></div>
          <div className="between" style={{ margin: ".75rem 0 1rem" }}><b>Total</b><b className="price" style={{ fontSize: "1.3rem" }}>{money(cart.total)}</b></div>
          <FormError message={error} />
          {problems.map((p) => <div className="alert alert-danger" key={p}>{p}</div>)}
          <fieldset className="stack" style={{ border: 0, padding: 0, margin: "1rem 0" }}>
            <legend className="h6">Payment method</legend>
            <label className="row"><input type="radio" name="payment" value="esewa" checked={paymentMethod === "esewa"} onChange={() => setPaymentMethod("esewa")} /> eSewa (online payment)</label>
            <label className="row"><input type="radio" name="payment" value="cod" checked={paymentMethod === "cod"} onChange={() => setPaymentMethod("cod")} /> Cash on delivery</label>
          </fieldset>
          <button className="btn btn-block" onClick={handlePay} disabled={busy || unavailable}>
            {busy ? "Processing..." : paymentMethod === "esewa" ? "Continue to eSewa" : "Place COD order"}
          </button>
          <p className="muted small" style={{ marginBottom: 0 }}>
            {paymentMethod === "esewa" ? "You will be taken to eSewa to complete payment." : "Pay the seller/courier when the phone is delivered. Verify the phone before paying."}
          </p>
        </div>
      </div>
    </>
  );
}
