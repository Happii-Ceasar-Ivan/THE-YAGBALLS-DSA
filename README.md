# THE-YAGBALLS-DSA
LE PYTHON TYPE SHI

Our GitHub Repo!: https://github.com/Happii-Ceasar-Ivan/THE-YAGBALLS-DSA

Project Overview:

EPSILON is a command-line interface (CLI) program that is designed to manage data, provide comprehensive grades analysis and report generation for students' grades. The system is built on Python and utilizes the rich library to make it lively, make it look professional, and be an interactive console experience.

"INSTALLATION AND SETUP"

If you wanna try this out
install these dependencies first by typing these in your python terminal (or in VSCODE termninal)

```bash
pip install matplotlib
python -m pip install rich -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install pytest
pip install numpy
`` ``` ``
File Functions
1. main.py - Core application logic. Contains the menu, rich for style and many more
2. config.json - Stores grade weights, letter grade thresholds, and report folder paths.
3. ingest.py - Reads the CSV, performs primary validation (range, required fields), and separates good records from bad rows.
4. transform.py - Calculates the weighted final_grade, applies the apply_grade_curve logic, and assigns letter_grade based on thresholds.
5. analyze.py - All the calculations. optimized by numpy
6. reports.py - ontains utility functions for grouping data, computing section-level stats, printing rich console summaries, and exporting final CSVs.
7. plot.py - for histogram 
8. test_core.py - for testing code integrity

HOW TO RUN (Assumming you have alread installed the dependencies):

1. Run main.py (If you have code runner in VS code:Ctrl + alt + N)
2. Pick what ya wanna do from the choices.
3. Follow as intructed.
4. Type in terminal "pytest test_core.py" to run tests.
5. Done

Note: Please run the code in a full screen terminal

Configuration Notes (config.json)The config.json file is essential as it dictates the entire grading logic:
1. grading_weights: Defines the percentage scheme used by transform.py to calculate the final score (e.g., Quizzes: 40%, Final: 35%).
2. grade_thresholds: Provides the numerical cutoffs for transform.py to assign letter grades (e.g., 93.0 = A)
3. output_folder: Specifies the directory where all report outputs (CSVs, At-Risk lists, and Histograms) are saved.

Complexity Discussions:
- Data Structure: The student data is managed by using various Python lists and libraries that are much needed for handling datas like names, scores and, etc.
- We used numpy in analyze.py for all stat computations for performance gains.
- Modularity: We modularized everything so we can share work to each other for each file as well as to prevent overtly long lines of codes. It also gives us an easier debugging experience as each function is in their own file.
- We used rich.py to improve the lame dull terminal so it will look livelier by using colors, as well as adding the loading animations to make it feel like an app. It improves readability (compared to just white texts) as well as improve the user experience. 

The people behind this code

1. Caiga, Ceasar Ivan A. - main.py, plot.py & test_core.py
2. Calayag, James Matthew T. - transform.py
3. Clarete, Marc Arthur - config.json, DSA_Yagballs.csv & ingsest.py
4. Magsila, Benjamin Magsila T. III - reports.py
5. Noriesta, Don B. - analyze.py

Matsaloves sa inyong lahat sah!