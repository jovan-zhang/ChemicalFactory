from flask import Flask, jsonify, request, g
import pyodbc
import os

app = Flask(__name__)


# 数据库配置
def get_db():
    if 'db' not in g:
        g.db = pyodbc.connect(
            'DRIVER={ODBC Driver 13 for SQL Server};' # ODBC驱动版本
            'SERVER=127.0.0.1;'
            'DATABASE=chemical_factory;'
            'Trusted_Connection=yes;'  # 使用Windows身份验证
        )
    return g.db


@app.teardown_appcontext
def close_db(error):
    if 'db' in g:
        g.db.close()

# 原料增删改查

# 原料数据格式
'''
{
  "name": "新原料名称",
  "cas_number": "可选 CAS 号",
  "stock": 0.00,
  "unit": "kg/L",
  "concentration": 99.50,
  "category": "原料类别",
  "storage_condition": "存储条件",
  "min_stock_threshold": 100.00
}'''

#  获取所有原料
@app.route('/materials', methods=['GET'])
def get_materials():
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM ChemicalMaterial")
    columns = [column[0] for column in cursor.description]
    return jsonify([dict(zip(columns, row)) for row in cursor.fetchall()])

# 由id获取单个原料
@app.route('/materials/<int:material_id>', methods=['GET'])
def get_material(material_id):
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM ChemicalMaterial WHERE material_id=?", (material_id,))
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    if row:
        return jsonify(dict(zip(columns, row)))
    else:
        return jsonify({'message': f'id为{material_id}的原料不存在'}), 404

# 由原料名搜索原料（未完成）

# 添加原料
@app.route('/materials', methods=['POST'])
def add_material():
    data = request.get_json()
    #  检查参数
    for key in ['name', 'cas_number', 'unit', 'concentration', 'category', 'storage_condition', 'min_stock_threshold']:
        if key not in data:
            return jsonify({'message': f'缺少参数 {key}'}),  400
        if data[key] is None:
            return jsonify({'message': f'参数 {key} 不能为空'}), 400

    if not isinstance(data['concentration'], float):
        return jsonify({'message': '浓度必须是数字'}), 400
    if data['concentration'] < 0 or data['concentration'] > 100:
        return jsonify({'message': '浓度必须在0-100之间'}), 400
    if not isinstance(data['min_stock_threshold'], float):
        return jsonify({'message': '最小库存阈值必须是数字'}), 400
    if data['min_stock_threshold'] < 0:
        return jsonify({'message': '最小库存阈值不能小于0'}), 400

    cursor = get_db().cursor()

    # cursor.execute("INSERT INTO ChemicalMaterial (name, cas_number, stock, unit, concentration, category, storage_condition, min_stock_threshold) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
    #               (data['name'], data['cas_number'], 0.0, data['unit'], data['concentration'], data['category'], data['storage_condition'], data['min_stock_threshold']))
    try:
        cursor.execute("INSERT INTO ChemicalMaterial (name, cas_number, stock, unit, concentration, category, storage_condition, min_stock_threshold) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (data['name'], data['cas_number'], 0.0, data['unit'], data['concentration'], data['category'], data['storage_condition'], data['min_stock_threshold']))
        get_db().commit()
        return jsonify({'message': '原料添加成功'}), 201
    except pyodbc.IntegrityError:
        return jsonify({'message': '原料存在重复名称或CAS编号，添加失败'}), 409

#  更新单个原料，不更新库存，库存只能由触发器自动更新
@app.route('/materials/<int:material_id>', methods=['PUT'])
def update_material(material_id):
    data = request.get_json()
    #  检查参数
    for key in ['name', 'cas_number', 'unit', 'concentration', 'category', 'storage_condition', 'min_stock_threshold']:
        if key not in data:
            return jsonify({'message': f'缺少参数 {key}'}), 400
        if data[key] is None:
            return jsonify({'message': f'参数 {key} 不能为空'}), 400

    if not isinstance(data['concentration'], float):
        return jsonify({'message': '浓度必须是数字'}), 400
    if data['concentration'] < 0 or data['concentration'] > 100:
        return jsonify({'message': '浓度必须在0-100之间'}), 400
    if not isinstance(data['min_stock_threshold'], float):
        return jsonify({'message': '最小库存阈值必须是数字'}), 400
    if data['min_stock_threshold'] < 0:
        return jsonify({'message': '最小库存阈值不能小于0'}), 400

    cursor = get_db().cursor()

    #检查是否存在该原料
    cursor.execute("SELECT * FROM ChemicalMaterial WHERE material_id=?", (material_id,))
    if not cursor.fetchone():
        return jsonify({'message': '该原料不存在'}), 404

    try:
        cursor.execute("UPDATE ChemicalMaterial SET name=?, cas_number=?, unit=?, concentration=?, category=?, storage_condition=?, min_stock_threshold=? WHERE material_id=?",
                      (data['name'], data['cas_number'], data['unit'], data['concentration'], data['category'], data['storage_condition'], data['min_stock_threshold'], material_id))
        get_db().commit()
        return jsonify({'message': '原料更新成功'}), 200
    except pyodbc.IntegrityError:
        return jsonify({'message': '原料存在重复名称或CAS编号，更新失败'}), 409

# 删除单个原料，如果存在关联的任何记录，则无法删除
@app.route('/materials/<int:material_id>', methods=['DELETE'])
def delete_material(material_id):
    cursor = get_db().cursor()
    #检查是否存在该原料
    cursor.execute("SELECT * FROM ChemicalMaterial WHERE material_id=?", (material_id,))
    if not cursor.fetchone():
        return jsonify({'message': '该原料不存在'}), 404
    #检查是否存在关联，进货，使用
    cursor.execute("SELECT * FROM PurchaseMaterial WHERE material_id=?", (material_id,))
    if cursor.fetchone():
        return jsonify({'message': '该原料存在关联进货记录，无法删除'}), 400
    cursor.execute("SELECT * FROM UseMaterial WHERE material_id=?", (material_id,))
    if cursor.fetchone():
        return jsonify({'message': '该原料存在关联使用记录，无法删除'}), 400

    cursor.execute("DELETE FROM ChemicalMaterial WHERE material_id=?", (material_id,))
    get_db().commit()
    return jsonify({'message': '原料删除成功'}), 200

# 产品增删改查

# 产品数据格式
'''
{
  "name": "产品名称",
  "unit": "单位（如kg/L）",
  "hazard_rating": "危险等级（I-V）"
}'''

# 获取所有产品
@app.route('/products', methods=['GET'])
def get_products():
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM ChemicalProduct")
    columns = [column[0] for column in cursor.description]
    return jsonify([dict(zip(columns, row)) for row in cursor.fetchall()])

# 由id获取单个产品
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM ChemicalProduct WHERE product_id=?", (product_id,))
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    if row:
        return jsonify(dict(zip(columns, row)))
    else:
        return jsonify({'message': f'id为{product_id}的产品不存在'}), 404


# 添加产品
@app.route('/products', methods=['POST'])
def add_product():
    data = request.get_json()

    # 参数检查
    required_fields = ['name', 'unit', 'hazard_rating']
    for key in required_fields:
        if key not in data or data[key] is None:
            return jsonify({'message': f'缺少参数 {key}'}), 400

    # 危险等级格式校验
    if data['hazard_rating'] not in ['I', 'II', 'III', 'IV', 'V']:
        return jsonify({'message': '危险等级必须为I-V的罗马数字'}), 400

    cursor = get_db().cursor()
    try:
        cursor.execute(
            "INSERT INTO ChemicalProduct (name, unit, hazard_rating, stock) VALUES (?, ?, ?, 0.0)",
            (data['name'], data['unit'], data['hazard_rating'])
        )
        get_db().commit()
        return jsonify({'message': '产品添加成功'}), 201
    except pyodbc.IntegrityError:
        return jsonify({'message': '产品名称已存在'}), 409


# 更新产品信息
@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()

    # 校验所有字段
    required_fields = ['name', 'unit', 'hazard_rating']
    for key in required_fields:
        if key not in data or data[key] is None:
            return jsonify({'message': f'缺少参数 {key}'}), 400

    # 校验危险等级格式
    if data['hazard_rating'] not in ['I', 'II', 'III', 'IV', 'V']:
        return jsonify({'message': '危险等级必须为I-V的罗马数字'}), 400

    cursor = get_db().cursor()

    # 检查产品是否存在
    cursor.execute("SELECT product_id FROM ChemicalProduct WHERE product_id=?", (product_id,))
    if not cursor.fetchone():
        return jsonify({'message': '该产品不存在'}), 404

    # 更新产品信息
    try:
        cursor.execute(
            "UPDATE ChemicalProduct SET name=?, unit=?, hazard_rating=? WHERE product_id=?",
            (data['name'], data['unit'], data['hazard_rating'], product_id)
        )
        get_db().commit()
        return jsonify({'message': '产品更新成功'}), 200
    except pyodbc.IntegrityError:
        return jsonify({'message': '产品名称已存在'}), 409


# 删除产品（存在关联记录时禁止删除）
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    cursor = get_db().cursor()

    # 检查产品是否存在
    cursor.execute("SELECT product_id FROM ChemicalProduct WHERE product_id=?", (product_id,))
    if not cursor.fetchone():
        return jsonify({'message': '该产品不存在'}), 404

    # 检查销售记录
    cursor.execute("SELECT TOP 1 record_id FROM SaleProduct WHERE product_id=?", (product_id,))
    if cursor.fetchone():
        return jsonify({'message': '存在关联销售记录，无法删除'}), 409

    # 检查生产记录
    cursor.execute("SELECT TOP 1 record_id FROM ProductionRecord WHERE product_id=?", (product_id,))
    if cursor.fetchone():
        return jsonify({'message': '存在关联生产记录，无法删除'}), 409

    cursor.execute("DELETE FROM ChemicalProduct WHERE product_id=?", (product_id,))
    get_db().commit()
    return jsonify({'message': '产品删除成功'})

# 进货记录增删改查

# 进货记录表数据格式
'''
    supplier_id INT,
    date DATE,
    employee_id INT,
'''
#进货联系集数据格式
'''
    material_id INT,
    record_id INT,
    quantity DECIMAL(10,2),
    unit_price DECIMAL(10,2),
'''
# 获取所有进货记录列表，返回格式为进货记录表数据格式
@app.route('/purchase_records', methods=['GET'])
def get_purchase_records():
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM PurchaseRecord")
    columns = [column[0] for column in cursor.description]
    return jsonify([dict(zip(columns, row)) for row in cursor.fetchall()])

# 查找某个进货记录id的原料列表,返回格式为json对象数组，每个对象为{原料id， 原料名称， 数量， 单价（每单位的价钱）， 原料单位}
@app.route('/purchase_records/<int:record_id>/materials', methods=['GET'])
def get_purchase_materials(record_id):
    cursor = get_db().cursor()
    cursor.execute("SELECT CM.material_id, CM.name, PM.quantity, PM.unit_price, CM.unit FROM ChemicalMaterial CM, PurchaseMaterial PM, PurchaseRecord PR WHERE CM.material_id = PM.material_id AND PM.record_id = PR.record_id AND PM.record_id = ?", (record_id,))
    columns = [column[0] for column in cursor.description]
    return jsonify([dict(zip(columns, row)) for row in cursor.fetchall()])

















if __name__ == '__main__':
    app.run(debug=True)

