cwlVersion: v1.2

$graph:
- class: CommandLineTool
  id: sync_git_repository_cli
  label: Clone or pull a Git repository
  doc: |
    Clones a Git repository when the target directory does not exist.
    If the target directory already contains a Git repository, checks out the
    requested branch and pulls it with `--ff-only`.

    Reads REPOSITORY_PATH, REPOSITORY_URL, BRANCH, and REMOTE from the preserved
    execution environment. BRANCH defaults to `main`; REMOTE defaults to `origin`.
  requirements:
    NetworkAccess:
      networkAccess: true
    InitialWorkDirRequirement:
      listing:
      - entryname: run.sh
        entry: |-
          #!/bin/bash
          set -euo pipefail

          : "\${REPOSITORY_PATH:?REPOSITORY_PATH is required}"
          : "\${REPOSITORY_URL:?REPOSITORY_URL is required}"
          : "\${BRANCH:=main}"
          : "\${REMOTE:=origin}"

          if [ -d "$REPOSITORY_PATH/.git" ]; then
            echo "Updating existing repository at $REPOSITORY_PATH"
            git -C "$REPOSITORY_PATH" fetch "$REMOTE" "$BRANCH"
            git -C "$REPOSITORY_PATH" checkout "$BRANCH" || git -C "$REPOSITORY_PATH" checkout -b "$BRANCH" "$REMOTE/$BRANCH"
            git -C "$REPOSITORY_PATH" pull --ff-only "$REMOTE" "$BRANCH"
          elif [ -e "$REPOSITORY_PATH" ]; then
            echo "Path exists but is not a Git repository: $REPOSITORY_PATH" >&2
            exit 1
          else
            echo "Cloning $REPOSITORY_URL into $REPOSITORY_PATH"
            mkdir -p "\$(dirname "$REPOSITORY_PATH")"
            git clone --branch "$BRANCH" "$REPOSITORY_URL" "$REPOSITORY_PATH"
          fi

          checkout_path="\$(cd "$REPOSITORY_PATH" && pwd -P)"
          printf '%s' "$checkout_path" > repository_path.txt
          ln -sfn "$checkout_path" checkout_directory
  baseCommand:
  - bash
  - run.sh
  inputs: []
  stdout: sync_git_repository_cli.log
  outputs:
    checkout_path:
      type: string
      outputBinding:
        glob: repository_path.txt
        loadContents: true
        outputEval: $(self[0].contents)
    checkout_directory:
      type: Directory
      outputBinding:
        glob: checkout_directory
    log:
      type: string
      outputBinding:
        glob: sync_git_repository_cli.log
        loadContents: true
        outputEval: $(self[0].contents)

- class: CommandLineTool
  id: commit_and_push_cli
  label: Commit changes and push
  doc: |
    Stages all repository changes with `git add --all`, commits them with the
    provided message, and pushes the selected branch.

    Requires `git` to be installed and authenticated in the execution
    environment when pushing to a remote repository.

    Reads REPOSITORY_PATH, BRANCH, and REMOTE from the preserved execution
    environment. REMOTE defaults to `origin`.
  requirements:
    NetworkAccess:
      networkAccess: true
    InitialWorkDirRequirement:
      listing:
      - entryname: run.sh
        entry: |-
          #!/bin/bash
          set -euo pipefail

          : "\${REPOSITORY_PATH:?REPOSITORY_PATH is required}"
          : "\${BRANCH:?BRANCH is required}"
          : "\${REMOTE:=origin}"

          commit_message="$1"
          printf '%s' "$BRANCH" > pushed_branch.txt

          if [ ! -d "$REPOSITORY_PATH/.git" ]; then
            echo "Path is not a Git repository: $REPOSITORY_PATH" >&2
            exit 1
          fi

          git -C "$REPOSITORY_PATH" fetch "$REMOTE" "$BRANCH" || true

          current_branch="\$(git -C "$REPOSITORY_PATH" rev-parse --abbrev-ref HEAD)"

          if [ "$current_branch" != "$BRANCH" ]; then
            if git -C "$REPOSITORY_PATH" show-ref --verify --quiet "refs/heads/$BRANCH"; then
              git -C "$REPOSITORY_PATH" checkout "$BRANCH"
            elif git -C "$REPOSITORY_PATH" show-ref --verify --quiet "refs/remotes/$REMOTE/$BRANCH"; then
              git -C "$REPOSITORY_PATH" checkout -b "$BRANCH" "$REMOTE/$BRANCH"
            else
              git -C "$REPOSITORY_PATH" checkout -b "$BRANCH"
            fi
          fi

          if git -C "$REPOSITORY_PATH" show-ref --verify --quiet "refs/remotes/$REMOTE/$BRANCH"; then
            git -C "$REPOSITORY_PATH" pull --ff-only "$REMOTE" "$BRANCH"
          fi

          git -C "$REPOSITORY_PATH" add --all

          if git -C "$REPOSITORY_PATH" diff --cached --quiet; then
            echo "No changes to commit; skipping push."
            printf 'false' > changes_pushed.txt
            exit 0
          fi

          git -C "$REPOSITORY_PATH" commit -m "$commit_message"
          git -C "$REPOSITORY_PATH" push --set-upstream "$REMOTE" "$BRANCH"
          printf 'true' > changes_pushed.txt
  baseCommand:
  - bash
  - run.sh
  inputs:
    commit_message:
      type: string
      doc: Commit message.
      inputBinding:
        position: 1
  stdout: commit_and_push_cli.log
  outputs:
    changes_pushed:
      type: string
      outputBinding:
        glob: changes_pushed.txt
        loadContents: true
        outputEval: $(self[0].contents)
    pushed_branch:
      type: string
      outputBinding:
        glob: pushed_branch.txt
        loadContents: true
        outputEval: $(self[0].contents)
    log:
      type: string
      outputBinding:
        glob: commit_and_push_cli.log
        loadContents: true
        outputEval: $(self[0].contents)

- class: CommandLineTool
  id: create_pull_request_cli
  label: Create a Pull Request
  doc: |
    Creates a Pull Request for the selected branch, or returns the URL of an
    existing Pull Request for that branch.

    Requires `gh` to be installed and authenticated in the execution
    environment.

    Reads REPOSITORY_PATH, BRANCH, BASE_BRANCH, and REMOTE from the preserved
    execution environment. BASE_BRANCH defaults to `main`; REMOTE defaults to
    `origin`.
  requirements:
    NetworkAccess:
      networkAccess: true
    InitialWorkDirRequirement:
      listing:
      - entryname: run.sh
        entry: |-
          #!/bin/bash
          set -euo pipefail

          : "\${REPOSITORY_PATH:?REPOSITORY_PATH is required}"
          : "\${BRANCH:?BRANCH is required}"
          : "\${BASE_BRANCH:=main}"
          : "\${REMOTE:=origin}"

          pull_request_title="\${1:-}"
          pull_request_body="\${2:-}"

          if [ ! -d "$REPOSITORY_PATH/.git" ]; then
            echo "Path is not a Git repository: $REPOSITORY_PATH" >&2
            exit 1
          fi

          output_dir="\$(pwd)"

          (
            cd "$REPOSITORY_PATH"

            if pull_request_url="\$(gh pr view "$BRANCH" --json url --jq .url 2>/dev/null)"; then
              printf '%s' "$pull_request_url" > "$output_dir/pull_request_url.txt"
              echo "Pull Request already exists: $pull_request_url"
            else
              if [ -z "$pull_request_title" ]; then
                echo "pull_request_title is required when creating a new Pull Request." >&2
                exit 1
              fi

              pull_request_url="\$(gh pr create --base "$BASE_BRANCH" --head "$BRANCH" --title "$pull_request_title" --body "$pull_request_body")"
              printf '%s' "$pull_request_url" > "$output_dir/pull_request_url.txt"
              echo "Created Pull Request: $pull_request_url"
            fi
          )
  baseCommand:
  - bash
  - run.sh
  inputs:
    pull_request_title:
      type: string
      default: ''
      doc: Pull Request title.
      inputBinding:
        position: 1
    pull_request_body:
      type: string
      default: ''
      doc: Pull Request body.
      inputBinding:
        position: 2
  stdout: create_pull_request_cli.log
  outputs:
    pull_request_url:
      type: string?
      outputBinding:
        glob: pull_request_url.txt
        loadContents: true
        outputEval: $(self[0].contents)
    log:
      type: string
      outputBinding:
        glob: create_pull_request_cli.log
        loadContents: true
        outputEval: $(self[0].contents)
