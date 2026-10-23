import seaborn as sns

WEEKDAYS_ES     = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
NIGHT_LABELS    = ["Lunes-Martes","Martes-Miércoles","Miércoles-Jueves","Jueves-Viernes","Viernes-Sábado","Sábado-Domingo","Domingo-Lunes"]
LE_SECONDS      = 7200
INDICATOR_ORDER = ["Ln", "Ld", "Le"]
PERIOD_ORDER    = ("Ld", "Le", "Ln")
PERIOD_ORDER_4H = ("Ld_1", "Ld_2", "Ld_3", "Le", "Ln_1", "Ln_2")

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

THIRD_OCTAVE_BANDS = (
    (12.5, "band_12_5_db"), 
    (16.0, "band_16_db"), 
    (20.0, "band_20_db"),
    (25.0, "band_25_db"), 
    (31.5, "band_31_5_db"), 
    (40.0, "band_40_db"),
    (50.0, "band_50_db"), 
    (63.0, "band_63_db"), 
    (80.0, "band_80_db"),
    (100.0, "band_100_db"), 
    (125.0, "band_125_db"), 
    (160.0, "band_160_db"),
    (200.0, "band_200_db"), 
    (250.0, "band_250_db"), 
    (315.0, "band_315_db"),
    (400.0, "band_400_db"), 
    (500.0, "band_500_db"), 
    (630.0, "band_630_db"),
    (800.0, "band_800_db"), 
    (1000.0, "band_1000_db"),
    (1250.0, "band_1250_db"), 
    (1600.0, "band_1600_db"),
    (2000.0, "band_2000_db"), 
    (2500.0, "band_2500_db"),
    (3150.0, "band_3150_db"), 
    (4000.0, "band_4000_db"),
    (5000.0, "band_5000_db"), 
    (6300.0, "band_6300_db"),
    (8000.0, "band_8000_db"), 
    (10000.0, "band_10000_db"),
    (12500.0, "band_12500_db"), 
    (16000.0, "band_16000_db"),
    (20000.0, "band_20000_db"),
)


