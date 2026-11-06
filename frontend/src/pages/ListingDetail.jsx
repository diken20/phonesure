import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, generalError, money } from "../api";
import { useAuth } from "../AuthContext.jsx";
import { useCart } from "../CartContext.jsx";
import ListingCard, { VERDICT } from "../components/ListingCard.jsx";
import { FormError } from "../components/Field.jsx";

const yesNo = (v) => (v ? "Yes" : "No");

export default function ListingDetail() {
  const { id } = useParams();
  const [phone, setPhone] = useState(null);
  const [error, setError] = useState(null);
  const { user } = useAuth();
  const { has, add } = useCart();
  const [adding, setAdding] = useState(false);
  const [cartError, setCartError] = useState(null);
  const [reportOpen, setReportOpen] = useState(false);
  const [reportText, setReportText] = useState("");
  const [reportDone, setReportDone] = useState(false);
  const [buying, setBuying] = useState(false);

  async function handleAdd() {
    setAdding(true);
    setCartError(null);
    try { await add(phone.id); } catch (err) { setCartError(err.data?.phone?.[0] || generalError(err) || "Could not add to cart."); }
    finally { setAdding(false); }
  }

  function postToEsewa({ url, fields }) {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = url;
    Object.entries(fields).forEach(([name, value]) => {
      const input = document.createElement("input");
      input.type = "hidden"; input.name = name; input.value = value;
      form.appendChild(input);
    });
    document.body.appendChild(form); form.submit();
  }

  async function buyNow() {
    setBuying(true); setCartError(null);
    try {
      const result = await api("/orders/checkout/", { method: "POST", body: { phone_id: phone.id, payment_method: "esewa" } });
      postToEsewa(result.esewa);
    } catch (err) {
      setCartError(generalError(err) || err.data?.detail || "Could not start eSewa checkout.");
      setBuying(false);
    }
  }

  async function reportScam(e) {
    e.preventDefault(); setCartError(null);
    try { await api("/problems/", { method: "POST", body: { phone: phone.id, category: "scam", description: reportText } }); setReportDone(true); setReportOpen(false); }
    catch (err) { setCartError(generalError(err) || "Could not send report. Please try again."); }
  }

  useEffect(() => {
    setPhone(null);
    setError(null);
    api(`/marketplace/${id}/`)
      .then(setPhone)
      .catch((err) => setError(err.status === 404 ? "This phone is no longer listed." : generalError(err) || "Could not load this phone."));
    window.scrollTo(0, 0);
  }, [id]);

  if (error) return <><FormError message={error} /><Link to="/marketplace">Back to marketplace</Link></>;
  if (!phone) return <p className="muted">Loading...</p>;

  const condition = phone.condition[0].toUpperCase() + phone.condition.slice(1);

  return (
    <>
      <p><Link to="/marketplace">&larr; Back to marketplace</Link></p>

      <div className="cols">
        <div className="stack">
          <div className="listing-photo detail-photo">
            {phone.photo ? <img src={phone.photo} alt={phone.title} /> : "Phone photo"}
          </div>
          <div className="card">
            <h1 className="h3" style={{ marginBottom: ".25rem" }}>{phone.brand} {phone.title}</h1>
            <div className="muted">{condition}, {phone.battery_health}% battery, {phone.age_label.toLowerCase()}</div>
            <div className="price" style={{ margin: ".5rem 0" }}>{money(phone.asking_price)}</div>
            <div className="row" style={{ gap: ".5rem" }}>
              <span className="badge">Trust {phone.trust_score}/100</span>
              <span className="badge badge-warn">{VERDICT[phone.price_verdict]}</span>
            </div>
            {user?.role === "buyer" && (
              <div style={{ marginTop: "1rem" }}>
                <FormError message={cartError} />
                {has(phone.id) ? (
                  <div className="row"><span className="badge">In your cart</span><Link className="btn" to="/cart">Go to cart</Link></div>
                ) : (
                  <button className="btn btn-block" onClick={handleAdd} disabled={adding}>{adding ? "Adding..." : "Add to cart"}</button>
                )}
                <button className="btn btn-block" style={{ marginTop: ".5rem" }} onClick={buyNow} disabled={buying}>{buying ? "Redirecting to eSewa..." : "Buy Now · Pay with eSewa"}</button>
              </div>
            )}
            {user?.role === "buyer" && <div style={{ marginTop: ".75rem" }}><button className="btn btn-outline btn-block" onClick={() => setReportOpen(!reportOpen)}>Report suspected scam</button>{reportDone && <p className="plus small">Report submitted to the moderation team.</p>}{reportOpen && <form className="stack" onSubmit={reportScam} style={{ marginTop: ".75rem" }}><label htmlFor="scam-report">Why do you think this listing is a scam?</label><textarea id="scam-report" className="textarea" minLength="10" maxLength="2000" required value={reportText} onChange={(e) => setReportText(e.target.value)} placeholder="Explain what seems suspicious (at least 10 characters)."/><button className="btn btn-danger" type="submit">Submit scam report</button></form>}
              {phone.scam_report_qr && <div className="qr" style={{ marginTop: "1rem" }}><img src={phone.scam_report_qr} alt="QR code to report this listing" width="130" height="130"/><div className="small muted">Scan to report this listing</div><Link to={`/report-listing/${phone.id}`} className="small">Open report form</Link></div>}
            </div>}
            {!user && <p className="muted small" style={{ marginBottom: 0 }}>Sign in as a buyer to buy or report this listing.</p>}
          </div>
          <div className="card">
            <h2 className="h6">Condition details</h2>
            <div className="between"><span>Year bought</span><b>{phone.purchase_year}</b></div>
            <div className="between"><span>Warranty left</span><b>{phone.warranty_months} months</b></div>
            <div className="between"><span>Repairs done</span><b>{yesNo(phone.repairs_done)}</b></div>
            <div className="between"><span>Box</span><b>{yesNo(phone.has_box)}</b></div>
            <div className="between"><span>Charger</span><b>{yesNo(phone.has_charger)}</b></div>
            <div className="between"><span>Original bill</span><b>{yesNo(phone.has_bill)}</b></div>
          </div>
        </div>

        <div className="stack">
          <div className="card">
            <h2 className="h6">Is the price fair?</h2>
            <div className="between"><span>Fair range (formula)</span><b>{money(phone.fair_low)} - {money(phone.fair_high).replace("Rs. ", "")}</b></div>
            {phone.market ? (
              <div className="note" style={{ marginTop: ".75rem" }}>
                Market check: the {phone.market.count} most similar listed phones average <b>{money(phone.market.price)}</b>.
                <div className="small">Found with K-Nearest Neighbors.</div>
              </div>
            ) : (
              <p className="muted small" style={{ marginBottom: 0 }}>Not enough similar listings for a market check yet.</p>
            )}
          </div>

          <div className="card">
            <div className="between"><h2 className="h6" style={{ margin: 0 }}>Trust score</h2><b>{phone.trust_score} / 100</b></div>
            <div className="meter"><div style={{ width: `${phone.trust_score}%` }} /></div>
            {phone.trust_details.map((t) => (
              <div className="between" key={t.label} style={{ marginTop: ".5rem" }}>
                <span className={t.earned ? "" : "muted"}>{t.label}</span>
                <span className={t.earned ? "plus" : "muted"}>{t.earned ? `+${t.points}` : "0"}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {phone.similar.length > 0 && (
        <section style={{ marginTop: "2.5rem" }}>
          <h2 className="h5">Similar phones you may like</h2>
          <div className="listings">
            {phone.similar.map((p) => <ListingCard key={p.id} phone={p} />)}
          </div>
        </section>
      )}
    </>
  );
}
