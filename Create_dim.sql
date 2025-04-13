CREATE OR REPLACE TABLE `bicycle-store-data-warehouse.OLAP.time_dim` AS
SELECT DISTINCT 
    order_date AS order_date,
    EXTRACT(YEAR FROM order_date) AS year,
    EXTRACT(QUARTER FROM order_date) AS quarter,
    EXTRACT(MONTH FROM order_date) AS month,
    EXTRACT(DAY FROM order_date) AS day
FROM `bicycle-store-data-warehouse.Data.sales_orders`;

CREATE OR REPLACE TABLE `bicycle-store-data-warehouse.OLAP.customer_dim` as
SELECT 
    customer_id,
    first_name,
    last_name,
    phone,
    email,
    city,
    state
FROM `bicycle-store-data-warehouse.Data.sales_customers`;

-- 3. Populate product_dim
CREATE OR REPLACE TABLE `bicycle-store-data-warehouse.OLAP.product_dim` AS
SELECT 
    p.product_id,
    p.product_name,
    b.brand_name,
    c.category_name,
    p.model_year,
    p.list_price
FROM `bicycle-store-data-warehouse.Data.production_products` p
JOIN `bicycle-store-data-warehouse.Data.production_brands` b ON p.brand_id = b.brand_id
JOIN `bicycle-store-data-warehouse.Data.production_categories` c ON p.category_id = c.category_id;

-- 4. Populate store_dim
CREATE OR REPLACE TABLE `bicycle-store-data-warehouse.OLAP.store_dim` AS
SELECT 
    store_id,
    store_name,
    city,
    state
FROM `bicycle-store-data-warehouse.Data.sales_stores`;
