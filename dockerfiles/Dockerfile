FROM mambaorg/micromamba:1.4.9-bullseye-slim AS micromamba

# The micromamba image is referenced in a multi-stage build.
# Note that around 90% of the content of this image is actually
# for micromamba users, permissions, dependencies, and SSH.
# The Autosubmit portion is rather small, being mainly install
# Autosubmit with pip, and run `autosubmit configure` and then
# `autosubmit install`. It would be possible to create another
# image autosubmit-base, for example, with the users, permissions,
# dependencies, and SSH. Which would tremendously reduce this.

FROM debian:bullseye-slim

ARG AUTOSUBMIT_ROOT_DIR=/app/autosubmit/

USER root

# micromamba docs, https://micromamba-docker.readthedocs.io/en/latest/advanced_usage.html#adding-micromamba-to-an-existing-docker-image

# if your image defaults to a non-root user, then you may want to make the
# next 3 ARG commands match the values in your image. You can get the values
# by running: docker run --rm -it my/image id -a
ARG MAMBA_USER=mamba
ARG MAMBA_USER_ID=1000
ARG MAMBA_USER_GID=1000
ENV MAMBA_USER=$MAMBA_USER
ENV MAMBA_ROOT_PREFIX="/opt/conda"
ENV MAMBA_EXE="/bin/micromamba"

COPY --from=micromamba "$MAMBA_EXE" "$MAMBA_EXE"
COPY --from=micromamba /usr/local/bin/_activate_current_env.sh /usr/local/bin/_activate_current_env.sh
COPY --from=micromamba /usr/local/bin/_dockerfile_shell.sh /usr/local/bin/_dockerfile_shell.sh
COPY --from=micromamba /usr/local/bin/_entrypoint.sh /usr/local/bin/_entrypoint.sh
COPY --from=micromamba /usr/local/bin/_dockerfile_initialize_user_accounts.sh /usr/local/bin/_dockerfile_initialize_user_accounts.sh
COPY --from=micromamba /usr/local/bin/_dockerfile_setup_root_prefix.sh /usr/local/bin/_dockerfile_setup_root_prefix.sh

RUN /usr/local/bin/_dockerfile_initialize_user_accounts.sh && \
    /usr/local/bin/_dockerfile_setup_root_prefix.sh

USER $MAMBA_USER

SHELL ["/usr/local/bin/_dockerfile_shell.sh"]

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh"]
# Optional: if you want to customize the ENTRYPOINT and have a conda
# environment activated, then do this:
# ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "my_entrypoint_program"]

# end micromamba

# micromamba docs, https://micromamba-docker.readthedocs.io/en/latest/advanced_usage.html#changing-the-user-id-or-name

ARG NEW_MAMBA_USER=autosubmit
ARG NEW_MAMBA_USER_ID=1000
ARG NEW_MAMBA_USER_GID=1000
USER root

RUN if grep -q '^ID=alpine$' /etc/os-release; then \
      # alpine does not have usermod/groupmod
      apk add --no-cache --virtual temp-packages shadow=4.13-r0; \
    fi && \
    usermod "--login=${NEW_MAMBA_USER}" "--home=/home/${NEW_MAMBA_USER}" \
      --move-home "-u ${NEW_MAMBA_USER_ID}" "${MAMBA_USER}" && \
    groupmod "--new-name=${NEW_MAMBA_USER}" \
      "-g ${NEW_MAMBA_USER_GID}" "${MAMBA_USER}" && \
    if grep -q '^ID=alpine$' /etc/os-release; then \
      # remove the packages that were only needed for usermod/groupmod
      apk del temp-packages; \
    fi && \
    # Update the expected value of MAMBA_USER for the
    # _entrypoint.sh consistency check.
    echo "${NEW_MAMBA_USER}" > "/etc/arg_mamba_user" && \
    :
ENV MAMBA_USER=$NEW_MAMBA_USER
USER $MAMBA_USER

# end micromamba

WORKDIR "${AUTOSUBMIT_ROOT_DIR}"

ENV ENV_NAME=base
ENV PATH "$MAMBA_ROOT_PREFIX/bin:/usr/bin:/usr/local/bin:$PATH"

# The directories the container will use for Autosubmit files.
USER root
RUN mkdir -pv "${AUTOSUBMIT_ROOT_DIR}/logs" && \
    mkdir -pv "${AUTOSUBMIT_ROOT_DIR}/metadata" && \
    chown -R "${MAMBA_USER}:${MAMBA_USER}" "${AUTOSUBMIT_ROOT_DIR}"

# update-ca-certificates is for: libmamba No CA certificates found on system.
# openssh-server is for: Autosubmit platforms.
# git is for: Autosubmit Git projects.
# bash, curl, dialog, graphviz, python3-tk, sqlite3 are for: Autosubmit dependencies listed at readthedocs.
# less, vim, iputils-ping, net-tools are for: convenience.
# TODO: add something like xpdf=3.04+git20210103-3 if GUI/X is needed.
RUN apt update && \
    apt install -y \
      bash=5.1-2+deb11u1 \
      ca-certificates=20210119 \
      curl=7.74.0-1.3+deb11u7 \
      desktop-file-utils=0.26-1 \
      dialog=1.3-20201126-1 \
      graphviz=2.42.2-5 \
      iputils-ping=3:20210202-1 \
      less=551-2 \
      net-tools=1.60+git20181103.0eebece-1 \
      openssh-server=1:8.4p1-5+deb11u1 \
      python3-tk=3.9.2-1 \
      sqlite3=3.34.1-3 \
      sudo=1.9.5p2-3+deb11u1 \
      vim=2:8.2.2434-3+deb11u1 \
      xdg-utils=1.1.3-4.1 && \
    update-ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER $MAMBA_USER

# Install and configure Autosubmit.

# Install Python.
RUN micromamba install --yes --name base --channel conda-forge \
      git=2.41.0 \
      python=3.9.16 && \
    micromamba clean --all --yes && \
    /usr/local/bin/_activate_current_env.sh

# Install Autosubmit.
RUN pip install autosubmit==4.0.84

# Configure Autosubmit.
RUN autosubmit configure \
      -db "${AUTOSUBMIT_ROOT_DIR}/database/" \
      -dbf autosubmit.db \
      -lr "${AUTOSUBMIT_ROOT_DIR}/experiments/" && \
    autosubmit install

# SSH (for Autosubmit local platform.)
USER root

RUN chown -R "${MAMBA_USER}:${MAMBA_USER}" "/home/${MAMBA_USER}/" && \
    chmod 0755 "/home/${MAMBA_USER}/" && \
    mkdir -pv /var/run/sshd && \
    mkdir -pv "/home/$MAMBA_USER/.ssh" && \
    chmod 0700 "/home/$MAMBA_USER/.ssh" && \
    touch "/home/$MAMBA_USER/.ssh/authorized_keys" && \
    chmod 600 "/home/$MAMBA_USER/.ssh/authorized_keys" && \
    chown -R "${MAMBA_USER}:${MAMBA_USER}" "/home/$MAMBA_USER/.ssh" && \
    usermod -a -G sudo "${MAMBA_USER}" && \
    sed -i "s/^%sudo.*$/%sudo ALL=(ALL:ALL) NOPASSWD:ALL/g" /etc/sudoers && \
    sed -i 's/#\?\(PasswordAuthentication\s*\).*$/\1 no/g' /etc/ssh/sshd_config && \
    sed -i 's/#\?\(SyslogFacility.*\)$/\1/g' /etc/ssh/sshd_config && \
    sed -i 's/#\?\(LogLevel\).*$/\1 VERBOSE/g' /etc/ssh/sshd_config && \
    sed -i 's/#\?.*StrictHostKeyChecking.*$/StrictHostKeyChecking accept-new/g' /etc/ssh/ssh_config && \
    env | egrep -v "^(HOME=|USER=|MAIL=|LC_ALL=|LS_COLORS=|LANG=|HOSTNAME=|PWD=|TERM=|SHLVL=|LANGUAGE=|_=)" >> /etc/environment

# TODO: For PDF and GUI/X support, we could use something similar to:
#
# COPY <<EOF /usr/share/applications/defaults.list
# application/pdf=xpdf.desktop
# EOF
#
# RUN update-mime-database /usr/share/mime

# entrypoint

COPY <<EOF /usr/local/bin/entrypoint.sh
#!/bin/bash
sudo service ssh restart
exec "\$@"
EOF

USER $MAMBA_USER

EXPOSE 22

LABEL maintainer="kinow"

ENTRYPOINT ["/bin/bash", "entrypoint.sh"]
CMD ["autosubmit"]
