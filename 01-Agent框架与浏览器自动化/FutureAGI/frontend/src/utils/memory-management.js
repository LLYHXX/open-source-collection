// Memory management utilities to prevent leaks

import logger from "./logger";

class BlobUrlManager {
  constructor() {
    this.activeBlobUrls = new Set();
  }

  createBlobUrl(blob) {
    const url = URL.createObjectURL(blob);
    this.activeBlobUrls.add(url);
    return url;
  }

  revokeBlobUrl(url) {
    if (this.activeBlobUrls.has(url)) {
      URL.revokeObjectURL(url);
      this.activeBlobUrls.delete(url);
    }
  }

  revokeAllBlobUrls() {
    this.activeBlobUrls.forEach((url) => {
      URL.revokeObjectURL(url);
    });
    this.activeBlobUrls.clear();
  }

  cleanup() {
    this.revokeAllBlobUrls();
  }
}

// Singleton instance
export const blobUrlManager = new BlobUrlManager();

// Audio context manager to prevent multiple instances
class AudioContextManager {
  constructor() {
    this.context = null;
  }

  getContext() {
    if (!this.context || this.context.state === "closed") {
      this.context = new AudioContext();
    }
    return this.context;
  }

  async resumeContext() {
    const context = this.getContext();
    if (context.state === "suspended") {
      await context.resume();
    }
    return context;
  }

  closeContext() {
    if (this.context && this.context.state !== "closed") {
      this.context.close();
      this.context = null;
    }
  }
}

export const audioContextManager = new AudioContextManager();

// Generic cleanup utility
export const createCleanupHandler = () => {
  const cleanupFunctions = [];

  const addCleanup = (fn) => {
    if (typeof fn === "function") {
      cleanupFunctions.push(fn);
    }
  };

  const cleanup = () => {
    cleanupFunctions.forEach((fn) => {
      try {
        fn();
      } catch (error) {
        logger.warn("Cleanup function failed:", error);
      }
    });
    cleanupFunctions.length = 0;
  };

  return { addCleanup, cleanup };
};

// Hook for component cleanup
export const useComponentCleanup = () => {
  const { addCleanup, cleanup } = createCleanupHandler();

  // Return cleanup function to be used in useEffect
  return { addCleanup, cleanup };
};

// Global cleanup for page unload
let globalCleanupRegistered = false;

export const registerGlobalCleanup = () => {
  if (!globalCleanupRegistered) {
    const handleBeforeUnload = () => {
      blobUrlManager.cleanup();
      audioContextManager.closeContext();
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    globalCleanupRegistered = true;

    // Return cleanup function
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      globalCleanupRegistered = false;
    };
  }
};
