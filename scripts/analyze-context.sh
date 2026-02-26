#!/bin/bash
# Flux Improve - Context Analysis Script
# Analyzes user's environment for workflow optimization recommendations

set -e

# Output JSON
output_json() {
    echo "$1"
}

# Detect repo type based on config files
detect_repo_type() {
    if [ -f "package.json" ]; then
        echo "javascript"
    elif [ -f "pyproject.toml" ] || [ -f "setup.py" ] || [ -f "requirements.txt" ]; then
        echo "python"
    elif [ -f "Cargo.toml" ]; then
        echo "rust"
    elif [ -f "go.mod" ]; then
        echo "go"
    elif [ -f "Gemfile" ]; then
        echo "ruby"
    else
        echo "unknown"
    fi
}

# Detect frameworks from package.json
detect_js_frameworks() {
    if [ ! -f "package.json" ]; then
        echo "[]"
        return
    fi
    
    frameworks=""
    
    # Check dependencies and devDependencies
    deps=$(cat package.json | jq -r '(.dependencies // {}) + (.devDependencies // {}) | keys[]' 2>/dev/null || echo "")
    
    for dep in $deps; do
        case "$dep" in
            next) frameworks="${frameworks}\"next\"," ;;
            react) frameworks="${frameworks}\"react\"," ;;
            vue) frameworks="${frameworks}\"vue\"," ;;
            svelte) frameworks="${frameworks}\"svelte\"," ;;
            express) frameworks="${frameworks}\"express\"," ;;
            fastify) frameworks="${frameworks}\"fastify\"," ;;
            convex) frameworks="${frameworks}\"convex\"," ;;
            prisma) frameworks="${frameworks}\"prisma\"," ;;
            drizzle-orm) frameworks="${frameworks}\"drizzle\"," ;;
            tailwindcss) frameworks="${frameworks}\"tailwind\"," ;;
            typescript) frameworks="${frameworks}\"typescript\"," ;;
        esac
    done
    
    # Remove trailing comma and wrap in array
    frameworks=$(echo "$frameworks" | sed 's/,$//')
    echo "[${frameworks}]"
}

# Detect Python frameworks
detect_python_frameworks() {
    frameworks=""
    
    if [ -f "pyproject.toml" ]; then
        content=$(cat pyproject.toml 2>/dev/null || echo "")
        [[ "$content" == *"fastapi"* ]] && frameworks="${frameworks}\"fastapi\","
        [[ "$content" == *"django"* ]] && frameworks="${frameworks}\"django\","
        [[ "$content" == *"flask"* ]] && frameworks="${frameworks}\"flask\","
        [[ "$content" == *"pytest"* ]] && frameworks="${frameworks}\"pytest\","
    fi
    
    if [ -f "requirements.txt" ]; then
        content=$(cat requirements.txt 2>/dev/null || echo "")
        [[ "$content" == *"fastapi"* ]] && frameworks="${frameworks}\"fastapi\","
        [[ "$content" == *"django"* ]] && frameworks="${frameworks}\"django\","
        [[ "$content" == *"flask"* ]] && frameworks="${frameworks}\"flask\","
    fi
    
    frameworks=$(echo "$frameworks" | sed 's/,$//')
    echo "[${frameworks}]"
}

# Check for test setup
has_tests() {
    if [ -d "test" ] || [ -d "tests" ] || [ -d "__tests__" ] || [ -d "spec" ]; then
        echo "true"
        return
    fi
    
    if [ -f "package.json" ]; then
        has_test_script=$(cat package.json | jq -r '.scripts.test // empty' 2>/dev/null)
        if [ -n "$has_test_script" ] && [ "$has_test_script" != "null" ]; then
            echo "true"
            return
        fi
    fi
    
    if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
        echo "true"
        return
    fi
    
    echo "false"
}

# Check for CI setup
has_ci() {
    if [ -d ".github/workflows" ] || [ -f ".gitlab-ci.yml" ] || [ -f ".circleci/config.yml" ] || [ -f "Jenkinsfile" ]; then
        echo "true"
    else
        echo "false"
    fi
}

# Check for linter
has_linter() {
    if [ -f ".eslintrc" ] || [ -f ".eslintrc.js" ] || [ -f ".eslintrc.json" ] || [ -f "eslint.config.js" ] || [ -f "biome.json" ] || [ -f "oxlint.json" ]; then
        echo "true"
    else
        echo "false"
    fi
}

# Check for formatter
has_formatter() {
    if [ -f ".prettierrc" ] || [ -f ".prettierrc.js" ] || [ -f ".prettierrc.json" ] || [ -f "biome.json" ]; then
        echo "true"
    else
        echo "false"
    fi
}

# Check for pre-commit hooks
has_hooks() {
    if [ -f "lefthook.yml" ] || [ -f ".husky/_/husky.sh" ] || [ -d ".husky" ] || [ -f ".pre-commit-config.yaml" ]; then
        echo "true"
    else
        echo "false"
    fi
}

# Get installed MCPs from config files
get_mcps() {
    local mcps="[]"
    
    # Check ~/.mcp.json (global)
    if [ -f "$HOME/.mcp.json" ]; then
        mcps=$(cat "$HOME/.mcp.json" | jq -r '.mcpServers // {} | keys' 2>/dev/null || echo "[]")
    fi
    
    # Check .mcp.json (local project)
    if [ -f ".mcp.json" ]; then
        local_mcps=$(cat ".mcp.json" | jq -r '.mcpServers // {} | keys' 2>/dev/null || echo "[]")
        # Merge arrays
        mcps=$(echo "$mcps $local_mcps" | jq -s 'add | unique' 2>/dev/null || echo "$mcps")
    fi
    
    # Check ~/.claude/settings.json (alternate location)
    if [ -f "$HOME/.claude/settings.json" ]; then
        alt_mcps=$(cat "$HOME/.claude/settings.json" | jq -r '.mcpServers // {} | keys' 2>/dev/null || echo "[]")
        if [ "$alt_mcps" != "[]" ] && [ "$alt_mcps" != "null" ]; then
            mcps=$(echo "$mcps $alt_mcps" | jq -s 'add | unique' 2>/dev/null || echo "$mcps")
        fi
    fi
    
    echo "$mcps"
}

# Get installed plugins
get_plugins() {
    local plugin_cache="$HOME/.claude/plugins/cache"
    
    if [ ! -d "$plugin_cache" ]; then
        echo "[]"
        return
    fi
    
    plugins=$(ls "$plugin_cache" 2>/dev/null | jq -R -s -c 'split("\n") | map(select(length > 0))' || echo "[]")
    echo "$plugins"
}

# Check for AGENTS.md or CLAUDE.md
has_agent_docs() {
    if [ -f "AGENTS.md" ] || [ -f "CLAUDE.md" ] || [ -f ".claude/AGENTS.md" ]; then
        echo "true"
    else
        echo "false"
    fi
}

# Main analysis
main() {
    local include_sessions="${1:-false}"
    
    repo_name=$(basename "$(pwd)")
    repo_type=$(detect_repo_type)
    
    if [ "$repo_type" = "javascript" ]; then
        frameworks=$(detect_js_frameworks)
    elif [ "$repo_type" = "python" ]; then
        frameworks=$(detect_python_frameworks)
    else
        frameworks="[]"
    fi
    
    # Get session insights if requested
    local session_insights='{"enabled":false,"reason":"Not requested"}'
    if [ "$include_sessions" = "true" ]; then
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        if [ -x "$SCRIPT_DIR/analyze-sessions.sh" ]; then
            session_insights=$("$SCRIPT_DIR/analyze-sessions.sh" 2>/dev/null || echo '{"enabled":false,"reason":"Analysis failed"}')
        fi
    fi
    
    cat <<EOF
{
  "repo": {
    "name": "$repo_name",
    "type": "$repo_type",
    "frameworks": $frameworks,
    "has_tests": $(has_tests),
    "has_ci": $(has_ci),
    "has_linter": $(has_linter),
    "has_formatter": $(has_formatter),
    "has_hooks": $(has_hooks),
    "has_agent_docs": $(has_agent_docs)
  },
  "installed": {
    "mcps": $(get_mcps),
    "plugins": $(get_plugins)
  },
  "session_insights": $session_insights
}
EOF
}

# Parse arguments
INCLUDE_SESSIONS="false"
for arg in "$@"; do
    case "$arg" in
        --include-sessions) INCLUDE_SESSIONS="true" ;;
    esac
done

main "$INCLUDE_SESSIONS"
