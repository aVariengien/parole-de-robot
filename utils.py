def fmt(x):
    # 6 crans
    qualifiers = {
        5: "Très peu probable",
        20: "Peu probable",
        40: "Possible",
        60: "Probable",
        80: "Très probable",
        95: "Quasi certain",
    }
    qualifiers = {
        0: "Extremement négatif",
        10: "Très négatif",
        40: "Négatif",
        50: "Mitigé",
        60: "Positif",
        90: "Très positif",
        100: "Extremement positif",
    }
    # Closest qualifier
    return qualifiers[min(qualifiers.keys(), key=lambda k: abs(k - x))] + f" ({x}/100)"
