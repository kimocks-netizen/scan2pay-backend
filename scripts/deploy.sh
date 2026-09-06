#!/usr/bin/env bash
# deploy.sh — build and deploy scan2pay-backend to AWS (account 542727784619)
# Usage:
#   ./scripts/deploy.sh          # deploy to dev (default)
#   ./scripts/deploy.sh prod     # deploy to prod

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
PROFILE="predictiq"
REGION="af-south-1"
STACK="scan2pay-backend"
ENV="${1:-dev}"
EXPECTED_ACCOUNT="542727784619"

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}▶ $*${NC}"; }
success() { echo -e "${GREEN}✓ $*${NC}"; }
warn()    { echo -e "${YELLOW}⚠ $*${NC}"; }
error()   { echo -e "${RED}✗ $*${NC}"; exit 1; }

# ── Guard: correct AWS account ────────────────────────────────────────────────
info "Verifying AWS account..."
ACCOUNT=$(aws sts get-caller-identity --profile "$PROFILE" --query Account --output text 2>&1) \
  || error "Could not authenticate with profile '$PROFILE'. Run: aws configure --profile $PROFILE"

if [ "$ACCOUNT" != "$EXPECTED_ACCOUNT" ]; then
  error "Wrong account! Got $ACCOUNT, expected $EXPECTED_ACCOUNT. Check your '$PROFILE' profile."
fi
success "Account $ACCOUNT confirmed (profile: $PROFILE)"

# ── Load .env ─────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

if [ ! -f "$ENV_FILE" ]; then
  error ".env file not found at $ENV_FILE"
fi

info "Loading .env..."
set -a; source "$ENV_FILE"; set +a

# ── Push SSM parameters ───────────────────────────────────────────────────────
info "Syncing SSM parameters to /scan2pay/$ENV/..."

ssm_put() {
  local NAME="$1" VALUE="$2"
  if [ -z "$VALUE" ]; then warn "Skipping $NAME — not set in .env"; return; fi
  aws ssm put-parameter \
    --profile "$PROFILE" --region "$REGION" \
    --name "/scan2pay/$ENV/$NAME" \
    --value "$VALUE" \
    --type String --overwrite --output text > /dev/null
  success "SSM /scan2pay/$ENV/$NAME"
}

ssm_put SUPABASE_URL              "${SUPABASE_URL:-}"
ssm_put SUPABASE_SERVICE_ROLE_KEY "${SUPABASE_SERVICE_ROLE_KEY:-}"
ssm_put JWT_SECRET                "${JWT_SECRET:-}"
ssm_put WINSMS_API_KEY            "${WINSMS_API_KEY:-}"
ssm_put PAYSTACK_SECRET_KEY       "${PAYSTACK_SECRET_KEY:-}"
ssm_put PAYSTACK_PUBLIC_KEY       "${PAYSTACK_PUBLIC_KEY:-}"
ssm_put PAYSTACK_WEBHOOK_SECRET   "${PAYSTACK_WEBHOOK_SECRET:-}"

# ── SAM build ─────────────────────────────────────────────────────────────────
info "Building..."
cd "$SCRIPT_DIR/.."
sam build --cached --parallel 2>&1 | tail -4

# ── SAM deploy ────────────────────────────────────────────────────────────────
info "Deploying stack '$STACK' to $REGION ($ENV)..."
sam deploy \
  --profile "$PROFILE" \
  --config-file samconfig.toml \
  --parameter-overrides "Environment=$ENV" \
  2>&1

# ── Print the API URL ─────────────────────────────────────────────────────────
API_URL=$(aws cloudformation describe-stacks \
  --profile "$PROFILE" \
  --region "$REGION" \
  --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text 2>&1)

echo ""
success "Deploy complete!"
echo -e "  ${CYAN}API:${NC} $API_URL"
echo -e "  ${CYAN}Health:${NC} $(curl -s "$API_URL/health" 2>/dev/null || echo 'check manually')"
echo ""
warn "Update scan2pay-web/.env → NEXT_PUBLIC_API_URL=$API_URL"


# bash scripts/deploy.sh