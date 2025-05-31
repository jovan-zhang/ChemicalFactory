
# 化学工厂管理系统 API 文档

## 1. 原料管理

### 1.1 获取所有原料
**URL**: `/materials`  
**Method**: GET  
**Response**:
```json
[
    {
        "material_id": 1,
        "name": "硫酸",
        "cas_number": "7664-93-9",
        "stock": 500.0,
        "unit": "kg",
        "concentration": 98.0,
        "category": "无机酸",
        "storage_condition": "阴凉干燥",
        "min_stock_threshold": 100.0
    }
]
```

### 1.2 获取单个原料
**URL**: `/materials/<int:material_id>`  
**Method**: GET  
**Response**:
```json
{
    "material_id": 1,
    "name": "硫酸",
    "cas_number": "7664-93-9",
    "stock": 500.0,
    "unit": "kg",
    "concentration": 98.0,
    "category": "无机酸",
    "storage_condition": "阴凉干燥",
    "min_stock_threshold": 100.0
}
```

### 1.3 添加原料
**URL**: `/materials`  
**Method**: POST  
**Request**:
```json
{
    "name": "盐酸",
    "cas_number": "7647-01-0",
    "unit": "L",
    "concentration": 36.5,
    "category": "无机酸",
    "storage_condition": "通风",
    "min_stock_threshold": 80.0
}
```
**Response**:
```json
{
    "message": "原料添加成功"
}
```

### 1.4 更新原料
**URL**: `/materials/<int:material_id>`  
**Method**: PUT  
**Request**:
```json
{
    "name": "盐酸(更新)",
    "cas_number": "7647-01-0",
    "unit": "L",
    "concentration": 37.0,
    "category": "强酸",
    "storage_condition": "密封",
    "min_stock_threshold": 100.0
}
```
**Response**:
```json
{
    "message": "原料更新成功"
}
```

### 1.5 删除原料
**URL**: `/materials/<int:material_id>`  
**Method**: DELETE  
**Response**:
```json
{
    "message": "原料删除成功"
}
```

## 2. 产品管理

### 2.1 获取所有产品
**URL**: `/products`  
**Method**: GET  
**Response**:
```json
[
    {
        "product_id": 1,
        "name": "消毒液",
        "unit": "L",
        "hazard_rating": "III",
        "stock": 200.0
    }
]
```

### 2.2 获取单个产品
**URL**: `/products/<int:product_id>`  
**Method**: GET  
**Response**:
```json
{
    "product_id": 1,
    "name": "消毒液",
    "unit": "L",
    "hazard_rating": "III",
    "stock": 200.0
}
```

### 2.3 添加产品
**URL**: `/products`  
**Method**: POST  
**Request**:
```json
{
    "name": "除锈剂",
    "unit": "罐",
    "hazard_rating": "IV"
}
```
**Response**:
```json
{
    "message": "产品添加成功"
}
```

### 2.4 更新产品
**URL**: `/products/<int:product_id>`  
**Method**: PUT  
**Request**:
```json
{
    "name": "强力除锈剂",
    "unit": "桶",
    "hazard_rating": "III"
}
```
**Response**:
```json
{
    "message": "产品更新成功"
}
```

### 2.5 删除产品
**URL**: `/products/<int:product_id>`  
**Method**: DELETE  
**Response**:
```json
{
    "message": "产品删除成功"
}
```

## 3. 进货记录管理

### 3.1 获取所有进货记录
**URL**: `/purchase_records`  
**Method**: GET  
**Response**:
```json
[
    {
        "record_id": 1,
        "supplier_id": 101,
        "date": "2023-05-10",
        "employee_id": 201
    }
]
```

### 3.2 获取进货详情
**URL**: `/purchase_records/<int:record_id>`  
**Method**: GET  
**Response**:
```json
{
    "record_id": 1,
    "date": "2023-05-10",
    "supplier_id": 101,
    "supplier_name": "化工原料公司",
    "employee_id": 201,
    "employee_name": "张三"
}
```

### 3.3 获取进货原料列表
**URL**: `/purchase_records/<int:record_id>/materials`  
**Method**: GET  
**Response**:
```json
[
    {
        "material_id": 1,
        "name": "硫酸",
        "quantity": 100.0,
        "unit_price": 5.8,
        "unit": "kg"
    }
]
```

### 3.4 添加进货记录
**URL**: `/purchase_records`  
**Method**: POST  
**Request**:
```json
{
    "supplier_id": 103,
    "date": "2023-05-15",
    "employee_id": 203,
    "materials": [
        {
            "material_id": 1,
            "quantity": 200.0,
            "unit_price": 5.5
        }
    ]
}
```
**Response**:
```json
{
    "message": "进货记录添加成功",
    "new_record_id": 3
}
```

### 3.5 删除进货记录
**URL**: `/purchase_records/<int:record_id>`  
**Method**: DELETE  
**Response**:
```json
{
    "message": "进货记录ID 1 删除成功"
}
```

## 4. 销售记录管理

### 4.1 获取所有销售记录
**URL**: `/sale_records`  
**Method**: GET  
**Response**:
```json
[
    {
        "record_id": 1,
        "customer_id": 301,
        "date": "2023-05-11",
        "employee_id": 401
    }
]
```

### 4.2 获取销售详情
**URL**: `/sale_records/<int:record_id>`  
**Method**: GET  
**Response**:
```json
{
    "record_id": 1,
    "date": "2023-05-11",
    "customer_id": 301,
    "customer_name": "医院采购部",
    "employee_id": 401,
    "employee_name": "李四"
}
```

### 4.3 获取销售产品列表
**URL**: `/sale_records/<int:record_id>/products`  
**Method**: GET  
**Response**:
```json
[
    {
        "product_id": 1,
        "name": "消毒液",
        "quantity": 50.0,
        "unit_price": 15.0,
        "unit": "L"
    }
]
```

### 4.4 添加销售记录
**URL**: `/sale_records`  
**Method**: POST  
**Request**:
```json
{
    "customer_id": 303,
    "date": "2023-05-16",
    "employee_id": 403,
    "products": [
        {
            "product_id": 1,
            "quantity": 40.0,
            "unit_price": 16.0
        }
    ]
}
```
**Response**:
```json
{
    "message": "销售记录添加成功",
    "new_record_id": 3
}
```

### 4.5 删除销售记录
**URL**: `/sale_records/<int:record_id>`  
**Method**: DELETE  
**Response**:
```json
{
    "message": "销售记录ID 1 删除成功"
}
```

## 5. 生产记录管理

### 5.1 获取所有生产记录
**URL**: `/production_records`  
**Method**: GET  
**Response**:
```json
[
    {
        "record_id": 1,
        "date": "2023-05-10",
        "theoretical_output": 100.0,
        "actual_output": 98.0,
        "product_name": "消毒液",
        "line_name": "A生产线"
    }
]
```

### 5.2 获取生产详情
**URL**: `/production_records/<int:record_id>`  
**Method**: GET  
**Response**:
```json
{
    "record_id": 1,
    "date": "2023-05-10",
    "product_id": 1,
    "product_name": "消毒液",
    "line_id": 1,
    "line_name": "A生产线",
    "theoretical_output": 100.0,
    "actual_output": 98.0
}
```

### 5.3 获取生产原料列表
**URL**: `/production_records/<int:record_id>/materials`  
**Method**: GET  
**Response**:
```json
[
    {
        "material_id": 1,
        "material_name": "硫酸",
        "quantity_used": 20.0,
        "unit": "kg"
    }
]
```

### 5.4 添加生产记录
**URL**: `/production_records`  
**Method**: POST  
**Request**:
```json
{
    "product_id": 3,
    "line_id": 2,
    "date": "2023-05-18",
    "theoretical_output": 150.0,
    "actual_output": 148.0,
    "materials": [
        {
            "material_id": 1,
            "quantity": 25.0
        }
    ]
}
```
**Response**:
```json
{
    "message": "生产记录添加成功",
    "new_record_id": 3
}
```

## 6. 错误处理

### 错误响应格式
```json
{
    "error": "错误描述",
    "message": "详细错误信息"
}
```

### 状态码说明
| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 资源创建成功 |
| 400 | 客户端请求错误 |
| 404 | 资源不存在 |
| 409 | 资源冲突/重复 |
| 500 | 服务器内部错误 |

**注**：
- 所有日期格式为 `YYYY-MM-DD`
- 数字字段需为有效数值
- 危险等级仅接受 `I`, `II`, `III`, `IV`, `V`
