#!/usr/bin/env bash
# Copy each pinned integration into /homeassistant/custom_components/<domain>, atomically.
# A folder without our marker was installed by hand (HACS, the HA screen, ...) — leave it alone.
set -euo pipefail

TARGET_ROOT=/homeassistant/custom_components
MARKER=.installed_by_addon
mkdir -p "${TARGET_ROOT}"

for SOURCE in /opt/integrations/*/; do
  SOURCE="${SOURCE%/}"
  DOMAIN="$(basename "${SOURCE}")"
  TARGET="${TARGET_ROOT}/${DOMAIN}"
  if [ -d "${TARGET}" ] && [ ! -f "${TARGET}/${MARKER}" ]; then
    echo "[${DOMAIN}] ${TARGET} was not installed by this add-on — leaving it untouched"
    continue
  fi
  if [ -f "${TARGET}/${MARKER}" ] && cmp -s "${TARGET}/${MARKER}" "${SOURCE}/${MARKER}"; then
    echo "[${DOMAIN}] $(cat "${SOURCE}/${MARKER}") already in place"
    continue
  fi
  STAGE="$(mktemp -d "${TARGET_ROOT}/.${DOMAIN}.new.XXXXXX")"
  cp -a "${SOURCE}/." "${STAGE}/"
  if [ -d "${TARGET}" ]; then
    OLD="${TARGET_ROOT}/.${DOMAIN}.old.$$"
    mv "${TARGET}" "${OLD}"
    mv "${STAGE}" "${TARGET}"
    rm -rf "${OLD}"
  else
    mv "${STAGE}" "${TARGET}"
  fi
  echo "[${DOMAIN}] installed $(cat "${TARGET}/${MARKER}") — restart Home Assistant to load it"
done
