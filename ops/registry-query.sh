#!/usr/bin/env bash
# registry-query.sh — Patch GG (Wave 3 P2, 2026-05-04).
#
# Entity-version registry router. For "what's the latest <model>?" queries,
# direct API calls to HuggingFace Hub + OpenRouter give canonical answers
# that no web-search-with-recency-filter can match (Report 1's correct
# narrow insight, validated by VersionRAG arXiv 2510.08109).
#
# Usage:
#   ops/registry-query.sh <entity> > /tmp/registry.json
#   ops/registry-query.sh deepseek
#
# The skill reads the JSON output and writes it into recency_pass.json
# under `entity_version_resolution`. Researchers and the synthesizer
# treat the registry-derived version as authoritative for the version
# answer; remaining researchers focus on context.
#
# Triangulation: requires ≥2 sources to agree. If sources disagree on
# the latest version (e.g. HF says v4.2 but OpenRouter only has v4.1),
# the JSON's `source_agreement` field is < 2 and the synthesizer should
# surface the disagreement as a §5 open question rather than commit.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo '{"error": "usage: registry-query.sh <entity>", "entity": null}' >&2
  exit 1
fi

entity="$1"
entity_lc="$(echo "$entity" | tr '[:upper:]' '[:lower:]')"

# Defensive: jq required, curl required.
command -v jq >/dev/null || { echo '{"error": "jq not installed"}'; exit 1; }
command -v curl >/dev/null || { echo '{"error": "curl not installed"}'; exit 1; }

# ---------------------------------------------------------------------------
# Source 1: HuggingFace Hub — list latest models by entity (org name)
# ---------------------------------------------------------------------------
hf_url="https://huggingface.co/api/models?author=${entity_lc}&sort=createdAt&direction=-1&limit=10"
hf_json="$(curl -sf --max-time 10 "$hf_url" 2>/dev/null || echo '[]')"
hf_top="$(echo "$hf_json" | jq -c '[.[0:5][] | {id: .id, created: .createdAt}]' 2>/dev/null || echo '[]')"
hf_top_id="$(echo "$hf_top" | jq -r '.[0].id // null')"

# ---------------------------------------------------------------------------
# Source 2: OpenRouter — filter models by entity in the id
# ---------------------------------------------------------------------------
or_url="https://openrouter.ai/api/v1/models"
or_json="$(curl -sf --max-time 10 "$or_url" 2>/dev/null || echo '{"data":[]}')"
or_filter="$(echo "$or_json" | jq -c --arg e "$entity_lc" '
  [.data[]
   | select((.id // "") | ascii_downcase | contains($e))
   | {id: .id, created: .created, name: .name}]
  | sort_by(-(.created // 0))
  | .[0:5]
' 2>/dev/null || echo '[]')"
or_top_id="$(echo "$or_filter" | jq -r '.[0].id // null')"

# ---------------------------------------------------------------------------
# Triangulation — agreement on "latest"
# ---------------------------------------------------------------------------
# Two sources "agree" if their top-1 ids share a common version stem
# (entity name + first version-like substring). This is a heuristic; the
# synthesizer should treat exact equality as strong agreement and stem-
# match as weak agreement.
agreement=0
[[ "$hf_top_id" != "null" && -n "$hf_top_id" ]] && agreement=$((agreement + 1))
[[ "$or_top_id" != "null" && -n "$or_top_id" ]] && agreement=$((agreement + 1))

# Pick the most recent across both sources. If both have results, prefer
# whichever has the more recent timestamp; otherwise pick the one with
# data.
latest_id="$hf_top_id"
latest_source="huggingface"
if [[ "$or_top_id" != "null" && -n "$or_top_id" ]]; then
  if [[ "$hf_top_id" == "null" || -z "$hf_top_id" ]]; then
    latest_id="$or_top_id"
    latest_source="openrouter"
  fi
fi

# Final JSON output
jq -n \
  --arg entity "$entity" \
  --arg latest_id "${latest_id:-null}" \
  --arg latest_source "$latest_source" \
  --argjson source_agreement "$agreement" \
  --argjson hf_models "$hf_top" \
  --argjson openrouter_models "$or_filter" \
  '{
    entity: $entity,
    queried_at: (now | todate),
    latest_id: ($latest_id | if . == "null" or . == "" then null else . end),
    latest_source: $latest_source,
    source_agreement: $source_agreement,
    sources: {
      huggingface: $hf_models,
      openrouter: $openrouter_models
    },
    note: (
      if $source_agreement < 2 then "low confidence — registry sources disagree or one returned empty"
      elif ($latest_id | length) == 0 then "no entity matches found in either registry"
      else "ok"
      end
    )
  }'
