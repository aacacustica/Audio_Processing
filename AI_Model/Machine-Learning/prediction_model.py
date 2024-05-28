import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

ocio_data = pd.read_excel(r"C:\Users\scjaa\AAC - CENTRO DE ACUSTICA APLICADA, S.L\I + D + i - Documentos\machine_learning\00_DATA\postprocessing\BI-RUI-C002LD-leisure.xlsx")
trafico_data = pd.read_excel(r"C:\Users\scjaa\AAC - CENTRO DE ACUSTICA APLICADA, S.L\I + D + i - Documentos\machine_learning\00_DATA\postprocessing\BI-RUI-BR11LD-traffic.xlsx")

ocio_data['datetime'] = pd.to_datetime(ocio_data['datetime'])
trafico_data['datetime'] = pd.to_datetime(trafico_data['datetime'])

ocio_data['hour'] = ocio_data['datetime'].dt.hour
ocio_data['day_of_week'] = ocio_data['datetime'].dt.dayofweek
trafico_data['hour'] = trafico_data['datetime'].dt.hour
trafico_data['day_of_week'] = trafico_data['datetime'].dt.dayofweek

ocio_data['label'] = 0
trafico_data['label'] = 1

combined_data = pd.concat([ocio_data, trafico_data], ignore_index=True)

X = combined_data[['Value', 'hour', 'day_of_week']]
y = combined_data['label']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
classification_rep = classification_report(y_test, y_pred)

print("Accuracy:", accuracy)
print("Classification Report:\n", classification_rep)
