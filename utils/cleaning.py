
import pandas as pd

def clean_data(df):

    # Xóa dòng thiếu CustomerID
    df = df.dropna(subset=["CustomerID"])

    # Chỉ giữ giao dịch hợp lệ
    df = df[df["Quantity"] > 0]
    df = df[df["UnitPrice"] > 0]

    # Đổi kiểu dữ liệu
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    # CustomerID về int
    df["CustomerID"] = df["CustomerID"].astype(int)

    # Thành tiền
    df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]

    return df
