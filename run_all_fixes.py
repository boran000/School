
import os
import subprocess
import sys

def run_script(script_path):
    """Run a Python script and print its output."""
    print(f"\n=== Running {script_path} ===\n")
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Errors encountered:\n{result.stderr}")
    return result.returncode == 0

# List of fix scripts to run
fix_scripts = [
    "fix_templates.py",
    "fix_urls.py",
    "fix_file_paths.py",
    "fix_gallery_paths.py",
    "fix_media_table.py",
    "update_db.py",
    "update_db_gallery_item.py",
    "update_db_media.py",
    "update_db_video_platform.py"
]

success_count = 0
total_scripts = len(fix_scripts)

for script in fix_scripts:
    script_path = os.path.join("SchoolHub", script)
    if os.path.exists(script_path):
        if run_script(script_path):
            success_count += 1
    else:
        print(f"Script {script_path} not found, skipping.")

print(f"\n=== Fix Summary ===\n")
print(f"Successfully ran {success_count} out of {total_scripts} fix scripts.")
print("Please check the output above for any errors that need manual intervention.")

if success_count == total_scripts:
    print("\nAll fixes were applied successfully!")
else:
    print("\nSome fixes may require manual intervention.")
