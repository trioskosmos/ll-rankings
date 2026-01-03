
import re

def find_sections():
    target_sections = [
        "liella.kanon_solos", "liella.keke_solos", "liella.chisato_solos",
        "liella.sumire_solos", "liella.ren_solos", "liella.kinako_solos",
        "liella.mei_solos", "liella.shiki_solos", "liella.natsumi_solos",
        "liella.wien_solos"
    ]
    
    with open('app/seeds/subgroups.toml', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_section = None
    section_start = -1
    
    # Map section -> (start, end)
    # End is inclusive
    ranges = {}
    
    for i, line in enumerate(lines):
        lineno = i + 1
        line = line.strip()
        
        # Check for section header
        m = re.match(r'^\[(.+)\]$', line)
        if m:
            new_section = m.group(1)
            
            # Close previous section
            if current_section in target_sections:
                # End line is the line before this one (lineno - 1), 
                # but we usually want to include empty lines before the next section?
                # Actually, TOML structure usually has empty lines between sections.
                # Let's say end line is lineno - 1.
                ranges[current_section] = (section_start, lineno - 1)
            
            section_start = lineno
            current_section = new_section
            
    # Handle last section
    if current_section in target_sections:
        ranges[current_section] = (section_start, len(lines))

    with open('sections_info.txt', 'w', encoding='utf-8') as f:
        for k in target_sections:
            if k in ranges:
                f.write(f"{k}: {ranges[k]}\n")
            else:
                f.write(f"{k}: Not Found\n")

if __name__ == "__main__":
    find_sections()
