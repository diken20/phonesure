import { Link } from "react-router-dom";
import { money } from "../api";

export const VERDICT = {
  within: "Fair price",
  above: "Above fair range",
  below: "Good deal",
};

export default function ListingCard({ phone }) {
  const condition = phone.condition[0].toUpperCase() + phone.condition.slice(1);
  return (
    <Link to={`/marketplace/${phone.id}`} className="listing-link">
      <article className="listing">
        <div className="listing-photo">
          {phone.photo ? <img src={phone.photo} alt={`${phone.brand} ${phone.title}`} /> : "Phone photo"}
        </div>
        <div className="listing-body">
          <h2 className="h6">{phone.title}</h2>
          <div className="muted">{condition}, {phone.battery_health}% battery, {phone.age_label.toLowerCase()}</div>
          <div className="price">{money(phone.asking_price)}</div>
          <div className="row" style={{ gap: ".5rem" }}>
            <span className="badge">Trust {phone.trust_score}/100</span>
            <span className="badge badge-warn">{VERDICT[phone.price_verdict]}</span>
          </div>
        </div>
      </article>
    </Link>
  );
}
