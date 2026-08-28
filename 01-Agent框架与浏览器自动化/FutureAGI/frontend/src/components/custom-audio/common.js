/**
 * Retrieves a cached value from a WaveSurfer instance or returns a fallback
 * @param {string} cacheKey - The key to identify the cached instance
 * @param {Function} getWaveSurferInstance - Function to retrieve the WaveSurfer instance
 * @param {string} key - The property key to retrieve from the cache
 * @param {*} fallback - The fallback value if cache is not available
 * @returns {*} The cached value or fallback
 */
export const getCachedValue = (
  cacheKey,
  getWaveSurferInstance,
  key,
  fallback,
) => {
  if (cacheKey && getWaveSurferInstance) {
    const cacheData = getWaveSurferInstance(cacheKey);
    return cacheData?.[key] != null ? cacheData[key] : fallback;
  }
  return fallback;
};
