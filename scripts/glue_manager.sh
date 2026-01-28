#!/bin/bash
# =============================================================================
# GLUE MANAGER - Gestion des jobs Glue UCCNCT
# =============================================================================

set -e

# Configuration
SCRIPTS_BUCKET="uccnt-ef98cc0f-scripts"
JOB_PREFIX="uccnt-dev"
SCRIPTS_DIR="$(dirname "$0")/glue"
SOURCES=("bluesky" "nostr" "hackernews" "stackoverflow" "rss")
AWS_REGION="us-east-1"
export AWS_DEFAULT_REGION="${AWS_REGION}"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# =============================================================================
# Fonctions
# =============================================================================

usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  upload              Upload les scripts Glue vers S3"
    echo "  transform <source>  Lance le job de transformation pour une source"
    echo "  transform-all       Lance tous les jobs de transformation"
    echo "  aggregate           Lance le job d'agregation"
    echo "  status <job-name>   Verifie le status d'un job"
    echo "  list                Liste tous les jobs Glue"
    echo "  full-pipeline       Execute le pipeline complet (transform-all + aggregate)"
    echo ""
    echo "Sources disponibles: ${SOURCES[*]}"
    echo ""
    echo "Exemples:"
    echo "  $0 upload"
    echo "  $0 transform bluesky"
    echo "  $0 transform-all"
    echo "  $0 aggregate"
    echo "  $0 full-pipeline"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

upload_scripts() {
    log_info "Upload des scripts Glue vers s3://${SCRIPTS_BUCKET}/glue/"

    if [ -f "${SCRIPTS_DIR}/social_transform.py" ]; then
        aws s3 cp "${SCRIPTS_DIR}/social_transform.py" "s3://${SCRIPTS_BUCKET}/glue/social_transform.py"
        log_info "social_transform.py uploade"
    else
        log_error "social_transform.py non trouve dans ${SCRIPTS_DIR}"
    fi

    if [ -f "${SCRIPTS_DIR}/social_aggregation.py" ]; then
        aws s3 cp "${SCRIPTS_DIR}/social_aggregation.py" "s3://${SCRIPTS_BUCKET}/glue/social_aggregation.py"
        log_info "social_aggregation.py uploade"
    else
        log_error "social_aggregation.py non trouve dans ${SCRIPTS_DIR}"
    fi

    log_info "Upload termine"
}

run_transform() {
    local source=$1
    local job_name="${JOB_PREFIX}-transform-${source}"

    log_info "Lancement du job: ${job_name}"

    run_id=$(aws glue start-job-run --job-name "${job_name}" --query 'JobRunId' --output text)

    if [ -n "$run_id" ]; then
        log_info "Job lance avec RunId: ${run_id}"
        echo "${run_id}"
    else
        log_error "Echec du lancement du job ${job_name}"
        return 1
    fi
}

run_transform_all() {
    log_info "Lancement de tous les jobs de transformation..."

    declare -A run_ids

    for source in "${SOURCES[@]}"; do
        log_info "Lancement transform-${source}..."
        run_id=$(run_transform "${source}" 2>/dev/null || echo "FAILED")
        run_ids[$source]=$run_id
    done

    echo ""
    log_info "Resume des jobs lances:"
    for source in "${SOURCES[@]}"; do
        echo "  - ${source}: ${run_ids[$source]}"
    done
}

run_aggregate() {
    local job_name="${JOB_PREFIX}-aggregation"

    log_info "Lancement du job: ${job_name}"

    run_id=$(aws glue start-job-run --job-name "${job_name}" --query 'JobRunId' --output text)

    if [ -n "$run_id" ]; then
        log_info "Job lance avec RunId: ${run_id}"
        echo "${run_id}"
    else
        log_error "Echec du lancement du job ${job_name}"
        return 1
    fi
}

check_status() {
    local job_name=$1

    log_info "Status du job: ${job_name}"

    aws glue get-job-runs --job-name "${job_name}" --max-items 5 \
        --query 'JobRuns[*].{RunId:Id,Status:JobRunState,StartTime:StartedOn,Duration:ExecutionTime}' \
        --output table
}

list_jobs() {
    log_info "Liste des jobs Glue UCCNCT:"

    aws glue get-jobs --query "Jobs[?contains(Name, '${JOB_PREFIX}')].{Name:Name,Status:LastRun.Status}" --output table
}

wait_for_job() {
    local job_name=$1
    local run_id=$2
    local timeout=${3:-600}  # 10 minutes par defaut
    local elapsed=0
    local interval=30

    log_info "Attente de la fin du job ${job_name} (RunId: ${run_id})..."

    while [ $elapsed -lt $timeout ]; do
        status=$(aws glue get-job-run --job-name "${job_name}" --run-id "${run_id}" \
            --query 'JobRun.JobRunState' --output text)

        case $status in
            SUCCEEDED)
                log_info "Job ${job_name} termine avec succes"
                return 0
                ;;
            FAILED|STOPPED|TIMEOUT)
                log_error "Job ${job_name} echoue avec status: ${status}"
                return 1
                ;;
            *)
                echo -n "."
                sleep $interval
                elapsed=$((elapsed + interval))
                ;;
        esac
    done

    log_error "Timeout en attendant le job ${job_name}"
    return 1
}

run_full_pipeline() {
    log_info "=== PIPELINE COMPLET UCCNCT ==="

    # Etape 1: Upload des scripts
    log_info "Etape 1/3: Upload des scripts"
    upload_scripts

    # Etape 2: Jobs de transformation
    log_info "Etape 2/3: Jobs de transformation"
    declare -A transform_runs

    for source in "${SOURCES[@]}"; do
        run_id=$(run_transform "${source}" 2>/dev/null || echo "FAILED")
        transform_runs[$source]=$run_id
        sleep 2  # Petit delai entre les lancements
    done

    # Attendre que tous les jobs de transformation soient termines
    log_info "Attente de la fin des transformations..."
    all_success=true

    for source in "${SOURCES[@]}"; do
        run_id=${transform_runs[$source]}
        if [ "$run_id" != "FAILED" ]; then
            if ! wait_for_job "${JOB_PREFIX}-transform-${source}" "$run_id" 900; then
                all_success=false
            fi
        else
            all_success=false
        fi
    done

    if [ "$all_success" = false ]; then
        log_warn "Certains jobs de transformation ont echoue, mais on continue avec l'agregation"
    fi

    # Etape 3: Job d'agregation
    log_info "Etape 3/3: Job d'agregation"
    agg_run_id=$(run_aggregate)

    if [ -n "$agg_run_id" ]; then
        wait_for_job "${JOB_PREFIX}-aggregation" "$agg_run_id" 900
    fi

    log_info "=== PIPELINE TERMINE ==="
}

# =============================================================================
# Main
# =============================================================================

case "${1:-}" in
    upload)
        upload_scripts
        ;;
    transform)
        if [ -z "${2:-}" ]; then
            log_error "Source manquante. Sources disponibles: ${SOURCES[*]}"
            exit 1
        fi
        run_transform "$2"
        ;;
    transform-all)
        run_transform_all
        ;;
    aggregate)
        run_aggregate
        ;;
    status)
        if [ -z "${2:-}" ]; then
            log_error "Nom du job manquant"
            exit 1
        fi
        check_status "$2"
        ;;
    list)
        list_jobs
        ;;
    full-pipeline)
        run_full_pipeline
        ;;
    *)
        usage
        exit 1
        ;;
esac
