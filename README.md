# 🌍 Global Crisis & Conflict Map
Global Crisis & Conflict Dashboard  
(or: turning geopolitical data into something you can actually see)

---

# 1. What is this project?

This project is an interactive dashboard for exploring global crises using real-world data.

It combines multiple international datasets (World Bank, UNHCR, IDMC, IMF) into a single visual framework and turns them into a map that allows you to:

- see global crisis patterns at a glance  
- compare different kinds of geopolitical stress  
- explore individual countries in detail  

The goal is not just to display data — but to make it interpretable.

---

## 🧠 Intuition (how to think about this project)

Think of global crises like layers of signals, not categories.

Each country is not just “in crisis” or “stable.”  
Instead, it has different types of pressure:

- conflict  
- displacement  
- instability  
- economic stress  

This project treats these as separate signals that can be:

- measured  
- compared  
- combined  

Instead of asking:

> “Is this country in crisis?”

we ask:

> “What kinds of pressure exist here, and how strong are they?”

---

# 2. Project structure

```
WORLD/
├── app.py        # Interactive dashboard (Dash + Plotly)
├── data.py
├── country_info.py           # Data loading + preprocessing
├── README.md     # This file
```

---

### ⚠️ Important note

This is not a collection of independent scripts.

- `data.py` builds structured datasets  
- `app.py` visualizes them  

Always run:
```
python app.py
```

Do NOT try to run data files individually.

---

# 3. Code overview (what lives where)

## data.py
Handles the entire data pipeline.

Includes:

- loading country list (ISO3 standard)  
- fetching World Bank indicators  
- cleaning + converting data  
- normalization of all metrics  

Core idea:
> Different datasets → unified scale (0–1)

---

## app.py
The main dashboard.

Responsible for:

- interactive world map  
- filter system (multiple crisis indicators)  
- threshold logic  
- country detail panel  

Core idea:
> Data → interpretable visualization

---

# 4. Data model (how data is treated)

Each country is represented as:


Country = {
conflict_score,
humanitarian_score,
terrorism_score,
refugee_outflow_score,
tariff_score
}

---

## Normalization

All indicators are scaled:
```
score = (value - min) / (max - min)
```

This ensures:

- comparability across datasets  
- no dataset dominates the map  
- consistent interpretation  

---

## Combined score

The map uses a combined score:
```
combined_score = max(selected_indicators)
```

Meaning:
→ a country appears if it is **significant in at least one dimension**

---

# 5. Data sources (real datasets only)

This project uses only **official, open data**:

- World Bank (conflict, tariffs, governance indicators)  
- UNHCR (refugee statistics)  
- IDMC (internal displacement data)  
- IMF-linked datasets via World Bank  

No proprietary datasets  
No restricted APIs  

---

## ⚠️ Important: what the data means

This map shows:

- **proxies of crisis intensity**
- not official classifications

Example:

- A country may appear due to:
  - displacement events  
  - minor instability  
  - reporting differences  

So results should always be interpreted with context.

---

# 6. How to run the project

## 🧑‍💻 With programming experience

Install dependencies:
```
pip install pandas plotly dash requests numpy
```

Run the app:
```
python app.py
```

Open in browser (Click + Ctrl):
http://127.0.0.1:8050

---

## 👶 Without coding experience (step-by-step)

### Step 1 – Install Python
- Go to https://www.python.org  
- Download + install Python  
- ✅ Check “Add Python to PATH”

---

### Step 2 – Open command prompt
Press:
```
Windows + R
```

Then type:
```
cmd
```

---

### Step 3 – Go to the project folder

Example:
```
cd Downloads\WORLD
```

---

### Step 4 – Install required packages
```
pip install pandas plotly dash requests numpy
```

---

### Step 5 – Run the dashboard
```
python app.py
```
---

### Step 6 – Open the map

Paste this in your browser:
```
http://127.0.0.1:8050
```

You should now see the interactive map.

---

# 7. What this project tries to do

This project is built around a simple idea:

> Data becomes useful when it becomes visible.

Instead of reading reports or tables, this tool lets you:

- explore patterns  
- spot global hotspots  
- compare countries quickly  

---

# 8. Limitations

- Not a predictive model  
- Not a classification system  
- Dependent on data availability  
- Some countries have incomplete data  

---

# 9. Key takeaway

Like in EPIGO:

> The goal is not prediction — it’s understanding. [1](https://github.com/cluehning/march_EPIGO)

This project applies the same philosophy to global data:

- not just “what is happening”  
- but “how does it structure itself globally?”

---

# ⭐ Final thought

You can’t understand the world by looking at one number.

But you can start to understand it  
when you look at patterns.
