# Remove start time and end time
REMOVE_START_TIME = 900
REMOVE_END_TIME = 900

# Limits
LIMITE_DIA = 65
LIMITE_NOCHE = 55
LIMITE_TARDE = 55

# Time limits for evaluation indicadores
LD_SECONDS = 21600
LE_SECONDS = 7200
LN_SECONDS = 14400


# Plotting Flags there are 9 flags to plot the following plots
PLOT_NIGHT_EVOLUTION = False
PLOT_NIGHT_EVOLUTION_15_MIN = False 

PLOT_PREDIC_LAEQ_15_MIN = False
PLOT_PREDICTION_STACK_BAR = False
PLOT_PREDICTION_MAP = False
PLOT_TREE_MAP = True

PLOT_MAKE_TIME_PLOT = False

PLOT_HEATMAP_EVOLUTION_HOUR = False 
PLOT_HEATMAP_EVOLUTION_15_MIN = False 
PLOT_INDICADORES_HEATMAP = False

PLOT_DAY_EVOLUTION = False 
PLOT_PERIOD_EVOLUTION = False 


######################## SLM COLUMN MAPS #####################################
"""Sonometer column maps for different SLMs. The column maps are used to
   standardize the column names of the different SLMs. The column maps are
        LAEQ_COLUMN: LAeq column name
        LAMAX_COLUMN: LAFmax column name
        LAMIN_COLUMN: LAFmin column name

   The column maps are used in the following functions:
        get_data_814
        get_data_824
        get_data_lx_ES
        get_data_lx_EN
        get_data_cesva
        get_data_SV307
        get_data_audio
"""
        
larsonlx_dict = {'LAEQ_COLUMN': 'LAeq',
                 'LAMAX_COLUMN': 'LAFmax',
                 'LAMIN_COLUMN': 'LAFmin'}


larson824_dict = {'LAEQ_COLUMN': 'Leq',
                  'LAMAX_COLUMN': 'Max',
                  'LAMIN_COLUMN': 'Min'}


larson814_dict = {'LAEQ_COLUMN': 'Leq',
                  'LAMAX_COLUMN': 'Max',
                  'LAMIN_COLUMN': 'Min'}


cesva_dict = {'LAEQ_COLUMN': 'LA1s',
              'LAMAX_COLUMN': 'LAFmax1s',
              'LAMIN_COLUMN': 'LAFmin1s'}


sv307_dict = {'LAEQ_COLUMN': 'LAeq (Ch1, P1) [dB]',
              'LAMAX_COLUMN': 'LAFmax (Ch1, P1) [dB]',
              'LAMIN_COLUMN': 'LAFmin (Ch1, P1) [dB]'} 


sonometer_bilbo_dict = {'LAEQ_COLUMN': 'Value'}


audiopost_dict = {'LAEQ_COLUMN': 'LA',
                  'LAMAX_COLUMN': 'LAmax',
                  'LAMIN_COLUMN': 'LAmin'}


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


COLOR_PALLET_URBAN = {
            'Other human': '#2986cc', # BLUE
            'Electro-mechanical': '#cc0000', # RED
            'Voice': '#6aa84f', #  green 6aa84f
            'Motorised transport': '#ffa500', # orange
            'Geonature': '#8e7cc3', # PURPLE
            'Animal': '#9b5f00', # BROWN
            'Music': '#d172a4', # PINK
            'Background': '#000000', # BLACK
            'Other Sounds': '#c9d631', # yellow
            'Social/communal': '#d8cbf8', # Light purple
            'Human movement': '#40b674', # light green 40b674
        }


C_MAP_GRADIENT = {
    1: '#C8FFC8',
    2: '#00C800',
    3: '#007800',
    4: '#FFFF00',
    5: '#FFC878',
    6: '#FF9600',
    7: '#FF0000',
    8: '#780000',
    9: '#FF00FF',
    10: '#8C3CFF',
    11: '#000078',
}