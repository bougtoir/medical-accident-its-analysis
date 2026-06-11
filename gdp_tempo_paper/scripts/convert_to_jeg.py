"""One-time script to convert manuscript from Economica format to
Journal of Economic Growth (Springer) format.

Changes:
  1. Section headings: Roman numerals → decimal (1, 2, 3..., 1.1, 1.2...)
  2. In-text cross-references: "Section III.3" → "Sect. 3.3"
  3. References: ALL CAPS surnames → APA 7 title case, 'and' → '&'
  4. JA cross-references: "第 III 節" → "第 3 節", "第 IV 節" → "第 4 節"
"""
import re
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
MS = os.path.join(ROOT, "manuscript")

# Roman numeral → Arabic mapping
ROMAN_MAP = {
    'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
    'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10',
}


def roman_to_arabic(roman: str) -> str:
    return ROMAN_MAP.get(roman, roman)


def convert_heading(line: str) -> str:
    m = re.match(r'^(## )([IVX]+)\s+(.*)$', line)
    if m:
        prefix, roman, title = m.groups()
        return f"{prefix}{roman_to_arabic(roman)} {title}"
    m = re.match(r'^(### )([IVX]+)\.(\d+)\s+(.*)$', line)
    if m:
        prefix, roman, sub, title = m.groups()
        return f"{prefix}{roman_to_arabic(roman)}.{sub} {title}"
    return line


def convert_crossrefs_en(text: str) -> str:
    def _replace_section_dot(m):
        return f"Sect. {roman_to_arabic(m.group(1))}.{m.group(2)}"
    text = re.sub(r'Section ([IVX]+)\.(\d+)', _replace_section_dot, text)
    
    def _replace_section(m):
        return f"Sect. {roman_to_arabic(m.group(1))}"
    text = re.sub(r'Section ([IVX]+)(?!\.\d)', _replace_section, text)
    
    def _replace_sym_dot(m):
        return f"Sect. {roman_to_arabic(m.group(1))}.{m.group(2)}"
    text = re.sub(r'§([IVX]+)\.(\d+)', _replace_sym_dot, text)
    
    def _replace_sym(m):
        return f"Sect. {roman_to_arabic(m.group(1))}"
    text = re.sub(r'§([IVX]+)(?!\.\d)', _replace_sym, text)
    
    return text


def convert_crossrefs_ja(text: str) -> str:
    def _replace_ja(m):
        return f"第 {roman_to_arabic(m.group(1))} 節"
    text = re.sub(r'第 ([IVX]+) 節', _replace_ja, text)
    text = re.sub(r'III\.(\d+) 節', lambda m: f'3.{m.group(1)} 節', text)
    text = re.sub(r'IV\.(\d+) 節', lambda m: f'4.{m.group(1)} 節', text)
    text = re.sub(r'V\.(\d+) 節', lambda m: f'5.{m.group(1)} 節', text)
    text = re.sub(r'VI\.(\d+) 節', lambda m: f'6.{m.group(1)} 節', text)
    return text


def _surname_to_titlecase(name: str) -> str:
    """Convert ALL CAPS surname to Title Case, handling hyphens and particles."""
    name = name.strip()
    if not name:
        return name
    # Keep short acronyms (OECD, UNECE)
    if len(name) <= 5 and name == name.upper() and ',' not in name and '.' not in name:
        return name
    
    # Check if already mixed case (not all caps) — leave it alone
    if name != name.upper():
        return name
    
    # Title case, handling hyphens
    parts = name.split('-')
    tc_parts = []
    for part in parts:
        if part:
            tc_parts.append(part[0].upper() + part[1:].lower())
        else:
            tc_parts.append(part)
    return '-'.join(tc_parts)


def convert_reference_line(line: str) -> str:
    """Convert a reference line from Economica to APA 7 format.
    
    Strategy: find ALL CAPS words before the (year) and convert them to title case.
    Also convert ' and ' to ' & ' in the author section.
    """
    # Find the (year) marker
    year_match = re.search(r'\((\d{4})\)', line)
    if not year_match:
        return line
    
    author_part = line[:year_match.start()].rstrip()
    rest = line[year_match.start():]
    
    # Check if this looks like a reference line (starts with a surname)
    if not author_part or not re.match(r'^[A-Z]', author_part):
        return line
    
    # Check if it has ALL CAPS surnames (at least one word of 2+ uppercase letters)
    if not re.search(r'\b[A-Z]{2,}', author_part):
        return line
    
    # Convert ALL CAPS surnames to title case
    # Pattern: match sequences of uppercase letters (possibly with hyphens, apostrophes)
    # that are followed by a comma and initials
    def _convert_surname(m):
        surname = m.group(0)
        return _surname_to_titlecase(surname)
    
    # Replace ALL CAPS words (2+ chars) that look like surnames
    # A surname is a sequence of uppercase+hyphen chars followed by comma
    converted = re.sub(
        r'\b([A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ][A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ\-\']+)\b(?=[\s,])',
        _convert_surname,
        author_part
    )
    
    # Replace " and " with " & " in author block
    converted = re.sub(r'\s+and\s+', ' & ', converted)
    
    # Handle "(eds.)" → keep as-is
    # Handle " In " editor names in the rest (after year) — don't touch those
    
    return converted + ' ' + rest


def convert_references_block(text: str) -> str:
    """Convert the references section."""
    lines = text.split('\n')
    in_refs = False
    result = []
    
    for line in lines:
        stripped = line.strip()
        if stripped in ('## References', '## 参考文献'):
            in_refs = True
            result.append(line)
            continue
        
        if in_refs and stripped and not stripped.startswith('#'):
            result.append(convert_reference_line(line))
        else:
            result.append(line)
    
    return '\n'.join(result)


def process_manuscript(lang: str):
    md_path = os.path.join(MS, f"manuscript_{lang}.md")
    with open(md_path, encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        line = convert_heading(line)
        new_lines.append(line)
    content = '\n'.join(new_lines)
    
    if lang == 'en':
        content = convert_crossrefs_en(content)
    else:
        content = convert_crossrefs_ja(content)
    
    content = convert_references_block(content)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Converted {md_path}")


if __name__ == '__main__':
    process_manuscript('en')
    process_manuscript('ja')
    print("Done.")
