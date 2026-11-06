import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "./api";
import { useAuth } from "./AuthContext.jsx";

const EMPTY = { items: [], count: 0, total: 0 };
const CartContext = createContext(null);
export const useCart = () => useContext(CartContext);

export function CartProvider({ children }) {
  const { user } = useAuth();
  const [cart, setCart] = useState(EMPTY);

  const refresh = useCallback(async () => {
    if (user?.role !== "buyer") return setCart(EMPTY);
    try { setCart(await api("/cart/")); } catch { /* shown on the cart page */ }
  }, [user]);

  useEffect(() => { refresh(); }, [refresh]);

  const value = {
    cart,
    refresh,
    has: (phoneId) => cart.items.some((i) => i.phone.id === phoneId),
    add: async (phoneId) => setCart(await api("/cart/", { method: "POST", body: { phone: phoneId } })),
    remove: async (itemId) => {
      await api(`/cart/items/${itemId}/`, { method: "DELETE" });
      await refresh();
    },
  };
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}
