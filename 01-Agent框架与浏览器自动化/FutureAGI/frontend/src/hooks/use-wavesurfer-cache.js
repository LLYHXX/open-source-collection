import { useCallback, useRef } from "react";

const useWavesurferCache = () => {
  const waveSurferCacheRef = useRef(new Map()); // Ref to store the cache

  // --- Cache Interaction Functions ---
  const getWaveSurferInstance = useCallback((key) => {
    return waveSurferCacheRef.current.get(key);
  }, []);

  const storeWaveSurferInstance = useCallback((key, instanceData) => {
    // console.log("storeWaveSurferInstance", key, instanceData);
    // Maybe clean up old instance if overwriting the same key?
    const existing = waveSurferCacheRef.current.get(key);
    if (existing && existing.instance !== instanceData.instance) {
      // console.log(`Destroying old instance for key: ${key}`);
      existing.instance.destroy();
    }
    waveSurferCacheRef.current.set(key, instanceData);
  }, []);

  const removeWaveSurferInstance = useCallback((key) => {
    const existing = waveSurferCacheRef.current.get(key);
    if (existing) {
      // console.log(`Destroying instance for key: ${key}`);
      existing.instance.destroy(); // Destroy before removing
      waveSurferCacheRef.current.delete(key);
      return true;
    }
    return false;
  }, []);

  /**
   * Updates the data associated with a key in the cache by merging new properties.
   * @param {string} key - The key of the instance to update.
   * @param {object} updates - An object containing properties to merge into the existing data.
   * @returns {boolean} - True if the update was successful, false otherwise.
   */
  const updateWaveSurferInstance = useCallback((key, updates) => {
    const existingInstanceData = waveSurferCacheRef.current.get(key);
    if (existingInstanceData) {
      // Merge the updates into the existing data
      const updatedData = { ...existingInstanceData, ...updates };
      waveSurferCacheRef.current.set(key, updatedData);
      // console.log(`Updated instance data for key: ${key}`, updatedData);
      return true;
    } else {
      // console.warn(`Attempted to update non-existent instance for key: ${key}`);
      return false;
    }
  }, []);

  const clearWaveSurferCache = useCallback(() => {
    // console.log("Clearing WaveSurfer cache and destroying instances...");
    waveSurferCacheRef.current.forEach((instanceData) => {
      try {
        instanceData.instance.destroy();
      } catch (e) {
        // console.error(`Error destroying wavesurfer for key ${key}:`, e);
      }
    });
    waveSurferCacheRef.current.clear();
  }, []);

  return {
    getWaveSurferInstance,
    storeWaveSurferInstance,
    removeWaveSurferInstance,
    updateWaveSurferInstance,
    clearWaveSurferCache,
  };
};

export default useWavesurferCache;
