ARG BUILD_FROM
FROM ${BUILD_FROM}

# The ACL text comes from the add-on options (set by the home server); this image only writes it.
COPY run.sh /run.sh
RUN chmod a+x /run.sh
CMD [ "/run.sh" ]
