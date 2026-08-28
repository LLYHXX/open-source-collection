#!/bin/bash

# Docker-based Test Runner for FutureAGI Core Backend
# This script orchestrates testing across all three services using Docker

set -e  # Exit on any error

# Enable Docker BuildKit for better caching and faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.test.yml"
PROJECT_NAME="futureagi-test"
TEST_REPORTS_DIR="./test-reports"
COVERAGE_DIR="./coverage-reports"
TEST_LOGS_DIR="./test-logs"
CURRENT_LOG_FILE=""

# Arrays to track test results
declare -a TEST_RESULTS_NAMES
declare -a TEST_RESULTS_STATUS
declare -a TEST_RESULTS_ERRORS

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to initialize log file
init_log_file() {
    mkdir -p $TEST_LOGS_DIR
    local timestamp=$(date +'%Y%m%d_%H%M%S')
    CURRENT_LOG_FILE="$TEST_LOGS_DIR/test_run_${timestamp}.log"

    # Create log file with header
    cat > "$CURRENT_LOG_FILE" <<EOF
================================================================================
FutureAGI Core Backend - Test Execution Log
================================================================================
Timestamp: $(date +'%Y-%m-%d %H:%M:%S')
Host: $(hostname)
User: $(whoami)
Project: $PROJECT_NAME
================================================================================

EOF
    print_status "Log file created: $CURRENT_LOG_FILE"
}

# Function to log to both console and file
log_message() {
    local message="$1"
    echo -e "$message" | tee -a "$CURRENT_LOG_FILE"
}

# Function to log to file only (no console)
log_to_file() {
    local message="$1"
    echo -e "$message" >> "$CURRENT_LOG_FILE"
}

# Function to record test result
record_test_result() {
    local test_name="$1"
    local status="$2"
    local error_details="$3"

    TEST_RESULTS_NAMES+=("$test_name")
    TEST_RESULTS_STATUS+=("$status")
    TEST_RESULTS_ERRORS+=("$error_details")
}

# Function to generate final summary
generate_summary() {
    local total_tests=${#TEST_RESULTS_NAMES[@]}
    local passed=0
    local failed=0

    # Count passed and failed
    for status in "${TEST_RESULTS_STATUS[@]}"; do
        if [ "$status" = "PASSED" ]; then
            passed=$((passed + 1))
        else
            failed=$((failed + 1))
        fi
    done

    # Write summary to log file
    cat >> "$CURRENT_LOG_FILE" <<EOF

================================================================================
TEST EXECUTION SUMMARY
================================================================================
Total Test Suites: $total_tests
Passed: $passed
Failed: $failed
Success Rate: $(awk "BEGIN {printf \"%.2f\", ($passed/$total_tests)*100}")%
================================================================================

DETAILED RESULTS:
--------------------------------------------------------------------------------
EOF

    # Write detailed results
    for i in "${!TEST_RESULTS_NAMES[@]}"; do
        local name="${TEST_RESULTS_NAMES[$i]}"
        local status="${TEST_RESULTS_STATUS[$i]}"
        local error="${TEST_RESULTS_ERRORS[$i]}"

        if [ "$status" = "PASSED" ]; then
            echo "✅ $name: PASSED" >> "$CURRENT_LOG_FILE"
        else
            echo "❌ $name: FAILED" >> "$CURRENT_LOG_FILE"
            if [ -n "$error" ]; then
                echo "   Error Details:" >> "$CURRENT_LOG_FILE"
                echo "$error" | sed 's/^/   /' >> "$CURRENT_LOG_FILE"
            fi
            echo "" >> "$CURRENT_LOG_FILE"
        fi
    done

    # Add footer
    cat >> "$CURRENT_LOG_FILE" <<EOF

================================================================================
End of Test Execution Log
Completed: $(date +'%Y-%m-%d %H:%M:%S')
================================================================================
EOF

    # Display summary to console
    echo ""
    echo "================================================================================"
    log_message "${GREEN}📊 TEST EXECUTION SUMMARY${NC}"
    echo "================================================================================"
    log_message "Total Test Suites: $total_tests"
    log_message "Passed: ${GREEN}$passed${NC}"
    log_message "Failed: ${RED}$failed${NC}"
    log_message "Success Rate: $(awk "BEGIN {printf \"%.2f\", ($passed/$total_tests)*100}")%"
    echo "================================================================================"

    # Show detailed results
    for i in "${!TEST_RESULTS_NAMES[@]}"; do
        local name="${TEST_RESULTS_NAMES[$i]}"
        local status="${TEST_RESULTS_STATUS[$i]}"

        if [ "$status" = "PASSED" ]; then
            echo -e "${GREEN}✅ $name: PASSED${NC}"
        else
            echo -e "${RED}❌ $name: FAILED${NC}"
        fi
    done

    echo "================================================================================"
    log_message "${BLUE}📝 Detailed log saved to: $CURRENT_LOG_FILE${NC}"
    echo "================================================================================"
}

# Cross-platform timeout function
# Works on both Linux (with timeout) and macOS (without timeout)
run_with_timeout() {
    local timeout_duration=$1
    shift

    # Check if timeout command exists (Linux)
    if command -v timeout &> /dev/null; then
        timeout "$timeout_duration" "$@"
        return $?
    else
        # macOS fallback using background process
        "$@" &
        local pid=$!
        local count=0

        # Wait for process or timeout
        while kill -0 $pid 2>/dev/null; do
            if [ $count -ge $timeout_duration ]; then
                kill -TERM $pid 2>/dev/null
                sleep 2
                kill -KILL $pid 2>/dev/null
                return 124  # Same exit code as timeout command
            fi
            sleep 1
            count=$((count + 1))
        done

        # Get the exit code of the background process
        wait $pid
        return $?
    fi
}

# Function to cleanup test environment
cleanup() {
    print_status "Cleaning up test environment..."
    docker compose -f $COMPOSE_FILE -p $PROJECT_NAME down -v --remove-orphans || true

    # Targeted cleanup for test environment only
    print_status "Performing test environment cleanup..."

    # Remove only test-specific dangling images
    print_status "Removing test images..."
    docker images "futureagi-test-*" -q | xargs -r docker rmi -f 2>/dev/null || true

    # Remove only test volumes (keeping other project volumes)
    print_status "Removing test volumes..."
    docker volume ls -q | grep "test-" | xargs -r docker volume rm 2>/dev/null || true

    # Remove only test networks (keeping other project networks)
    print_status "Removing test networks..."
    docker network ls --filter name=futureagi-test -q | xargs -r docker network rm 2>/dev/null || true

    # Clean ONLY test-related build cache (not all build cache)
    # Using filter to target specific images
    print_status "Cleaning test-related build cache..."
    docker builder prune --filter "label!=keep" --filter "until=24h" -f || true

    # Show reclaimed space
    print_status "Test environment cleanup completed"
}

# Function to verify git submodules
verify_submodules() {
    print_status "Verifying git submodules..."

    # Check if agentic_eval submodule exists and is initialized
    if [ ! -d "agentic_eval" ] || [ -z "$(ls -A agentic_eval 2>/dev/null)" ]; then
        print_warning "agentic_eval submodule is missing or empty"
        print_status "Attempting to initialize submodules..."

        if git submodule update --init --recursive; then
            print_success "Submodules initialized successfully"
        else
            print_error "Failed to initialize submodules"
            print_error "Please run: git submodule update --init --recursive"
            exit 1
        fi
    else
        print_success "agentic_eval submodule is present"
    fi

    # Show submodule status
    if command -v git &> /dev/null; then
        git submodule status 2>/dev/null || true
    fi
}

# Function to setup test environment
setup() {
    print_status "Setting up test environment..."

    # Verify submodules first
    verify_submodules

    # Create test reports directories
    mkdir -p $TEST_REPORTS_DIR
    mkdir -p $COVERAGE_DIR
    mkdir -p $TEST_LOGS_DIR

    # Build test images
    print_status "Building test images..."

    # In CI environments (GitHub Actions, GitLab CI, etc.), use cache to save space
    # Otherwise, use --no-cache for clean local builds
    if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ] || [ -n "$GITLAB_CI" ]; then
        print_status "CI environment detected - using build cache"
        docker compose -f $COMPOSE_FILE -p $PROJECT_NAME build
    else
        print_status "Local environment - building without cache"
        docker compose -f $COMPOSE_FILE -p $PROJECT_NAME build
    fi
}

# Function to run specific test suite
run_test_suite() {
    local service_name=$1
    local description=$2

    print_status "Running $description..."
    log_to_file ""
    log_to_file "--------------------------------------------------------------------------------"
    log_to_file "Running: $description"
    log_to_file "Service: $service_name"
    log_to_file "Started: $(date +'%Y-%m-%d %H:%M:%S')"
    log_to_file "--------------------------------------------------------------------------------"

    # Capture output to temporary file
    local temp_log=$(mktemp)

    # Enable pipefail to catch exit codes from piped commands
    set -o pipefail

    # Run with timeout and better error handling
    # -T flag disables pseudo-TTY allocation for non-interactive mode
    run_with_timeout 7200 docker compose -f $COMPOSE_FILE -p $PROJECT_NAME run --rm -T $service_name 2>&1 | tee "$temp_log"
    local exit_code=$?

    # Disable pipefail after capturing exit code
    set +o pipefail

    if [ $exit_code -eq 0 ]; then
        print_success "$description completed successfully"
        log_to_file "Status: PASSED"
        log_to_file "Completed: $(date +'%Y-%m-%d %H:%M:%S')"

        # Optionally log summary of passed tests (first 20 and last 20 lines)
        log_to_file ""
        log_to_file "Test Output Summary (first 20 lines):"
        head -n 20 "$temp_log" >> "$CURRENT_LOG_FILE" 2>/dev/null || true
        log_to_file "..."
        log_to_file "Test Output Summary (last 20 lines):"
        tail -n 20 "$temp_log" >> "$CURRENT_LOG_FILE" 2>/dev/null || true

        # Record successful result
        record_test_result "$description" "PASSED" ""

        rm -f "$temp_log"
        return 0
    else
        local error_msg=""

        if [ $exit_code -eq 124 ]; then
            error_msg="$description timed out after 30 minutes"
            print_error "$error_msg"
        else
            error_msg="$description failed with exit code $exit_code"
            print_error "$error_msg"
        fi

        log_to_file "Status: FAILED"
        log_to_file "Exit Code: $exit_code"
        log_to_file "Error: $error_msg"
        log_to_file "Completed: $(date +'%Y-%m-%d %H:%M:%S')"

        # Show last 50 lines of logs to console
        print_warning "Showing last 50 lines of test output:"
        tail -n 50 "$temp_log" 2>/dev/null || echo "Could not retrieve test output"

        # Log COMPLETE test output to file for debugging
        log_to_file ""
        log_to_file "================================================================================"
        log_to_file "COMPLETE TEST OUTPUT (Full Trace):"
        log_to_file "================================================================================"
        cat "$temp_log" >> "$CURRENT_LOG_FILE" 2>/dev/null || echo "Could not capture test output" >> "$CURRENT_LOG_FILE"
        log_to_file "================================================================================"
        log_to_file "END OF TEST OUTPUT"
        log_to_file "================================================================================"

        # Also get container logs if available
        log_to_file ""
        log_to_file "Container Logs (last 50 lines):"
        local container_logs=$(docker compose -f $COMPOSE_FILE -p $PROJECT_NAME logs --tail=50 $service_name 2>/dev/null || echo "Could not retrieve container logs")
        log_to_file "$container_logs"

        # Capture error details for summary (use first 100 lines for summary)
        local error_summary=$(head -n 100 "$temp_log" 2>/dev/null || echo "Could not capture error summary")
        local error_details="Exit Code: $exit_code\nError Message: $error_msg\n\nError Summary (first 100 lines):\n$error_summary\n\n(See log file for complete trace)"

        # Record failed result
        record_test_result "$description" "FAILED" "$error_details"

        rm -f "$temp_log"
        return 1
    fi
}

# Function to run all tests
run_all_tests() {
    local failed=0

    # Initialize log file
    init_log_file

    print_status "🚀 Starting comprehensive test suite for FutureAGI Core Backend"
    log_to_file "🚀 Starting comprehensive test suite for FutureAGI Core Backend"
    echo "=" * 80

    # Wait for infrastructure services to be ready
    print_status "Starting infrastructure services..."
    docker compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d test-db test-clickhouse test-rabbitmq test-minio

    # Wait for health checks with better monitoring
    print_status "Waiting for services to be healthy..."

    # Check database health
    print_status "Checking database health..."
    for i in {1..30}; do
        if docker compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T test-db pg_isready -U test_user -d test_tfc >/dev/null 2>&1; then
            print_success "Database is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Database health check timeout - continuing anyway"
        fi
        sleep 2
    done

    # Check ClickHouse health
    print_status "Checking ClickHouse health..."
    for i in {1..15}; do
        if docker compose -f $COMPOSE_FILE -p $PROJECT_NAME exec -T test-clickhouse wget --quiet --tries=1 --spider http://localhost:8123/ping >/dev/null 2>&1; then
            print_success "ClickHouse is ready"
            break
        fi
        if [ $i -eq 15 ]; then
            print_warning "ClickHouse health check timeout - continuing anyway"
        fi
        sleep 2
    done

    sleep 10

    # Run backend tests
    if ! run_test_suite "test-backend" "Django Backend Tests"; then
        failed=$((failed + 1))
    fi

    # Run model serving tests
    if ! run_test_suite "test-model-serving" "Model Serving Tests"; then
        failed=$((failed + 1))
    fi

    # Run agentic eval tests (standalone)
    if ! run_test_suite "test-agentic-eval" "Agentic Eval Tests (Standalone)"; then
        failed=$((failed + 1))
    fi

    # Run agentic eval integration tests
    if ! run_test_suite "test-agentic-integration" "Agentic Eval Integration Tests"; then
        failed=$((failed + 1))
    fi

    # Run end-to-end tests
    if ! run_test_suite "test-e2e" "End-to-End Integration Tests"; then
        failed=$((failed + 1))
    fi

    # Aggregate reports
    run_test_suite "test-reports" "Test Report Aggregation"

    # Generate final summary
    generate_summary

    return $failed
}

# Function to run quick smoke tests
run_smoke_tests() {
    # Initialize log file
    init_log_file

    print_status "🔥 Running smoke tests..."
    log_to_file "🔥 Running smoke tests..."

    # Start minimal infrastructure
    docker compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d test-db test-clickhouse
    sleep 15

    # Run quick backend tests (parallel execution via pytest.ini configuration)
    log_to_file "Running quick backend tests..."
    if docker compose -f $COMPOSE_FILE -p $PROJECT_NAME run --rm -T test-backend python -m pytest tests/ -m "not slow" --maxfail=3 -q 2>&1 | tee -a "$CURRENT_LOG_FILE"; then
        record_test_result "Backend Smoke Tests" "PASSED" ""
    else
        record_test_result "Backend Smoke Tests" "FAILED" "Quick backend tests failed"
    fi

    # Run quick model serving tests (parallel execution via pytest.ini configuration)
    log_to_file "Running quick model serving tests..."
    if docker compose -f $COMPOSE_FILE -p $PROJECT_NAME run --rm -T test-model-serving uv run pytest tests/ -m "not slow" --maxfail=3 -q 2>&1 | tee -a "$CURRENT_LOG_FILE"; then
        record_test_result "Model Serving Smoke Tests" "PASSED" ""
    else
        record_test_result "Model Serving Smoke Tests" "FAILED" "Quick model serving tests failed"
    fi

    generate_summary
    print_success "Smoke tests completed"
}

# Function to run specific service tests
run_service_tests() {
    local service=$1

    # Initialize log file
    init_log_file

    case $service in
        "backend"|"django")
            print_status "Running Django backend tests only..."
            log_to_file "Running Django backend tests only..."
            docker compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d test-db test-clickhouse test-rabbitmq test-minio
            sleep 20
            run_test_suite "test-backend" "Django Backend Tests"
            ;;
        "model-serving"|"serving")
            print_status "Running model serving tests only..."
            log_to_file "Running model serving tests only..."
            run_test_suite "test-model-serving" "Model Serving Tests"
            ;;
        "agentic"|"agentic-eval")
            print_status "Running agentic eval tests only..."
            log_to_file "Running agentic eval tests only..."
            docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d test-clickhouse
            sleep 15
            run_test_suite "test-agentic-eval" "Agentic Eval Tests"
            ;;
        "integration"|"e2e")
            print_status "Running integration tests only..."
            log_to_file "Running integration tests only..."
            docker compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d test-db test-clickhouse test-rabbitmq test-minio
            sleep 30
            run_test_suite "test-e2e" "End-to-End Integration Tests"
            ;;
        *)
            print_error "Unknown service: $service"
            print_status "Available services: backend, model-serving, agentic, integration"
            exit 1
            ;;
    esac

    # Generate summary for service-specific tests
    generate_summary
}

# Function to show test reports
show_reports() {
    print_status "📊 Test Reports Summary"
    echo "=========================="

    if [ -d "$TEST_REPORTS_DIR" ]; then
        echo "📄 Test reports available in: $TEST_REPORTS_DIR"
        ls -la "$TEST_REPORTS_DIR" || true
    fi

    if [ -d "$COVERAGE_DIR" ]; then
        echo "📊 Coverage reports available in: $COVERAGE_DIR"
        ls -la "$COVERAGE_DIR" || true
    fi

    if [ -d "$TEST_LOGS_DIR" ]; then
        echo "📝 Test logs available in: $TEST_LOGS_DIR"
        echo "Latest log file:"
        ls -lt "$TEST_LOGS_DIR"/*.log 2>/dev/null | head -1 || true
    fi

    # Look for HTML coverage reports
    find . -name "htmlcov" -type d 2>/dev/null | while read dir; do
        echo "🌐 HTML coverage report: $dir/index.html"
    done
}

# Function to monitor test progress
monitor_tests() {
    print_status "🔍 Monitoring test containers..."
    docker compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f --tail=50
}

# Main script logic
main() {
    # Parse command line arguments
    COMMAND=${1:-"all"}

    case $COMMAND in
        "all"|"full")
            cleanup
            setup
            if run_all_tests; then
                print_success "🎉 All tests passed!"
                show_reports
                exit 0
            else
                failed_count=$?
                print_error "❌ $failed_count test suite(s) failed"
                show_reports
                exit 1
            fi
            ;;
        "smoke")
            cleanup
            setup
            run_smoke_tests
            cleanup
            ;;
        "backend"|"django"|"model-serving"|"serving"|"agentic"|"agentic-eval"|"integration"|"e2e")
            cleanup
            setup
            run_service_tests $COMMAND
            cleanup
            ;;
        "clean")
            cleanup
            print_success "Test environment cleaned"
            ;;
        "setup")
            setup
            print_success "Test environment setup completed"
            ;;
        "reports")
            show_reports
            ;;
        "monitor")
            monitor_tests
            ;;
        "help"|"--help"|"-h")
            echo "FutureAGI Docker Test Runner"
            echo "Usage: $0 [COMMAND]"
            echo ""
            echo "Commands:"
            echo "  all|full         Run all test suites (default)"
            echo "  smoke            Run quick smoke tests"
            echo "  backend          Run Django backend tests only"
            echo "  model-serving    Run model serving tests only"
            echo "  agentic          Run agentic eval tests only"
            echo "  integration      Run integration tests only"
            echo "  clean            Clean up test environment"
            echo "  setup            Setup test environment"
            echo "  reports          Show test reports summary"
            echo "  monitor          Monitor test container logs"
            echo "  help             Show this help message"
            echo ""
            echo "Test Results:"
            echo "  Each test run creates a timestamped log file in ./test-logs/"
            echo "  The log file contains a detailed summary of all test suites,"
            echo "  including which tests passed/failed and error details."
            echo ""
            echo "Examples:"
            echo "  $0 all           # Run all tests"
            echo "  $0 smoke         # Quick smoke test"
            echo "  $0 backend       # Only backend tests"
            echo "  $0 clean         # Cleanup"
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Trap to ensure cleanup on script exit
trap cleanup EXIT

# Run main function with all arguments
main "$@"
