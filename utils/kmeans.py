
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def segment_customer(rfm):

    scaler = StandardScaler()

    X = scaler.fit_transform(
        rfm[["Recency","Frequency","Monetary"]]
    )

    model = KMeans(
        n_clusters=4,
        random_state=42
    )

    rfm["Cluster"] = model.fit_predict(X)

    return rfm
