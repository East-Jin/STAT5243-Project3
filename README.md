# STAT5243-Project3
## OLD LINKS: 
## Live App(Original): https://zd2372.shinyapps.io/data_explorer/
## Live App(Changed): https://xl3548.shinyapps.io/my-python-app1/

## UPDATED LINKS: 
## https://dz2590.shinyapps.io/project3-router/ (This randomly assigns user version A or B)
## Version A: https://dz2590.shinyapps.io/project3-1/
## Version B: https://dz2590.shinyapps.io/project3-2/ 

---
title: "Untitled"
output: html_document
date: "2026-04-19"
---


## 4. Results & Insights

#### **4.1 Statistical Analysis Results**

This A/B test aimed to determine whether a guided onboarding experience with a built-in demo dataset (Version B) would significantly increase the dataset loading success rate compared to a blank interface requiring manual upload (Version A). The experiment recorded 70 active users, with 40 users cleanly assigned to the two variants (n=20 users in Group A and n=20 users in Group B).

-   **Primary Metric (Dataset Loading Success Rate):**

    -   **Version A (Control):** 9 out of 20 users successfully loaded a dataset (45.0% success rate).

    -   **Version B (Treatment):** 4 out of 20 users successfully loaded a dataset (20.0% success rate).

-   **Significance Testing:** Due to the small sample size (n = 40), a two-sided Fisher's Exact Test was employed rather than a standard Chi-square test.

    -   **P-value:** 0.1760

    -   **Conclusion:** At a significance level of α = 0.05, the p-value is greater than 0.05. Therefore, we **fail to reject the null hypothesis**. While there is a 25% absolute difference in conversion rates favoring the Control group, this difference is not statistically significant.

#### **4.2 User Behavior Insights**

Although the statistical results did not achieve significance, the behavioral data from Google Analytics 4 (GA4) revealed several counter-intuitive patterns:

-   **Engagement Disparity:** The Control group (Version A) generated significantly more page interactions, recording 400 `tab_view` events compared to 242 events in the Treatment group (Version B). This suggests that users presented with a blank interface spent more time navigating the application, potentially exploring the interface to understand how to upload their own data.

-   **The Conversion Bottleneck:** Across the experiment, 15 unique users reached the "EDA" tab, yet only 11 users successfully triggered the `dataset_loaded_success` event. This indicates a 35% drop-off rate between navigating to the analysis environment and actually loading data, highlighting a critical point of friction in the user journey.

-   **Demo Data Utilization:** In Version B, the built-in demo datasets (such as Titanic and Ames Housing) triggered 14 distinct interactions. This demonstrates that the guided design successfully captured initial user attention, but failed to translate that engagement into full task completion.

#### **4.3 Discussion and Limitations**

The unexpected underperformance of the guided onboarding version can be attributed to several factors and experimental limitations:

-   **Selection Bias:** All acquired traffic was categorized as "(direct) / (none)" within GA4. Given the context of this project, the user base primarily consisted of graduate statistics students. This highly technical demographic likely possesses a higher tolerance for blank interfaces and a strong preference for uploading their own custom datasets. For these users, the "blank page" was an expected workspace rather than a point of friction.

-   **Tracking Fragmentation:** Approximately 24 active users were categorized under the `(not set)` group dimension. This data loss was likely caused by advanced client-side privacy settings (e.g., ad-blockers, browser tracking prevention) prevalent among technical users, or by JavaScript race conditions where the tracking payload fired before the randomization algorithm completed its assignment. While we isolated the cleanly tracked users for a valid complete-case analysis, this fragmentation reduced the overall power of our statistical test.

-   **Cognitive Load of Onboarding:** While Version B was designed to reduce friction, a guided walkthrough can inadvertently introduce a different type of cognitive load. For advanced users who already understand data analysis workflows, a forced tutorial or pre-loaded demo may feel restrictive, leading to premature abandonment of the application.

```{python}
import pandas as pd
from scipy.stats import fisher_exact

# 1. Read the CSV file exported from GA4
# The first 6-7 lines of GA4 exports are usually report metadata, so we use skiprows to bypass them.
try:
    df = pd.read_csv("download.csv", skiprows=7, names=['Group', 'Event name', 'Active users', 'Event count', 'Extra'])
except FileNotFoundError:
    print("Error: File not found. Please ensure you have uploaded 'download.csv' to the Colab files pane on the left!")
    raise

# 2. Data Cleaning
# Remove empty rows without group information and filter out the '(not set)' ghost users
df = df.dropna(subset=['Group'])
df = df[df['Group'] != '(not set)']
if 'Extra' in df.columns:
    df = df.drop(columns=['Extra'])

# 3. Extract Core Metrics
# Find the active users who successfully loaded data ('dataset_loaded_success') for Group A and Group B
success_a_series = df[(df['Group'] == 'A') & (df['Event name'] == 'dataset_loaded_success')]['Active users']
success_b_series = df[(df['Group'] == 'B') & (df['Event name'] == 'dataset_loaded_success')]['Active users']

success_a = int(success_a_series.iloc[0]) if not success_a_series.empty else 0
success_b = int(success_b_series.iloc[0]) if not success_b_series.empty else 0

# Based on the GA4 data, the total number of users for each group is 20
total_a = 20
total_b = 20

fail_a = total_a - success_a
fail_b = total_b - success_b

print("=== Data Summary ===")
print(f"Group A (Control)   - Success: {success_a}, Fail: {fail_a}")
print(f"Group B (Treatment) - Success: {success_b}, Fail: {fail_b}")

# 4. Build Contingency Table & Perform Fisher's Exact Test
contingency_table = [[success_a, fail_a], 
                     [success_b, fail_b]]

odds_ratio, p_value = fisher_exact(contingency_table, alternative='two-sided')

print("\n=== Hypothesis Test Results ===")
print(f"Group A Conversion Rate: {(success_a / total_a) * 100:.1f}%")
print(f"Group B Conversion Rate: {(success_b / total_b) * 100:.1f}%")
print(f"P-value (Fisher's Exact Test): {p_value:.4f}")

if p_value < 0.05:
    print("Conclusion: Reject the null hypothesis. The difference is statistically significant.")
else:
    print("Conclusion: Fail to reject the null hypothesis. The difference is not statistically significant.")
```
