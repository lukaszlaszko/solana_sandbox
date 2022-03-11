#!/usr/bin/env bash

VERSION=v1.9.9

if [ ! -d .solana_tools ]; then
  mkdir -p .solana_tools
  pushd .solana_tools

  wget -O solana_tools.tar.bz2 https://github.com/solana-labs/solana/releases/download/${VERSION}/solana-release-x86_64-unknown-linux-gnu.tar.bz2
  tar -xf solana_tools.tar.bz2 --strip-components=1

  popd
fi

export PATH="${PWD}/.solana_tools/bin:$PATH"

pyfiglet "Solana tools"
printf "\033[01;30mstart_validator\033[0m to start Solana test validator\n"
printf "\033[01;30mmake_bpf <dapp>\033[0m to build dapp\n"
printf "\033[01;reformat\033[0m to reformat C/C++ files\n"
printf "\n"

$SHELL --rcfile <(
  echo "PS1='\e[01;35m(Solana ${VERSION}):\e[m \e[01;34m\w\e[m\$ '"
  echo "alias make_bpf='V=1 make -C ./dapps '"
  echo "alias start_validator='solana-test-validator --ledger=.solana_ledger'"
  echo "alias reformat='find . \( -iname \*.c -o -iname \*.cc -o -iname \*.h \) -exec clang-format -i {} \; '") -i
