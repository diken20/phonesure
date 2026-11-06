import { createContext, useContext, useEffect, useState } from "react";
import { api, getToken, setToken } from "./api";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(getToken()));

  // Restore the session after a page refresh.
  useEffect(() => {
    if (!getToken()) return;
    api("/auth/me/")
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  async function authenticate(path, body) {
    const data = await api(path, { method: "POST", body });
    setToken(data.token);
    setUser(data.user);
    return data.user;
  }

  const value = {
    user,
    loading,
    isSeller: user && (user.role === "seller" || user.role === "admin"),
    login: (username, password) => authenticate("/auth/login/", { username, password }),
    register: (form) => authenticate("/auth/register/", form),
    async logout() {
      try { await api("/auth/logout/", { method: "POST" }); } catch { /* token already invalid */ }
      setToken(null);
      setUser(null);
    },
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
