# import pandas as pd

# # --- Tên file nguồn và file đích ---
# source_file = "Monteria_Aquaculture_Data.xlsx"
# target_file = "test.xlsx"

# # --- Đọc file nguồn ---
# df = pd.read_excel(source_file)

# # --- Tính số dòng 20% cuối ---
# n_rows = len(df)
# tail_size = int(n_rows * 0.2)

# print(f"Tổng số dòng: {n_rows}")
# print(f"Lấy {tail_size} dòng cuối (~20%).")

# # --- Lấy 20% cuối ---
# df_tail = df.tail(tail_size)

# # --- Ghi ra file mới ---
# df_tail.to_excel(target_file, index=False)

# print(f"Đã tạo file {target_file} chứa 20% cuối của dữ liệu.")
import pandas as pd

pd.set_option('display.max_columns', None)   # hiện tất cả cột
pd.set_option('display.width', None)         # không giới hạn chiều rộng

df = pd.read_excel("Monteria_Aquaculture_Data.xlsx")

print(df.head(10))
