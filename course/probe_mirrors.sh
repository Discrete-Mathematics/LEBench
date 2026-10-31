#!/bin/bash
base='default_ubuntu_kernels/v4.0.5/linux-image-4.0.5-040005-generic_4.0.5-040005.201506061639_amd64.deb'
urls=(
  "https://github.com/LinuxPerfStudy/ExperimentSetup/raw/master/${base}"
  "https://raw.githubusercontent.com/LinuxPerfStudy/ExperimentSetup/master/${base}"
  "https://ghfast.top/https://github.com/LinuxPerfStudy/ExperimentSetup/raw/master/${base}"
  "https://mirror.ghproxy.com/https://github.com/LinuxPerfStudy/ExperimentSetup/raw/master/${base}"
  "https://gitclone.com/github.com/LinuxPerfStudy/ExperimentSetup/raw/master/${base}"
)
for u in "${urls[@]}"; do
  echo "URL $u"
  wget -S --spider --timeout=20 "$u" 2>&1 | head -n 15
  echo "----"
done
