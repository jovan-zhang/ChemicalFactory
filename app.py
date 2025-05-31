from flask import Flask, jsonify, request, g
import pyodbc


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


# 根据id获取进货记录详情
@app.route('/purchase_records/<int:record_id>', methods=['GET'])
def get_purchase_record_detail(record_id):
    try:
        cursor = get_db().cursor()

        # 查询进货记录详情
        cursor.execute("""
            SELECT 
                pr.record_id,
                pr.date,
                pr.supplier_id,
                s.name AS supplier_name,
                pr.employee_id,
                e.name AS employee_name
            FROM PurchaseRecord pr
            JOIN Supplier s ON pr.supplier_id = s.supplier_id
            JOIN Buyer e ON pr.employee_id = e.employee_id
            WHERE pr.record_id = ?
        """, (record_id,))

        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": f"进货记录ID {record_id} 不存在"}), 404

        return jsonify(dict(zip(columns, row))), 200

    except pyodbc.Error as e:
        error_msg = str(e).split('\n')[0]
        return jsonify({"error": f"数据库错误: {error_msg}"}), 500

# 查找某个进货记录id的原料列表,返回格式为json对象数组，每个对象为{原料id， 原料名称， 数量， 单价（每单位的价钱）， 原料单位}
@app.route('/purchase_records/<int:record_id>/materials', methods=['GET'])
def get_purchase_materials(record_id):
    cursor = get_db().cursor()
    cursor.execute("SELECT CM.material_id, CM.name, PM.quantity, PM.unit_price, CM.unit FROM ChemicalMaterial CM, PurchaseMaterial PM, PurchaseRecord PR WHERE CM.material_id = PM.material_id AND PM.record_id = PR.record_id AND PM.record_id = ?", (record_id,))
    columns = [column[0] for column in cursor.description]
    return jsonify([dict(zip(columns, row)) for row in cursor.fetchall()])




# 添加进货记录（直接处理，不使用存储过程）
@app.route('/purchase_records', methods=['POST'])
def add_purchase_record():
    data = request.get_json()

    # 基本参数校验
    required_fields = ['supplier_id', 'date', 'employee_id', 'materials']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必要字段: {field}'}), 400

    if not isinstance(data['materials'], list) or len(data['materials']) == 0:
        return jsonify({'error': 'materials必须非空'}), 400

    for idx, item in enumerate(data['materials']):
        for key in ['material_id', 'quantity', 'unit_price']:
            if key not in item:
                return jsonify({'error': f'materials[{idx}] 缺少字段: {key}'}), 400
            if key in ['quantity', 'unit_price']:
                try:
                    item[key] = float(item[key])
                except ValueError:
                    return jsonify({'error': f'materials[{idx}].{key} 必须是数字'}), 400

    # 准备参数
    supplier_id = data['supplier_id']
    record_date = data['date']
    employee_id = data['employee_id']
    materials = data['materials']
    conn = get_db()
    cursor = conn.cursor()
    try:

        # 开始事务
        conn.autocommit = False

        # 1. 插入进货记录主表
        cursor.execute(
            "INSERT INTO PurchaseRecord (supplier_id, date, employee_id) OUTPUT INSERTED.record_id VALUES (?, ?, ?)",
            (supplier_id, record_date, employee_id)
        )

        # 获取新生成的record_id
        result = cursor.fetchone()
        if not result:
            conn.rollback()
            return jsonify({"error": "无法获取新进货记录ID"}), 500

        new_record_id = result[0]

        # 2. 插入进货联系集（PurchaseMaterial）
        for material in materials:
            cursor.execute(
                "INSERT INTO PurchaseMaterial (material_id, record_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (material['material_id'], new_record_id, material['quantity'], material['unit_price'])
            )
        # 提交事务
        conn.commit()

        return jsonify({
            "message": "进货记录添加成功",
            "new_record_id": new_record_id
        }), 201

    except pyodbc.Error as e:
        # 提取更详细的错误信息
        error_msg = str(e)
        if hasattr(e, 'args') and len(e.args) > 1:
            error_msg = e.args[1]

        # 记录错误信息以便调试
        app.logger.error(f"数据库错误: {error_msg}")

        # 回滚事务
        try:
            if 'conn' in locals():
                conn.rollback()
        except:
            pass
        return jsonify({"error": f"数据库错误: {error_msg}"}), 500

    except Exception as e:
        app.logger.error(f"服务器错误: {str(e)}")
        # 回滚事务
        try:
            if 'conn' in locals():
                conn.rollback()
        except:
            pass
        return jsonify({"error": f"服务器错误: {str(e)}"}), 500


# 删除进货记录
@app.route('/purchase_records/<int:record_id>', methods=['DELETE'])
def delete_purchase_record(record_id):
    try:
        conn = get_db()
        cursor = conn.cursor()

        # 检查进货记录是否存在
        cursor.execute("SELECT record_id FROM PurchaseRecord WHERE record_id = ?", (record_id,))
        if not cursor.fetchone():
            return jsonify({'message': f'进货记录ID {record_id} 不存在'}), 404

        # 调用存储过程删除记录
        cursor.execute("EXEC sp_DeletePurchaseRecord @record_id = ?", (record_id,))
        conn.commit()

        return jsonify({'message': f'进货记录ID {record_id} 删除成功'}), 200

    except pyodbc.Error as e:
        # 简化错误处理
        error_msg = str(e).split('\n')[0]  # 只取第一行错误信息
        return jsonify({"error": f"数据库错误: {error_msg}"}), 500

    except Exception as e:
        return jsonify({"error": f"服务器错误: {str(e)}"}), 500

# 获取所有销售记录列表，返回格式为销售记录表数据格式
@app.route('/sale_records', methods=['GET'])
def get_sale_records():
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM SalesRecord")
    columns = [column[0] for column in cursor.description]
    return jsonify([dict(zip(columns, row)) for row in cursor.fetchall()])


# 获取销售记录详情
@app.route('/sale_records/<int:record_id>', methods=['GET'])
def get_sale_record_detail(record_id):
    try:
        cursor = get_db().cursor()

        # 查询销售记录详情
        cursor.execute("""
            SELECT 
                sr.record_id,
                sr.date,
                sr.customer_id,
                c.name AS customer_name,
                sr.employee_id,
                e.name AS employee_name
                
            FROM SalesRecord sr
            JOIN Customer c ON sr.customer_id = c.customer_id
            JOIN Distributor e ON sr.employee_id = e.employee_id
            WHERE sr.record_id = ?
        """, (record_id,))

        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": f"销售记录ID {record_id} 不存在"}), 404

        return jsonify(dict(zip(columns, row))), 200

    except pyodbc.Error as e:
        error_msg = str(e).split('\n')[0]
        return jsonify({"error": f"数据库错误: {error_msg}"}), 500

# 查找某个销售记录id的产品列表，返回格式为json对象数组，每个对象为{产品id， 产品名称， 数量， 单价（每单位的价钱）， 产品单位}
@app.route('/sale_records/<int:record_id>/products', methods=['GET'])
def get_sale_products(record_id):
    cursor = get_db().cursor()
    cursor.execute("""
        SELECT CP.product_id, CP.name, SP.quantity, SP.unit_price, CP.unit 
        FROM ChemicalProduct CP, SaleProduct SP, SalesRecord SR 
        WHERE CP.product_id = SP.product_id 
          AND SP.record_id = SR.record_id 
          AND SP.record_id = ?
    """, (record_id,))
    columns = [column[0] for column in cursor.description]
    return jsonify([dict(zip(columns, row)) for row in cursor.fetchall()])



# 添加销售记录
@app.route('/sale_records', methods=['POST'])
def add_sale_record():
    data = request.get_json()

    # 基本参数校验
    required_fields = ['customer_id', 'date', 'employee_id', 'products']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必要字段: {field}'}), 400

    if not isinstance(data['products'], list) or len(data['products']) == 0:
        return jsonify({'error': 'products必须是非空数组'}), 400

    for idx, item in enumerate(data['products']):
        for key in ['product_id', 'quantity', 'unit_price']:
            if key not in item:
                return jsonify({'error': f'products[{idx}] 缺少字段: {key}'}), 400
            if key in ['quantity', 'unit_price']:
                try:
                    item[key] = float(item[key])
                except ValueError:
                    return jsonify({'error': f'products[{idx}].{key} 必须是数字'}), 400
                if item[key] <= 0:
                    return jsonify({'error': f'products[{idx}].{key} 必须大于0'}), 400

    # 准备参数
    customer_id = data['customer_id']
    record_date = data['date']
    employee_id = data['employee_id']
    products = data['products']
    conn = get_db()
    cursor = conn.cursor()
    try:
        # 开始事务
        conn.autocommit = False

        # 1. 插入销售记录主表
        cursor.execute(
            "INSERT INTO SalesRecord (customer_id, date, employee_id) OUTPUT INSERTED.record_id VALUES (?, ?, ?)",
            (customer_id, record_date, employee_id)
        )

        # 获取新生成的record_id
        result = cursor.fetchone()
        if not result:
            conn.rollback()
            return jsonify({"error": "无法获取新销售记录ID"}), 500

        new_record_id = result[0]

        # 2. 插入销售产品联系集（SaleProduct）
        for product in products:
            cursor.execute(
                "INSERT INTO SaleProduct (product_id, record_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (product['product_id'], new_record_id, product['quantity'], product['unit_price'])
            )

        # 提交事务（库存更新由触发器自动处理）
        conn.commit()

        return jsonify({
            "message": "销售记录添加成功",
            "new_record_id": new_record_id
        }), 201

    except pyodbc.Error as e:
        error_msg = str(e).split('\n')[0]  # 只取第一行错误信息
        try:
            if 'conn' in locals():
                conn.rollback()
        except:
            pass
        return jsonify({"error": f"数据库错误: {error_msg}"}), 500

    except Exception as e:
        try:
            if 'conn' in locals():
                conn.rollback()
        except:
            pass
        return jsonify({"error": f"服务器错误: {str(e)}"}), 500


# 删除销售记录
@app.route('/sale_records/<int:record_id>', methods=['DELETE'])
def delete_sale_record(record_id):
    try:
        conn = get_db()
        cursor = conn.cursor()

        # 检查销售记录是否存在
        cursor.execute("SELECT record_id FROM SalesRecord WHERE record_id = ?", (record_id,))
        if not cursor.fetchone():
            return jsonify({'message': f'销售记录ID {record_id} 不存在'}), 404

        # 调用存储过程删除记录
        cursor.execute("EXEC sp_DeleteSalesRecord @record_id = ?", (record_id,))
        conn.commit()

        return jsonify({'message': f'销售记录ID {record_id} 删除成功'}), 200

    except pyodbc.Error as e:
        # 处理数据库错误
        error_msg = str(e).split('\n')[0]  # 取错误信息第一行

        return jsonify({"error": f"数据库错误: {error_msg}"}), 500

    except Exception as e:
        return jsonify({"error": f"操作失败: {str(e)}"}), 500


# 获取所有生产记录（简要信息）
@app.route('/production_records', methods=['GET'])
def get_production_records():
    try:
        cursor = get_db().cursor()

        # 查询生产记录主表信息
        cursor.execute("""
            SELECT 
                pr.record_id,
                pr.date,
                pr.theoretical_output,
                pr.actual_output,
                cp.name AS product_name,
                pl.name AS line_name
            FROM ProductionRecord pr
            JOIN ChemicalProduct cp ON pr.product_id = cp.product_id
            JOIN ProductionLine pl ON pr.line_id = pl.line_id
            ORDER BY pr.date DESC, pr.record_id DESC
        """)

        columns = [column[0] for column in cursor.description]
        records = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(records), 200

    except pyodbc.Error as e:
        error_msg = str(e).split('\n')[0]
        return jsonify({"error": f"数据库错误: {error_msg}"}), 500


# 获取生产记录详情
@app.route('/production_records/<int:record_id>', methods=['GET'])
def get_production_record_detail(record_id):
    try:
        cursor = get_db().cursor()

        # 查询生产记录详情
        cursor.execute("""
            SELECT 
                pr.record_id,
                pr.date,
                pr.product_id,
                cp.name AS product_name,
                pr.line_id,
                pl.name AS line_name,
                pr.theoretical_output,
                pr.actual_output
            FROM ProductionRecord pr
            JOIN ChemicalProduct cp ON pr.product_id = cp.product_id
            JOIN ProductionLine pl ON pr.line_id = pl.line_id
            WHERE pr.record_id = ?
        """, (record_id,))

        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": f"生产记录ID {record_id} 不存在"}), 404

        return jsonify(dict(zip(columns, row))), 200

    except pyodbc.Error as e:
        error_msg = str(e).split('\n')[0]
        return jsonify({"error": f"数据库错误: {error_msg}"}), 500

# 获取单个生产记录的原料使用列表
@app.route('/production_records/<int:record_id>/materials', methods=['GET'])
def get_production_record_materials(record_id):
    try:
        conn = get_db()
        cursor = conn.cursor()

        # 1. 验证生产记录是否存在
        cursor.execute("SELECT record_id FROM ProductionRecord WHERE record_id = ?", (record_id,))
        if not cursor.fetchone():
            return jsonify({"error": f"生产记录ID {record_id} 不存在"}), 404

        # 2. 获取原料使用列表
        cursor.execute("""
            SELECT 
                um.material_id,
                cm.name AS material_name,
                um.quantity_used,
                cm.unit
            FROM UseMaterial um
            JOIN ChemicalMaterial cm ON um.material_id = cm.material_id
            WHERE um.record_id = ?
        """, (record_id,))

        columns = [column[0] for column in cursor.description]
        materials = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(materials), 200

    except pyodbc.Error as e:
        error_msg = str(e).split('\n')[0]
        return jsonify({"error": f"数据库错误: {error_msg}"}), 500


# 添加生产记录
@app.route('/production_records', methods=['POST'])
def add_production_record():
    data = request.get_json()

    # 基本参数校验
    required_fields = ['product_id', 'line_id', 'date', 'theoretical_output', 'actual_output', 'materials']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必要字段: {field}'}), 400

    # 校验产量值
    try:
        theoretical_output = float(data['theoretical_output'])
        actual_output = float(data['actual_output'])
        if theoretical_output <= 0 or actual_output <= 0:
            return jsonify({'error': '理论产量和实际产量必须大于0'}), 400
    except (TypeError, ValueError):
        return jsonify({'error': '产量值必须是有效数字'}), 400

    # 校验原料列表
    if not isinstance(data['materials'], list) or len(data['materials']) == 0:
        return jsonify({'error': 'materials必须是非空数组'}), 400

    for idx, material in enumerate(data['materials']):
        for key in ['material_id', 'quantity']:
            if key not in material:
                return jsonify({'error': f'materials[{idx}] 缺少字段: {key}'}), 400
        try:
            material['quantity'] = float(material['quantity'])
            if material['quantity'] <= 0:
                return jsonify({'error': f'materials[{idx}].quantity 必须大于0'}), 400
        except (TypeError, ValueError):
            return jsonify({'error': f'materials[{idx}].quantity 必须是有效数字'}), 400

    # 准备参数
    product_id = data['product_id']
    line_id = data['line_id']
    record_date = data['date']
    materials = data['materials']

    # 检查产品是否存在
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT product_id FROM ChemicalProduct WHERE product_id = ?", (product_id,))
    if not cursor.fetchone():
        return jsonify({'error': f'产品ID {product_id} 不存在'}), 400

    # 检查生产线是否存在
    cursor.execute("SELECT line_id FROM ProductionLine WHERE line_id = ?", (line_id,))
    if not cursor.fetchone():
        return jsonify({'error': f'生产线ID {line_id} 不存在'}), 400

    # 检查所有原料是否存在
    material_ids = [m['material_id'] for m in materials]
    if material_ids:  # 确保列表不为空
        placeholders = ','.join(['?'] * len(material_ids))
        cursor.execute(f"SELECT material_id FROM ChemicalMaterial WHERE material_id IN ({placeholders})", material_ids)
        existing_ids = [row[0] for row in cursor.fetchall()]

        missing_ids = set(material_ids) - set(existing_ids)
        if missing_ids:
            return jsonify({'error': f'以下原料ID不存在: {", ".join(map(str, missing_ids))}'}), 400

    try:
        # 开始事务
        conn.autocommit = False

        # 1. 插入生产记录主表
        cursor.execute(
            "INSERT INTO ProductionRecord (product_id, line_id, date, theoretical_output, actual_output) "
            "OUTPUT INSERTED.record_id VALUES (?, ?, ?, ?, ?)",
            (product_id, line_id, record_date, theoretical_output, actual_output)
        )

        # 获取新生成的record_id
        result = cursor.fetchone()
        if not result:
            conn.rollback()
            return jsonify({"error": "无法获取新生产记录ID"}), 500

        new_record_id = result[0]

        # 2. 插入原料使用联系集（UseMaterial）
        for material in materials:
            cursor.execute(
                "INSERT INTO UseMaterial (material_id, record_id, quantity_used) VALUES (?, ?, ?)",
                (material['material_id'], new_record_id, material['quantity'])
            )

        # 提交事务
        conn.commit()

        return jsonify({
            "message": "生产记录添加成功",
            "new_record_id": new_record_id
        }), 201

    except pyodbc.Error as e:
        # 处理数据库错误
        error_msg = str(e).split('\n')[0]
        try:
            conn.rollback()
        except:
            pass
        return jsonify({"error": f"数据库错误: {error_msg}"}), 500

    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        return jsonify({"error": f"操作失败: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)

