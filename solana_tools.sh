#!/usr/bin/env bash

VERSION=v1.9.9

if [ ! -d .solana_tools ]; then
  mkdir -p .solana_tools
  pushd .solana_tools

  wget -O solana_tools.tar.bz2 https://github.com/solana-labs/solana/releases/download/${VERSION}/solana-release-x86_64-unknown-linux-gnu.tar.bz2
  tar -xf solana_tools.tar.bz2 --strip-components=1
fi

export PATH="${PWD}/bin:$PATH"

$SHELL --rcfile <(
  echo "PS1='\e[01;35m(Solana ${VERSION}):\e[m \e[01;34m\w\e[m\$ '"
  echo "alias make_bpf='V=1 make -C ./dapps '"
  ) -i
