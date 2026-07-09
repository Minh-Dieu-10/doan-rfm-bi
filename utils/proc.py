import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules


# ======================================================
# 1. CLEAN DATA
# ======================================================

def clean_data(df):

    # Xóa CustomerID bị thiếu
    df = df.dropna(subset=["CustomerID"])

    # Chỉ giữ giao dịch hợp lệ
    df = df[df["Quantity"] > 0]
    df = df[df["UnitPrice"] > 0]

    # Chuyển kiểu dữ liệu
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

    df["CustomerID"] = df["CustomerID"].astype(int)

    # Thành tiền
    df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]

    return df


# ======================================================
# 2. RFM
# ======================================================

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

    rfm = rfm.reset_index()

    return rfm


# ======================================================
# 3. KMEANS
# ======================================================

def segment_customer(rfm):

    scaler = StandardScaler()

    X = scaler.fit_transform(

        rfm[

            [

                "Recency",

                "Frequency",

                "Monetary"

            ]

        ]

    )

    model = KMeans(

        n_clusters=5,

        random_state=42,

        n_init=10

    )

    rfm["Cluster"] = model.fit_predict(X)

    return rfm


# ======================================================
# 4. ĐỔI TÊN PHÂN KHÚC
# ======================================================

def rename_segment(rfm):

    cluster_mean = (

        rfm.groupby("Cluster")[

            [

                "Recency",

                "Frequency",

                "Monetary"

            ]

        ]

        .mean()

    )

    order = cluster_mean.sort_values(

        by=[

            "Monetary",

            "Frequency"

        ],

        ascending=False

    ).index.tolist()

    mapping = {

        order[0]: "Champions",

        order[1]: "Loyal",

        order[2]: "Potential",

        order[3]: "At Risk",

        order[4]: "Hibernating"

    }

    rfm["Segment"] = rfm["Cluster"].map(mapping)

    return rfm


# ======================================================
# 5. APRIORI
# ======================================================

def recommendation(df):

    basket = (

        df.groupby(

            [

                "InvoiceNo",

                "Description"

            ]

        )["Quantity"]

        .sum()

        .unstack()

        .fillna(0)

    )

    basket = basket.apply(

        lambda x: x > 0

    )

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

    # Chuyển frozenset thành chuỗi

    rules["antecedents"] = rules["antecedents"].apply(

        lambda x: ", ".join(list(x))

    )

    rules["consequents"] = rules["consequents"].apply(

        lambda x: ", ".join(list(x))

    )

    rules = rules.sort_values(

        by="confidence",

        ascending=False

    )

    rules = rules.reset_index(drop=True)

    return rules
