import pandas as pd
from pca import pca

# Load dataset
df = pd.read_csv("final_sep_data/basic_stats.csv")
y = pd.read_csv("final_sep_data/scored.csv")
df 
X = (df - df.mean())/df.std()
col_labels = df.columns

# Initialize pca with default parameters
model = pca(n_components= 2, normalize=True)

# Fit transform and include the column labels and row labels
results = model.fit_transform(X, col_labels = df.columns, row_labels = y['Scored?'].tolist())
fig, ax = model.biplot(cmap=None, legend=False, figsize=(20, 12), dpi=50)
model.plot()


# Scatter plot with loadings
model.biplot()