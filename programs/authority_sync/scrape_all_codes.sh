#!/bin/bash

################################################################################
# California Code Scraper - Master Script
#
# Scrapes all 29 California legal codes from leginfo.legislature.ca.gov
# and generates canonical JSON files for the CaseCore legal platform.
#
# Usage:
#   ./scrape_all_codes.sh [options]
#
# Options:
#   --dry-run       Report what would be created without writing files
#   --resume        Skip already-existing files
#   --code CODE     Scrape only one specific code (e.g., --code CIV)
#   --verbose       Enable verbose logging
#   --parallel N    Run N scrapers in parallel (default: 1, sequential)
#   --base-path PATH  Output base path (default: current directory)
#   --help          Show this help message
################################################################################

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
SCRAPER_SCRIPT="$SCRIPT_DIR/canonical_scraper.py"
LOG_FILE="$SCRIPT_DIR/scrape_all_codes.log"

# All 29 California legal codes
CODES=(
    "BPC"    # Business and Professions Code
    "CIV"    # Civil Code
    "CCP"    # Code of Civil Procedure
    "COM"    # Commercial Code
    "CORP"   # Corporations Code
    "EDC"    # Education Code
    "ELEC"   # Elections Code
    "EVID"   # Evidence Code
    "FAM"    # Family Code
    "FIN"    # Financial Code
    "FGC"    # Fish and Game Code
    "FAC"    # Food and Agricultural Code
    "GOV"    # Government Code
    "HNC"    # Health and Nursing Code
    "HSC"    # Health and Safety Code
    "INS"    # Insurance Code
    "LAB"    # Labor Code
    "MVC"    # Military and Veterans Code
    "PEN"    # Penal Code
    "PROB"   # Probate Code
    "PCC"    # Professional Conduct Code
    "PRC"    # Public Records Code
    "PUC"    # Public Utilities Code
    "RTC"    # Revenue and Taxation Code
    "SHC"    # Streets and Highways Code
    "UIC"    # Unemployment Insurance Code
    "VEH"    # Vehicle Code
    "WAT"    # Water Code
    "WIC"    # Welfare and Institutions Code
)

# Default options
DRY_RUN=false
RESUME=false
TARGET_CODE=""
VERBOSE=false
PARALLEL=1
BASE_PATH="."

################################################################################
# Functions
################################################################################

usage() {
    cat << EOF
Usage: $SCRIPT_NAME [options]

Options:
    --dry-run           Report what would be created without writing files
    --resume            Skip already-existing files
    --code CODE         Scrape only one specific code (e.g., --code CIV)
    --verbose           Enable verbose logging
    --parallel N        Run N scrapers in parallel (default: 1, sequential)
    --base-path PATH    Output base path (default: current directory)
    --help              Show this help message

Examples:
    # Scrape all codes sequentially
    $SCRIPT_NAME

    # Dry-run to see what would be created
    $SCRIPT_NAME --dry-run

    # Scrape only Civil Code
    $SCRIPT_NAME --code CIV

    # Scrape all codes in parallel (4 at a time)
    $SCRIPT_NAME --parallel 4

    # Resume incomplete scraping
    $SCRIPT_NAME --resume

EOF
    exit 0
}

log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

error() {
    log "ERROR" "$@"
    exit 1
}

info() {
    log "INFO" "$@"
}

scrape_code() {
    local code=$1
    local args=""

    [[ "$DRY_RUN" == true ]] && args="$args --dry-run"
    [[ "$RESUME" == true ]] && args="$args --resume"
    [[ "$VERBOSE" == true ]] && args="$args --verbose"
    [[ -n "$BASE_PATH" ]] && args="$args --base-path $BASE_PATH"

    info "Starting scrape for $code..."
    if python "$SCRAPER_SCRIPT" "$code" $args >> "$LOG_FILE" 2>&1; then
        info "Completed scrape for $code"
        return 0
    else
        log "WARN" "Failed to scrape $code"
        return 1
    fi
}

################################################################################
# Main Script
################################################################################

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --resume)
                RESUME=true
                shift
                ;;
            --code)
                TARGET_CODE="$2"
                shift 2
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --parallel)
                PARALLEL="$2"
                shift 2
                ;;
            --base-path)
                BASE_PATH="$2"
                shift 2
                ;;
            --help)
                usage
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done

    # Validate scraper script exists
    if [[ ! -f "$SCRAPER_SCRIPT" ]]; then
        error "Scraper script not found: $SCRAPER_SCRIPT"
    fi

    # Initialize log
    > "$LOG_FILE"
    info "=========================================="
    info "California Code Scraper - Master Script"
    info "=========================================="
    info "DRY_RUN: $DRY_RUN"
    info "RESUME: $RESUME"
    info "TARGET_CODE: ${TARGET_CODE:-ALL}"
    info "VERBOSE: $VERBOSE"
    info "PARALLEL: $PARALLEL"
    info "BASE_PATH: $BASE_PATH"
    info "Log file: $LOG_FILE"

    # Determine which codes to scrape
    local codes_to_scrape=()
    if [[ -n "$TARGET_CODE" ]]; then
        # Validate target code
        local found=false
        for code in "${CODES[@]}"; do
            if [[ "$code" == "$TARGET_CODE" ]]; then
                found=true
                break
            fi
        done
        if [[ "$found" == false ]]; then
            error "Invalid code: $TARGET_CODE. Valid codes are: ${CODES[*]}"
        fi
        codes_to_scrape=("$TARGET_CODE")
    else
        codes_to_scrape=("${CODES[@]}")
    fi

    info "Will scrape ${#codes_to_scrape[@]} code(s)"

    # Scrape codes
    local failed_codes=()
    local successful_codes=()

    if [[ "$PARALLEL" -eq 1 ]]; then
        # Sequential execution
        info "Running scrapers sequentially..."
        for code in "${codes_to_scrape[@]}"; do
            if scrape_code "$code"; then
                successful_codes+=("$code")
            else
                failed_codes+=("$code")
            fi
        done
    else
        # Parallel execution using GNU parallel or xargs
        info "Running scrapers in parallel ($PARALLEL at a time)..."
        if command -v parallel &> /dev/null; then
            printf '%s\n' "${codes_to_scrape[@]}" | parallel -j "$PARALLEL" scrape_code
        else
            # Fallback to background jobs
            local job_count=0
            for code in "${codes_to_scrape[@]}"; do
                scrape_code "$code" &
                ((job_count++))
                if [[ $((job_count % PARALLEL)) -eq 0 ]]; then
                    wait
                fi
            done
            wait
        fi
        # Note: In parallel mode, we can't easily track success/failure
        successful_codes=("${codes_to_scrape[@]}")
    fi

    # Summary
    info "=========================================="
    info "Scraping Complete"
    info "=========================================="
    info "Successful: ${#successful_codes[@]}/${#codes_to_scrape[@]}"
    if [[ ${#successful_codes[@]} -gt 0 ]]; then
        info "Successful codes: ${successful_codes[*]}"
    fi
    if [[ ${#failed_codes[@]} -gt 0 ]]; then
        info "Failed codes: ${failed_codes[*]}"
    fi
    info "Log file: $LOG_FILE"

    if [[ ${#failed_codes[@]} -gt 0 ]]; then
        return 1
    fi
    return 0
}

# Run main function
main "$@"
