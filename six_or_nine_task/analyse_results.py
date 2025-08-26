import os
import pandas as pd
import glob
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

path = os.getcwd()

## load results
experiment_dir = os.path.join(path, "six_or_nine_task")
results_dir = os.path.join(experiment_dir, "results")

models = ["gpt-4o"]
ai_df = pd.DataFrame()
for base_model in models:
    pattern = f"SoN_{base_model}_full_1000*.csv"
    filepaths = glob.glob(os.path.join(results_dir, pattern))
    for filepath in filepaths:
        temp_df = pd.read_csv(filepath)
        ai_df = pd.concat([ai_df, temp_df], ignore_index=True)
ai_df["accuracy"] = (ai_df["answer"] == ai_df["correct_answer"]).astype(int)
ai_df["subject_type"] = "AI"

### Select subset
subset = "level"
ai_df2 = ai_df[ai_df["set"].str.contains(subset)].copy()

## Display results
grouped = ai_df2.groupby(['set', 'type'])['accuracy'].mean().reset_index()
sns.barplot(data=grouped, x='set', y='accuracy', hue='type')
plt.ylabel('Mean Accuracy')
plt.title('Mean Accuracy by Set and Type')
plt.tight_layout()
plt.show()

n_bins = 50
ai_df2['rotation_bin'] = pd.cut(ai_df2['figure_rotation'],
                               bins=n_bins,
                               labels=False,
                               include_lowest=True)
bin_edges = np.linspace(0, 360, n_bins + 1)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
ai_df2['rotation_bin_center'] = ai_df2['rotation_bin'].map(
    lambda x: bin_centers[int(x)] if pd.notna(x) else np.nan
)
plt.figure(figsize=(15, 8))
g = sns.FacetGrid(ai_df2, col='type', hue='set', col_wrap=2, height=4, aspect=1.2, palette='Blues')
g.map(sns.lineplot, 'rotation_bin_center', 'accuracy', marker='o', linewidth=2, markersize=6)
g.set_xlabels('Figure Rotation (degrees)')
g.set_ylabels('Mean Accuracy')
g.set_titles('{col_name}')
for ax in g.axes.flat:
    ax.set_xlim(0, 360)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(np.arange(0, 361, 45))
g.add_legend(title='set', loc='upper right')
plt.suptitle('Accuracy vs Figure Rotation by Set and Type', y=0.99)
plt.tight_layout()
plt.show()




