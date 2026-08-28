import { useContext } from "react";

import { AuthContext } from "../context/jwt/auth-context";

// ----------------------------------------------------------------------

export const useAuthContext = () => {
  const context = useContext(AuthContext);

  if (!context)
    throw new Error("useAuthContext context must be use inside AuthProvider");

  return context;
};

// Safe version that returns defaults instead of throwing during initialization this is happening when there is slow network
// 1. Page loads
// 2. AuthProvider initializes (still loading user data)
// 3. WebSocketProvider uses useSafeAuthContext()
// 4. Gets default values { user: null, isAuthenticated: false } ✅
// 5. WebSocket waits for auth to complete
// 6. Once user loads, WebSocket connects properly ✅
export const useSafeAuthContext = () => {
  const context = useContext(AuthContext);
  return !context?.authenticated
    ? { user: null, authenticated: false }
    : context;
};
