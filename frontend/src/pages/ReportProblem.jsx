import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, generalError, money } from "../api";
import { Field, FormError } from "../components/Field.jsx";

const CATEGORIES = [
  ["not_as_described", "Not as described"],
  ["battery", "Battery problem"],
  ["screen_or_body", "Screen or body damage"],
  ["not_working", "Not working properly"],
  ["missing_items", "Missing box, charger or bill"],
  ["other", "Other"],
];

// This is the page the QR code on the receipt opens.
export default function ReportProblem({ listingReport = false }) {
  const { publicId, listingId } = useParams();
  const [item, setItem] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [form, setForm] = useState({ category: listingReport ? "scam" : "not_as_described", description: "" });
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (listingReport) {
      api(`/marketplace/${listingId}/`).then((phone) => setItem({
        public_id: String(phone.id), title: `${phone.brand} ${phone.title}`, price: phone.asking_price,
        listing_id: phone.id, order_id: "Marketplace listing"
      })).catch(() => setNotFound(true));
    } else {
      api(`/problems/lookup/${publicId}/`).then(setItem).catch(() => setNotFound(true));
    }
  }, [publicId, listingId, listingReport]);

  async function handleSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    try {
      const payload = listingReport
        ? { phone: Number(listingId), category: "scam", description: form.description }
        : { item: publicId, ...form };
      await api("/problems/", { method: "POST", body: payload });
      setDone(true);
    } catch (err) {
      setErrors({ ...err.data, general: generalError(err) });
    } finally {
      setBusy(false);
    }
  }

  if (notFound) {
    return (
      <div className="card center">
        <h1 className="h3">{listingReport ? "Listing not found" : "Purchase not found"}</h1>
        <p className="muted">{listingReport ? "This marketplace listing is no longer available." : "This QR code does not belong to a paid order on your account. Sign in with the account that bought the phone."}</p>
        <Link className="btn" to={listingReport ? "/marketplace" : "/orders"}>{listingReport ? "Marketplace" : "My orders"}</Link>
      </div>
    );
  }
  if (!item) return <p className="muted">Loading...</p>;

  if (done) {
    return (
      <div className="card center">
        <h1 className="h3">Report sent</h1>
        <p className="muted">Thank you. The moderation team can now review your {listingReport ? "scam report" : "problem report"} about <b>{item.title}</b>.</p>
        <Link className="btn" to="/problems">View my reports</Link>
      </div>
    );
  }

  return (
    <div className="card center">
      <h1 className="h3">{listingReport ? "Report suspected scam" : "Report a problem"}</h1>
      <p><b>{item.title}</b> <span className="muted">&middot; {money(item.price)} {listingReport ? "· Marketplace listing" : `· Order #${item.order_id}`}</span></p>
      <form onSubmit={handleSubmit}>
        <FormError message={errors.general || errors.item?.[0]} />
        {!listingReport && <Field label="What is wrong?" htmlFor="category" error={errors.category}>
          <select id="category" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            {CATEGORIES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </Field>}
        <Field label="Describe the problem" htmlFor="description" error={errors.description} help="At least 10 characters.">
          <textarea id="description" className="textarea" rows="5" value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })} required />
        </Field>
        <button className="btn btn-block" disabled={busy}>{busy ? "Sending..." : listingReport ? "Submit scam report" : "Send report"}</button>
      </form>
    </div>
  );
}
