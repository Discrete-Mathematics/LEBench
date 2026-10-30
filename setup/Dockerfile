# Userspace toolchain for building and launching LEBench.
# The suite measures the kernel that is actually running. Inside this
# image that is the host kernel, so the image pins the compiler and
# Python used to build OS_Eval. Comparing kernel versions still requires
# booting those kernels; a container cannot do that.
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        python3 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/LEBench
COPY . .

# OS_Eval joins this value directly onto relative paths, so the
# trailing slash is required.
ENV LEBENCH_DIR=/opt/LEBench/

CMD ["python3", "scripts/run_current_kernel.py", "--runs", "3"]
