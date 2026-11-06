// One place that talks to the Django API.
const TOKEN_KEY = "phonesure_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (token) =>
  token ? localStorage.setItem(TOKEN_KEY, token) : localStorage.removeItem(TOKEN_KEY);

export class ApiError extends Error {
  constructor(status, data) {
    super("API error");
    this.status = status;
    this.data = data || {};
  }
}

// body = JSON object, form = FormData (used for photo uploads)
export async function api(path, { method = "GET", body, form } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Token ${token}`;

  let payload;
  if (form) {
    payload = form; // the browser sets the multipart boundary itself
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const res = await fetch(`/api${path}`, { method, headers, body: payload });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, data);
  return data;
}

// First general (non-field) message from a DRF error, if any.
export function generalError(err) {
  const d = err?.data || {};
  if (d.detail) return d.detail;
  if (d.non_field_errors?.length) return d.non_field_errors[0];
  return err?.status ? null : "Cannot reach the server. Is Django running?";
}

// Nepali-style digit grouping, e.g. Rs. 1,05,000
export const money = (n) => "Rs. " + Number(n).toLocaleString("en-IN");
export const number = (n) => Number(n).toLocaleString("en-IN");
