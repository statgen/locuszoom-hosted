FROM postgres:10.5

ARG UID
ARG GID

COPY ./compose/production/postgres/maintenance /usr/local/bin/maintenance
RUN chmod +x /usr/local/bin/maintenance/*
RUN \
  if [ -n "$UID" ] && [ -n "$GID" ]; then \
    chown -R $UID:$GID /usr/local/bin/maintenance/*; \
  fi
RUN mv /usr/local/bin/maintenance/* /usr/local/bin \
    && rmdir /usr/local/bin/maintenance
