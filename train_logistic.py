import pandas as pd
from sklearn.linear_model import LogisticRegression
import joblib
import os

# Load dataset
df = pd.read_csv("data/customer_data.csv")

# Select only numeric features
X = df[["Age", "Income", "PreviousPurchases", "TimeSpent"]]

# Target column
y = df["Purchased"]

# Train model
model = LogisticRegression(max_iter=1000)
model.fit(X, y)

# Create folder if it doesn't exist
os.makedirs("saved_models", exist_ok=True)

# Save model
joblib.dump(model, "saved_models/logistic_model.pkl")

print("✅ Logistic Regression Model Trained Successfully!")