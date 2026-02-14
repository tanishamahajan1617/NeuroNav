🚖 Project Title: NeuroNav (Fatigue & Context-Aware Routing System)
1. Abstract (The "Elevator Pitch")
NeuroNav is an intelligent navigation system designed to prioritize driver safety over speed. Unlike traditional navigation apps (like Google Maps) that always suggest the fastest route, NeuroNav dynamically alters the path based on the driver's physical state (fatigue level) and environmental conditions (weather, time, traffic).
It uses a Deep Learning Neural Network to analyze road risks in real-time and calculates a "Safety Cost" for every road segment, ensuring that a tired driver in the rain is guided through a safer, simpler route rather than a high-speed, risky highway.
2. The Problem Statement
Standard navigation systems optimize for Distance or Time. However, they fail to account for human factors:
Driver Fatigue: A driver who has been on a 10-hour shift has slower reaction times. Sending them on a high-speed highway or a complex intersection is dangerous.
Contextual Risk: A road that is safe on a sunny day becomes deadly during a rainy night.
Static Routing: Current apps do not change their recommendation logic based on who is driving and how they are feeling.

3. The Solution & Business Logic
NeuroNav introduces a "Fatigue-Aware" Algorithm. The system takes the driver's shift duration (hours_driven) as a key input.
Driver State Logic Applied Route Characteristic
Fresh (0-4 hours) Reaction time is high. Priority is Efficiency. Fastest Route (Highways, Main Roads).
Moderate (4-8 hours) Caution advised. Balanced Route (Avoids extreme traffic).
Fatigued (8+ hours) Reaction time is low. Priority is Survival. Safest Route (Slower speeds, fewer turns, avoids highways).

4. Technical Architecture
The project follows a modular Data Science Pipeline:
A. The Brain (Deep Learning Model)
Type: Feed-Forward Neural Network (MLP - Multi-Layer Perceptron).
Framework: TensorFlow / Keras.
Inputs: Road Type, Weather Condition, Time of Day, Traffic Density, Speed Limit, Hours Driven.
Output: A Risk Score (0.0 to 1.0) for every single road segment.
Training: Trained on synthetic datasets representing real-world accident probabilities (e.g., Rain + Night + Fatigue = High Risk).
B. The Environment (Graph Theory)
Data Source: OpenStreetMap (OSM) via osmnx.
Location: Patiala, Punjab (can be scaled to any city).
Dynamic Weighting: instead of just distance, every edge has a safety_cost:

        Safety Cost = Length (1 + (Risk Score x Fatigue Penalty))
