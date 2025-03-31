#!/usr/bin/env python3
"""
PineScript Optimizer - A tool for managing, optimizing, and debugging large Pine Scripts with AI assistance

This tool helps you maintain a complete working copy of your Pine Script while allowing you to:
1. Extract specific sections for AI optimization
2. Apply AI changes back to the main script
3. Track versions and changes with Git
4. Validate script completeness and structural integrity
5. Generate targeted prompts for AI assistance

Usage:
    python pine_optimizer.py init <script_path>       # Initialize repository with your script
    python pine_optimizer.py extract <section_name>   # Extract a section for optimization
    python pine_optimizer.py apply <section_file>     # Apply an optimized section
    python pine_optimizer.py validate                 # Check script integrity
    python pine_optimizer.py prompt <section_name>    # Generate an AI prompt for a section
    python pine_optimizer.py optimize <section_name> <description>  # Generate optimization prompt
"""

import os
import sys
import re
import subprocess
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime

# Configuration
CONFIG_FILE = ".pine_optimizer.json"
SECTIONS = [
    "INPUT PARAMETERS",
    "VOLATILITY ANALYSIS",
    "WEIGHTED VOLUME CALCULATION",
    "PIVOT POINT CALCULATION",
    "MULTI-TIMEFRAME DATA",
    "PIVOT ARRAYS AND LABELS",
    "PIVOT ZONE AND CONFLUENCE DETECTION",
    "STRATEGY SIGNAL CALCULATION",
    "OPTIONS STRATEGY SELECTION",
    "VISUALIZATION",
    "PLOTTING AND VISUALIZATION",
    "ALERTS AND PERFORMANCE TRACKING"
]

def initialize_repo(script_path):
    """Initialize a Git repository with the Pine Script and structure for optimization"""
    
    # Check if file exists
    if not os.path.exists(script_path):
        print(f"Error: Script file '{script_path}' not found.")
        return False
    
    # Read the script content
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Create directory structure
    os.makedirs("sections", exist_ok=True)
    os.makedirs("optimized", exist_ok=True)
    os.makedirs("backups", exist_ok=True)
    
    # Save the original script
    original_file = "original.pine"
    shutil.copy(script_path, original_file)
    
    # Create working copy
    working_file = "working.pine"
    shutil.copy(script_path, working_file)
    
    # Parse sections
    sections = parse_sections(content)
    
    # Save sections to files
    for name, section_content in sections.items():
        safe_name = name.lower().replace(" ", "_")
        section_file = f"sections/{safe_name}.pine"
        with open(section_file, 'w') as f:
            f.write(section_content)
    
    # Create backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backups/{os.path.basename(script_path)}_{timestamp}"
    shutil.copy(script_path, backup_file)
    
    # Initialize Git repo if not already a git repo
    if not os.path.exists(".git"):
        subprocess.run(["git", "init"], check=True)
        
        # Create .gitignore
        with open(".gitignore", 'w') as f:
            f.write("__pycache__/\n*.pyc\n")
        
        # Initial commit
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit with Pine Script Optimizer"], check=True)
    
    # Save configuration
    config = {
        "original_script": original_file,
        "working_script": working_file,
        "last_backup": backup_file,
        "sections": {name: f"sections/{name.lower().replace(' ', '_')}.pine" for name in sections.keys()}
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Initialized Pine Script Optimizer with '{script_path}'")
    print(f"- Original saved as: {original_file}")
    print(f"- Working copy: {working_file}")
    print(f"- Extracted {len(sections)} sections to 'sections/' directory")
    
    return True

def parse_sections(content):
    """Parse the script into sections based on comments"""
    sections = {}
    
    # Find section headers in format: // SECTION X: NAME
    section_pattern = r"//==+\s*\n// SECTION \d+: ([A-Z0-9 ]+)"
    section_matches = re.finditer(section_pattern, content)
    
    section_positions = []
    for match in section_matches:
        section_name = match.group(1).strip()
        start_pos = match.start()
        section_positions.append((section_name, start_pos))
    
    # Add end of file as the final position
    section_positions.append(("END", len(content)))
    
    # Extract sections
    for i in range(len(section_positions) - 1):
        name, start = section_positions[i]
        _, end = section_positions[i + 1]
        sections[name] = content[start:end]
    
    # If there are predefined sections that weren't found, add empty placeholders
    for section in SECTIONS:
        if section not in sections:
            sections[section] = f"// SECTION: {section}\n// (This section is currently empty or not explicitly defined)\n"
    
    return sections

def extract_section(section_name):
    """Extract a specific section for optimization"""
    # Load configuration
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: Repository not initialized. Run 'init' command first.")
        return False
    
    # Find the section
    section_file = None
    for name, path in config["sections"].items():
        if section_name.lower() in name.lower():
            section_file = path
            break
    
    if not section_file:
        print(f"Error: Section '{section_name}' not found.")
        return False
    
    # Copy to optimized folder with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    optimized_file = f"optimized/{os.path.basename(section_file)[:-5]}_{timestamp}.pine"
    
    shutil.copy(section_file, optimized_file)
    
    print(f"Extracted section '{section_name}' to: {optimized_file}")
    return optimized_file

def apply_section(section_file):
    """Apply an optimized section back to the working script"""
    # Load configuration
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: Repository not initialized. Run 'init' command first.")
        return False
    
    # Check if section file exists
    if not os.path.exists(section_file):
        print(f"Error: Section file '{section_file}' not found.")
        return False
    
    # Read section content
    with open(section_file, 'r') as f:
        section_content = f.read()
    
    # Extract section name from filename
    section_basename = os.path.basename(section_file)
    matched_section = None
    
    for name in config["sections"]:
        safe_name = name.lower().replace(" ", "_")
        if safe_name in section_basename.lower():
            matched_section = name
            break
    
    if not matched_section:
        print(f"Error: Could not match section file to a known section.")
        return False
    
    # Update the section in its original file
    original_section_file = config["sections"][matched_section]
    with open(original_section_file, 'w') as f:
        f.write(section_content)
    
    # Read working script
    with open(config["working_script"], 'r') as f:
        working_content = f.read()
    
    # Create backup before modifying
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backups/working_{timestamp}.pine"
    with open(backup_file, 'w') as f:
        f.write(working_content)
    
    # Now we need to replace the section in the working script
    sections = parse_sections(working_content)
    
    if matched_section in sections:
        # Replace section
        working_content = working_content.replace(sections[matched_section], section_content)
        
        # Save updated working script
        with open(config["working_script"], 'w') as f:
            f.write(working_content)
        
        print(f"Applied changes from '{section_file}' to working script.")
        
        # Update config with new backup
        config["last_backup"] = backup_file
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Commit changes to git
        subprocess.run(["git", "add", config["working_script"], original_section_file], check=True)
        subprocess.run(["git", "commit", "-m", f"Applied optimizations to section: {matched_section}"], check=True)
        
        return True
    else:
        print(f"Error: Section '{matched_section}' not found in working script.")
        return False

def validate_script():
    """Validate the working script for completeness and structural integrity"""
    # Load configuration
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: Repository not initialized. Run 'init' command first.")
        return False
    
    # Read working script
    with open(config["working_script"], 'r') as f:
        content = f.read()
    
    # Check for basic structural elements
    checks = {
        "has_version": re.search(r"// @version", content) is not None,
        "has_indicator": re.search(r"indicator\(", content) is not None,
        "has_input_params": len(re.findall(r"input\.", content)) > 0,
        "balanced_brackets": content.count("{") == content.count("}"),
        "balanced_parentheses": content.count("(") == content.count(")"),
        "no_unfinished_comments": "/*" not in content or (content.count("/*") == content.count("*/")),
    }
    
    # Check for section headers
    section_headers = re.findall(r"//==+\s*\n// SECTION \d+:", content)
    checks["has_sections"] = len(section_headers) > 0
    
    # Calculate section count
    sections = parse_sections(content)
    checks["section_count"] = len(sections)
    
    # Check for common Pine Script errors
    checks["no_unused_vars"] = content.count("Unused variable") == 0
    checks["no_misplaced_var"] = content.count("Cannot use 'var' with") == 0
    
    # Print validation results
    print("Script Validation Results:")
    print(f"- Has @version tag: {checks['has_version']}")
    print(f"- Has indicator() function: {checks['has_indicator']}")
    print(f"- Has input parameters: {checks['has_input_params']}")
    print(f"- Balanced brackets: {checks['balanced_brackets']}")
    print(f"- Balanced parentheses: {checks['balanced_parentheses']}")
    print(f"- No unfinished comments: {checks['no_unfinished_comments']}")
    print(f"- Has section headers: {checks['has_sections']}")
    print(f"- Number of sections: {checks['section_count']}")
    
    # Calculate overall validation success
    critical_checks = ["has_version", "has_indicator", "balanced_brackets", 
                      "balanced_parentheses", "no_unfinished_comments"]
    
    is_valid = all(checks[check] for check in critical_checks)
    
    if is_valid:
        print("\n✅ Script passed basic validation checks.")
    else:
        print("\n❌ Script failed one or more critical validation checks.")
    
    # Calculate hash of working file for integrity checking
    with open(config["working_script"], 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
        
    print(f"\nMD5 Checksum: {file_hash}")
    return is_valid

def generate_prompt(section_name, is_optimization=False, description=""):
    """Generate an AI prompt for a specific section"""
    # Load configuration
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: Repository not initialized. Run 'init' command first.")
        return False
    
    # Find the section
    section_file = None
    matched_section = None
    for name, path in config["sections"].items():
        if section_name.lower() in name.lower():
            section_file = path
            matched_section = name
            break
    
    if not section_file:
        print(f"Error: Section '{section_name}' not found.")
        return False
    
    # Read section content
    with open(section_file, 'r') as f:
        section_content = f.read()
    
    # Read full working script to get context
    with open(config["working_script"], 'r') as f:
        full_script = f.read()
    
    # Create section summary and global context
    section_lines = section_content.split('\n')
    context_lines = []
    
    # Extract global variable definitions
    global_vars = re.findall(r'^var\s+\w+.*$', full_script, re.MULTILINE)
    
    # Count lines in each section for reference
    sections = parse_sections(full_script)
    section_counts = {name: len(content.split('\n')) for name, content in sections.items()}
    
    # Generate prompt based on whether this is for optimization or general assistance
    if is_optimization:
        prompt = f"""# Pine Script Optimization Task

I need to optimize the following section of my Pine Script trading strategy:

## Section: {matched_section}
{description}

## Current Implementation:
```pine
{section_content}
```

## Global Context:
The script contains {len(sections)} sections with these line counts:
{', '.join([f"{name} ({count} lines)" for name, count in section_counts.items()])}

Key global variables that might be referenced:
```pine
{os.linesep.join(global_vars[:20])}  # Showing first 20 global variables
```

## Optimization Requirements:
1. Please optimize this code section while maintaining ALL original functionality
2. Focus on improving: performance, error handling, and code quality
3. You MUST keep ALL function signatures, input parameters, and output formats EXACTLY the same
4. The optimized code should be a DROP-IN REPLACEMENT for the original section
5. Return the COMPLETE optimized section, not just code snippets
6. DO NOT reduce functionality - improve the implementation without removing features
7. Add proper error handling for all operations
8. Add helpful comments explaining major optimizations

## Important Instructions:
- Provide the FULL optimized section code that I can directly copy and use
- Explain your key optimization changes after the code
- If any parts cannot be optimized further, explain why
"""
    else:
        prompt = f"""# Pine Script Code Review and Assistance

I need help with the following section of my Pine Script trading strategy:

## Section: {matched_section}

```pine
{section_content}
```

## Context:
This is part of a larger trading strategy script with {len(sections)} sections.
This specific section handles the {matched_section} functionality.

## What I need help with:
1. Review this code section for potential bugs, errors, or issues
2. Suggest improvements while keeping the same overall functionality
3. Answer questions about the approach and implementation

## Important Instructions:
- Do not rewrite the entire section unless necessary
- Focus on specific improvements to the existing code
- Explain any suggestions or changes you recommend
"""

    # Print prompt
    print("\nGenerated AI Prompt:")
    print("-" * 80)
    print(prompt)
    print("-" * 80)
    
    # Save prompt to file
    prompt_type = "optimization" if is_optimization else "assistance"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prompt_file = f"prompts/{matched_section.lower().replace(' ', '_')}_{prompt_type}_{timestamp}.txt"
    
    # Create prompts directory if it doesn't exist
    os.makedirs("prompts", exist_ok=True)
    
    with open(prompt_file, 'w') as f:
        f.write(prompt)
    
    print(f"\nSaved prompt to: {prompt_file}")
    return prompt_file

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == "init":
        if len(sys.argv) < 3:
            print("Error: Missing script path. Usage: python pine_optimizer.py init <script_path>")
            return
        initialize_repo(sys.argv[2])
    
    elif command == "extract":
        if len(sys.argv) < 3:
            print("Error: Missing section name. Usage: python pine_optimizer.py extract <section_name>")
            return
        extract_section(sys.argv[2])
    
    elif command == "apply":
        if len(sys.argv) < 3:
            print("Error: Missing section file. Usage: python pine_optimizer.py apply <section_file>")
            return
        apply_section(sys.argv[2])
    
    elif command == "validate":
        validate_script()
    
    elif command == "prompt":
        if len(sys.argv) < 3:
            print("Error: Missing section name. Usage: python pine_optimizer.py prompt <section_name>")
            return
        generate_prompt(sys.argv[2])
    
    elif command == "optimize":
        if len(sys.argv) < 4:
            print("Error: Missing section name or description. Usage: python pine_optimizer.py optimize <section_name> <description>")
            return
        generate_prompt(sys.argv[2], is_optimization=True, description=sys.argv[3])
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)

if __name__ == "__main__":
    main()
