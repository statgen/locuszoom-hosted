"""
Convert raw SNOMED CT files into a format (JSON) that can be used by django loaddata

https://docs.djangoproject.com/en/2.2/howto/initial-data/

Data format reference: https://www.nlm.nih.gov/research/umls/Snomed/core_subset.html
"""

import collections
import json


def warn_on_format_change(headers):
    """This script assumes a specific header scheme. SNOMED files have been known to change fields over time."""
    assert headers == 'SNOMED_CID|SNOMED_FSN|SNOMED_CONCEPT_STATUS|UMLS_CUI|OCCURRENCE|USAGE|FIRST_IN_SUBSET|' \
                      'IS_RETIRED_FROM_SUBSET|LAST_IN_SUBSET|REPLACED_BY_SNOMED_CID\n',\
        "Assumed file format may have changed- check row values before continuing"


def print_metrics(rows):
    """Provide some quick information about file format. The codebook is not very clear and it can change"""
    # Comment lines specify metrics as of the May 2019 release
    print('Total number of codes', len(rows))
    print('unique_status', set(r[2] for r in rows))  # {'Not current', 'Current'}  - ~275 codes Not Current
    print('unique_retired', set(r[7] for r in rows))  # {'True', 'False'}  - ~335 codes retired
    print('usage stats', collections.Counter(r[4] for r in rows))  # Should be blank or 1-8 (they track 8 institutions)
    print('used in more than one place', sum(1 for r in rows  # Codes used by > 1 of the (8) institutions
                                             if r[4] and int(r[4]) >= 2))


def to_json(rows):
    """
    Filter the set of SNOMED-CORE codes to some reusable subset, and serialize each one in a JSON format that will be
    recognized by Django loaddata script
    """
    return [
        {
            'model': 'gwas.ontologyterm',
            'fields': {
                'code': row[0],
                'label': row[1],
                'scheme': 1  # These are all SNOMED CT codes (id refers to a hardcoded rule in our django model)
            }
        } for row in rows
        if row[7] == 'False' and row[2] == 'Current'  # exclude retired , and outdated concepts
        # and row[4]  # usage stat info must be available...
        # and int(row[4]) >= 2  # ...and code must be used by >1 of the institutions tracked.
        # We'll skip this rule for now because 6k codes is still reasonable and doesn't need filtering
    ]


with open('raw/SNOMEDCT_CORE_SUBSET_201905.txt') as f:
    headers = next(f)  # Skip header rows
    rows = [line.split('|') for line in f]  # < 7k rows, convenient to just work in memory

# Safeguards for future use
warn_on_format_change(headers)
print_metrics(rows)

with open('sources/snomed.json', 'w') as f:
    formatted = to_json(rows)
    print(f'Saving {len(formatted)} codes')
    json.dump(formatted, f)
