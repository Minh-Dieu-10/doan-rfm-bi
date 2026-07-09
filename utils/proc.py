import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules


# ==================================================
# 1. CLEANING
# ==================================================
def clean_data(df):

    # Xóa CustomerID bị thiếu
    df = df.dropna(subset=["CustomerID"])

    # Chỉ giữ giao dịch hợp lệ
    df = df[df["Quantity"] > 0]
    df = df[df["UnitPrice"] > 0]

    # Đổi kiểu dữ liệu
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    # CustomerID
    df["CustomerID"] = df["CustomerID"].astype(int)

    # Thành tiền
    df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]

    return df


# ==================================================
# 2. RFM
# ==================================================
def create_rfm(df):

    reference_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)

    rfm = df.groupby("CustomerID").agg({

        "InvoiceDate":
            lambda x: (reference_date - x.max()).days,

        "InvoiceNo":
            "nunique",

        "TotalPrice":
            "sum"

    })

    rfm.columns = [

        "Recency",
        "Frequency",
        "Monetary"

    ]

    return rfm.reset_index()


# ==================================================
# 3. KMEANS
# ==================================================
def segment_customer(rfm):

    scaler = StandardScaler()

    X = scaler.fit_transform(

        rfm[

            ["Recency", "Frequency", "Monetary"]

        ]

    )

    model = KMeans(

        n_clusters=4,

        random_state=42,

        n_init=10

    )

    rfm["Cluster"] = model.fit_predict(X)

    return rfm


# ==================================================
# ĐỔI TÊN PHÂN KHÚC
# ==================================================
def rename_segment(rfm):

    score = (

        rfm.groupby("Cluster")[

            ["Recency", "Frequency", "Monetary"]

        ]

        .mean()

    )

    order = score.sort_values(

        by=["Monetary", "Frequency"],

        ascending=False

    ).index.tolist()

    mapping = {

        order[0]: "Champions",

        order[1]: "Loyal",

        order[2]: "Potential",

        order[3]: "Hibernating"

    }

    rfm["Segment"] = rfm["Cluster"].map(mapping)

    return rfm


# ==================================================
# 4. APRIORI
# ==================================================
def recommendation(df):

    basket = (

        df.groupby(

            ["InvoiceNo", "Description"]

        )["Quantity"]

        .sum()

        .unstack()

        .fillna(0)

    )

    basket = basket > 0

    frequent = apriori(

        basket,

        min_support=0.02,

        use_colnames=True

    )

    rules = association_rules(

        frequent,

        metric="lift",

        min_threshold=1

    )

    rules = rules[

        [

            "antecedents",

            "consequents",

            "support",

            "confidence",

            "lift"

        ]

    ]

    rules["antecedents"] = rules["antecedents"].astype(str)

    rules["consequents"] = rules["consequents"].astype(str)

    return rules
