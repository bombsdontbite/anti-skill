#!/bin/sh
# UserPromptSubmit hook: one routing line when the prompt mentions speed or a score.
# Local only: reads the hook's JSON on stdin, writes nothing but stdout, exits 0 on any error.
# One word per line, because an alternation over one long line of pasted code takes seconds in
# BSD grep.
LC_ALL=C
export LC_ALL
words='^(faster|speed|speedup|benchmark.*|scor(e|es|ed|ing)|optimi[sz].*|slow.*|profil(e|er|es|ing))$'
# Only a JSON object with a string "prompt". The path fields may name a folder such as "bench";
# the other fields hold no such word.
sed -E -e '/"prompt"[[:space:]]*:[[:space:]]*"/!d' -e '/}[[:space:]]*$/!d' \
    -e 's/"transcript_path"[[:space:]]*:[[:space:]]*"[^"]*"//' -e 's/"cwd"[[:space:]]*:[[:space:]]*"[^"]*"//' \
    -e 's/\\[nrt]/ /g' \
  | tr -cs 'A-Za-z' '\n' \
  | grep -qiE "$words" \
  && echo 'anti-skill: this request mentions speed or a score. If it asks to change code to run faster or score higher, load evolve when a benchmark, test suite or metric already measures it, or profile-first when the code is slow and nothing measures it yet; otherwise ignore this line.'
exit 0
