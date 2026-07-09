import pandas as pd

def create_rfm(df):

    reference_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)

    rfm = df.groupby("CustomerID").agg({

        "InvoiceDate": lambda x: (reference_date - x.max()).days,

        "InvoiceNo": "nunique",

        "TotalPrice": "sum"

    })

    rfm.columns = ["Recency", "Frequency", "Monetary"]

    return rfm.reset_index()
