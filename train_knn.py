import pandas as pd
from sklearn.neighbors import NearestNeighbors
import joblib
import os

# Load dataset
df = pd.read_csv("data/products.csv")

# Features for KNN
X = df[["Price", "Rating"]]

# Train model
knn = NearestNeighbors(n_neighbors=5)
knn.fit(X)

# Save model
os.makedirs("saved_models", exist_ok=True)
joblib.dump(knn, "saved_models/knn_model.pkl")

print("✅ KNN Model Trained Successfully")