/**
 * Keep-Alive Utility
 * Pings the backend health endpoint periodically to prevent Render from spinning down
 * This keeps the backend warm and reduces cold start times
 */

const KEEP_ALIVE_INTERVAL = 10 * 60 * 1000; // 10 minutes in milliseconds
const HEALTH_ENDPOINT = '/health';

/**
 * Ping the backend health endpoint
 * @param {string} baseUrl - Base API URL (from VITE_API_URL env var)
 * @returns {Promise<boolean>} - Returns true if ping successful
 */
export const pingHealth = async (baseUrl) => {
  try {
    const healthUrl = baseUrl 
      ? `${baseUrl}${HEALTH_ENDPOINT}` 
      : `${import.meta.env.VITE_API_URL}${HEALTH_ENDPOINT}`;
    
    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
    
    const response = await fetch(healthUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      console.log('✅ Backend keep-alive ping successful:', data.status);
      return true;
    } else {
      console.warn('⚠️ Backend health check returned non-OK status:', response.status);
      return false;
    }
  } catch (error) {
    // Silently fail - don't spam console on network errors
    if (error.name !== 'AbortError') {
      console.warn('⚠️ Keep-alive ping failed (backend may be spinning up):', error.message);
    }
    return false;
  }
};

/**
 * Start the keep-alive service
 * @param {string} baseUrl - Optional base URL override
 * @returns {Function} - Cleanup function to stop the keep-alive
 */
export const startKeepAlive = (baseUrl = null) => {
  // Ping immediately on start
  pingHealth(baseUrl);

  // Set up interval for periodic pings
  const intervalId = setInterval(() => {
    pingHealth(baseUrl);
  }, KEEP_ALIVE_INTERVAL);

  // Return cleanup function
  return () => {
    clearInterval(intervalId);
    console.log('🛑 Keep-alive service stopped');
  };
};

/**
 * React hook for keep-alive (optional - can use startKeepAlive directly)
 * Usage in component: useKeepAlive();
 */
export const useKeepAlive = () => {
  // This is just a convenience wrapper - components can use startKeepAlive directly
  // with useEffect if they prefer
};

