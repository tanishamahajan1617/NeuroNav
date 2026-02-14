import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib

def generate_driver_data(n=20000):
    print("Generating driver data...")

    road_types = np.random.choice(['highway', 'primary','residential','service','unclassified'], size=n)
    weather = np.random.choice(['sunny', 'rainy', 'foggy'], size=n)
    traffic = np.random.choice(['low','normal','high'],n)
    speed = np.random.randint(20, 120, size=n)

    hours_driven = np.random.randint(0, 14, size=n)


    risk_scores = []
    for i in range(n):
        r = 0.1

        fatigue_factor = 0
        if hours_driven[i] > 8:
            fatigue_factor = 0.4
        elif hours_driven[i]>5:
            fatigue_factor =0.2

        if weather[i] in ['rainy', 'foggy']:
            r += 0.3
            if fatigue_factor > 0:
                r += 0.2
        if traffic[i] == 'high' and fatigue_factor > 0:
            r += 0.3
        if road_types[i] == 'highway' and speed[i] > 90:
            if fatigue_factor > 0.3:

                r += 0.5
            else:
                r += 0.02

        r+= fatigue_factor
        risk_scores.append(min(r, 1.0))


     
    df = pd.DataFrame({
        'road_type': road_types,
        'weather': weather,
        'traffic': traffic,
        'speed': speed,
        'hours_driven': hours_driven,
        'risk_score': risk_scores
    })
    
    return df



if __name__ == "__main__":
    df = generate_driver_data()
    
    le_road = LabelEncoder()
    le_weather = LabelEncoder()
    le_traffic = LabelEncoder()
    
    df['road_type'] = le_road.fit_transform(df['road_type'])
    df['weather'] = le_weather.fit_transform(df['weather'])
    df['traffic'] = le_traffic.fit_transform(df['traffic'])

    joblib.dump(le_road, 'data/le_road.pkl')
    joblib.dump(le_weather, 'data/le_weather.pkl')
    joblib.dump(le_traffic, 'data/le_traffic.pkl')

    X = df.drop('risk_score', axis=1)
    y = df['risk_score']
    
    X_train , X_test , y_train , y_test = train_test_split(X,y,test_size=0.2,random_state=42)    
    model = keras.Sequential([
        layers.Dense(64, activation='relu', input_shape=(5,)),
        layers.BatchNormalization(),
        layers.Dense(32, activation='relu'),
        layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])
    
    model.fit(X_train, y_train, epochs=20, batch_size=32, validation_split=0.2)
    print(model.predict(X_test))
    print(y_test)
    model.save('data/driver_risk_model.h5')
    
