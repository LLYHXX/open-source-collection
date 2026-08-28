/**
 * Production-ready logger utility with Sentry integration
 * Provides type-safe logging methods with IDE autocomplete support
 */
export class Logger {
  constructor();

  /**
   * Debug level logging - only in development
   * @param message - The log message
   * @param data - Additional data to log
   * @param context - Additional context for Sentry
   */
  debug(message: string, data?: any, context?: Record<string, any>): void;

  /**
   * Info level logging
   * @param message - The log message
   * @param data - Additional data to log
   * @param context - Additional context for Sentry
   */
  info(message: string, data?: any, context?: Record<string, any>): void;

  /**
   * Warning level logging
   * @param message - The warning message
   * @param data - Additional data to log
   * @param context - Additional context for Sentry
   */
  warn(message: string, data?: any, context?: Record<string, any>): void;

  /**
   * Error level logging with Sentry integration
   *
   * ⚠️ IMPORTANT: First parameter must be a descriptive string message
   *
   * @param message - A descriptive error message (REQUIRED STRING)
   * @param error - The error object or additional data (optional)
   * @param context - Additional context for Sentry (optional)
   *
   * @example
   * ```typescript
   * // ✅ Correct usage:
   * logger.error("Failed to fetch user data", error);
   * logger.error("Database connection failed", new Error("timeout"));
   *
   * // ❌ Wrong usage (will show type error):
   * logger.error(error); // Type error: Expected string, got Error
   * logger.error({ message: "failed" }); // Type error: Expected string, got object
   * ```
   */
  error(
    message: string,
    error?: Error | unknown,
    context?: Record<string, any>,
  ): void;

  /**
   * Fatal error logging - for critical errors that require immediate attention
   * @param message - The fatal error message
   * @param error - The error object or additional data
   * @param context - Additional context for Sentry
   */
  fatal(
    message: string,
    error?: Error | any,
    context?: Record<string, any>,
  ): void;

  /**
   * Set user context for Sentry
   * @param user - User information
   */
  setUser(user: Record<string, any>): void;

  /**
   * Set additional context for Sentry
   * @param key - Context key
   * @param context - Context data
   */
  setContext(key: string, context: Record<string, any>): void;

  /**
   * Add tags to Sentry context
   * @param tags - Tags to add
   */
  setTags(tags: Record<string, string>): void;

  /**
   * Add a breadcrumb to Sentry
   * @param breadcrumb - Breadcrumb data
   */
  addBreadcrumb(breadcrumb: Record<string, any>): void;

  /**
   * Start performance timing
   * @param label - Timer label
   */
  time(label: string): void;

  /**
   * End performance timing
   * @param label - Timer label
   */
  timeEnd(label: string): void;

  /**
   * Performance monitoring with Sentry
   * @param name - Transaction name
   * @param callback - Function to monitor
   * @param context - Additional context
   */
  withPerformance<T>(
    name: string,
    callback: () => T | Promise<T>,
    context?: Record<string, any>,
  ): Promise<T>;
}

export const logger: Logger;
export default logger;
