# STAT5243-Project3

A Python Shiny web application for interactive data analysis, extended with an A/B testing framework to study how onboarding design influences early task completion.

## Project Overview

This project was completed for STAT 5243: Applied Data Science.

We built a live Data Explorer app and then designed an A/B test to evaluate whether different onboarding experiences affect users’ ability to successfully begin using the application.

The app supports a multi-step workflow for:

* data loading
* data cleaning
* feature engineering
* exploratory data analysis

Since dataset loading is the first required step before users can access the rest of the workflow, our experiment focused on whether onboarding design affects dataset loading success.

## Research Question

Does a guided onboarding experience improve the likelihood that a user successfully loads a dataset into the application, compared with a more minimal interface?

### Hypotheses

* **H0:** There is no difference in dataset loading success rate between the two interface variants.
* **H1:** There is a difference in dataset loading success rate between the two interface variants.

## Live Apps

### Current Experiment Links

* **Router:** [https://dz2590.shinyapps.io/project3-router/](https://dz2590.shinyapps.io/project3-router/)
  Randomly assigns users to Version A or Version B.
* **Version A:** [https://dz2590.shinyapps.io/project3-1/](https://dz2590.shinyapps.io/project3-1/)
* **Version B:** [https://dz2590.shinyapps.io/project3-2/](https://dz2590.shinyapps.io/project3-2/)

### Earlier Deployment Links

* **Original App:** [https://zd2372.shinyapps.io/data_explorer/](https://zd2372.shinyapps.io/data_explorer/)
* **Changed App:** [https://xl3548.shinyapps.io/my-python-app1/](https://xl3548.shinyapps.io/my-python-app1/)

## What the App Does

The Data Explorer app was designed as a modular workflow with the following tabs:

* User Guide
* Data Loading
* Data Cleaning
* Feature Engineering
* EDA

The application supports multiple file formats, including CSV, TSV, Excel, JSON, and Parquet, and also includes built-in datasets such as Titanic and Ames Housing.

## A/B Testing Design

This study used a between-subjects A/B design.

Users first entered through a router application, which randomly assigned them to one of two app versions, stored the assignment in local storage, and redirected them to the corresponding deployment.

To measure user behavior, the app was instrumented with Google Analytics 4. Tracked events included:

* experimental assignment
* tab views
* engagement-related interactions
* button clicks
* dataset loading success

The main outcome metric was dataset loading success, since loading a dataset is the first necessary step before users can proceed to cleaning, feature engineering, or EDA.

## Data Collection

User interaction data were collected from the live deployed application through GA4 event tracking.

* Total active users recorded: 70
* Users cleanly assigned and retained for inference: 40
* Group A: 20 users
* Group B: 20 users

For analysis, the exported GA4 data were cleaned by:

* removing rows with missing group labels
* excluding observations marked as “(not set)”

The cleaned data were then used to construct a 2×2 contingency table for statistical testing.

## Statistical Analysis

Because the primary outcome was binary, users were classified as either:

* successful dataset loading
* unsuccessful dataset loading

Given the small usable sample size, a two-sided Fisher’s Exact Test was used instead of a Chi-square test.

### Primary Metric Results

* **Version A:** 9/20 users succeeded (45.0%)
* **Version B:** 4/20 users succeeded (20.0%)

### Test Result

* **P-value:** 0.1760

At the 0.05 significance level, we **failed to reject the null hypothesis**. The observed difference was not statistically significant, although the raw conversion rate was higher in Version A.

## Results and Insights

Even though the difference was not statistically significant, the experiment still revealed several useful behavioral patterns.

* Higher interaction volume in Version A:
  Version A recorded 400 `tab_view` events, compared with 242 `tab_view` events in Version B.

* A conversion bottleneck remained early in the workflow:
  15 users reached the EDA tab, but only 11 users triggered `dataset_loaded_success`.

* Built-in demo datasets attracted attention in Version B:
  Demo datasets such as "Titanic" and "Ames Housing" generated 14 interactions, but that engagement did not translate into higher completion of the main task.

Overall, the experiment suggests that onboarding design can influence how users interact with the application, even when it does not improve the primary conversion outcome.

## Interpretation

The main takeaway is that the guided onboarding intervention did not produce a statistically significant improvement in dataset-loading success.

A possible explanation is that many users in this study were already comfortable with data workflows. For those users, a simpler workspace with direct upload options may have felt faster and more intuitive than a more guided first-use experience.

This result suggests that onboarding is not equally beneficial for every audience. A future improvement would be to make the existing pathways more adaptive, so that experienced users can move quickly into the workflow while less experienced users receive stronger guidance when needed.

## Limitations

This study has several limitations:

* The usable sample size was small.
* The participant pool likely came from direct sharing and was not broadly representative.
* A portion of traffic appeared under “(not set)”, which reduced the usable sample.
* Assignment was stored at the browser level rather than through authenticated user identities.
* The experiment focused on early task completion rather than longer-term engagement.

## Repository Structure

```text
STAT5243-Project3/
│
├── .idea/
│   ├── inspectionProfiles/
│   │   └── profiles_settings.xml
│   ├── .name
│   ├── STAT5234-Project3.iml
│   ├── misc.xml
│   ├── modules.xml
│   ├── vcs.xml
│   └── workspace.xml
│
├── __pycache__/
│   ├── app.cpython-313.pyc
│   └── app_B.cpython-313.pyc
│
├── data/
│   ├── ames_housing.csv
│   └── titanic.csv
│
├── docs/
│   └── ARCHITECTURE.md
│
├── modules/
│   ├── __pycache__/
│   │   ├── __init__.cpython-313.pyc
│   │   ├── data_cleaning.cpython-313.pyc
│   │   ├── data_loading.cpython-313.pyc
│   │   ├── data_loading_c.cpython-313.pyc
│   │   ├── eda.cpython-313.pyc
│   │   ├── feature_engineering.cpython-313.pyc
│   │   ├── user_guide.cpython-313.pyc
│   │   └── user_guide_c.cpython-313.pyc
│   ├── __init__.py
│   ├── data_cleaning.py
│   ├── data_loading.py
│   ├── data_loading_c.py
│   ├── eda.py
│   ├── feature_engineering.py
│   ├── user_guide.py
│   └── user_guide_c.py
│
├── router/
│   ├── rsconnect-python/
│   │   └── router.json
│   ├── requirements.txt
│   └── router_app.py
│
├── rsconnect-python/
│   └── STAT5234-Project3-main.json
│
├── shared/
│   ├── __pycache__/
│   │   ├── __init__.cpython-313.pyc
│   │   ├── data_store.cpython-313.pyc
│   │   └── sample_datasets.cpython-313.pyc
│   ├── __init__.py
│   ├── data_store.py
│   └── sample_datasets.py
│
├── README.md
├── app.py
├── app_B.py
└── requirements.txt
```

## How to Run Locally

1. Clone the repository.
2. Install dependencies from `requirements.txt`.
3. Run the files
   * `app.py` - Version A
   * `app_B.py` - Version B
  
For the router-based experiment setup,

4. Deploy the files to shinyapps.io
  * `app.py`
  * `app_B.py`
5. Copy and paste the URLs assigned to these versions into the file: 
  * `router_app.py`
6. Deploy the file to shinyapps.io
  * `router_app.py`

