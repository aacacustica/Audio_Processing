import seaborn as sns

WEEKDAYS_ES     = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
NIGHT_LABELS    = ["Lunes-Martes","Martes-Miércoles","Miércoles-Jueves","Jueves-Viernes","Viernes-Sábado","Sábado-Domingo","Domingo-Lunes"]
LE_SECONDS      = 7200
INDICATOR_ORDER = ["Ln", "Ld", "Le"]
PERIOD_ORDER    = ("Ld", "Le", "Ln")

LEGACY_CMAP = sns.color_palette(
    palette=[
        "#C8FFC8", "#00C800", "#007800", "#FFFF00",
        "#FFC878", "#FF9600", "#FF0000", "#780000",
        "#FF00FF", "#8C3CFF", "#000078",
    ],
    n_colors=11,
)

OCA_LIMITS = {
    "OCA_RESIDENTIAL": {"ld": 65.0, "le": 65.0, "ln": 55.0},
    "OCA_LEISURE":     {"ld": 73.0, "le": 73.0, "ln": 63.0},
    "OCA_OFFICE":      {"ld": 70.0, "le": 70.0, "ln": 65.0},
    "OCA_INDUSTRIAL":  {"ld": 75.0, "le": 75.0, "ln": 65.0},
    "OCA_CULTURE":     {"ld": 60.0, "le": 60.0, "ln": 50.0},
}

NIGHT_PALETTE = {
    "Lunes-Martes":          "#cc0000",
    "Martes-Miércoles":      "#8e7cc3",
    "Miércoles-Jueves":      "#9b5f00",
    "Jueves-Viernes":        "#2986cc",
    "Viernes-Sábado":        "#ffa500",
    "Sábado-Domingo":        "#6aa84f",
    "Domingo-Lunes":         "#d172a4",
}

URBAN_COLORS = {
    "Other human":          "#2986cc",
    "Electro-mechanical":   "#cc0000",
    "Voice":                 "#6aa84f",
    "Motorised transport":   "#ffa500",
    "Geonature":             "#8e7cc3",
    "Animal":                "#9b5f00",
    "Music":                 "#d172a4",
    "Background":            "#000000",
    "Other Sounds":          "#c9d631",
    "Social/communal":       "#d8cbf8",
    "Human movement":        "#40b674",
}

PORT_COLORS = {
    "Siren":                "#2986cc",
    "Sound Event":          "#cc0000",
    "Transport":            "#6aa84f",
    "Human":                "#ffa500",
    "Nature":               "#8e7cc3",
    "Animal":               "#9b5f00",
    "Music":                "#d172a4",
    "Engine":               "#000000",
}
