import re
import sys
from pathlib import Path

def normalize_name(name):
    """Convert name to flag format (lowercase with underscores)"""
    return name.lower().replace(' ', '_').replace('-', '_').replace("'", '')

def get_body_type_suffix(planet_class):
    """Determine the suffix based on planet class"""
    if '_star' in planet_class:
        return '_star'
    elif planet_class == 'pc_habitat':
        return '_station'
    else:
        return '_planet'

def extract_name(block):
    """Extract the name from a planet/moon block"""
    name_match = re.search(r'name\s*=\s*"([^"]+)"', block)
    return name_match.group(1) if name_match else None

def extract_class(block):
    """Extract the class from a planet/moon block"""
    class_match = re.search(r'class\s*=\s*(\S+)', block)
    return class_match.group(1) if class_match else None

def has_required_flag(block, flag_name):
    """Check if the block already has the required flag"""
    flags_match = re.search(r'flags\s*=\s*\{([^}]+)\}', block)
    if flags_match:
        flags_content = flags_match.group(1)
        # Check if the specific flag exists
        return flag_name in flags_content
    return False

def find_size_line_end(block):
    """Find the position after the size line"""
    size_match = re.search(r'(\n\s*size\s*=\s*\d+\s*\n)', block)
    return size_match.end() if size_match else None

def get_indentation_at_position(content, position):
    """Get the indentation level at a specific position"""
    # Go back to find the start of the line
    line_start = content.rfind('\n', 0, position) + 1
    line = content[line_start:position]
    # Count leading spaces/tabs
    indent = len(line) - len(line.lstrip())
    return ' ' * indent

def add_flag_after_size(block, flag_name, base_indent):
    """Add a flags line after the size line if it doesn't exist"""
    size_pos = find_size_line_end(block)
    if size_pos is None:
        return block
    
    # Check if flags already exist
    if 'flags = {' in block:
        # Flags exist, add to existing flags
        flags_match = re.search(r'(flags\s*=\s*\{)([^}]*)(})', block)
        if flags_match:
            existing_flags = flags_match.group(2).strip()
            if flag_name not in existing_flags:
                if existing_flags:
                    new_flags = f"{flags_match.group(1)}{existing_flags} {flag_name}{flags_match.group(3)}"
                else:
                    new_flags = f"{flags_match.group(1)} {flag_name} {flags_match.group(3)}"
                block = block[:flags_match.start()] + new_flags + block[flags_match.end():]
    else:
        # No flags exist, add new flags line after size
        new_flag_line = f"{base_indent}flags = {{ {flag_name} }}\n"
        block = block[:size_pos] + new_flag_line + block[size_pos:]
    
    return block

def process_celestial_body(content, start_pos, end_pos, parent_indent):
    """Process a single planet or moon block"""
    block = content[start_pos:end_pos]
    
    name = extract_name(block)
    planet_class = extract_class(block)
    
    if not name or not planet_class:
        return content, 0
    
    # Generate the appropriate flag
    suffix = get_body_type_suffix(planet_class)
    flag_name = f"{normalize_name(name)}{suffix}"
    
    # Check if flag already exists
    if has_required_flag(block, flag_name):
        print(f"  Skipping {name} - already has flag '{flag_name}'")
        return content, 0
    
    # Get the indentation for the flags line (same as size line)
    indent_match = re.search(r'\n(\s*)size\s*=', block)
    if indent_match:
        base_indent = indent_match.group(1)
    else:
        base_indent = parent_indent + "    "
    
    # Add the flag
    modified_block = add_flag_after_size(block, flag_name, base_indent)
    
    if modified_block != block:
        print(f"  Added '{flag_name}' to {name}")
        content = content[:start_pos] + modified_block + content[end_pos:]
        # Adjust end position for any content length changes
        length_diff = len(modified_block) - len(block)
        return content, length_diff
    
    return content, 0

def process_file(filepath):
    """Process a single initializer file"""
    print(f"\nProcessing {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Find all planet blocks (including nested moons)
    # We'll process from end to start to avoid position shifting issues
    planet_pattern = r'(\n\s*)(planet|moon)\s*=\s*\{'
    
    matches = list(re.finditer(planet_pattern, content))
    
    # Process in reverse order to maintain correct positions
    for match in reversed(matches):
        indent = match.group(1)
        block_type = match.group(2)
        start = match.start()
        
        # Find the matching closing brace
        brace_count = 1
        pos = match.end()
        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1
        
        end = pos
        
        # Process this block
        content, length_diff = process_celestial_body(content, start, end, indent)
    
    # Write back to file if changes were made
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ File updated successfully")
    else:
        print(f"  No changes needed")

def main():
    if len(sys.argv) < 2:
        print("Usage: python add_planet_flags.py <file1> <file2> ... <file5>")
        print("Or: python add_planet_flags.py *.txt")
        sys.exit(1)
    
    files = sys.argv[1:]
    
    print(f"Processing {len(files)} file(s)...")
    
    for filepath in files:
        path = Path(filepath)
        if not path.exists():
            print(f"Warning: {filepath} not found, skipping...")
            continue
        
        try:
            process_file(filepath)
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n✓ All files processed!")

if __name__ == "__main__":
    main()