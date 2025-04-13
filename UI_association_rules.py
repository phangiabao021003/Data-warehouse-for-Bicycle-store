import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
import streamlit as st
import matplotlib.pyplot as plt
import networkx as nx

# Tiêu đề của ứng dụng
st.title("Phân Tích Quy Tắc Kết Hợp (Association Rules)")

# Mô tả ứng dụng
st.markdown("""
Ứng dụng này giúp bạn thực hiện khai phá quy tắc kết hợp từ dữ liệu bán hàng. Bạn có thể tải lên file CSV chứa thông tin giao dịch và xem các quy tắc kết hợp cùng các biểu đồ trực quan.
""")

# Sidebar cho các tùy chọn
st.sidebar.header("Cấu Hình")

# Tải lên file CSV
uploaded_file = st.sidebar.file_uploader("Tải lên file CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Đọc dữ liệu từ file CSV
        df = pd.read_csv(uploaded_file)
        
        # Hiển thị thông tin dữ liệu
        st.subheader("Thông Tin Dữ Liệu")
        st.write(df.head())

        # Kiểm tra các cột cần thiết
        required_columns = ['order_id', 'category_name']
        if not all(col in df.columns for col in required_columns):
            st.error(f"Dữ liệu của bạn thiếu một hoặc nhiều cột sau: {required_columns}")
        else:
            # Tiền xử lý dữ liệu: Loại bỏ trùng lặp trong mỗi giao dịch
            transactions = df.groupby('order_id')['category_name'].apply(lambda x: list(set(x))).values.tolist()

            st.subheader("Các Giao Dịch")
            st.write(transactions)

            # One-Hot Encoding
            te = TransactionEncoder()
            te_ary = te.fit(transactions).transform(transactions)
            df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

            st.subheader("Dữ Liệu Đã Được Mã Hóa (One-Hot Encoding)")
            st.write(df_encoded.head(5))

            # Thiết lập tham số
            min_support = st.sidebar.slider("Mức Hỗ Trợ Tối Thiểu (Support)", min_value=0.1, max_value=1.0, value=0.2, step=0.05)
            min_confidence = st.sidebar.slider("Mức Độ Tin Cậy Tối Thiểu (Confidence)", min_value=0.1, max_value=1.0, value=0.2, step=0.05)

            # Áp dụng Apriori
            frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True)

            st.subheader("Frequent Itemsets")
            st.write(frequent_itemsets)

            if frequent_itemsets.empty:
                st.warning("Không tìm thấy tập mục thường xuyên với mức hỗ trợ đã chọn.")
            else:
                # Tạo các quy tắc kết hợp
                rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)

                st.subheader("Các Quy Tắc Kết Hợp")
                st.write(rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']])

                if rules.empty:
                    st.warning("Không tìm thấy quy tắc kết hợp với mức độ tin cậy đã chọn.")
                else:
                    # Hiển thị các quy tắc kết hợp chi tiết
                    st.subheader("Các Quy Tắc Kết Hợp Chi Tiết")
                    for index, row in rules.iterrows():
                        antecedents = ', '.join(list(row['antecedents']))
                        consequents = ', '.join(list(row['consequents']))
                        support = row['support']
                        confidence = row['confidence']
                        lift = row['lift']
                        st.write(f"**{antecedents} → {consequents}** (Support: {support:.2f}, Confidence: {confidence:.2f}, Lift: {lift:.2f})")

                    # Trực quan hóa các quy tắc với Lift > 1
                    st.subheader("Trực Quan Hóa Quy Tắc Kết Hợp với Lift > 1")

                    strong_rules = rules[rules['lift'] > 1]
                    if not strong_rules.empty:
                        G = nx.DiGraph()
                        for _, row in strong_rules.iterrows():
                            antecedents = ', '.join(list(row['antecedents']))
                            consequents = ', '.join(list(row['consequents']))
                            G.add_edge(antecedents, consequents, weight=row['lift'])

                        pos = nx.spring_layout(G, k=2)
                        plt.figure(figsize=(10, 8))
                        edges = G.edges(data=True)
                        weights = [edge[2]['weight'] for edge in edges]
                        nx.draw(G, pos, with_labels=True, node_color='skyblue', edge_color=weights, width=2, edge_cmap=plt.cm.Blues, arrows=True)
                        plt.title('Quy Tắc Kết Hợp với Lift > 1')
                        st.pyplot(plt)
                    else:
                        st.info("Không có quy tắc nào có Lift > 1 để trực quan hóa.")
    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi xử lý file: {e}")
else:
    st.info("Vui lòng tải lên file CSV để bắt đầu.")
