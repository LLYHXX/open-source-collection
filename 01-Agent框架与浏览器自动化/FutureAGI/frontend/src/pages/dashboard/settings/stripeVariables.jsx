import { loadStripe } from "@stripe/stripe-js";
import logger from "src/utils/logger";

const stripeKey = import.meta.env.VITE_STRIPE_PUBLIC_KEY;

// Handle loadStripe rejection to prevent "Unhandled Promise Rejection: Failed to load Stripe.js"
const stripePromise = stripeKey
  ? loadStripe(stripeKey).catch((err) => {
      logger.warn("[Stripe] Failed to load Stripe.js:", err?.message || err);
      return null;
    })
  : Promise.resolve(null);

export { stripePromise }; // Export the stripePromise variable
