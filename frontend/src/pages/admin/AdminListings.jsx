import { useCallback, useEffect, useState } from "react";
import { api, generalError, money, number } from "../../api";
import AdminTabs from "../../components/AdminTabs.jsx";
import { Field, FormError } from "../../components/Field.jsx";

const FILTERS = [["pending", "Waiting for review"], ["listed", "Listed"], ["rejected", "Rejected"], ["draft", "Drafts"], ["sold", "Sold"], ["all", "All"]];
const VERDICT = { within: ["Price is fair", ""], above: ["Above fair range", "badge-warn"], below: ["Below fair range", "badge-warn"] };
const yes = (v) => (v ? "Yes" : "No");

function PhoneReviewCard({ phone, onApprove, onReject }) {
  const [verdictLabel, verdictClass] = VERDICT[phone.price_verdict];
  return (
    <div className="card review">
      <div className="review-photo">{phone.photo ? <img src={phone.photo} alt="" /> : "No photo"}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="between">
          <div><b>{phone.reference_label}</b> <span className="muted small">&middot; seller {phone.seller}</span></div>
          <span className={`badge ${phone.status === "listed" || phone.status === "sold" ? "" : phone.status === "rejected" ? "badge-danger" : "badge-warn"}`}>{phone.status_label}</span>
        </div>
        <div className="row" style={{ margin: ".5rem 0" }}>
          <b>{money(phone.asking_price)}</b>
          <span className="muted small">fair range {number(phone.fair_low)} - {number(phone.fair_high)}</span>
          <span className={`badge ${verdictClass}`}>{verdictLabel}</span>
          <span className="badge">Trust {phone.trust_score}/100</span>
        </div>
        <div className="muted small">
          Bought {phone.purchase_year} &middot; {phone.condition} &middot; battery {phone.battery_health}% &middot; warranty {phone.warranty_months} mo &middot;
          repairs {yes(phone.repairs_done)} &middot; box {yes(phone.has_box)} &middot; charger {yes(phone.has_charger)} &middot; bill {yes(phone.has_bill)}
        </div>
        {phone.review_note && <div className="note small" style={{ marginTop: ".5rem" }}>Reason given: {phone.review_note}</div>}
        {(phone.status === "pending" || phone.status === "listed") && (
          <div className="row" style={{ marginTop: ".75rem" }}>
            {phone.status === "pending" && <button className="btn btn-small" onClick={() => onApprove(phone)}>Approve</button>}
            <button className="btn btn-outline btn-small" onClick={() => onReject(phone)}>{phone.status === "pending" ? "Reject" : "Take down"}</button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AdminListings() {
  const [filter, setFilter] = useState("pending");
  const [phones, setPhones] = useState(null);
  const [error, setError] = useState(null);
  const [flash, setFlash] = useState(null);
  const [rejecting, setRejecting] = useState(null);
  const [note, setNote] = useState("");
  const [noteError, setNoteError] = useState(null);

  const load = useCallback(() => {
    setPhones(null);
    api(`/admin/phones/?status=${filter}`).then(setPhones).catch((e) => setError(generalError(e) || "Could not load phones."));
  }, [filter]);
  useEffect(load, [load]);

  async function approve(phone) {
    setError(null);
    try {
      await api(`/admin/phones/${phone.id}/approve/`, { method: "POST" });
      setFlash(`${phone.reference_label} is now visible to buyers.`);
      load();
    } catch (e) { setError(e.data?.detail || generalError(e) || "Could not approve."); }
  }

  async function reject() {
    setNoteError(null);
    try {
      await api(`/admin/phones/${rejecting.id}/reject/`, { method: "POST", body: { note } });
      setFlash(`${rejecting.reference_label} was removed from buyers' view. The seller can see your reason.`);
      setRejecting(null);
      setNote("");
      load();
    } catch (e) { setNoteError(e.data?.note?.[0] || e.data?.detail || generalError(e) || "Could not reject."); }
  }

  return (
    <>
      <h1 className="h3">Admin portal</h1>
      <AdminTabs />
      <div className="row" style={{ marginBottom: "1rem" }}>
        <label htmlFor="filter" className="muted small">Show</label>
        <select id="filter" className="input" value={filter} onChange={(e) => { setFlash(null); setFilter(e.target.value); }}>
          {FILTERS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </div>
      <FormError message={error} />
      {flash && <div className="alert alert-success">{flash}</div>}
      <div className="stack">
        {phones === null ? <p className="muted">Loading...</p>
          : phones.length === 0 ? <div className="card muted">Nothing here. {filter === "pending" && "Every submitted phone has been reviewed."}</div>
          : phones.map((p) => <PhoneReviewCard key={p.id} phone={p} onApprove={approve} onReject={(ph) => { setRejecting(ph); setNote(""); setNoteError(null); }} />)}
      </div>

      {rejecting && (
        <div className="overlay" onClick={() => setRejecting(null)}>
          <div className="modal" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
            <h2 className="h5">{rejecting.status === "pending" ? "Reject" : "Take down"} {rejecting.reference_label}</h2>
            <Field label="Reason (the seller will read this)" htmlFor="note" error={noteError}>
              <textarea id="note" className="textarea" rows="4" value={note} onChange={(e) => setNote(e.target.value)} />
            </Field>
            <div className="row">
              <button className="btn btn-danger" onClick={reject}>{rejecting.status === "pending" ? "Reject phone" : "Take down"}</button>
              <button className="btn btn-outline" onClick={() => setRejecting(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
