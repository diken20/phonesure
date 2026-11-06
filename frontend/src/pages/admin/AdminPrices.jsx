import { useCallback, useEffect, useState } from "react";
import { api, generalError } from "../../api";
import AdminTabs from "../../components/AdminTabs.jsx";
import { Field, FormError } from "../../components/Field.jsx";

const BLANK = { brand: "", model_name: "", storage_gb: "", base_price: "" };

function PriceRow({ item, onSave, onDelete }) {
  const [price, setPrice] = useState(String(item.base_price));
  const changed = Number(price) !== item.base_price;
  return (
    <tr>
      <td><b>{item.label}</b></td>
      <td>{item.phone_count}</td>
      <td><input className="input" type="number" min="1" style={{ width: 140 }} value={price} aria-label={`Base price for ${item.label}`} onChange={(e) => setPrice(e.target.value)} /></td>
      <td><div className="row">
        <button className="btn btn-small" disabled={!changed} onClick={() => onSave(item, Number(price))}>Save</button>
        <button className="btn btn-outline btn-small" onClick={() => onDelete(item)}>Delete</button>
      </div></td>
    </tr>
  );
}

export default function AdminPrices() {
  const [items, setItems] = useState(null);
  const [form, setForm] = useState(BLANK);
  const [errors, setErrors] = useState({});
  const [flash, setFlash] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    api("/admin/references/").then(setItems).catch((e) => setError(generalError(e) || "Could not load prices."));
  }, []);
  useEffect(load, [load]);

  const set = (name) => (e) => setForm({ ...form, [name]: e.target.value });

  async function add(e) {
    e.preventDefault();
    setErrors({}); setFlash(null);
    try {
      await api("/admin/references/", { method: "POST", body: { ...form, storage_gb: Number(form.storage_gb), base_price: Number(form.base_price) } });
      setForm(BLANK); setFlash("Phone model added."); load();
    } catch (err) {
      setErrors({ ...err.data, general: err.data?.non_field_errors?.[0] || generalError(err) });
    }
  }

  async function save(item, base_price) {
    setError(null); setFlash(null);
    try { await api(`/admin/references/${item.id}/`, { method: "PATCH", body: { base_price } }); setFlash(`${item.label} updated. New calculations use the new price.`); load(); }
    catch (e) { setError(e.data?.base_price?.[0] || generalError(e) || "Could not save."); }
  }

  async function remove(item) {
    if (!window.confirm(`Delete ${item.label}?`)) return;
    setError(null); setFlash(null);
    try { await api(`/admin/references/${item.id}/`, { method: "DELETE" }); load(); }
    catch (e) { setError(e.data?.detail || generalError(e) || "Could not delete."); }
  }

  return (
    <>
      <h1 className="h3">Admin portal</h1>
      <AdminTabs />
      <form className="card" onSubmit={add} style={{ marginBottom: "1.5rem" }}>
        <h2 className="h6">Add a phone model</h2>
        <FormError message={errors.general} />
        <div className="grid-4">
          <Field label="Brand" htmlFor="brand" error={errors.brand}><input id="brand" value={form.brand} onChange={set("brand")} required /></Field>
          <Field label="Model" htmlFor="model" error={errors.model_name}><input id="model" value={form.model_name} onChange={set("model_name")} required /></Field>
          <Field label="Storage (GB)" htmlFor="storage" error={errors.storage_gb}><input id="storage" type="number" min="1" value={form.storage_gb} onChange={set("storage_gb")} required /></Field>
          <Field label="Base price (Rs.)" htmlFor="base" error={errors.base_price}><input id="base" type="number" min="1" value={form.base_price} onChange={set("base_price")} required /></Field>
        </div>
        <button className="btn">Add model</button>
      </form>

      <FormError message={error} />
      {flash && <div className="alert alert-success">{flash}</div>}
      <div className="card" style={{ padding: 0 }}>
        {items === null ? <p className="muted" style={{ padding: "2rem" }}>Loading...</p> : (
          <div className="table-wrap"><table>
            <thead><tr><th>Phone model</th><th>Phones using it</th><th>Base price (Rs.)</th><th></th></tr></thead>
            <tbody>{items.map((i) => <PriceRow key={`${i.id}-${i.base_price}`} item={i} onSave={save} onDelete={remove} />)}</tbody>
          </table></div>
        )}
      </div>
      <p className="muted small">The base price is the starting point of the valuation formula. Changing it changes every new price calculation.</p>
    </>
  );
}
