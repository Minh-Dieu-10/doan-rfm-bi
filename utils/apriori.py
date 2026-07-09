from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules

def recommendation(df):

    basket = (

        df.groupby(["InvoiceNo","Description"])["Quantity"]

        .sum()

        .unstack()

        .fillna(0)

    )

    basket = basket.apply(lambda x: x > 0)

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

    recommend = rules[[

        "antecedents",

        "consequents",

        "support",

        "confidence",

        "lift"

    ]]

    return recommend
