<div align="center">

# WhatIf

### Financial Decision Support Platform

A Django-based platform that combines **Large Language Models**,  
**Machine Learning**, and **Explainable AI** to evaluate financial decisions before execution.

<br>

<img src="images/home.png" width="100%" alt="WhatIf Home Page">

<br>

![Django](https://img.shields.io/badge/Django-Web%20Framework-092E20?logo=django)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![CatBoost](https://img.shields.io/badge/CatBoost-Machine%20Learning-EF7B45)
![SHAP](https://img.shields.io/badge/SHAP-Explainable%20AI-5B5FC7)
![LLM](https://img.shields.io/badge/LLM-Generative%20AI-8A5CF6)

</div>

---

## About

**WhatIf** is an AI-powered financial decision support platform designed to help organizations evaluate high-impact financial decisions before execution.

Instead of manually reviewing financial reports, spreadsheets, and multiple financial indicators, the user describes a decision in natural language, such as opening a new branch or purchasing equipment.

The platform then extracts the decision details, combines them with the company’s financial indicators, predicts the associated risk level, and explains the factors that influenced the prediction.

By combining an **LLM**, **CatBoost**, and **SHAP**, WhatIf provides faster, clearer, and more transparent financial decision support.

---

## The Problem

Organizations regularly make decisions involving significant financial impact, including:

- Opening new branches
- Purchasing equipment and assets
- Expanding the workforce
- Launching marketing campaigns
- Entering new markets
- Developing technical systems

Evaluating these decisions often requires financial expertise, reviewing several reports, and calculating multiple indicators. This process can take considerable time, while some small or emerging organizations may not have dedicated financial analysts.

---

## The Solution

WhatIf provides an intelligent assistant that allows the user to enter a financial decision in natural language.

The platform:

1. Understands the decision using an LLM.
2. Extracts the decision type and estimated cost.
3. Combines the decision with the company’s financial indicators.
4. Predicts the risk level using CatBoost.
5. Explains the prediction using SHAP.
6. Displays the result through a clear and interactive interface.
7. Stores previous analyses in a personalized decision dashboard.

---

## Key Features

<table>
<tr>
<td width="50%">

### Natural Language Analysis
Users can describe financial decisions naturally without completing complex financial forms.

</td>
<td width="50%">

### Risk Classification
The platform classifies decisions as low, medium, or high risk.

</td>
</tr>

<tr>
<td width="50%">

### Explainable Predictions
SHAP identifies the financial factors that contributed most to each prediction.

</td>
<td width="50%">

### AI-Generated Explanation
The prediction is transformed into a clear financial explanation that supports user understanding.

</td>
</tr>

<tr>
<td width="50%">

### Decision Dashboard
Users can review previous decisions and monitor their risk distribution.

</td>
<td width="50%">

### User Authentication
Each user has a secure account and an independent decision history.

</td>
</tr>
</table>

---

## System Workflow

```text
Natural Language Financial Decision
                  │
                  ▼
        Large Language Model
     Decision Type & Cost Extraction
                  │
                  ▼
      Financial Feature Construction
                  │
                  ▼
       CatBoost Risk Classification
                  │
          ┌───────┴───────┐
          ▼               ▼
 SHAP Explainability   Risk Level
          │               │
          └───────┬───────┘
                  ▼
      AI-Generated Explanation
                  │
                  ▼
       Financial Decision Report
```

---

## Machine Learning

Six machine learning models were trained and evaluated:

- CatBoost
- LightGBM
- XGBoost
- Random Forest
- Decision Tree
- Logistic Regression

**CatBoost** was selected as the final model after achieving the best overall performance among the evaluated models.

The final evaluation used **10-Fold Cross-Validation** to provide a more reliable estimate of model performance.

### Model Inputs

The prediction pipeline uses financial indicators such as:

- Annual revenue
- Operating expenses
- Net profit
- Profit margin
- Number of employees
- Total assets
- Total debt
- Debt-to-assets ratio
- Cash flow
- Decision type
- Decision cost

### Risk Output

The model classifies each decision into one of three levels:

```text
Low Risk
Medium Risk
High Risk
```

---

## Explainable AI

WhatIf uses **SHAP** to explain the model’s prediction.

Instead of displaying only the final risk level, the platform shows which financial factors increased or decreased the predicted risk.

This makes the result more transparent and allows financial analysts and decision-makers to verify the reasoning behind the model’s output.

---

## Screenshots

### Home Page

<img src="images/home.png" width="100%" alt="WhatIf Home Page">

The home page presents an overview of the user’s analyses and provides quick access to new decisions and previous records.

---

### Decision Dashboard

<img src="images/dashboard.png" width="100%" alt="WhatIf Decision Dashboard">

The dashboard displays the total number of analyzed decisions, their risk distribution, and the user’s decision history.

---

### AI Decision Analysis

<img src="images/analysis.png" width="100%" alt="WhatIf Decision Analysis">

The analysis page displays:

- The extracted decision and cost
- The predicted risk level
- The financial reasons behind the prediction
- The most influential factors according to SHAP
- A clear recommendation based on the analysis

---

## Technology Stack

| Layer | Technologies |
|---|---|
| Backend | Django, Python |
| Generative AI | Large Language Model |
| Machine Learning | CatBoost, Scikit-learn |
| Explainable AI | SHAP |
| Data Processing | Pandas |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLite |
| Version Control | Git, GitHub |

---

## Project Structure

```text
WhatIf/
│
├── accounts/
│   ├── Authentication views
│   ├── Login and registration templates
│   └── Authentication styling
│
├── ml_app/
│   ├── Machine learning pipeline
│   ├── LLM integration
│   ├── SHAP explainability
│   ├── Decision dashboard
│   ├── Templates and static files
│   ├── Trained model
│   └── Database migrations
│
├── whatif/
│   ├── Django settings
│   ├── Main URL configuration
│   ├── ASGI configuration
│   └── WSGI configuration
│
├── manage.py
├── requirements.txt
└── .gitignore
```

---

## Data

The current prototype was developed using synthetic financial data representing hypothetical companies.

Synthetic data was used because real organizational financial data is sensitive and generally not publicly available.

The dataset includes company financial indicators, decision information, and corresponding risk classifications.

---

## Future Enhancements

- Train and validate the platform using anonymized real-world financial data to improve prediction accuracy and reliability.
- Expand the platform beyond financial institutions to support small, medium, and large companies across different industries.
- Add an intelligent alternative-decision engine that recommends a lower-risk option whenever a financial decision is classified as high risk.

---

## Important Notice

This platform is a decision-support prototype and is not intended to replace professional financial analysis or human judgment.

Its results should be reviewed by qualified decision-makers before being used in real financial environments.


No permission is granted to copy, modify, distribute, reproduce, or use this source code or any part of it without prior written permission from the author.
