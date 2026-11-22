#!/usr/bin/env bash
# Write /share/<folder>/accesscontrollist (the ACL text from the options) and /share/<folder>/acl.conf (which points
# Mosquitto at it), atomically. The Mosquitto add-on reads /share/<folder>/*.conf when its customize option is active.
# An empty ACL is refused: with acl_file set, users not listed get no access at all.
set -euo pipefail

OPTIONS=/data/options.json
FOLDER="$(jq -r '.folder // ""' "${OPTIONS}")"
case "${FOLDER}" in
  '' | *[!a-z0-9_]*) echo "[mosquitto_acl] folder option is not a plain name — nothing written"; exit 1 ;;
esac
ACL="$(jq -r '.acl // ""' "${OPTIONS}")"
if [ -z "${ACL//[[:space:]]/}" ]; then
  echo "[mosquitto_acl] acl option is empty — nothing written"
  exit 1
fi

DIR="/share/${FOLDER}"
mkdir -p "${DIR}"
put() {
  local name="$1" tmp
  tmp="$(mktemp "${DIR}/.${name}.XXXXXX")"
  cat > "${tmp}"
  chmod 0644 "${tmp}"
  mv -f "${tmp}" "${DIR}/${name}"
}
printf '%s\n' "${ACL}" | put accesscontrollist
printf 'acl_file %s/accesscontrollist\n' "${DIR}" | put acl.conf
echo "[mosquitto_acl] wrote ${DIR}/acl.conf and ${DIR}/accesscontrollist — restart Mosquitto to apply"
