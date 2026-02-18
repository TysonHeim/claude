#!/bin/bash
# Format usage stats for status line display
# Aggregates across all active parallel sessions
# Output: "A:3(exp,cr) S:2(design,tdd)" or "A:0 S:0"

STATE_DIR="$HOME/.claude/sessions"

# If no sessions directory, show zeros
if [ ! -d "$STATE_DIR" ]; then
    echo "A:0 S:0"
    exit 0
fi

# Aggregate all active session files
agents=0
skills=0
all_agent_types=""
all_skill_names=""

for f in "$STATE_DIR"/session-*.json; do
    [ -f "$f" ] || continue
    agents=$((agents + $(jq -r '.agents // 0' "$f")))
    skills=$((skills + $(jq -r '.skills // 0' "$f")))

    # Collect agent/skill names
    file_agents=$(jq -r '.agent_types | keys | join(",")' "$f" 2>/dev/null)
    file_skills=$(jq -r '.skill_names | keys | join(",")' "$f" 2>/dev/null)
    [ -n "$file_agents" ] && all_agent_types="${all_agent_types},${file_agents}"
    [ -n "$file_skills" ] && all_skill_names="${all_skill_names},${file_skills}"
done

# Deduplicate names
agent_list=$(echo "$all_agent_types" | tr ',' '\n' | sort -u | grep -v '^$' | tr '\n' ',' | sed 's/,$//')
skill_list=$(echo "$all_skill_names" | tr ',' '\n' | sort -u | grep -v '^$' | tr '\n' ',' | sed 's/,$//')

# Customize abbreviation mappings for your project
# Add your own agent/skill abbreviations here
abbrev() {
    echo "$1" | sed \
        -e 's/skills-manager/sm/g' \
        -e 's/Explore/exp/g' \
        -e 's/code-reviewer/cr/g' \
        -e 's/unknown/unk/g'
}

agent_abbr=$(abbrev "$agent_list")
skill_abbr=$(abbrev "$skill_list")

if [ "$agents" -gt 0 ] && [ -n "$agent_abbr" ]; then
    agent_str="A:$agents($agent_abbr)"
else
    agent_str="A:$agents"
fi

if [ "$skills" -gt 0 ] && [ -n "$skill_abbr" ]; then
    skill_str="S:$skills($skill_abbr)"
else
    skill_str="S:$skills"
fi

echo "$agent_str $skill_str"
