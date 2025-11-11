# THE-YAGBALLS-DSA
LE PYTHON TYPE SHI

Our GitHub Repo!: https://github.com/Happii-Ceasar-Ivan/THE-YAGBALLS-DSA

If you wanna try this out
install these dependencies first by typing these in your python terminal (or in VSCODE termninal)
1. pip install matplotlib
2. python -m pip install rich -i https://pypi.tuna.tsinghua.edu.cn/simple
3. pip install pytest
4. pip install numpy

File Functions
1. main.py - Core application logic. Contains the menu, rich for style and many more
2. config.json - Stores grade weights, letter grade thresholds, and report folder paths.
3. ingest.py - Reads the CSV, performs primary validation (range, required fields), and separates good records from bad rows.
4. transform.py - Calculates the weighted final_grade, applies the apply_grade_curve logic, and assigns letter_grade based on thresholds.
5. analyze.py - All the calculations. optimized by numpy
6. reports.py - ontains utility functions for grouping data, computing section-level stats, printing rich console summaries, and exporting final CSVs.
7. plot.py - for histogram 
8. test_core.py - for testing code integrity

How to use:

1. Pick what ya wanna do from the choices.
2. Follow as intructed.
3. Done

Notes: Please run the code in a full screen terminal

The people behind this code

1. Caiga, Ceasar Ivan A. - main.py, plot.py & test_core.py
2. Calayag, James Matthew T. - transform.py
3. Clarete, Marc Arthur - config.json, DSA_Yagballs.csv & ingsest.py
4. Magsila, Benjamin Magsila T. III - reports.py
5. Noriesta, Don B. - analyze.py
