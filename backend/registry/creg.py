"""Class-I HLA cross-reactive groups used for clinical decision support.

The labels and group membership mirror the table supplied for Renalloc. CREG
findings are advisory: exact donor/Anti-HLA conflicts remain the hard exclusion,
while a shared CREG is surfaced as a potential conflict requiring laboratory
review and physical cross-match.
"""

import re


CREG_GROUPS = {
    "A1C": ["A1", "A3", "A11", "A19", "A29", "A30", "A31", "A36", "A80"],
    "A2": ["A2", "A9", "A23", "A24", "A28", "A68", "A69", "B17", "B57", "B58"],
    "A10C": ["A10", "A25", "A26", "A34", "A66", "A32", "A33", "A43", "A74"],
    "BW4": [
        "A9", "A23", "A24", "A25", "A32", "B13", "B27", "B37", "B38",
        "B44", "B47", "B49", "B51", "B52", "B53", "B57", "B58", "B59",
        "B63", "B67",
    ],
    "B5C": ["B5", "B51", "B52", "B18", "B35", "B53"],
    "B5C2": [
        "B5", "B51", "B52", "B15", "B62", "B63", "B71", "B72", "B75",
        "B76", "B77", "B17", "B57", "B58", "B21", "B49", "B50", "B35",
        "B53", "B73", "B78",
    ],
    "BW6": [
        "B7", "B8", "B14", "B18", "B35", "B39", "B40", "B60", "B61",
        "B41", "B42", "B45", "B46", "B48", "B50", "B54", "B55", "B56",
        "B62", "B64", "B65", "B67", "B71", "B72", "B73", "B75", "B76",
    ],
    "B7C": [
        "B7", "B8", "B13", "B27", "B41", "B42", "B47", "B48", "B54",
        "B55", "B56", "B60", "B61", "B81",
    ],
    "B8C": ["B8", "B18", "B38", "B39", "B64", "B65"],
    "B12C": [
        "B12", "B44", "B45", "B13", "B37", "B41", "B47", "B21", "B49",
        "B50", "B40", "B60", "B61",
    ],
}


def antigen_to_serotype(value):
    """Convert A*02:01/B*57 to A2/B57; non class-I values return None."""
    match = re.match(r"^([AB])\*?0*(\d+)", str(value or "").upper())
    return f"{match.group(1)}{int(match.group(2))}" if match else None


def groups_for_antigen(value):
    serotype = antigen_to_serotype(value)
    if not serotype:
        return []
    return [name for name, antigens in CREG_GROUPS.items() if serotype in antigens]


def evaluate_creg(antibodies, donor_alleles=()):
    antibody_serotypes = sorted(
        {serotype for item in antibodies if (serotype := antigen_to_serotype(item))}
    )
    donor_serotypes = sorted(
        {serotype for item in donor_alleles if (serotype := antigen_to_serotype(item))}
    )
    active_groups = sorted(
        {
            group
            for antigen in antibody_serotypes
            for group in groups_for_antigen(antigen)
        }
    )
    potential = []
    for donor_antigen in donor_serotypes:
        shared_groups = sorted(
            set(groups_for_antigen(donor_antigen)).intersection(active_groups)
        )
        if shared_groups and donor_antigen not in antibody_serotypes:
            potential.append({"donor_antigen": donor_antigen, "groups": shared_groups})
    return {
        "has_antibody": bool(antibody_serotypes),
        "antibody_antigens": antibody_serotypes,
        "active_groups": active_groups,
        "donor_antigens": donor_serotypes,
        "potential_conflicts": potential,
        "has_potential_conflict": bool(potential),
    }


def table_for_antibodies(antibodies):
    active = {
        group
        for antibody in antibodies
        for group in groups_for_antigen(antibody)
    }
    antibody_serotypes = {
        serotype for item in antibodies if (serotype := antigen_to_serotype(item))
    }
    return [
        {
            "name": name,
            "active": name in active,
            "antigens": [
                {"name": antigen, "exact": antigen in antibody_serotypes}
                for antigen in antigens
            ],
        }
        for name, antigens in CREG_GROUPS.items()
    ]
