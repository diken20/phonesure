// Same label / hint / error layout for every form field in the app.
export function Field({ label, htmlFor, error, help, children }) {
  return (
    <div className="field">
      <label htmlFor={htmlFor}>{label}</label>
      {children}
      {help && <div className="help">{help}</div>}
      {error && <div className="error">{Array.isArray(error) ? error.join(" ") : error}</div>}
    </div>
  );
}

export function Check({ id, label, checked, onChange }) {
  return (
    <label className="check" htmlFor={id}>
      <input id={id} type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      {label}
    </label>
  );
}

export function FormError({ message }) {
  return message ? <div className="alert alert-danger">{message}</div> : null;
}
