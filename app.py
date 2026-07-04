-- 1. Tạo Database mới
CREATE DATABASE Retail_RFM_DWH;
GO

USE Retail_RFM_DWH;
GO

-- 2. Tạo bảng Kích thước Khách hàng (Dim_Customer)
CREATE TABLE Dim_Customer (
    CustomerKey INT IDENTITY(1,1) PRIMARY KEY,
    CustomerID NVARCHAR(50) NOT NULL,
    Country NVARCHAR(100),
    Recency_Score INT,
    Frequency_Score INT,
    Monetary_Score INT,
    RFM_Group NVARCHAR(50) -- Lưu nhóm: Champions, At Risk, Lost...
);

-- 3. Tạo bảng Kích thước Sản phẩm (Dim_Product)
CREATE TABLE Dim_Product (
    ProductKey INT IDENTITY(1,1) PRIMARY KEY,
    StockCode NVARCHAR(50) NOT NULL,
    Description NVARCHAR(255)
);

-- 4. Tạo bảng Kích thước Thời gian (Dim_Date)
CREATE TABLE Dim_Date (
    DateKey INT PRIMARY KEY, -- Định dạng: YYYYMMDD
    FullDate DATE,
    Day INT,
    Month INT,
    Quarter INT,
    Year INT
);

-- 5. Tạo bảng Thực tế Bán hàng (Fact_Sales)
CREATE TABLE Fact_Sales (
    SalesKey INT IDENTITY(1,1) PRIMARY KEY,
    InvoiceNo NVARCHAR(50) NOT NULL,
    CustomerKey INT,
    ProductKey INT,
    DateKey INT,
    Quantity INT,
    UnitPrice DECIMAL(18,2),
    TotalAmount DECIMAL(18,2),
    FOREIGN KEY (CustomerKey) REFERENCES Dim_Customer(CustomerKey),
    FOREIGN KEY (ProductKey) REFERENCES Dim_Product(ProductKey),
    FOREIGN KEY (DateKey) REFERENCES Dim_Date(DateKey)
);

-- 6. Tạo bảng lưu Lịch sử Import & Hệ thống (Dành cho Web App)
CREATE TABLE Import_History (
    ImportID INT IDENTITY(1,1) PRIMARY KEY,
    ImportDate DATETIME DEFAULT GETDATE(),
    FileName NVARCHAR(255),
    Status NVARCHAR(50), -- Success / Failed
    LogMessage NVARCHAR(MAX)
);
GO