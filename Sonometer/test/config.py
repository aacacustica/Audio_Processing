# Limits
LIMITE_DIA = 65
LIMITE_NOCHE = 55
LIMITE_TARDE = 55

# Time limits for evaluation indicadores
LD_SECONDS = 21600
LE_SECONDS = 7200
LN_SECONDS = 14400

# Plotting Flags
PLOT_MAKE_TIME_PLOT = True # Done
PLOT_HEATMAP_EVOLUTION = True # Done
PLOT_INDICADORES_HEATMAP = True # Done 
PLOT_DAY_EVOLUTION = True # Done
PLOT_PERIOD_EVOLUTION = True # Done
PLOT_NIGHT_EVOLUTION = True # Done
PLOT_NIGHT_EVOLUTION_15_MIN = True # Almost done

# Constants for plotting Colors
C_MAP_WEEKDAY = {
            'Lunes': '#cc0000', # RED
            'Martes': '#8e7cc3', # PURPLE
            'Miércoles': '#9b5f00', # BROWN
            'Jueves': '#2986cc', # BLUE
            'Viernes': '#ffa500', # ORANGE
            'Sábado': '#6aa84f', # GREEN
            'Domingo': '#d172a4', # PINK
        }

C_MAP_WEEKDAY_NIGHT = {
            'Lunes-Martes': '#cc0000', # RED
            'Martes-Miércoles': '#8e7cc3', # PURPLE
            'Miércoles-Jueves': '#9b5f00', # BROWN
            'Jueves-Viernes': '#2986cc', # BLUE
            'Viernes-Sábado': '#ffa500', # ORANGE
            'Sábado-Domingo': '#6aa84f', # GREEN
            'Domingo-Lunes': '#d172a4', # PINK
}

PERCENTIL_COLOUR = {
    1: '#B28DFF',
    5: '#6EB5FF',
    10: '#B2E2F2',
    50: '#FFABAB',
    90: '#9E9E9E'
}