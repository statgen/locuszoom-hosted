"""
Auto-detect the appropriate options for parsing a GWAS file
"""

# pvalue or logpvalue
# How many header rows? (in a text file, we don't necessarily know this)
# What are the headers names?
# Get columns for chrom/pos/ref/alt

from .const import MISSING_VALUES


def is_numeric(val: str) -> bool:
    if val in MISSING_VALUES:
        return True

    try:
        float(val)
    except Exception:
        return False
    else:
        return True


def is_header(row: str, *, comment_char="#", delimiter='\t') -> bool:
    """
    This assumes two basic rules: the line is not a comment, and gwas data is more likely to be numeric than headers
    """
    return row.startswith(comment_char) or all(not is_numeric(field) for field in row.split(delimiter))
