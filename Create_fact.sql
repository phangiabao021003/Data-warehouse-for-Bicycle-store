CREATE OR REPLACE TABLE `bicycle-store-data-warehouse.OLAP.sales_fact` AS
SELECT 
    oi.order_id,
    -- CAST(FORMAT_DATE('%Y%m%d', o.order_date) AS INT64) AS time_key, -- Map to time_dim
    o.order_date,
    o.customer_id, -- Map to customer_dim
    oi.product_id, -- Map to product_dim
    o.store_id, -- Map to store_dim
    pd.category_name,
    oi.quantity,
    oi.list_price,
    oi.discount,
    (oi.quantity * oi.list_price) * (1 - oi.discount / 100) AS sales_amount -- Calculate sales amount
FROM `bicycle-store-data-warehouse.Data.sales_orders` o
JOIN `bicycle-store-data-warehouse.Data.sales_order_items` oi ON o.order_id = oi.order_id
JOIN `bicycle-store-data-warehouse.OLAP.customer_dim` cd ON o.customer_id = cd.customer_id
JOIN `bicycle-store-data-warehouse.OLAP.product_dim` pd ON oi.product_id = pd.product_id
JOIN `bicycle-store-data-warehouse.OLAP.time_dim` td ON o.order_date=td.order_date
JOIN `bicycle-store-data-warehouse.OLAP.store_dim` sd ON o.store_id = sd.store_id;

Create OR REPLACE TABLE `bicycle-store-data-warehouse.OLAP.RFM_factless` AS SELECT 
    customer_id,
    -- Recency: Sự khác biệt giữa ngày hiện tại và ngày đơn hàng gần nhất của khách hàng
    order_date,  
    -- Monetary: Tổng số tiền mà khách hàng đã chi tiêu
    DATE_DIFF(MAX(order_date) OVER (), order_date,MONTH) as recency,
    SUM(sales_amount) AS revenue_per_order
FROM `bicycle-store-data-warehouse.OLAP.sales_fact`
GROUP BY customer_id,order_date;


-- ETL Process to Populate RFM Fact Table
Create OR REPLACE TABLE `bicycle-store-data-warehouse.OLAP.RFM_fact` as
Select 
  fl.customer_id,
  min(fl.recency) as min_recency,
  Count(fl.customer_id) as frequency,
  SUM(fl.revenue_per_order) as monetary,
    
    -- Scoring (NTILE to divide into 5 quantiles)
    NTILE(4) OVER (ORDER BY min(fl.recency) DESC) AS r_score, -- The lower recency, the higher r_score
    NTILE(4) OVER (ORDER BY Count(fl.customer_id) ASC) AS f_score, -- The higher frequency, the higher f_score
    NTILE(4) OVER (ORDER BY SUM(fl.revenue_per_order) ASC) AS m_score, -- The higher monetary, the higher m_score
    
    -- Calculate combined RFM Score as a concatenated string of R, F, and M
    CONCAT(
        CAST(NTILE(4) OVER (ORDER BY min(fl.recency) DESC) AS STRING), '-', 
        CAST(NTILE(4) OVER (ORDER BY Count(fl.customer_id) ASC) AS STRING), '-', 
        CAST(NTILE(4) OVER (ORDER BY SUM(fl.revenue_per_order) ASC) AS STRING)
    ) AS rfm_score,  -- Concatenated RFM Score
    
    -- Phân khúc khách hàng theo logic mới
    CASE 
        WHEN NTILE(4) OVER (ORDER BY min(fl.recency) DESC) = 1 THEN 'Lost' -- R = 1 => Lost
        WHEN NTILE(4) OVER (ORDER BY min(fl.recency) DESC) = 2 THEN 'Could be lost' -- R = 2 => Could be lost
        WHEN NTILE(4) OVER (ORDER BY min(fl.recency) DESC) >= 3 THEN
        CASE
            WHEN NTILE(4) OVER (ORDER BY Count(fl.customer_id) ASC) = 1 THEN 'New Customer' -- F = 1 => New Customer 
            WHEN NTILE(4) OVER (ORDER BY Count(fl.customer_id) ASC) >= 3 THEN
                CASE
                    WHEN NTILE(4) OVER (ORDER BY SUM(fl.revenue_per_order) ASC) >= 3 THEN 'Special Customer' -- M >= 4 => Special Customer
                    ELSE 'Loyal Customer' -- F >= 4 and M < 4 => Loyal Customer
                END
            ELSE 'Normal' -- Các trường hợp khác => Normal
        END
    ELSE 'Normal' -- Các trường hợp không thuộc phân khúc khác => Normal
END AS customer_segment
From `bicycle-store-data-warehouse.OLAP.RFM_factless` fl
JOIN `bicycle-store-data-warehouse.OLAP.customer_dim` cd
    ON fl.customer_id = cd.customer_id
GROUP BY fl.customer_id;

