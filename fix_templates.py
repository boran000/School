
import os
import re

def fix_template(file_path):
    """Fix duplicate content blocks in templates."""
    if not os.path.exists(file_path):
        print(f"Template file not found: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count occurrences of content block
    content_block_count = content.count("{% block content %}")
    
    if content_block_count > 1:
        print(f"Found {content_block_count} content blocks in {file_path}")
        
        # If template extends base.html, we need to keep only one content block
        if "{% extends" in content:
            # Find the position of the first content block
            first_block_pos = content.find("{% block content %}")
            
            # Find the position of subsequent content blocks
            next_block_pos = content.find("{% block content %}", first_block_pos + 1)
            
            if next_block_pos != -1:
                # Remove the extra block tag, but keep the content
                modified_content = content[:next_block_pos] + content[next_block_pos + len("{% block content %}"):].replace("{% endblock %}", "", 1)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                print(f"Fixed duplicate content block in {file_path}")
                return True
    
    print(f"No duplicate content blocks found in {file_path}")
    return False

# Fix the templates with duplicate content blocks
templates_to_fix = [
    "SchoolHub/templates/dashboard/manage_tc.html",
    "SchoolHub/templates/dashboard/manage_announcements.html"
]

for template in templates_to_fix:
    fixed = fix_template(template)
    if fixed:
        print(f"Successfully fixed {template}")
    else:
        print(f"Could not fix {template}")

print("Template fixing completed.")
