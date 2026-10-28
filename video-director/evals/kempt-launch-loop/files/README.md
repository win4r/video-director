# kempt

Format messy JSON. Fast.

kempt reformats JSON files of any size with stable key order and consistent indentation.

## Install

    brew install kempt

## Usage

    kempt messy.json > clean.json
    kempt --check *.json   # exits 1 if anything would change

## Facts

- Formats a 1 GB JSON file in 2.1 s on an M3 MacBook Air (bench/README.md, run 2026-09-30)
- Single static binary, zero runtime dependencies
- MIT licensed
- v1.0 releases 2026-10-28

## Brand

- Colours: ink #0E1116, paper #F4F1EA, accent #FF5A36
- Fonts: JetBrains Mono for code, Inter for text
