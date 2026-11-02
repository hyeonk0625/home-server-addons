#!/usr/bin/env bash
# Copy SmartIR into /homeassistant/custom_components/smartir, atomically.
# A folder without our marker was installed by hand (HACS etc.) — leave it alone.
set -euo pipefail

TARGET_ROOT=/homeassistant/custom_components
TARGET="${TARGET_ROOT}/smartir"
SOURCE=/opt/smartir/smartir
MARKER=.installed_by_addon

if [ -d "${TARGET}" ] && [ ! -f "${TARGET}/${MARKER}" ]; then
  echo "[smartir] ${TARGET} was not installed by this add-on — leaving it untouched"
  exit 0
fi
if [ -f "${TARGET}/${MARKER}" ] && cmp -s "${TARGET}/${MARKER}" "${SOURCE}/${MARKER}"; then
  echo "[smartir] $(cat "${SOURCE}/${MARKER}") already in place"
  exit 0
fi

mkdir -p "${TARGET_ROOT}"
STAGE="$(mktemp -d "${TARGET_ROOT}/.smartir.new.XXXXXX")"
cp -a "${SOURCE}/." "${STAGE}/"
if [ -d "${TARGET}" ]; then
  OLD="${TARGET_ROOT}/.smartir.old.$$"
  mv "${TARGET}" "${OLD}"
  mv "${STAGE}" "${TARGET}"
  rm -rf "${OLD}"
else
  mv "${STAGE}" "${TARGET}"
fi
echo "[smartir] installed $(cat "${TARGET}/${MARKER}") — restart Home Assistant to load it"
