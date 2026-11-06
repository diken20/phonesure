import { Link } from "react-router-dom";

export default function Home() {
  return (
    <>
      <div className="card hero">
        <h1>What is your phone really worth?</h1>
        <p className="muted">Fair prices, honest condition reports and trusted resale in Nepal.</p>
        <div className="row" style={{ justifyContent: "center" }}>
          <Link className="btn" to="/valuation">Check a price</Link>
          <Link className="btn btn-outline" to="/marketplace">Browse phones</Link>
        </div>
      </div>
      <div className="features">
        <div className="card"><h2 className="h5">Fair price range</h2><p className="muted">See exactly how age, condition and battery change the price.</p></div>
        <div className="card"><h2 className="h5">Condition report</h2><p className="muted">A trust score and QR code that prove a phone's condition.</p></div>
        <div className="card"><h2 className="h5">Simple resale</h2><p className="muted">List a phone and let buyers search and compare.</p></div>
      </div>
    </>
  );
}
