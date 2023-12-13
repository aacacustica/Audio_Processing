# 0.1
# Pass by usando medidas de aforadores automáticos
# A continuación se tratará de extraer el pass by usando los datos de un sonómetro en continuo que
# esta en simultaneo con una estación aforadora. El objetivo es relacionar la información de niveles
# de ruido cada segundo con las detecciones de pasos y velocidades que entrega la estación aforadora

# [1]: 
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
#plt.style.use("bmh")
# %matplotlib inline


# [2]:
def leq(levels:np.ndarray)->float:
    levels = levels[~np.isnan(levels)]
    l = np.array(levels)
    return 10*np.log10(np.mean(np.power(10,l/10)))

# 0.2
# Lectura de datos de la estación aforadora
# El rada entrega información de dirección de circulación, velocidad y tipo de vehiculo según longitud
# entre las siguientes clases:
# * 1:bicis y motos
# * 2:turismos
# * 3:camión
# * 4:camión largo


df = pd.read_csv("20230203.CSV", sep=";")
df.head()


df["datetime"] = pd.to_datetime(df["Date"] + " " + df["Time"], format="%d/%m/%y %H:%M:%S")
# Delay con respecto a sonómetro
df["datetime"] = df["datetime"] + pd.Timedelta("25S")
# el 95% de las detecciones son de vehiculos tipo turismo, y 3% para camiones


df["Type"].value_counts(normalize=True)
sns.catplot(data=df, x="Type",y="Speed");



#  1 LECTURA DE DATOS NIVELES DE RUIDO
df_noise = pd.read_csv("Audiomoth2_Tanis_Aguirrebengoa_20230203_spl.csv",parse_dates=["date"])
df_noise["date"] = df_noise["date"] + pd.Timedelta("1H")

# Inicilamente se usa el campo que contiene la información de los timestamps de las detecciónes para
# unir los datos de la estación de aforos con los niveles de ruido. Como la longitud de los datos
# de ruido no es igual a la de los datos de los aforos, se realiza una union “izquierda” en donde se
# conservan los datos de la tabla izquierda(ruido) y solo se unen los datos de aforo en los campos
# coincidentes.


# [8]: 
df_join = pd.merge(df_noise,df,left_on="date", right_on="datetime",how="left")
# Se puede observar en el siguiente gráfico como la detecciones del sistema de aforos concuerdan con
# los picos de niveles de ruido en este segmento.


# [9]: 
df_join = df_join.set_index("date")
df_temp = df_join.loc["2023-02-03 23:55:00":"2023-02-03 23:58:00"]
levels = df_temp["LA"].values
speed = df_temp["Speed"].values
plt.figure(figsize=(15,6))
plt.plot(df_temp.index, levels);
plt.plot(df_temp.index,speed+40,"*");


# 1.1
# Selección de pass bys
# Se seleccionan aquellas detecciones que tiene un espacio mayor a 10 segundos con la detección
# anteior y la siguiente

df_car_detections = df_join[~df_join["Speed"].isna()].copy()
df_car_detections["left"] = df_car_detections["datetime"].shift()
df_car_detections["right"] = df_car_detections["datetime"].shift(-1)
df_car_detections["diff_left"] = df_car_detections["datetime"] - df_car_detections["left"]
df_car_detections["diff_right"] = df_car_detections["right"] - df_car_detections["datetime"]

# Select clean pass bys
df_clean_pass_by = df_car_detections[ (df_car_detections["diff_left"] > "10s") & (df_car_detections["diff_right"] > "10s") ].copy()


# Usando estas detecciones se calcula el nivel exposición sonora con los datos de ruido y se grafican
# los niveles para comprpbar que corresponden con las formas de onda tipicas de pass by. Se puede
# observar que la mayoria siguen en este patrón aunque existen otras tantas que difieren del patrón
# tipico de pass-by

pass_by_width_seconds = 10
sel_pass = []
i = 0
plt.figure(figsize=(15,8))
for date_paso, pass_by in df_clean_pass_by.iterrows():

    df_temp = df_join.loc[date_paso - pd.Timedelta(f"{pass_by_width_seconds}s"):
    date_paso + pd.Timedelta(f"{pass_by_width_seconds}s") ]
    levels = df_temp["LA"]
    sel_pass.append(leq(levels) + np.log(8))
    plt.plot(levels.values, linewidth=0.15)
    #i+=1
    if i == 5:
        break

plt.xlabel("seconds")
plt.ylabel("LAeq1s")
plt.show()
df_clean_pass_by["SEL"] = sel_pass

# Finalmente se puede observar la relación entre velocidad y SEL de los datos recogidos con el pass
# by automático
sns.jointplot(data=df_clean_pass_by, x="Speed", y = "SEL",);