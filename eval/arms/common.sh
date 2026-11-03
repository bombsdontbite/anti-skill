# Sourced by eval/<stick>/arms/setup_arms.sh: the run root outside the repository, the skill copy
# at a commit, one folder per agent under an opaque id, the queue and the run's README. The caller
# sets STICK and defines `skill_line <agent-dir>` and `brief_body <agent-dir> <case-dir>`; the skill
# arm's brief is the plain one with skill_line's line put first, and arms_finish checks that.
set -eu
EVAL=${${(%):-%x}:A:h:h}
REPO=$(git -C $EVAL rev-parse --show-toplevel)
SKILLS=(); SKILL_NAMES=()

arms_begin() {  # <run> <load-gate>
  run=${1:?usage: setup_arms.sh <run>}
  [[ $run =~ '^[A-Za-z0-9._-]+$' ]] || { echo "run name: letters, digits, . _ - only" >&2; exit 2; }
  ROOT=${ARMS_ROOT:-$HOME/aruns}/$run; H=$ROOT/.harness
  # Every agent sees this path in its brief.
  [[ ${ROOT:l} == *(skill|plain|${STICK:l})* ]] && {
    echo "$ROOT names an arm or the stick; pick a neutral run name or ARMS_ROOT" >&2; exit 2; }
  [[ -e $ROOT ]] && { echo "$ROOT exists; pick another run name" >&2; exit 2; }
  mkdir -p $H/skills $ROOT/.pristine
  cp $EVAL/arms/run_queue.sh $H/
  echo $STICK > $H/STICK
  echo ${MODEL:-claude-opus-5-5} > $H/MODEL
  echo ${MAX_USD:-4} > $H/MAX_USD
  GATE=${LOAD_MAX:-$2}; echo $GATE > $H/LOAD_MAX
  : > $H/queue
}

skill_at() {  # <ref> <name>: the skill folder at that commit, into .harness/skills/<name>
  local sha
  [[ ${ROOT:l} == *${2:l}* ]] && { echo "$ROOT names $2; remove it and pick another run name" >&2; exit 2; }
  sha=$(git -C $REPO rev-parse --verify "$1^{commit}")
  git -C $REPO archive $sha plugins/anti-skill/skills/$2 | tar -x -C $H/skills --strip-components=3
  [[ -f $H/skills/$2/SKILL.md ]] || { echo "no SKILL.md for $2 at $1" >&2; exit 2; }
  SKILLS+=("| $2 | \`$1\` | \`$sha\` |"); SKILL_NAMES+=($2)
}

agent_add() {  # <arm> <rep> <case> <source-case-dir> [<condition> <seed>]
  local arm=$1 rep=$2 c=$3 src=$4 id A s
  [[ -d $ROOT/.pristine/$c ]] || rsync -a --exclude __pycache__ --exclude .DS_Store $src/ $ROOT/.pristine/$c/
  # A random id, so neither the path nor the folder order tells an agent its arm.
  id=; while [[ -z $id || -e $ROOT/$id ]]; do id=$(od -An -N4 -tx1 /dev/urandom | tr -d ' \n'); done
  A=$ROOT/$id
  mkdir -p $A/tmp
  cp -R $ROOT/.pristine/$c $A/$c
  if [[ $arm == skill ]]; then for s in $SKILL_NAMES; do cp -R $H/skills/$s $A/$s; done; fi
  { [[ $arm == skill ]] && skill_line $A; brief_body $A $A/$c } > $A/BRIEF.txt
  echo "$id $c $arm $rep ${5:-} ${6:-}" >> $H/queue
}

briefs_check() {  # each skill brief is its pair's plain brief plus skill_line first, and no more
  local id c arm rep rest pid a p s bad=()
  while read -r id c arm rep rest; do
    [[ $arm == skill ]] || continue
    pid=$(awk -v c=$c -v r=$rep '$2 == c && $3 == "plain" && $4 == r {print $1; exit}' $H/queue)
    [[ -n $pid ]] || { bad+=("$id: no plain agent for $c r$rep"); continue; }
    a=$ROOT/$pid; p=$(<$a/BRIEF.txt); p=${p//$a/AGENT}
    a=$ROOT/$id; s=$(<$a/BRIEF.txt); s=${s//$a/AGENT}
    [[ $s == "$(skill_line AGENT)"$'\n'"$p" ]] || bad+=("$id/$pid: the briefs differ in more than the skill line")
    [[ -z $(find $ROOT/$pid -name SKILL.md -print -quit) ]] || bad+=("$pid: a plain agent has a SKILL.md")
    s=$(cd $a && find . -iname '*skill*' ! -name SKILL.md -print -quit)
    [[ -z $s ]] || bad+=("$id: $s names the skill beyond its pointer")
  done < $H/queue
  (( $#bad == 0 )) || { print -l "briefs check failed:" $bad >&2; exit 2; }
}

arms_finish() {  # <usd-low> <usd-high> <markdown notes>: per agent, so the estimate is the count times these
  local n head dirty lo hi cap
  briefs_check
  n=$(grep -c . $H/queue); cap=$(<$H/MAX_USD)
  lo=$(printf %.0f $(( n * $1 ))); hi=$(printf %.0f $(( n * $2 )))
  head=$(git -C $REPO rev-parse HEAD)
  dirty=$(git -C $REPO status --porcelain -- eval | head -1)
  cat > $H/README.md <<EOF
# $STICK arms run \`$run\`

Set up $(date '+%Y-%m-%d %H:%M') from harness commit \`$head\`${dirty:+ (eval/ had uncommitted changes)}.
Model \`$(<$H/MODEL)\`; load gate: 1-minute load ≤ $(<$H/LOAD_MAX) before each agent; cost cap
\$$cap per agent in both arms (\`--max-budget-usd\`).

| skill | ref | commit tested |
|---|---|---|
${(F)SKILLS}

The skill arm's copy is \`.harness/skills/\` here and \`<id>/<skill>/\` in each skill agent's
folder. Agents: $n (queue order below; \`.harness/queue\` maps each id to its arm). Estimated cost:
\$$lo–\$$hi at \$$1–$2 per agent, at most \$$(printf %.0f $(( n * cap ))) under the cap.

$3

## Briefs

The first plain agent's:

\`\`\`
$(<$ROOT/$(awk '$3 == "plain" {print $1; exit}' $H/queue)/BRIEF.txt)
\`\`\`

The skill arm's adds one line before it (checked for every pair at setup):

\`\`\`
$(head -1 $ROOT/$(awk '$3 == "skill" {print $1; exit}' $H/queue)/BRIEF.txt)
\`\`\`

## Queue

\`<id> <case> <arm> <repeat> [<condition> <seed>]\`

\`\`\`
$(<$H/queue)
\`\`\`
EOF
  echo "made $ROOT: $n agents, about \$$lo–\$$hi (cap \$$cap each)"
  echo "start it on a free machine: nohup zsh $H/run_queue.sh $ROOT > $H/nohup.out 2>&1 &"
}
