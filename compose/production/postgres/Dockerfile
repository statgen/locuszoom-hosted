FROM postgres:10.5

# Optional arguments, if specified then maintenance scripts will be set as owned
# by the UID and GID given.
# This is useful if you are running postgres as a different user, usually via your
# compose file `user:` option.
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
