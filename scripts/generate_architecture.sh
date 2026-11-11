#!/usr/bin/env bash
# ==============================================================================
# Script: scripts/generate_architecture.sh
# Description: Generates ARCHITECTURE.md and ARCHITECTURE.json artifacts with
#              UTC logging, schema validation, backup/rollback, and dry-run support.
# 
# Features:
#   - Idempotent: Safe to run multiple times
#   - Dry-run: Preview changes without modifying filesystem
#   - Backup: Automatic .bak files before overwriting
#   - Exit codes: 0=success, 1=validation failed, 2=env error, 3=dry-run
#   - Config-driven: Reads from config/architecture_config.yaml
#
# Exit Codes:
#   0 - Success
#   1 - Validation failure
#   2 - Environment/configuration error
#   3 - Dry-run mode (no changes made)
# ==============================================================================
set -euo pipefail

# ==============================================================================
# Configuration Section
# ==============================================================================
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
readonly CONFIG_FILE="${PROJECT_ROOT}/config/architecture_config.yaml"
readonly BACKUP_DIR="${PROJECT_ROOT}/backups/architecture/$(date +%Y%m%d_%H%M%S)"

# Default configuration (override via config file if exists)
ARTIFACT_VERSION="${ARTIFACT_VERSION:-2027.1.0}"
ENABLE_BACKUP="${ENABLE_BACKUP:-true}"
DRY_RUN="${DRY_RUN:-false}"
VERBOSE="${VERBOSE:-false}"
SYSTEM_NAME="${SYSTEM_NAME:-Pennsylvania Health Insurance Audit Engine}"
RATING_AREAS_COUNT="${RATING_AREAS_COUNT:-9}"

# Log level control
LOG_LEVEL="${LOG_LEVEL:-INFO}"  # DEBUG, INFO, WARN, ERROR

# ==============================================================================
# Logging Functions with Levels
# ==============================================================================
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Only show messages at or above configured log level
    local -A level_priority=( [DEBUG]=0 [INFO]=1 [WARN]=2 [ERROR]=3 )
    local show_msg=false
    
    [[ ${level_priority[$level]:-1} -ge ${level_priority[$LOG_LEVEL]:-1} ]] && show_msg=true
    
    if $show_msg; then
        case "$level" in
            DEBUG) echo "[${timestamp}] [DEBUG] ${message}" ;;
            INFO)  echo "[${timestamp}] [INFO ] ${message}" ;;
            WARN)  echo "[${timestamp}] [WARN ] ${message}" >&2 ;;
            ERROR) echo "[${timestamp}] [ERROR] ${message}" >&2 ;;
        esac
    fi
}

log_debug() { log "DEBUG" "$@"; }
log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }

# ==============================================================================
# Utility Functions
# ==============================================================================
create_backup() {
    local file_path="$1"
    
    if [[ ! -f "$file_path" ]]; then
        log_debug "No existing file at ${file_path}, skipping backup"
        return 0
    fi
    
    if $DRY_RUN; then
        log_debug "Dry-run: Skipping backup of ${file_path}"
        return 0
    fi
    
    if [[ "$ENABLE_BACKUP" == "true" ]]; then
        mkdir -p "$BACKUP_DIR"
        local backup_path="${BACKUP_DIR}/$(basename "$file_path")"
        cp -v "$file_path" "$backup_path"
        log_info "Created backup: ${backup_path}"
        
        # Store SHA-256 hash for integrity verification
        sha256sum "$file_path" > "${backup_path}.sha256"
        log_debug "Stored SHA-256 hash: ${backup_path}.sha256"
    fi
}

compute_file_hash() {
    local file_path="$1"
    if [[ -f "$file_path" ]]; then
        sha256sum "$file_path" | cut -d' ' -f1
    else
        echo "N/A"
    fi
}

load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        log_info "Loading configuration from ${CONFIG_FILE}"
        
        # Parse YAML configuration (basic parsing, no external deps)
        while IFS=': ' read -r key value; do
            key=$(echo "$key" | tr -d ' ')
            value=$(echo "$value" | sed 's/^"\(.*\)"$/\1/')
            case "$key" in
                system_name) SYSTEM_NAME="$value" ;;
                version) ARTIFACT_VERSION="$value" ;;
                rating_areas) RATING_AREAS_COUNT="$value" ;;
            esac
        done < <(grep -E "^(system_name|version|rating_areas):" "$CONFIG_FILE" 2>/dev/null || true)
        
        log_debug "Loaded config: system=${SYSTEM_NAME}, version=${ARTIFACT_VERSION}, rating_areas=${RATING_AREAS_COUNT}"
    else
        log_warn "No configuration file found at ${CONFIG_FILE}, using defaults"
    fi
}

validate_environment() {
    log_debug "Validating environment prerequisites..."
    
    local missing_tools=()
    
    # Check for required commands
    for cmd in date mkdir cat python3 sha256sum; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_tools+=("$cmd")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        return 1
    fi
    
    # Validate write permissions
    if [[ ! -w "$PROJECT_ROOT" ]]; then
        log_error "Project root is not writable: ${PROJECT_ROOT}"
        return 1
    fi
    
    # Validate Python availability
    if ! python3 --version &> /dev/null; then
        log_error "Python 3 is required but not found"
        return 1
    fi
    
    log_debug "Environment validation passed"
    return 0
}

# ==============================================================================
# Artifact Generation Functions
# ==============================================================================
generate_markdown_artifact() {
    local output_path="${PROJECT_ROOT}/docs/ARCHITECTURE.md"
    local generated_at
    generated_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local source_hash
    source_hash=$(compute_file_hash "$0")
    
    log_info "Generating markdown artifact: ${output_path}"
    
    if $DRY_RUN; then
        log_debug "Dry-run: Would generate ${output_path}"
        log_debug "Preview (first 10 lines):"
        cat << 'EOF'
# Pennsylvania Health Insurance Audit System Architecture

## Core Components
- **Data Ingestion Engine**: SERFF rate filings, CMS geographic rating area crosswalks, Pennie exchange enrollment logs.
- **Actuarial Audit Engine**: Evaluates carrier-mix weighted averages, Section 1332 reinsurance offsets, and 2-year compounded rate changes.
- **Statistical Anomaly Detector**: Stratified Robust Median Absolute Deviation (MAD) for thin counties ($N < 5$) and modified $Z$-scores for dense markets.
- **Deterministic Calculation Pipeline**: Precision `Decimal` calculations enforcing `ROUND_HALF_UP` for all effective premiums.

## Pipeline Flow
1. **Ingest & Validate**: Verify incoming SERFF URRT v8.2 XML/CSV feeds.
2. **Stratified Outlier Screening**: Group by CMS Rating Area; compute robust MAD bounds.
3. **Reinsurance & CSR Adjustment**: Apply state 1332 waiver parameters ($60k attachment, $100k cap, 34% coinsurance).
4. **Audit Logging & Reconciliation**: Persist reconciliation records in PostgreSQL.

## Non-Negotiable Design Rules
 * Canonical schema first.
 * Raw inputs are immutable.
 * Every output must be reproducible.
 * Every report must include generation time and source hash.
 * Every crosswalk decision must be explainable.
 * Every module must be independently testable.
EOF
        return 0
    fi
    
    create_backup "$output_path"
    
    cat > "$output_path" << EOF
# Pennsylvania Health Insurance Audit System Architecture

Generated: ${generated_at}
Source Script Hash (SHA-256): ${source_hash}
Version: ${ARTIFACT_VERSION}

## Core Components
- **Data Ingestion Engine**: SERFF rate filings, CMS geographic rating area crosswalks, Pennie exchange enrollment logs.
- **Actuarial Audit Engine**: Evaluates carrier-mix weighted averages, Section 1332 reinsurance offsets, and 2-year compounded rate changes.
- **Statistical Anomaly Detector**: Stratified Robust Median Absolute Deviation (MAD) for thin counties (\$N < 5\$) and modified \$Z\`-scores for dense markets.
- **Deterministic Calculation Pipeline**: Precision \`Decimal\` calculations enforcing \`ROUND_HALF_UP\` for all effective premiums.

## Pipeline Flow
1. **Ingest & Validate**: Verify incoming SERFF URRT v8.2 XML/CSV feeds.
2. **Stratified Outlier Screening**: Group by CMS Rating Area; compute robust MAD bounds.
3. **Reinsurance & CSR Adjustment**: Apply state 1332 waiver parameters (\$60k attachment, \$100k cap, 34% coinsurance).
4. **Audit Logging & Reconciliation**: Persist reconciliation records in PostgreSQL.

## Non-Negotiable Design Rules
 * Canonical schema first.
 * Raw inputs are immutable.
 * Every output must be reproducible.
 * Every report must include generation time and source hash.
 * Every crosswalk decision must be explainable.
 * Every module must be independently testable.
EOF
    
    local new_hash
    new_hash=$(compute_file_hash "$output_path")
    log_info "Generated ${output_path} (SHA-256: ${new_hash:0:16}...)"
}

generate_json_artifact() {
    local output_path="${PROJECT_ROOT}/docs/ARCHITECTURE.json"
    local generated_at
    generated_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local source_hash
    source_hash=$(compute_file_hash "$0")
    
    log_info "Generating JSON artifact: ${output_path}"
    
    if $DRY_RUN; then
        log_debug "Dry-run: Would generate ${output_path}"
        log_debug "Preview:"
        jq -n \
            --arg system "$SYSTEM_NAME" \
            --arg version "$ARTIFACT_VERSION" \
            --argjson rating_areas "$RATING_AREAS_COUNT" \
            --arg generated "$generated_at" \
            '{system: $system, version: $version, rating_areas: $rating_areas, generated_at: $generated, modules: ["ingestion", "actuarial_audit", "robust_mad_anomaly_detector", "deterministic_decimal_engine"]}' | head -10
        return 0
    fi
    
    create_backup "$output_path"
    
    cat > "$output_path" << EOF
{
  "system": "${SYSTEM_NAME}",
  "version": "${ARTIFACT_VERSION}",
  "rating_areas": ${RATING_AREAS_COUNT},
  "reinsurance_parameters": {
    "attachment_point": 60000.00,
    "cap": 100000.00,
    "coinsurance_rate": 0.34
  },
  "modules": [
    "ingestion",
    "actuarial_audit",
    "robust_mad_anomaly_detector",
    "deterministic_decimal_engine"
  ],
  "generation_metadata": {
    "generated_at": "${generated_at}",
    "source_script_hash": "${source_hash}",
    "generator_version": "1.0.0"
  }
}
EOF
    
    local new_hash
    new_hash=$(compute_file_hash "$output_path")
    log_info "Generated ${output_path} (SHA-256: ${new_hash:0:16}...)"
}

# ==============================================================================
# Validation Functions
# ==============================================================================
validate_json_artifact() {
    local json_path="${PROJECT_ROOT}/docs/ARCHITECTURE.json"
    
    log_info "Validating JSON artifact: ${json_path}"
    
    if $DRY_RUN; then
        log_debug "Dry-run: Skipping validation"
        return 0
    fi
    
    python3 - "$json_path" << 'PYEOF'
import json
import sys
from pathlib import Path

json_path = Path(sys.argv[1])

try:
    # File existence
    if not json_path.exists():
        print(f"[ERROR] JSON file does not exist: {json_path}", file=sys.stderr)
        sys.exit(1)
    
    # File not empty
    if json_path.stat().st_size == 0:
        print(f"[ERROR] JSON file is empty: {json_path}", file=sys.stderr)
        sys.exit(1)
    
    # Parse JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Required keys
    required_keys = {"system", "version", "rating_areas", "modules"}
    missing = required_keys - set(data.keys())
    if missing:
        print(f"[ERROR] Missing required keys: {missing}", file=sys.stderr)
        sys.exit(1)
    
    # Type validations
    if not isinstance(data["system"], str) or not data["system"]:
        print("[ERROR] 'system' must be a non-empty string", file=sys.stderr)
        sys.exit(1)
    
    if not isinstance(data["version"], str):
        print("[ERROR] 'version' must be a string", file=sys.stderr)
        sys.exit(1)
    
    if not isinstance(data["rating_areas"], int) or data["rating_areas"] <= 0:
        print("[ERROR] 'rating_areas' must be a positive integer", file=sys.stderr)
        sys.exit(1)
    
    if not isinstance(data["modules"], list) or len(data["modules"]) == 0:
        print("[ERROR] 'modules' must be a non-empty list", file=sys.stderr)
        sys.exit(1)
    
    # Metadata presence
    if "generation_metadata" not in data:
        print("[WARN] 'generation_metadata' field not found (recommended but not required)", file=sys.stderr)
    
    print(f"[OK] JSON validation passed")
    print(f"  - System: {data['system']}")
    print(f"  - Version: {data['version']}")
    print(f"  - Rating Areas: {data['rating_areas']}")
    print(f"  - Modules: {len(data['modules'])}")
    sys.exit(0)

except json.JSONDecodeError as e:
    print(f"[ERROR] Invalid JSON syntax: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Validation failed: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
    
    return $?
}

# ==============================================================================
# Main Execution
# ==============================================================================
main() {
    log_info "=============================================="
    log_info "Architecture Artifact Generator v1.0.0"
    log_info "=============================================="
    log_info "Project Root: ${PROJECT_ROOT}"
    log_info "Log Level: ${LOG_LEVEL}"
    log_info "Dry Run: ${DRY_RUN}"
    log_info "Backup Enabled: ${ENABLE_BACKUP}"
    
    # Load configuration if available
    load_config
    
    # Validate environment
    if ! validate_environment; then
        log_error "Environment validation failed"
        exit 2
    fi
    
    # Create required directories
    log_info "Creating output directories..."
    if $DRY_RUN; then
        log_debug "Dry-run: Would create directories"
    else
        mkdir -p "${PROJECT_ROOT}/docs" "${PROJECT_ROOT}/backups/architecture"
    fi
    
    # Generate artifacts
    generate_markdown_artifact
    generate_json_artifact
    
    # Validate artifacts
    if ! validate_json_artifact; then
        log_error "Artifact validation failed"
        exit 1
    fi
    
    # Summary
    log_info "=============================================="
    log_info "Generation completed successfully"
    log_info "=============================================="
    log_info "Artifacts created:"
    log_info "  - docs/ARCHITECTURE.md"
    log_info "  - docs/ARCHITECTURE.json"
    
    if [[ -n "${BACKUP_DIR:-}" && "$ENABLE_BACKUP" == "true" ]]; then
        log_info "Backups stored in: ${BACKUP_DIR}"
    fi
    
    # Exit with code 3 if dry-run was used (non-zero to indicate no changes made)
    if $DRY_RUN; then
        log_info "Dry-run mode: No filesystem changes were made"
        exit 3
    fi
    
    exit 0
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --no-backup)
            ENABLE_BACKUP=false
            shift
            ;;
        --verbose|-v)
            LOG_LEVEL=DEBUG
            shift
            ;;
        --quiet|-q)
            LOG_LEVEL=ERROR
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run       Preview changes without modifying filesystem"
            echo "  --no-backup     Skip creating backup files"
            echo "  --verbose, -v   Enable debug-level logging"
            echo "  --quiet, -q     Show only errors"
            echo "  --help          Display this help message"
            echo ""
            echo "Environment Variables:"
            echo "  LOG_LEVEL       Set log level (DEBUG, INFO, WARN, ERROR)"
            echo "  ENABLE_BACKUP   Set to 'false' to disable backups"
            echo "  DRY_RUN         Set to 'true' for dry-run mode"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 2
            ;;
    esac
done

main "$@"
