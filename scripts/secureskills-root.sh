#!/usr/bin/env bash

secureskills_project_root() {
    git -C "${1:-.}" rev-parse --show-toplevel 2>/dev/null || printf '%s\n' "${1:-$(pwd)}"
}

secureskills_git_common_dir() {
    local project_root="${1:-.}"
    git -C "$project_root" rev-parse --git-common-dir --path-format=absolute 2>/dev/null || true
}

secureskills_storage_dir() {
    local project_root="${1:-.}"
    local common_dir
    common_dir="$(secureskills_git_common_dir "$project_root")"
    if [ -n "$common_dir" ]; then
        printf '%s\n' "$common_dir/flux-secureskills"
    else
        printf '%s\n' "$project_root/.secureskills"
    fi
}

secureskills_manifest_path() {
    local project_root="${1:-.}"
    local skill_name="${2:-}"
    printf '%s\n' "$(secureskills_storage_dir "$project_root")/store/$skill_name/manifest.json"
}

secureskills_ignore_in_git() {
    local project_root="${1:-.}"
    local common_dir
    local exclude_file

    common_dir="$(secureskills_git_common_dir "$project_root")"
    if [ -z "$common_dir" ]; then
        return 0
    fi

    exclude_file="$common_dir/info/exclude"
    mkdir -p "$(dirname "$exclude_file")"
    touch "$exclude_file"

    if ! grep -Fqx '.secureskills' "$exclude_file" 2>/dev/null; then
        printf '%s\n' '.secureskills' >> "$exclude_file"
    fi
}

ensure_secureskills_root() {
    local project_root="${1:-.}"
    local mode="${2:-always}"
    local link_path storage_dir

    project_root="$(secureskills_project_root "$project_root")"
    link_path="$project_root/.secureskills"
    storage_dir="$(secureskills_storage_dir "$project_root")"

    if [ "$storage_dir" = "$link_path" ]; then
        if [ "$mode" = "always" ]; then
            mkdir -p "$storage_dir"
        fi
        return 0
    fi

    if [ "$mode" = "if-present" ] && [ ! -L "$link_path" ] && [ ! -e "$link_path" ] && [ ! -e "$storage_dir" ]; then
        return 0
    fi

    mkdir -p "$(dirname "$storage_dir")"

    if [ -L "$link_path" ]; then
        rm -f "$link_path"
    elif [ -d "$link_path" ]; then
        if [ -e "$storage_dir" ] && [ "$(find "$storage_dir" -mindepth 1 -maxdepth 1 2>/dev/null | head -n 1)" ]; then
            echo "Flux secure skills migration blocked: both '$link_path' and '$storage_dir' contain state." >&2
            return 1
        fi

        if [ -e "$storage_dir" ]; then
            rmdir "$storage_dir" 2>/dev/null || true
        fi

        if [ ! -e "$storage_dir" ]; then
            mv "$link_path" "$storage_dir"
        fi
    elif [ -e "$link_path" ]; then
        echo "Flux secure skills migration blocked: '$link_path' exists but is not a directory or symlink." >&2
        return 1
    fi

    mkdir -p "$storage_dir"
    ln -sfn "$storage_dir" "$link_path"
    secureskills_ignore_in_git "$project_root"
}
