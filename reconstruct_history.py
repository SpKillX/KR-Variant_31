import subprocess
import os

mapping = {
    "Initial commit": "chore: initial commit",
    "create data models": "feat: implement database models",
    "create main.py and tests": "feat: implement main application and initial tests",
    "Create README.md": "docs: create project README",
    "improved structure": "refactor: improve project directory structure",
    "update db": "fix: update database schema",
    "improving booking logic": "feat: improve booking business logic",
    "fix db": "fix: resolve database connectivity issues",
    "add registration": "feat: implement user registration",
    "add admin-panel": "feat: add administration panel",
    "fix login": "fix: resolve authentication issues",
    "upgrade index.html": "style: update frontend landing page",
    "add roles": "feat: implement user role management",
    "add booking list": "feat: add booking list view",
    "fix booking": "fix: resolve booking overlap conflicts",
    "release alpha": "chore: release alpha version",
    "add test data": "chore: add database seed data",
    "fix admin-panel": "fix: resolve admin panel bugs",
    "add tests": "test: implement comprehensive API tests",
    "docs: expand README with architecture diagrams and manual testing guide": "docs: expand README with architecture diagrams",
}

def run(cmd, env=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"Error executing: {cmd}\\n{result.stderr}")
    return result.stdout.strip()

def main():
    # Get all commits from the current main branch in reverse order
    log_output = run('git log --reverse --pretty=format:"%H|%ai|%s"')
    if not log_output:
        print("No commits found.")
        return

    commits = log_output.splitlines()
    print(f"Found {len(commits)} commits to reconstruct.")

    # Create an orphan branch
    run('git checkout --orphan semantic-main')
    run('git rm -rf .')

    for i, line in enumerate(commits):
        parts = line.split('|', 2)
        if len(parts) < 3:
            continue
        
        commit_hash, commit_date, original_msg = parts
        new_msg = mapping.get(original_msg, original_msg)
        if original_msg.startswith("Merge branch"):
            new_msg = f"merge: {original_msg}"
        
        print(f"[{i+1}/{len(commits)}] Reconstructing {commit_hash[:7]} as '{new_msg}' ({commit_date})")

        # Checkout files and commit
        run(f'git checkout {commit_hash} -- .')
        run('git add .')

        custom_env = os.environ.copy()
        custom_env["GIT_AUTHOR_DATE"] = commit_date
        custom_env["GIT_COMMITTER_DATE"] = commit_date
        
        run(f'git commit -m "{new_msg}"', env=custom_env)

    # Finalize
    run('git checkout main')
    run('git reset --hard semantic-main')
    run('git branch -D semantic-main')

    print("\nHistory successfully reconstructed!")

if __name__ == "__main__":
    main()
