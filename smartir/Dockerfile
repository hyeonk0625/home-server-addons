ARG BUILD_FROM
FROM ${BUILD_FROM}

# SmartIR release pinned by version and checksum — bump both together with config.yaml `version`.
ARG SMARTIR_VERSION=1.18.1
ARG SMARTIR_SHA256=ae6628696f2b748939d0a8d12dec0dfceb4ddbe1d642e474f1746fb93b2850f0

RUN set -eux; \
    curl -fsSL -o /tmp/smartir.tar.gz \
      "https://github.com/smartHomeHub/SmartIR/archive/refs/tags/${SMARTIR_VERSION}.tar.gz"; \
    echo "${SMARTIR_SHA256}  /tmp/smartir.tar.gz" | sha256sum -c -; \
    mkdir -p /tmp/src /opt/smartir; \
    tar -xzf /tmp/smartir.tar.gz -C /tmp/src --strip-components=1; \
    cp -a /tmp/src/custom_components/smartir /opt/smartir/smartir; \
    echo "${SMARTIR_VERSION}" > /opt/smartir/smartir/.installed_by_addon; \
    rm -rf /tmp/src /tmp/smartir.tar.gz

COPY run.sh /run.sh
RUN chmod a+x /run.sh
CMD [ "/run.sh" ]
