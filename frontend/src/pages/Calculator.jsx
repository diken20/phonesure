import { useEffect, useState } from "react";
import { api, generalError, money } from "../api";
import { Check, Field, FormError } from "../components/Field.jsx";

const AGES = [
  ["0.5", "Under 1 year"],
  ["1.5", "1 to 2 years"],
  ["2.5", "2 to 3 years"],
  ["4", "3 years or more"],
];
const CONDITIONS = [["excellent", "Excellent"], ["good", "Good"], ["fair", "Fair"], ["poor", "Poor"]];

const VERDICTS = {
  within: "The asking price is within the fair range.",
  above: "The asking price is above the fair range. There is room to negotiate.",
  below: "The asking price is below the fair range. Check the phone's condition carefully.",
};

export default function Calculator() {
  const [refs, setRefs] = useState([]);
  const [form, setForm] = useState({
    reference: "", age_years: "1.5", condition: "good", battery_health: "86",
    asking_price: "", has_box: false, has_charger: false, has_bill: false,
  });
  const [result, setResult] = useState(null);
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);

  useEffect(() => { api("/references/").then(setRefs).catch(() => setErrors({ general: "Cannot load phone models." })); }, []);

  const set = (name) => (e) => setForm({ ...form, [name]: e.target.value });
  const toggle = (name) => (value) => setForm({ ...form, [name]: value });

  async function handleSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    try {
      const body = {
        ...form,
        reference: Number(form.reference),
        age_years: Number(form.age_years),
        battery_health: Number(form.battery_health),
        asking_price: form.asking_price ? Number(form.asking_price) : null,
      };
      setResult(await api("/valuation/", { method: "POST", body }));
    } catch (err) {
      setResult(null);
      setErrors({ ...err.data, general: generalError(err) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="cols">
      <div className="card">
        <h1 className="h3">What is this phone worth?</h1>
        <form onSubmit={handleSubmit}>
          <FormError message={errors.general} />
          <Field label="Phone model" htmlFor="reference" error={errors.reference}>
            <select id="reference" value={form.reference} onChange={set("reference")} required>
              <option value="">Select a phone</option>
              {refs.map((r) => <option key={r.id} value={r.id}>{r.label}</option>)}
            </select>
          </Field>
          <div className="grid-2">
            <Field label="Age" htmlFor="age" error={errors.age_years}>
              <select id="age" value={form.age_years} onChange={set("age_years")}>
                {AGES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </Field>
            <Field label="Condition" htmlFor="condition" error={errors.condition}>
              <select id="condition" value={form.condition} onChange={set("condition")}>
                {CONDITIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </Field>
            <Field label="Battery health (%)" htmlFor="battery" error={errors.battery_health}>
              <input id="battery" type="number" min="1" max="100" value={form.battery_health} onChange={set("battery_health")} required />
            </Field>
            <Field label="Asking price (Rs.)" htmlFor="asking" error={errors.asking_price}
              help="Optional. Buyers: enter the seller's price to check if it is fair.">
              <input id="asking" type="number" min="1" value={form.asking_price} onChange={set("asking_price")} />
            </Field>
          </div>
          <div className="checks">
            <Check id="box" label="Box" checked={form.has_box} onChange={toggle("has_box")} />
            <Check id="charger" label="Charger" checked={form.has_charger} onChange={toggle("has_charger")} />
            <Check id="bill" label="Original bill" checked={form.has_bill} onChange={toggle("has_bill")} />
          </div>
          <button className="btn btn-block" disabled={busy}>{busy ? "Calculating..." : "Calculate fair price"}</button>
        </form>
      </div>

      <div className="stack">
        {result ? (
          <>
            <div className="result">
              <div>Fair price range</div>
              <div className="range">{money(result.low)} - {money(result.high).replace("Rs. ", "")}</div>
              <div>Estimated value: {money(result.estimate)}</div>
            </div>
            <div className="card">
              <h2 className="h6">How we got here</h2>
              <div className="between"><span>Base price</span><span>{money(result.base_price)}</span></div>
              {result.steps.map((s) => (
                <div className="between" key={s.label} style={{ marginTop: ".5rem" }}>
                  <span>{s.label}</span>
                  {s.amount < 0 ? <span className="minus">- {money(-s.amount)}</span>
                    : s.amount > 0 ? <span className="plus">+ {money(s.amount)}</span>
                    : <span className="muted">Rs. 0</span>}
                </div>
              ))}
            </div>
            {result.verdict && <div className="note">{VERDICTS[result.verdict]}</div>}
            {result.market ? (
              <div className="note">
                Market check: the {result.market.count} most similar listed phones average <b>{money(result.market.price)}</b>.
                <div className="small">Found with K-Nearest Neighbors on real listings.</div>
              </div>
            ) : (
              <div className="card muted small">No market check yet: there are not enough similar listings.</div>
            )}
          </>
        ) : (
          <div className="card muted">Fill in the details and press <b>Calculate</b> to see the fair price range and how each factor changes it.</div>
        )}
      </div>
    </div>
  );
}
