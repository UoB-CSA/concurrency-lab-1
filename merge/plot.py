import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Read in the saved CSV data.
benchmark_data = pd.read_csv('results.csv', header=0, names=['name', 'time', 'range'])

# Go stores benchmark results in nanoseconds. Convert all results to seconds.
benchmark_data['time'] /= 1e+9

# Use the name of the benchmark to extract the length of the array.
benchmark_data['array_length'] = benchmark_data['name'].str.extract('(\d+)').apply(pd.to_numeric)

# Use the name of the benchmark to extract the type of code (sequential or parallel).
benchmark_data['type'] = benchmark_data['name'].str.extract('(\w+)/')

# Plot a bar chart.
ax = sns.barplot(data=benchmark_data, x='array_length', y='time', hue='type')

# Set descriptive axis lables.
ax.set(xlabel='Array Length', ylabel='Time taken (s)')

# Display the full figure.
plt.show()