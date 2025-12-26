import pandas as pd

df = pd.read_excel("Monteria_Aquaculture_Data.xlsx")
df.to_csv("tilapia_wq.csv", index=False)
