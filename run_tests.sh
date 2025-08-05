#!/bin/bash

# RAG Test Runner
# This script runs comprehensive tests for the RAG project

set -e

echo "RAG Test Suite"
echo "========================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "Virtual environment not detected. Please activate it first."
    print_status "You can activate it with: source src/venv/bin/activate"
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "src/main.py" ]]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Install test dependencies
print_status "Installing test dependencies..."
pip install -r src/helpers/tests/requirements-test.txt

# Create test database if it doesn't exist
print_status "Setting up test database..."
if ! psql -h localhost -U postgres -lqt | cut -d \| -f 1 | grep -qw minirag_test; then
    print_status "Creating test database..."
    createdb -h localhost -U postgres minirag_test
    print_success "Test database created"
else
    print_status "Test database already exists"
fi

# Function to run tests with specific markers
run_tests() {
    local marker=$1
    local description=$2
    local extra_args=$3
    
    print_status "Running $description tests..."
    if pytest src/helpers/tests/ -m "$marker" $extra_args; then
        print_success "$description tests passed"
        return 0
    else
        print_error "$description tests failed"
        return 1
    fi
}

# Function to run all tests
run_all_tests() {
    print_status "Running all tests..."
    if pytest src/helpers/tests/ -v; then
        print_success "All tests passed"
        return 0
    else
        print_error "Some tests failed"
        return 1
    fi
}

# Function to run tests with coverage
run_tests_with_coverage() {
    print_status "Running tests with coverage..."
    if pytest src/helpers/tests/ --cov=src --cov-report=html --cov-report=term-missing; then
        print_success "Tests with coverage completed"
        print_status "Coverage report generated in htmlcov/index.html"
        return 0
    else
        print_error "Tests with coverage failed"
        return 1
    fi
}

# Function to run specific test categories
run_unit_tests() {
    run_tests "unit" "Unit" "-v"
}

run_integration_tests() {
    run_tests "integration" "Integration" "-v"
}

run_model_tests() {
    run_tests "models" "Model" "-v"
}

run_route_tests() {
    run_tests "routes" "Route" "-v"
}

run_controller_tests() {
    run_tests "controllers" "Controller" "-v"
}

run_store_tests() {
    run_tests "stores" "Store" "-v"
}

run_utils_tests() {
    run_tests "utils" "Utility" "-v"
}

# Main execution
case "${1:-all}" in
    "unit")
        run_unit_tests
        ;;
    "integration")
        run_integration_tests
        ;;
    "models")
        run_model_tests
        ;;
    "routes")
        run_route_tests
        ;;
    "controllers")
        run_controller_tests
        ;;
    "stores")
        run_store_tests
        ;;
    "utils")
        run_utils_tests
        ;;
    "coverage")
        run_tests_with_coverage
        ;;
    "all")
        run_all_tests
        ;;
    "help")
        echo "Usage: $0 [test_category]"
        echo ""
        echo "Available test categories:"
        echo "  all         - Run all tests"
        echo "  unit        - Run unit tests only"
        echo "  integration - Run integration tests only"
        echo "  models      - Run model tests only"
        echo "  routes      - Run route tests only"
        echo "  controllers - Run controller tests only"
        echo "  stores      - Run store tests only"
        echo "  utils       - Run utility tests only"
        echo "  coverage    - Run all tests with coverage report"
        echo "  help        - Show this help message"
        ;;
    *)
        print_error "Unknown test category: $1"
        echo "Use '$0 help' for available options"
        exit 1
        ;;
esac

# Generate test report
if [[ "$1" == "coverage" || "$1" == "all" ]]; then
    print_status "Generating test report..."
    pytest src/helpers/tests/ --html=test_report.html --self-contained-html
    print_success "Test report generated: test_report.html"
fi

print_success "Test execution completed!" 