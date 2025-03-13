
import os
import re

def fix_url_endpoint(file_path):
    """Fix incorrect URL endpoint in template."""
    if not os.path.exists(file_path):
        print(f"Template file not found: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if the incorrect URL endpoint exists
    if "url_for('dashboard.admin_change_user_password'" in content:
        # Replace with the correct endpoint
        modified_content = content.replace(
            "url_for('dashboard.admin_change_user_password'", 
            "url_for('dashboard.change_password'"
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print(f"Fixed URL endpoint in {file_path}")
        return True
    
    print(f"No incorrect URL endpoint found in {file_path}")
    return False

# Fix the template with incorrect URL endpoint
template_to_fix = "SchoolHub/templates/dashboard/manage_users.html"
fixed = fix_url_endpoint(template_to_fix)

if fixed:
    print(f"Successfully fixed {template_to_fix}")
else:
    print(f"Could not fix {template_to_fix}")

print("URL endpoint fixing completed.")
