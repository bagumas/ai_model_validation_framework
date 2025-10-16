import pickle
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

# Load iris and train a tiny classifier
iris = load_iris(as_frame=True)
X = iris.data
y = iris.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

clf = LogisticRegression(max_iter=200)
clf.fit(X_train, y_train)

# Save model
with open("models/iris_logreg.pkl", "wb") as f:
    pickle.dump(clf, f)

# Export test set to CSV (features + target as last column)
df = X_test.copy()
df["target"] = y_test
df.to_csv("data/iris.csv", index=False)

print("Sample model saved to models/iris_logreg.pkl and data/iris.csv created.")
