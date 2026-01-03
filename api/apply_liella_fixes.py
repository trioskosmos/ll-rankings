
import re

def apply_fixes():
    # Load new content
    new_sections = {}
    current_key = None
    cur_lines = []
    
    with open('generated_solos.toml', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = re.match(r'^\[(.+)\]$', line)
            if m:
                if current_key:
                    new_sections[current_key] = "\n".join(cur_lines)
                current_key = m.group(1)
                cur_lines = [line] # Keep the header in the content
            else:
                cur_lines.append(line)
        if current_key:
            new_sections[current_key] = "\n".join(cur_lines)

    # Read original
    with open('app/seeds/subgroups.toml', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    output_lines = []
    skipping = False
    
    target_keys = set(new_sections.keys())
    
    for line in lines:
        stripped = line.strip()
        
        # Check for section header
        m = re.match(r'^\[(.+)\]$', stripped)
        if m:
            sec_name = m.group(1)
            
            if skipping:
                # We reached the next section, stop skipping
                skipping = False
            
            if sec_name in target_keys:
                # This is a target section. Write the NEW content.
                # We need to make sure we don't write it multiple times if there are duplicates? (unlikely)
                print(f"Replacing section [{sec_name}]")
                output_lines.append(new_sections[sec_name])
                output_lines.append("") # Add a blank line after
                skipping = True 
                continue # Skip the header line of the old section
            
            # Normal section, just continue
        
        if skipping:
            continue
            
        output_lines.append(line.rstrip())
        
    # Write back
    with open('app/seeds/subgroups.toml', 'w', encoding='utf-8') as f:
        f.write("\n".join(output_lines))
        
    print("Done applying fixes.")

if __name__ == "__main__":
    apply_fixes()
