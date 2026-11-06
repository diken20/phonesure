import { useEffect, useState } from "react";
import { api, generalError } from "../api";
import ListingCard from "../components/ListingCard.jsx";
import { FormError } from "../components/Field.jsx";

const PRICE_OPTIONS = [
  ["", "Any price"],
  ["30000", "Under Rs. 30,000"],
  ["50000", "Under Rs. 50,000"],
  ["70000", "Under Rs. 70,000"],
  ["100000", "Under Rs. 1,00,000"],
];

export default function Marketplace() {
  const [brands, setBrands] = useState([]);
  const [filters, setFilters] = useState({ q: "", brand: "", max_price: "" });
  const [phones, setPhones] = useState(null);
  const [error, setError] = useState(null);

  async function load(f) {
    const params = new URLSearchParams();
    Object.entries(f).forEach(([k, v]) => v && params.set(k, v));
    setError(null);
    try {
      setPhones(await api(`/marketplace/?${params}`));
    } catch (err) {
      setError(generalError(err) || "Could not load phones.");
    }
  }

  useEffect(() => {
    load(filters);
    api("/references/").then((refs) => setBrands([...new Set(refs.map((r) => r.brand))]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const set = (name) => (e) => setFilters({ ...filters, [name]: e.target.value });

  function handleSubmit(e) {
    e.preventDefault();
    load(filters);
  }

  return (
    <>
      <form className="search" onSubmit={handleSubmit}>
        <input className="input grow" placeholder="Search phones, e.g. iphone 13" aria-label="Search phones"
          value={filters.q} onChange={set("q")} />
        <select className="input" aria-label="Brand" value={filters.brand} onChange={set("brand")}>
          <option value="">All brands</option>
          {brands.map((b) => <option key={b} value={b}>{b}</option>)}
        </select>
        <select className="input" aria-label="Maximum price" value={filters.max_price} onChange={set("max_price")}>
          {PRICE_OPTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <button className="btn">Search</button>
      </form>

      <FormError message={error} />
      {phones && (
        <p className="muted">{phones.length} {phones.length === 1 ? "phone" : "phones"} found</p>
      )}
      {phones === null && !error && <p className="muted">Loading...</p>}
      {phones && phones.length === 0 && (
        <div className="card muted">No phones match your search. Try a different keyword or clear the filters.</div>
      )}
      <div className="listings">
        {phones && phones.map((p) => <ListingCard key={p.id} phone={p} />)}
      </div>
    </>
  );
}
