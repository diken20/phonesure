import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, generalError } from "../api";
import { Check, Field, FormError } from "../components/Field.jsx";

const CONDITIONS = [["excellent", "Excellent"], ["good", "Good"], ["fair", "Fair"], ["poor", "Poor"]];
const EMPTY = {
  reference: "", brand: "", model_name: "", storage_gb: "", base_price: "", purchase_year: String(new Date().getFullYear()), condition: "good",
  battery_health: "", warranty_months: "0", asking_price: "", status: "draft",
  repairs_done: false, has_box: false, has_charger: false, has_bill: false,
};

export default function PhoneForm() {
  const { id } = useParams(); // present when editing
  const navigate = useNavigate();

  const [form, setForm] = useState(EMPTY);
  const [photo, setPhoto] = useState(null);
  const [currentPhoto, setCurrentPhoto] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);
  const [reviewNote, setReviewNote] = useState("");
  const [live, setLive] = useState(false);

  useEffect(() => {
    if (id) {
      api(`/phones/${id}/`)
        .then((p) => {
          setForm({ ...EMPTY, ...Object.fromEntries(Object.keys(EMPTY).map((k) => [k, typeof EMPTY[k] === "boolean" ? p[k] : String(p[k])])), status: p.status === "draft" ? "draft" : "pending" });
          setForm((prev) => ({ ...prev, brand: p.reference_label?.split(" ")[0] || "", model_name: p.reference_label?.split(" ").slice(1, -1).join(" ") || "", storage_gb: p.reference_label?.match(/(\d+)GB/)?.[1] || "", base_price: "" }));
          setCurrentPhoto(p.photo);
          setReviewNote(p.review_note);
          setLive(p.status === "listed");
        })
        .catch(() => navigate("/phones"));
    }
  }, [id, navigate]);

  const set = (name) => (e) => setForm({ ...form, [name]: e.target.value });
  function choosePhoto(file) { setPhoto(file); setPhotoPreview(file ? URL.createObjectURL(file) : null); }
  const toggle = (name) => (value) => setForm({ ...form, [name]: value });

  async function handleSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    // FormData (not JSON) because a photo file may be attached.
    const data = new FormData();
    Object.entries(form).forEach(([k, v]) => { if (v !== "" || !["reference", "base_price"].includes(k)) data.append(k, String(v)); });
    if (photo) data.append("photo", photo);
    try {
      await api(id ? `/phones/${id}/` : "/phones/", { method: id ? "PATCH" : "POST", form: data });
      navigate("/phones", { state: { flash: form.status === "pending" ? "Submitted for review. Buyers can see it once an admin approves it." : "Draft saved." } });
    } catch (err) {
      setErrors({ ...err.data, general: generalError(err) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h1 className="h3">{id ? "Edit phone" : "Add a phone"}</h1>
      <form onSubmit={handleSubmit} className="stack">
        <FormError message={errors.general} />
        {reviewNote && <div className="alert alert-danger">An admin rejected this phone: {reviewNote} Fix it and submit again.</div>}
        {live && <div className="note">This phone is live. Saving changes sends it back for approval, so it disappears from the marketplace until an admin approves it again.</div>}

        <div className="card">
          <h2 className="h6">1. Phone details</h2>
          <div className="grid-2">
            <Field label="Brand" htmlFor="brand" error={errors.brand}><input id="brand" value={form.brand} onChange={set("brand")} placeholder="e.g. Apple, Samsung" required /></Field>
            <Field label="Model name" htmlFor="model_name" error={errors.model_name}><input id="model_name" value={form.model_name} onChange={set("model_name")} placeholder="e.g. iPhone 13 Pro" required /></Field>
            <Field label="Storage (GB)" htmlFor="storage_gb" error={errors.storage_gb}><input id="storage_gb" type="number" min="1" value={form.storage_gb} onChange={set("storage_gb")} placeholder="128" required /></Field>
            <Field label="Estimated new price (Rs.)" htmlFor="base_price" error={errors.base_price}><input id="base_price" type="number" min="1" value={form.base_price} onChange={set("base_price")} placeholder="Price when new" required={!id} /></Field>
            <Field label="Year bought" htmlFor="year" error={errors.purchase_year}>
              <input id="year" type="number" value={form.purchase_year} onChange={set("purchase_year")} required />
            </Field>
          </div>
        </div>

        <div className="card">
          <h2 className="h6">2. Condition</h2>
          <div className="grid-3">
            <Field label="Overall condition" htmlFor="condition" error={errors.condition}>
              <select id="condition" value={form.condition} onChange={set("condition")}>
                {CONDITIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </Field>
            <Field label="Battery health (%)" htmlFor="battery" error={errors.battery_health}>
              <input id="battery" type="number" min="1" max="100" value={form.battery_health} onChange={set("battery_health")} required />
            </Field>
            <Field label="Warranty left (months)" htmlFor="warranty" error={errors.warranty_months}>
              <input id="warranty" type="number" min="0" value={form.warranty_months} onChange={set("warranty_months")} />
            </Field>
          </div>
          <div className="checks">
            <Check id="repairs" label="Repairs done" checked={form.repairs_done} onChange={toggle("repairs_done")} />
            <Check id="box" label="Box" checked={form.has_box} onChange={toggle("has_box")} />
            <Check id="charger" label="Charger" checked={form.has_charger} onChange={toggle("has_charger")} />
            <Check id="bill" label="Original bill" checked={form.has_bill} onChange={toggle("has_bill")} />
          </div>
        </div>

        <div className="card">
          <h2 className="h6">3. Photo and price</h2>
          <div className="grid-3">
            <Field label="Asking price (Rs.)" htmlFor="asking" error={errors.asking_price}>
              <input id="asking" type="number" min="1" value={form.asking_price} onChange={set("asking_price")} required />
            </Field>
            <Field label="What next?" htmlFor="status" error={errors.status}
              help="An admin checks every phone before buyers can see it.">
              <select id="status" value={form.status} onChange={set("status")}>
                <option value="draft">Save as draft (only you can see it)</option>
                <option value="pending">Submit for review</option>
              </select>
            </Field>
            <Field label="Photo" htmlFor="photo" error={errors.photo}>
              <input id="photo" type="file" accept="image/*" onChange={(e) => choosePhoto(e.target.files[0] || null)} />
            </Field>
          </div>
          {(photoPreview || currentPhoto) && <div style={{ marginTop: ".75rem" }}><p className="muted small">Photo preview</p><img className="thumb" style={{ width: 220, height: 220, objectFit: "contain" }} src={photoPreview || currentPhoto} alt="Phone preview" /></div>}
        </div>

        <div className="row">
          <button className="btn" disabled={busy}>{busy ? "Saving..." : "Save phone"}</button>
          <Link className="btn btn-outline" to="/phones">Cancel</Link>
        </div>
      </form>
    </>
  );
}
