# syntax=docker/dockerfile:1

# =============================================================================
# Soaratorium — Phase 1 analysis environment
# =============================================================================
# Ghidra + Switch/NSO tooling live here so the whole pipeline is reproducible
# and no host Java install is required (the JDK lives in this image).
#
# The *build* toolchain (cross-compiler, SDK) is deliberately NOT pinned here:
# it depends on the compiler identified against the real NSO (see AGENTS.md),
# and lands in Phase 2. Do not add it until then.
# =============================================================================

ARG BASE_IMAGE=ubuntu:24.04
FROM ${BASE_IMAGE}

# ---------------------------------------------------------------------------
# Build arguments — pin these in devcontainer.json or a `docker build` command.
# ---------------------------------------------------------------------------
# Treat GHIDRA_VERSION as PINNED. Only change it deliberately (see AGENTS.md).
# NOTE: pinned to 12.1.2 to match the prebuilt Switch-Loader extension
# (adubbz/ghidra-switch-loader) compiled against this exact version.
ARG GHIDRA_VERSION=12.1.2
# Exact download URL. The `_PUBLIC_YYYYMMDD` suffix is the release date and
# must match the GitHub releases page:
#   https://github.com/NationalSecurityAgency/ghidra/releases
ARG GHIDRA_URL=https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_${GHIDRA_VERSION}_build/ghidra_${GHIDRA_VERSION}_PUBLIC_20260605.zip
# Release SHA-256 (pinned for reproducible builds; verified against /tmp/ghidra.zip).
ARG GHIDRA_SHA256=b62e81a0390618466c019c60d8c2f796ced2509c4c1aea4a37644a77272cf99d

# Switch/NSO loader extension (analysis phase). Prebuilt by upstream CI against
# Ghidra 12.1.2; release tag is `<ver>-<commit>-Ghidra_<ver>` (auto-published per
# commit, so this exact tag MUST be pinned). See:
#   https://github.com/adubbz/ghidra-switch-loader
ARG SWITCH_LOADER_VERSION=1.6.1-c600d05-Ghidra_12.1.2
ARG SWITCH_LOADER_SHA256=0bc6374c11cb7a1275a0eda22184b9b2efe5a9a7e415cc29361c334966c1f477

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64 \
    GHIDRA_HOME=/opt/ghidra

# ---------------------------------------------------------------------------
# System dependencies
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        unzip \
        # Java 21 JDK — REQUIRED by Ghidra. The PUBLIC release zip does NOT ship
        # a JDK, and a plain JRE is rejected (Ghidra compiles scripts at
        # runtime). application.properties: application.java.min=21, no max.
        # Use openjdk-21-jdk-headless instead to drop AWT/X11 if GUI is never
        # needed (headless Ghidra still works either way).
        openjdk-21-jdk \
        # Optional GUI stack (noVNC over a browser, cross-platform):
        xvfb \
        x11vnc \
        novnc \
        websockify \
        # X11/GL libs required by Ghidra's AWT/Swing (GUI + some JDK init):
        libx11-6 \
        libxext6 \
        libxi6 \
        libxrender1 \
        libxtst6 \
        libxrandr2 \
        libfreetype6 \
        fontconfig \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Ghidra
# ---------------------------------------------------------------------------
# The Ghidra PUBLIC release zip does NOT bundle a JDK, so Java 21 is installed
# above (pinned via JAVA_HOME). The launcher auto-detects it from JAVA_HOME/PATH.
RUN set -eux; \
    curl -fL --retry 3 -o /tmp/ghidra.zip "${GHIDRA_URL}"; \
    if [ -n "${GHIDRA_SHA256}" ]; then \
        echo "${GHIDRA_SHA256}  /tmp/ghidra.zip" | sha256sum -c -; \
    fi; \
    unzip -q /tmp/ghidra.zip -d /opt; \
    rm /tmp/ghidra.zip; \
    mv "/opt/ghidra_${GHIDRA_VERSION}_PUBLIC" "${GHIDRA_HOME}"

# ---------------------------------------------------------------------------
# NSO / Switch loader extension
# ---------------------------------------------------------------------------
# adubbz/ghidra-switch-loader: loads NSO0/NRO0/KIP1, auto-detects AArch32 vs
# AArch64 (critical for confirming the MHGU NSO architecture). Ghidra loads any
# extension placed under Ghidra/Extensions on next launch (headless or GUI).
RUN set -eux; \
    curl -fL --retry 3 -o /tmp/switch-loader.zip \
      "https://github.com/Adubbz/Ghidra-Switch-Loader/releases/download/${SWITCH_LOADER_VERSION}/SwitchLoader-${SWITCH_LOADER_VERSION}.zip"; \
    if [ -n "${SWITCH_LOADER_SHA256}" ]; then \
        echo "${SWITCH_LOADER_SHA256}  /tmp/switch-loader.zip" | sha256sum -c -; \
    fi; \
    unzip -q /tmp/switch-loader.zip -d "${GHIDRA_HOME}/Ghidra/Extensions"; \
    rm /tmp/switch-loader.zip

# ---------------------------------------------------------------------------
# TODO (Phase 3): Python decomp tooling
# ---------------------------------------------------------------------------
# Deliberately NOT installed yet. The analysis + build tooling (reccmp, splat,
# asm-differ, ...) isn't needed until we start translating functions, and its
# package names/versions are unverified. Add Python + a pinned venv here once
# the toolchain is confirmed against a real function (see AGENTS.md).

# ---------------------------------------------------------------------------
# Non-root user
# ---------------------------------------------------------------------------
# The workspace is a host bind mount, so anything created as root would be
# root-owned on the host and unusable by the contributor. The Ubuntu base image
# already ships a default non-root account, `ubuntu` (UID/GID 1000), so we reuse
# it rather than creating one; it is selected via `remoteUser` in
# devcontainer.json. On Linux the dev-container tooling then remaps its UID/GID
# to the host user's (updateRemoteUserUID, on by default), so files written into
# the bind-mounted workspace are owned by the host user instead of root.
# `sudo` is deliberately not installed: every dependency is baked into this
# image, so the contributor never needs to install packages at runtime.
#
# NOTE: this relies on the base image providing the `ubuntu` account. If
# BASE_IMAGE is ever swapped for a distro without it, add an explicit
# `groupadd`/`useradd` here (mind colliding with UID/GID 1000).

# ---------------------------------------------------------------------------
# Entry point / workspace
# ---------------------------------------------------------------------------
# Select the non-root user before WORKDIR so /workspace is created writable by
# the contributor when the image is run without a bind mount.
USER ubuntu
WORKDIR /workspace
CMD ["/bin/bash"]
