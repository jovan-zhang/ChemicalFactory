-- 创建数据库

-- CREATE DATABASE chemical_factory;

USE chemical_factory;

-- 化工原料表 (ChemicalMaterial)
CREATE TABLE ChemicalMaterial (
    material_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    cas_number VARCHAR(20) UNIQUE,
    stock DECIMAL(10,2),
    unit VARCHAR(10),
    concentration DECIMAL(5,2),
    category VARCHAR(50),
    storage_condition NVARCHAR(MAX),
    min_stock_threshold DECIMAL(10,2)
);

-- 化工产品表 (ChemicalProduct)
CREATE TABLE ChemicalProduct (
    product_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    unit VARCHAR(10),
    stock DECIMAL(10,2),
    hazard_rating VARCHAR(5)
);

-- 生产线表 (ProductionLine)
CREATE TABLE ProductionLine (
    line_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL
);

-- 采购员工表 (Buyer)
CREATE TABLE Buyer (
    employee_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    contact VARCHAR(100),
    purchase_category VARCHAR(50) 
);

-- 经销员工表 (Distributor)
CREATE TABLE Distributor (
    employee_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    contact VARCHAR(100),
    qualification VARCHAR(20)
);

-- 车间员工表 (Worker)
CREATE TABLE Worker (
    employee_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    contact VARCHAR(100),
    work_time NVARCHAR(MAX),
    line_id INT,
    FOREIGN KEY (line_id) REFERENCES ProductionLine(line_id)
);

-- 供应商表 (Supplier)
CREATE TABLE Supplier (
    supplier_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    main_materials NVARCHAR(MAX),
    credit_rating VARCHAR(5)
);

-- 客户表 (Customer)
CREATE TABLE Customer (
    customer_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    main_product_requirements NVARCHAR(MAX),
    credit_rating VARCHAR(5)
);

-- 进货记录表 (PurchaseRecord)
CREATE TABLE PurchaseRecord (
    record_id INT IDENTITY(1,1) PRIMARY KEY,
    supplier_id INT,
    date DATE,
    employee_id INT,
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id),
    FOREIGN KEY (employee_id) REFERENCES Buyer(employee_id)
);

-- 生产记录表 (ProductionRecord)
CREATE TABLE ProductionRecord (
    record_id INT IDENTITY(1,1) PRIMARY KEY,
    product_id INT,
    line_id INT,
    date DATE,
    theoretical_output DECIMAL(10,2),
    actual_output DECIMAL(10,2),
    FOREIGN KEY (product_id) REFERENCES ChemicalProduct(product_id),
    FOREIGN KEY (line_id) REFERENCES ProductionLine(line_id)
);

-- 销售记录表 (SalesRecord)
CREATE TABLE SalesRecord (
    record_id INT IDENTITY(1,1) PRIMARY KEY,
    customer_id INT,
    date DATE,
    employee_id INT,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
    FOREIGN KEY (employee_id) REFERENCES Distributor(employee_id)
);

-- 进货联系集 (PurchaseMaterial)
CREATE TABLE PurchaseMaterial (
    material_id INT,
    record_id INT,
    quantity DECIMAL(10,2),
    unit_price DECIMAL(10,2),
    PRIMARY KEY (material_id, record_id),
    FOREIGN KEY (material_id) REFERENCES ChemicalMaterial(material_id),
    FOREIGN KEY (record_id) REFERENCES PurchaseRecord(record_id)
);

-- 销售联系集 (SaleProduct)
CREATE TABLE SaleProduct (
    product_id INT,
    record_id INT,
    quantity DECIMAL(10,2),
    unit_price DECIMAL(10,2),
    PRIMARY KEY (product_id, record_id),
    FOREIGN KEY (product_id) REFERENCES ChemicalProduct(product_id),
    FOREIGN KEY (record_id) REFERENCES SalesRecord(record_id)
);

-- 使用原料联系集 (UseMaterial)
CREATE TABLE UseMaterial (
    material_id INT,
    record_id INT,
    quantity_used DECIMAL(10,2) NOT NULL DEFAULT 0,
    PRIMARY KEY (material_id, record_id),
    FOREIGN KEY (material_id) REFERENCES ChemicalMaterial(material_id),
    FOREIGN KEY (record_id) REFERENCES ProductionRecord(record_id)
);

-- 用户数据表 (users)
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL, 
    CONSTRAINT CK_UserRole CHECK (role IN ('admin', 'buyer', 'distributor')) 
);

-- 创建三个表值类型
USE chemical_factory;
GO

-- 进货物料详情类型
CREATE TYPE PurchaseMaterialType AS TABLE (
    material_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL
);
GO

-- 销售产品详情类型
CREATE TYPE SaleProductType AS TABLE (
    product_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL
);
GO

-- 生产原料使用详情类型

CREATE TYPE ProductionMaterialUseType AS TABLE (
    material_id INT NOT NULL,
    quantity_used DECIMAL(10,2) NOT NULL
);
GO

USE chemical_factory;
GO
-- 添加进货记录的存储过程
CREATE PROCEDURE sp_AddPurchaseRecord
    @supplier_id INT,
    @record_date DATE,
    @employee_id INT,
    @materials PurchaseMaterialType READONLY -- 接收表值参数，READONLY 是必须的
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @new_record_id INT;

    BEGIN TRANSACTION; -- 开始事务，确保原子性

    BEGIN TRY
        -- 1. 插入进货记录主表
        INSERT INTO PurchaseRecord (supplier_id, date, employee_id)
        VALUES (@supplier_id, @record_date, @employee_id);

        SET @new_record_id = SCOPE_IDENTITY(); -- 获取新插入的 record_id

        -- 2. 批量插入进货物料详情表
        INSERT INTO PurchaseMaterial (material_id, record_id, quantity, unit_price)
        SELECT
            material_id,
            @new_record_id, -- 关联到刚生成的 record_id
            quantity,
            unit_price
        FROM @materials; -- 从表值参数中读取数据

        COMMIT TRANSACTION; -- 提交事务
        SELECT @new_record_id AS NewPurchaseRecordId; -- 返回新生成的 record_id
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION; -- 出现错误，回滚事务
        -- 抛出原始错误，以便前端或调用者能够捕获和处理
        THROW;
    END CATCH
END;
GO

-- 删除进货记录存储过程
CREATE PROCEDURE sp_DeletePurchaseRecord
    @record_id INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRANSACTION;
    BEGIN TRY
        -- 先删除子表记录（触发库存回滚）
        DELETE FROM PurchaseMaterial WHERE record_id = @record_id;
        
        -- 再删除主表记录
        DELETE FROM PurchaseRecord WHERE record_id = @record_id;
        
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

-- 修改进货记录存储过程
CREATE PROCEDURE sp_UpdatePurchaseRecord
    @record_id INT,
    @supplier_id INT,
    @record_date DATE,
    @employee_id INT,
    @materials PurchaseMaterialType READONLY
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRANSACTION;
    BEGIN TRY
        -- 更新主表信息
        UPDATE PurchaseRecord SET
            supplier_id = @supplier_id,
            date = @record_date,
            employee_id = @employee_id
        WHERE record_id = @record_id;

        -- 删除原有物料（触发库存回滚）
        DELETE FROM PurchaseMaterial WHERE record_id = @record_id;

        -- 插入新物料（触发库存更新）
        INSERT INTO PurchaseMaterial (material_id, record_id, quantity, unit_price)
        SELECT material_id, @record_id, quantity, unit_price
        FROM @materials;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

USE chemical_factory;
GO
-- 添加销售记录的存储过程
CREATE PROCEDURE sp_AddSalesRecord
    @customer_id INT,
    @record_date DATE,
    @employee_id INT,
    @products SaleProductType READONLY -- 接收表值参数
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @new_record_id INT;

    BEGIN TRANSACTION;

    BEGIN TRY
        -- 1. 插入销售记录主表
        INSERT INTO SalesRecord (customer_id, date, employee_id)
        VALUES (@customer_id, @record_date, @employee_id);

        SET @new_record_id = SCOPE_IDENTITY();

        -- 2. 批量插入销售产品详情表
        INSERT INTO SaleProduct (product_id, record_id, quantity, unit_price)
        SELECT
            product_id,
            @new_record_id,
            quantity,
            unit_price
        FROM @products;

        COMMIT TRANSACTION;
        SELECT @new_record_id AS NewSalesRecordId;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

USE chemical_factory;
GO

-- 删除销售记录存储过程
CREATE PROCEDURE sp_DeleteSalesRecord
    @record_id INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRANSACTION;
    BEGIN TRY
        -- 先删除子表记录（触发库存恢复）
        DELETE FROM SaleProduct WHERE record_id = @record_id;
        
        -- 再删除主表记录
        DELETE FROM SalesRecord WHERE record_id = @record_id;
        
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

-- 修改销售记录存储过程
CREATE PROCEDURE sp_UpdateSalesRecord
    @record_id INT,
    @customer_id INT,
    @record_date DATE,
    @employee_id INT,
    @products SaleProductType READONLY
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRANSACTION;
    BEGIN TRY
        -- 更新主表信息
        UPDATE SalesRecord SET
            customer_id = @customer_id,
            date = @record_date,
            employee_id = @employee_id
        WHERE record_id = @record_id;

        -- 删除原有产品（触发库存恢复）
        DELETE FROM SaleProduct WHERE record_id = @record_id;

        -- 插入新产品（触发库存更新）
        INSERT INTO SaleProduct (product_id, record_id, quantity, unit_price)
        SELECT product_id, @record_id, quantity, unit_price
        FROM @products;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO


-- 添加生产记录的存储过程
CREATE PROCEDURE sp_AddProductionRecord
    @product_id INT,
    @line_id INT,
    @record_date DATE,
    @theoretical_output DECIMAL(10,2),
    @actual_output DECIMAL(10,2),
    @materials_used ProductionMaterialUseType READONLY -- 接收表值参数
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @new_record_id INT;

    BEGIN TRANSACTION;

    BEGIN TRY
        -- 1. 插入生产记录主表
        INSERT INTO ProductionRecord (product_id, line_id, date, theoretical_output, actual_output)
        VALUES (@product_id, @line_id, @record_date, @theoretical_output, @actual_output);

        SET @new_record_id = SCOPE_IDENTITY();

        -- 2. 批量插入原料使用详情表
        INSERT INTO UseMaterial (material_id, record_id, quantity_used)
        SELECT
            material_id,
            @new_record_id,
            quantity_used
        FROM @materials_used;

        COMMIT TRANSACTION;
        SELECT @new_record_id AS NewProductionRecordId;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO


USE chemical_factory;
GO
-- 进货更新库存
CREATE TRIGGER trg_UpdateMaterialStock
ON PurchaseMaterial
AFTER INSERT, UPDATE, DELETE -- 监听插入、更新、删除操作
AS
BEGIN
    SET NOCOUNT ON;

    -- 处理 INSERT (库存增加)
    IF EXISTS (SELECT 1 FROM INSERTED) AND NOT EXISTS (SELECT 1 FROM DELETED)
    BEGIN
        UPDATE CM
        SET stock = CM.stock + I.quantity
        FROM ChemicalMaterial CM
        INNER JOIN INSERTED I ON CM.material_id = I.material_id;
    END

    -- 处理 DELETE (库存减少)
    IF EXISTS (SELECT 1 FROM DELETED) AND NOT EXISTS (SELECT 1 FROM INSERTED)
    BEGIN
        UPDATE CM
        SET stock = CM.stock - D.quantity
        FROM ChemicalMaterial CM
        INNER JOIN DELETED D ON CM.material_id = D.material_id;
    END

    -- 处理 UPDATE (库存变化 = 新数量 - 旧数量)
    IF EXISTS (SELECT 1 FROM INSERTED) AND EXISTS (SELECT 1 FROM DELETED)
    BEGIN
        UPDATE CM
        SET stock = CM.stock + (I.quantity - D.quantity)
        FROM ChemicalMaterial CM
        INNER JOIN INSERTED I ON CM.material_id = I.material_id
        INNER JOIN DELETED D ON CM.material_id = D.material_id AND I.record_id = D.record_id;
    END
END;
GO

USE chemical_factory;
GO
-- 销售更新库存
CREATE TRIGGER trg_UpdateProductStock
ON SaleProduct
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    -- 处理 INSERT (库存减少)
    IF EXISTS (SELECT 1 FROM INSERTED) AND NOT EXISTS (SELECT 1 FROM DELETED)
    BEGIN
        UPDATE CP
        SET stock = CP.stock - I.quantity
        FROM ChemicalProduct CP
        INNER JOIN INSERTED I ON CP.product_id = I.product_id;
    END

    -- 处理 DELETE (库存恢复)
    IF EXISTS (SELECT 1 FROM DELETED) AND NOT EXISTS (SELECT 1 FROM INSERTED)
    BEGIN
        UPDATE CP
        SET stock = CP.stock + D.quantity
        FROM ChemicalProduct CP
        INNER JOIN DELETED D ON CP.product_id = D.product_id;
    END

    -- 处理 UPDATE (库存变化 = 旧数量 - 新数量)
    IF EXISTS (SELECT 1 FROM INSERTED) AND EXISTS (SELECT 1 FROM DELETED)
    BEGIN
        UPDATE CP
        SET stock = CP.stock - (I.quantity - D.quantity) -- 注意这里是 - (new - old)
        FROM ChemicalProduct CP
        INNER JOIN INSERTED I ON CP.product_id = I.product_id
        INNER JOIN DELETED D ON CP.product_id = D.product_id AND I.record_id = D.record_id;
    END
END;
GO

USE chemical_factory;
GO

-- 生产使用原料触发器（处理库存变动）
CREATE TRIGGER trg_UpdateMaterialStockOnProduction
ON UseMaterial
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- 处理插入（减少库存）
    IF EXISTS (SELECT 1 FROM INSERTED) AND NOT EXISTS (SELECT 1 FROM DELETED)
    BEGIN
        UPDATE CM
        SET stock = CM.stock - I.quantity_used
        FROM ChemicalMaterial CM
        INNER JOIN INSERTED I ON CM.material_id = I.material_id
    END
    
    -- 处理删除（恢复库存）
    IF EXISTS (SELECT 1 FROM DELETED) AND NOT EXISTS (SELECT 1 FROM INSERTED)
    BEGIN
        UPDATE CM
        SET stock = CM.stock + D.quantity_used
        FROM ChemicalMaterial CM
        INNER JOIN DELETED D ON CM.material_id = D.material_id
    END
    
    -- 处理更新（调整库存差额）
    IF EXISTS (SELECT 1 FROM INSERTED) AND EXISTS (SELECT 1 FROM DELETED)
    BEGIN
        UPDATE CM
        SET stock = CM.stock - (I.quantity_used - D.quantity_used)
        FROM ChemicalMaterial CM
        INNER JOIN INSERTED I ON CM.material_id = I.material_id
        INNER JOIN DELETED D ON CM.material_id = D.material_id AND I.record_id = D.record_id
    END
END;
GO

-- 化工原料表 (ChemicalMaterial)
INSERT INTO ChemicalMaterial (name, cas_number, stock, unit, concentration, category, storage_condition, min_stock_threshold) VALUES
('硫酸', '7664-93-9', 5000.00, 'kg', 98.00, '无机酸', '阴凉干燥处，避免与金属接触', 1000.00),
('氢氧化钠', '1310-73-2', 3000.00, 'kg', 99.00, '碱', '密封干燥，避免潮湿', 800.00),
('甲醇', '67-56-1', 2000.00, 'L', 99.90, '醇类', '远离火源，通风良好', 500.00),
('乙酸乙酯', '141-78-6', 1500.00, 'L', 99.50, '酯类', '阴凉通风，远离氧化剂', 400.00),
('过氧化氢', '7722-84-1', 1000.00, 'L', 30.00, '氧化剂', '避光冷藏，单独存放', 200.00),
('甲苯', '108-88-3', 2500.00, 'L', 99.80, '芳烃', '通风良好，远离火源', 600.00),
('氯化钠', '7647-14-5', 10000.00, 'kg', 99.50, '盐类', '普通仓库', 2000.00),
('丙酮', '67-64-1', 1800.00, 'L', 99.50, '酮类', '阴凉通风，远离火源', 450.00),
('盐酸', '7647-01-0', 3500.00, 'L', 36.50, '无机酸', '耐酸容器，通风良好', 900.00),
('乙二醇', '107-21-1', 1200.00, 'L', 99.00, '醇类', '密封保存，避免泄漏', 300.00);

-- 化工产品表 (ChemicalProduct)
INSERT INTO ChemicalProduct (name, unit, stock, hazard_rating) VALUES
('工业清洁剂', '桶', 1200.00, 'III'),
('塑料添加剂', 'kg', 2500.00, 'II'),
('涂料溶剂', 'L', 1800.00, 'III'),
('橡胶软化剂', 'kg', 900.00, 'II'),
('消毒液', 'L', 1500.00, 'IV'),
('粘合剂', 'kg', 800.00, 'III'),
('表面活性剂', 'kg', 2000.00, 'II'),
('阻燃剂', 'kg', 700.00, 'II'),
('染料中间体', 'kg', 600.00, 'III'),
('农药乳化剂', 'L', 1000.00, 'I');

-- 生产线表 (ProductionLine)
INSERT INTO ProductionLine (name, status) VALUES
('1号生产线', '运行中'),
('2号生产线', '运行中'),
('3号生产线', '维护中'),
('4号生产线', '待机中'),
('5号生产线', '运行中');

-- 采购员工表 (Buyer)
INSERT INTO Buyer (name, contact, purchase_category) VALUES
('张采购', '13800138001', '无机原料'),
('李采购', '13800138002', '有机原料'),
('王采购', '13800138003', '溶剂类');

-- 经销员工表 (Distributor)
INSERT INTO Distributor (name, contact, qualification) VALUES
('赵销售', '13900139001', '高级'),
('钱销售', '13900139002', '中级'),
('孙销售', '13900139003', '初级');

-- 车间员工表 (Worker)
INSERT INTO Worker (name, contact, work_time, line_id) VALUES
('周工人', '13700137001', '早班:8:00-16:00', 1),
('吴工人', '13700137002', '中班:16:00-24:00', 1),
('郑工人', '13700137003', '早班:8:00-16:00', 2),
('王工人', '13700137004', '夜班:0:00-8:00', 3),
('冯工人', '13700137005', '中班:16:00-24:00', 4),
('陈工人', '13700137006', '早班:8:00-16:00', 5);

-- 供应商表 (Supplier)
INSERT INTO Supplier (name, main_materials, credit_rating) VALUES
('华东化工', '硫酸,盐酸,氢氧化钠', 'A'),
('北方溶剂', '甲醇,丙酮,乙酸乙酯', 'B+'),
('南方有机', '甲苯,乙二醇,乙酸乙酯', 'A-'),
('西部原料', '氯化钠,过氧化氢', 'B'),
('中原化学', '甲醇,甲苯,丙酮', 'B+');

-- 客户表 (Customer)
INSERT INTO Customer (name, main_product_requirements, credit_rating) VALUES
('蓝天塑料', '塑料添加剂,橡胶软化剂', 'AA'),
('绿洲涂料', '涂料溶剂,表面活性剂', 'A'),
('白云清洁', '工业清洁剂,消毒液', 'BBB'),
('金盾消防', '阻燃剂', 'A+'),
('彩虹印染', '染料中间体', 'BB');

-- 进货记录表 (PurchaseRecord)
INSERT INTO PurchaseRecord (supplier_id, date, employee_id) VALUES
(1, '2023-05-10', 1),
(2, '2023-05-12', 2),
(3, '2023-05-15', 1),
(4, '2023-05-18', 3),
(5, '2023-05-20', 2);

-- 生产记录表 (ProductionRecord)
INSERT INTO ProductionRecord (product_id, line_id, date, theoretical_output, actual_output) VALUES
(1, 1, '2023-05-11', 500.00, 480.00),
(2, 2, '2023-05-13', 800.00, 790.00),
(3, 1, '2023-05-16', 600.00, 610.00),
(4, 3, '2023-05-19', 300.00, 290.00),
(5, 5, '2023-05-21', 400.00, 405.00);

-- 销售记录表 (SalesRecord)
INSERT INTO SalesRecord (customer_id, date, employee_id) VALUES
(1, '2023-05-12', 1),
(2, '2023-05-14', 2),
(3, '2023-05-17', 1),
(4, '2023-05-20', 3),
(5, '2023-05-22', 2);

-- 进货联系集 (PurchaseMaterial)
INSERT INTO PurchaseMaterial (material_id, record_id, quantity, unit_price) VALUES
(1, 1, 1000.00, 1.20),
(2, 1, 500.00, 0.80),
(3, 2, 800.00, 2.50),
(4, 2, 300.00, 3.20),
(5, 3, 200.00, 1.80),
(6, 3, 500.00, 2.10),
(7, 4, 1500.00, 0.50),
(8, 5, 600.00, 2.80),
(9, 5, 400.00, 1.50);

-- 销售联系集 (SaleProduct)
INSERT INTO SaleProduct (product_id, record_id, quantity, unit_price) VALUES
(2, 1, 200.00, 15.00),
(4, 1, 100.00, 12.00),
(3, 2, 300.00, 8.50),
(7, 2, 150.00, 10.00),
(1, 3, 80.00, 25.00),
(5, 3, 120.00, 6.00),
(8, 4, 50.00, 18.00),
(10, 5, 70.00, 14.00);

-- 使用原料联系集 (UseMaterial)
INSERT INTO UseMaterial (material_id, record_id, quantity_used) VALUES
(1, 1, 120.00),
(2, 1, 60.00),
(3, 2, 200.00),
(4, 2, 80.00),
(5, 3, 50.00),
(6, 3, 100.00),
(7, 4, 300.00),
(8, 5, 150.00),
(9, 5, 80.00);

-- 用户数据表 (users)
INSERT INTO users (username, password, role) VALUES
('admin', 'admin123', 'admin'),
('buyer1', 'buyer123', 'buyer'),
('buyer2', 'buyer456', 'buyer'),
('dist1', 'dist123', 'distributor'),
('dist2', 'dist456', 'distributor');

