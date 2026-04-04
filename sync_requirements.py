import os
import ast
import pkg_resources

# --- CONFIG ---
PROJECT_DIR = "."              # Root folder of your Django project
REQUIREMENTS_FILE = "requirements.txt"
AUTO_ADD = True                # Add missing packages automatically
AUTO_REMOVE_UNUSED = True      # Remove packages not used in project

def get_imports_from_file(filepath):
    """Extract top-level imports from a Python file."""
    imports = set()
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError:
            return imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
    return imports

def get_project_imports(project_dir):
    """Recursively collect all imported modules from .py files."""
    all_imports = set()
    for root, _, files in os.walk(project_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                all_imports |= get_imports_from_file(filepath)
    return all_imports

def get_requirements_packages(requirements_file):
    """Parse top-level packages from requirements.txt."""
    if not os.path.exists(requirements_file):
        return set()
    with open(requirements_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    packages = set()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pkg = line.split("==")[0].split(">=")[0].split("<=")[0]
        packages.add(pkg.lower())
    return packages

def write_requirements(packages):
    """Rewrite the requirements.txt with the given set of packages and their versions."""
    with open(REQUIREMENTS_FILE, "w", encoding="utf-8") as f:
        for pkg in sorted(packages):
            try:
                version = pkg_resources.get_distribution(pkg).version
                f.write(f"{pkg}=={version}\n")
            except Exception:
                f.write(f"{pkg}\n")

if __name__ == "__main__":
    print("🔍 Scanning Django project for imports...")

    project_imports = get_project_imports(PROJECT_DIR)
    requirements_pkgs = get_requirements_packages(REQUIREMENTS_FILE)
    installed_pkgs = {pkg.key for pkg in pkg_resources.working_set}

    # Exclude Python built-in and stdlib modules
    stdlib_pkgs = {
        "os", "sys", "json", "re", "datetime", "math", "logging",
        "pathlib", "typing", "subprocess", "time", "collections",
        "itertools", "functools", "shutil", "tempfile", "uuid"
    }

    # Detect missing and unused packages
    missing = [
        imp for imp in project_imports
        if imp.lower() not in requirements_pkgs
        and imp.lower() not in stdlib_pkgs
        and imp.lower() in installed_pkgs
    ]
    unused = [
        pkg for pkg in requirements_pkgs
        if pkg not in project_imports and pkg not in ("django",)
    ]

    print("\n🧾 Missing imports (not in requirements.txt):")
    if missing:
        for imp in sorted(missing):
            print(f"  - {imp}")
    else:
        print("✅ None — all imports are already listed.")

    print("\n🧹 Unused packages (in requirements.txt but not imported):")
    if unused:
        for pkg in sorted(unused):
            print(f"  - {pkg}")
    else:
        print("✅ None — all listed packages are used.")

    # Update requirements.txt if configured
    if AUTO_ADD or AUTO_REMOVE_UNUSED:
        print("\n🔧 Syncing requirements.txt...")
        updated_pkgs = set(requirements_pkgs)
        if AUTO_ADD:
            for pkg in missing:
                updated_pkgs.add(pkg.lower())
        if AUTO_REMOVE_UNUSED:
            for pkg in unused:
                updated_pkgs.discard(pkg.lower())

        write_requirements(updated_pkgs)
        print("✅ requirements.txt updated successfully.")
    else:
        print("\n(No changes made — AUTO_ADD and AUTO_REMOVE_UNUSED are both False.)")
