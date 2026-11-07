ARG BUILD_FROM
FROM ${BUILD_FROM}

# Each integration is pinned by commit and archive checksum — bump both together with config.yaml `version`.
# The list (domain, repository, commit) is chosen by the home server's HA Manager area (HAM-261107-63).
ARG WINIX_COMMIT=9653e5040bc36e9e884f678de25c6324f4042a13
ARG WINIX_SHA256=5f7efa43f432f4abc75b1c82ca86d2298320929b0b3caf73c6d04dd9ba9dfd4a
ARG SONOFF_COMMIT=3f329db36477fcc6ebc148db7b35e1187c20097d
ARG SONOFF_SHA256=08adf7a41e127cfc91f9c17ac73ba28c2351f5e271a08e269b6a99e8bcd26624

RUN set -eux; \
    fetch() { \
      domain="$1"; repo="$2"; commit="$3"; sum="$4"; \
      curl -fsSL -o "/tmp/${domain}.tar.gz" "https://github.com/${repo}/archive/${commit}.tar.gz"; \
      echo "${sum}  /tmp/${domain}.tar.gz" | sha256sum -c -; \
      mkdir -p "/tmp/src-${domain}" /opt/integrations; \
      tar -xzf "/tmp/${domain}.tar.gz" -C "/tmp/src-${domain}" --strip-components=1; \
      cp -a "/tmp/src-${domain}/custom_components/${domain}" "/opt/integrations/${domain}"; \
      echo "${commit}" > "/opt/integrations/${domain}/.installed_by_addon"; \
      rm -rf "/tmp/src-${domain}" "/tmp/${domain}.tar.gz"; \
    }; \
    fetch winix iprak/winix "${WINIX_COMMIT}" "${WINIX_SHA256}"; \
    fetch sonoff AlexxIT/SonoffLAN "${SONOFF_COMMIT}" "${SONOFF_SHA256}"

COPY run.sh /run.sh
RUN chmod a+x /run.sh
CMD [ "/run.sh" ]
