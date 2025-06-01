// js/app.js
import { API, setAuthToken, getAuthToken } from './api.js';

// Global UI Elements
const sidebarToggle = document.getElementById('sidebarToggle');
const mainAppContainer = document.getElementById('main-app-container'); // New
const loginPage = document.getElementById('login-page');               // New

const pageTitle = document.getElementById('pageTitle');
const logoutBtn = document.getElementById('logoutBtn');
const userInfoSpan = document.getElementById('userInfo');

// Login Page Elements
const loginForm = document.getElementById('loginForm');
const loginErrorAlert = document.getElementById('loginErrorAlert');


// Modals (still used for CRUD operations *within* the main app)
const materialModal = new bootstrap.Modal(document.getElementById('materialModal'));
const materialForm = document.getElementById('materialForm');
const productModal = new bootstrap.Modal(document.getElementById('productModal'));
const productForm = document.getElementById('productForm');
const purchaseRecordModal = new bootstrap.Modal(document.getElementById('purchaseRecordModal'));
const purchaseRecordForm = document.getElementById('purchaseRecordForm');
const saleRecordModal = new bootstrap.Modal(document.getElementById('saleRecordModal'));
const saleRecordForm = document.getElementById('saleRecordForm');
const productionRecordModal = new bootstrap.Modal(document.getElementById('productionRecordModal'));
const productionRecordForm = document.getElementById('productionRecordForm');

// Global state - Now directly retrieves from localStorage (or defaults to null)
let currentView = 'dashboard';
let currentUser = localStorage.getItem('currentUsername') || null; // 从 localStorage 读取
let currentRole = localStorage.getItem('currentRole') || null;       // 从 localStorage 读取

// Permission mapping based on backend ROLE_PERMISSIONS
// This is for client-side UI control. Backend still enforces actual permissions.
const ROLE_PERMISSIONS = {
    'admin': {
        'materials': ['GET', 'POST', 'PUT', 'DELETE'],
        'products': ['GET', 'POST', 'PUT', 'DELETE'],
        'purchase_records': ['GET', 'POST', 'DELETE'],
        'sale_records': ['GET', 'POST', 'DELETE'],
        'production_records': ['GET', 'POST']
    },
    'buyer': {
        'materials': ['GET'],
        'products': ['GET'],
        'purchase_records': ['GET', 'POST'],
        'sale_records': [],
        'production_records': []
    },
    'distributor': {
        'materials': ['GET'],
        'products': ['GET'],
        'purchase_records': [],
        'sale_records': ['GET', 'POST'],
        'production_records': []
    },
    'worker': {
        'materials': ['GET'],
        'products': ['GET'],
        'purchase_records': [],
        'sale_records': [],
        'production_records': ['GET', 'POST']
    }
};

// Helper to check if current user has permission for an action (UI control)
const hasPermission = (resource, method) => {
    if (!currentRole) return false;
    const allowedMethods = ROLE_PERMISSIONS[currentRole] && ROLE_PERMISSIONS[currentRole][resource];
    return allowedMethods && allowedMethods.includes(method);
};

// Helper to update UI elements (sidebar links, buttons) based on user's role
const updateUIPermissions = () => {
    // Control sidebar visibility
    document.querySelectorAll('.list-group-item[data-view]').forEach(link => {
        const resource = link.dataset.view;
        // Dashboard is always visible if logged in
        if (resource === 'dashboard') {
            link.classList.remove('d-none');
            return;
        }
        // Other links depend on GET permission for their resource
        if (hasPermission(resource, 'GET')) { // <-- 这里依赖 currentRole，会因为 updateLoginStatus 设置而更新
            link.classList.remove('d-none');
        } else {
            link.classList.add('d-none');
        }
    });

    // Control "Add" buttons visibility
    document.querySelectorAll('.add-btn').forEach(btn => {
        const requiredRoles = btn.dataset.permissionRoles ? btn.dataset.permissionRoles.split(',') : [];
        if (requiredRoles.includes(currentRole) || requiredRoles.includes('all')) { // <-- 这里依赖 currentRole
            btn.classList.remove('d-none');
        } else {
            btn.classList.add('d-none');
        }
    });
};

// Helper for displaying alerts (Toast notifications)
const showAlert = (message, type = 'success') => {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show alert-message`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        <span>${message}</span>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertDiv);

    setTimeout(() => {
        if (alertDiv && alertDiv.parentNode) {
            alertDiv.classList.remove('show');
            alertDiv.classList.add('fade');
            setTimeout(() => alertDiv.parentNode.removeChild(alertDiv), 150); // Remove after fade out
        }
    }, 5000); // Remove after 5 seconds
};

// --- Authentication Functions ---
const handleLogin = async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    loginErrorAlert.classList.add('d-none'); // Hide previous errors

    try {
        const data = await API.login(username, password);
        setAuthToken(data.token); // 存储 token
        localStorage.setItem('currentUsername', data.username); // <-- 新增：存储后端返回的用户名
        localStorage.setItem('currentRole', data.role);         // <-- 新增：存储后端返回的角色

        updateLoginStatus(); // 更新UI状态
        loginPage.classList.add('d-none'); // 隐藏登录页面
        mainAppContainer.classList.remove('d-none'); // 显示主应用界面
        showAlert('登录成功！', 'success');
        showView('dashboard'); // 导航到仪表盘
    } catch (error) {
        loginErrorAlert.textContent = error.message.replace(/HTTP Error \d+: /, ''); // 清理错误信息
        loginErrorAlert.classList.remove('d-none');
        console.error('Login failed:', error);
    }
};

const handleLogout = () => {
    setAuthToken(null); // 清除 token
    localStorage.removeItem('currentUsername'); // <-- 修改：清除存储的用户名
    localStorage.removeItem('currentRole');     // <-- 修改：清除存储的角色

    updateLoginStatus(); // 更新UI状态
    showAlert('注销成功！', 'info');
    mainAppContainer.classList.add('d-none'); // 隐藏主应用界面
    loginPage.classList.remove('d-none'); // 显示登录页面
    loginForm.reset(); // 清空登录表单
    loginErrorAlert.classList.add('d-none'); // 隐藏任何登录错误信息
};

// 重新编写的 updateLoginStatus 逻辑
const updateLoginStatus = () => {
    // 直接从 localStorage 获取用户信息和 token
    currentUser = localStorage.getItem('currentUsername'); // <-- 直接赋值
    currentRole = localStorage.getItem('currentRole');     // <-- 直接赋值
    const token = getAuthToken(); // 检查 token 是否仍然存在

    // 只有当 token、用户名和角色都存在时，才视为已登录状态
    if (token && currentUser && currentRole) {
        userInfoSpan.textContent = `欢迎, ${currentUser} (${currentRole})`;
        mainAppContainer.classList.remove('d-none'); // 确保主应用界面可见
        loginPage.classList.add('d-none');           // 确保登录界面隐藏
    } else {
        // 否则，清除所有相关信息，并显示登录界面
        currentUser = null;
        currentRole = null;
        setAuthToken(null); // 确保 token 也被清除
        localStorage.removeItem('currentUsername');
        localStorage.removeItem('currentRole');
        userInfoSpan.textContent = '';
        mainAppContainer.classList.add('d-none');  // 确保主应用界面隐藏
        loginPage.classList.remove('d-none');      // 确保登录界面可见
    }
    updateUIPermissions(); // 根据新的登录状态更新UI权限
};

// --- Navigation and View Management ---
const showView = async (viewId) => {
    // Hide all content views
    document.querySelectorAll('.content-view').forEach(view => {
        view.classList.add('d-none');
    });

    // Show the selected view
    const targetView = document.getElementById(`${viewId}-view`);
    if (targetView) {
        targetView.classList.remove('d-none');
        pageTitle.textContent = document.querySelector(`#nav-${viewId}`)?.textContent || '仪表盘';
        currentView = viewId;

        // Update active class for sidebar links
        document.querySelectorAll('.list-group-item').forEach(link => {
            link.classList.remove('active');
        });
        const currentNavLink = document.getElementById(`nav-${viewId}`);
        if (currentNavLink) {
            currentNavLink.classList.add('active');
        }

        // Load data for the view if logged in and has permission
        if (currentUser) {
            if (viewId === 'materials') {
                await loadMaterials();
            } else if (viewId === 'products') {
                await loadProducts();
            } else if (viewId === 'purchase_records') {
                await loadPurchaseRecords();
            } else if (viewId === 'sale_records') {
                await loadSaleRecords();
            } else if (viewId === 'production_records') {
                await loadProductionRecords();
            }
        }
    } else {
        console.warn(`View ID ${viewId} not found.`);
    }
};

// --- Generic Table Renderer ---
const renderTable = (tableBodyId, data, columns, actions = []) => {
    const tableBody = document.getElementById(tableBodyId);
    tableBody.innerHTML = ''; // Clear existing rows

    if (!data || data.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="${columns.length + (actions.length > 0 ? 1 : 0)}" class="text-center text-muted">暂无数据</td></tr>`;
        return;
    }

    data.forEach(item => {
        const row = document.createElement('tr');
        columns.forEach(col => {
            const cell = document.createElement('td');
            cell.textContent = item[col];
            row.appendChild(cell);
        });

        if (actions.length > 0) {
            const actionCell = document.createElement('td');
            actions.forEach(action => {
                let showButton = true;
                if (action.permissionResource && action.permissionMethod) {
                    showButton = hasPermission(action.permissionResource, action.permissionMethod);
                }
                
                if (showButton) {
                    const button = document.createElement('button');
                    button.className = `btn btn-sm btn-${action.type} me-2`;
                    button.textContent = action.label;
                    button.onclick = () => action.handler(item);
                    actionCell.appendChild(button);
                }
            });
            row.appendChild(actionCell);
        }
        tableBody.appendChild(row);
    });
};

// --- Material Management ---
const loadMaterials = async () => {
    if (!hasPermission('materials', 'GET')) {
        document.getElementById('materialsTableBody').innerHTML = `<tr><td colspan="10" class="text-center text-danger">您没有权限查看原料信息。</td></tr>`;
        return;
    }

    try {
        const materials = await API.getMaterials();
        const columns = ['material_id', 'name', 'cas_number', 'stock', 'unit', 'concentration', 'category', 'storage_condition', 'min_stock_threshold'];
        const actions = [
            { label: '编辑', type: 'info', handler: editMaterial, permissionResource: 'materials', permissionMethod: 'PUT' },
            { label: '删除', type: 'danger', handler: deleteMaterial, permissionResource: 'materials', permissionMethod: 'DELETE' }
        ];
        renderTable('materialsTableBody', materials, columns, actions);
    } catch (error) {
        showAlert(`加载原料失败: ${error.message}`, 'danger');
    }
};

const handleMaterialFormSubmit = async (e) => {
    e.preventDefault();
    const mode = materialForm.dataset.mode;
    const materialId = document.getElementById('materialId').value;
    const data = {
        name: document.getElementById('materialName').value,
        cas_number: document.getElementById('materialCasNumber').value,
        unit: document.getElementById('materialUnit').value,
        concentration: parseFloat(document.getElementById('materialConcentration').value),
        category: document.getElementById('materialCategory').value,
        storage_condition: document.getElementById('materialStorageCondition').value,
        min_stock_threshold: parseFloat(document.getElementById('materialMinStockThreshold').value),
    };

    try {
        if (mode === 'add') {
            await API.addMaterial(data);
            showAlert('原料添加成功！', 'success');
        } else if (mode === 'edit') {
            await API.updateMaterial(materialId, data);
            showAlert('原料更新成功！', 'success');
        }
        materialModal.hide();
        await loadMaterials();
    } catch (error) {
        showAlert(`操作失败: ${error.message}`, 'danger');
    }
};

const editMaterial = async (material) => {
    materialForm.dataset.mode = 'edit';
    document.getElementById('materialModalLabel').textContent = '编辑原料';
    document.getElementById('materialId').value = material.material_id;
    document.getElementById('materialName').value = material.name;
    document.getElementById('materialCasNumber').value = material.cas_number;
    document.getElementById('materialUnit').value = material.unit;
    document.getElementById('materialConcentration').value = material.concentration;
    document.getElementById('materialCategory').value = material.category;
    document.getElementById('materialStorageCondition').value = material.storage_condition;
    document.getElementById('materialMinStockThreshold').value = material.min_stock_threshold;
    materialModal.show();
};

const deleteMaterial = async (material) => {
    if (!confirm(`确定要删除原料: ${material.name} (ID: ${material.material_id}) 吗？`)) {
        return;
    }
    try {
        await API.deleteMaterial(material.material_id);
        showAlert('原料删除成功！', 'success');
        await loadMaterials();
    } catch (error) {
        showAlert(`删除失败: ${error.message}`, 'danger');
    }
};

// --- Product Management ---
const loadProducts = async () => {
    if (!hasPermission('products', 'GET')) {
        document.getElementById('productsTableBody').innerHTML = `<tr><td colspan="6" class="text-center text-danger">您没有权限查看产品信息。</td></tr>`;
        return;
    }
    try {
        const products = await API.getProducts();
        const columns = ['product_id', 'name', 'unit', 'hazard_rating', 'stock'];
        const actions = [
            { label: '编辑', type: 'info', handler: editProduct, permissionResource: 'products', permissionMethod: 'PUT' },
            { label: '删除', type: 'danger', handler: deleteProduct, permissionResource: 'products', permissionMethod: 'DELETE' }
        ];
        renderTable('productsTableBody', products, columns, actions);
    } catch (error) {
        showAlert(`加载产品失败: ${error.message}`, 'danger');
    }
};

const handleProductFormSubmit = async (e) => {
    e.preventDefault();
    const mode = productForm.dataset.mode;
    const productId = document.getElementById('productId').value;
    const data = {
        name: document.getElementById('productName').value,
        unit: document.getElementById('productUnit').value,
        hazard_rating: document.getElementById('productHazardRating').value,
    };

    try {
        if (mode === 'add') {
            await API.addProduct(data);
            showAlert('产品添加成功！', 'success');
        } else if (mode === 'edit') {
            await API.updateProduct(productId, data);
            showAlert('产品更新成功！', 'success');
        }
        productModal.hide();
        await loadProducts();
    } catch (error) {
        showAlert(`操作失败: ${error.message}`, 'danger');
    }
};

const editProduct = async (product) => {
    productForm.dataset.mode = 'edit';
    document.getElementById('productModalLabel').textContent = '编辑产品';
    document.getElementById('productId').value = product.product_id;
    document.getElementById('productName').value = product.name;
    document.getElementById('productUnit').value = product.unit;
    document.getElementById('productHazardRating').value = product.hazard_rating;
    productModal.show();
};

const deleteProduct = async (product) => {
    if (!confirm(`确定要删除产品: ${product.name} (ID: ${product.product_id}) 吗？`)) {
        return;
    }
    try {
        await API.deleteProduct(product.product_id);
        showAlert('产品删除成功！', 'success');
        await loadProducts();
    } catch (error) {
        showAlert(`删除失败: ${error.message}`, 'danger');
    }
};

// --- Purchase Record Management ---
let purchaseMaterialCounter = 0; // Use a counter to assign unique IDs
const addPurchaseMaterialInput = (material = {}) => {
    const container = document.getElementById('purchaseMaterialsContainer');
    const div = document.createElement('div');
    div.className = 'material-item';
    div.dataset.index = purchaseMaterialCounter++; // Assign a unique index
    div.innerHTML = `
        <input type="number" class="form-control form-control-sm" placeholder="原料ID" value="${material.material_id || ''}" required data-field="material_id">
        <input type="number" step="0.01" min="0" class="form-control form-control-sm" placeholder="数量" value="${material.quantity || ''}" required data-field="quantity">
        <input type="number" step="0.01" min="0" class="form-control form-control-sm" placeholder="单价" value="${material.unit_price || ''}" required data-field="unit_price">
        <button type="button" class="btn btn-danger btn-sm remove-material-btn">移除</button>
    `;
    container.appendChild(div);

    div.querySelector('.remove-material-btn').onclick = () => {
        div.remove();
    };
};

const loadPurchaseRecords = async () => {
    if (!hasPermission('purchase_records', 'GET')) {
        document.getElementById('purchaseRecordsTableBody').innerHTML = `<tr><td colspan="5" class="text-center text-danger">您没有权限查看进货记录。</td></tr>`;
        return;
    }
    try {
        const records = await API.getPurchaseRecords();
        const columns = ['record_id', 'date', 'supplier_id', 'employee_id'];
        const actions = [
            { label: '查看', type: 'primary', handler: viewPurchaseRecordDetail, permissionResource: 'purchase_records', permissionMethod: 'GET' },
            { label: '删除', type: 'danger', handler: deletePurchaseRecord, permissionResource: 'purchase_records', permissionMethod: 'DELETE' }
        ];
        renderTable('purchaseRecordsTableBody', records, columns, actions);
    } catch (error) {
        showAlert(`加载进货记录失败: ${error.message}`, 'danger');
    }
};

const viewPurchaseRecordDetail = async (record) => {
    // Reset modal state
    document.getElementById('purchaseRecordForm').classList.add('d-none');
    document.getElementById('purchaseRecordDetails').classList.remove('d-none');
    document.getElementById('purchaseRecordModalLabel').textContent = '进货记录详情';

    try {
        const detail = await API.getPurchaseRecordDetail(record.record_id);
        document.getElementById('detailPurchaseRecordId').textContent = detail.record_id;
        document.getElementById('detailPurchaseDate').textContent = detail.date;
        document.getElementById('detailPurchaseSupplierName').textContent = detail.supplier_name;
        document.getElementById('detailPurchaseSupplierId').textContent = detail.supplier_id;
        document.getElementById('detailPurchaseEmployeeName').textContent = detail.employee_name;
        document.getElementById('detailPurchaseEmployeeId').textContent = detail.employee_id;

        const materials = await API.getPurchaseMaterials(record.record_id);
        const materialsTableBody = document.getElementById('detailPurchaseMaterialsTableBody');
        materialsTableBody.innerHTML = '';
        if (materials.length === 0) {
            materialsTableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">无原料信息</td></tr>';
        } else {
            materials.forEach(mat => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${mat.material_id}</td>
                    <td>${mat.name}</td>
                    <td>${mat.quantity}</td>
                    <td>${mat.unit}</td>
                    <td>${mat.unit_price}</td>
                `;
                materialsTableBody.appendChild(row);
            });
        }
        purchaseRecordModal.show();
    } catch (error) {
        showAlert(`加载进货记录详情失败: ${error.message}`, 'danger');
    }
};

const handlePurchaseRecordFormSubmit = async (e) => {
    e.preventDefault();
    const data = {
        supplier_id: parseInt(document.getElementById('purchaseSupplierId').value),
        date: document.getElementById('purchaseDate').value,
        employee_id: parseInt(document.getElementById('purchaseEmployeeId').value),
        materials: []
    };

    document.querySelectorAll('#purchaseMaterialsContainer .material-item').forEach(itemDiv => {
        data.materials.push({
            material_id: parseInt(itemDiv.querySelector('[data-field="material_id"]').value),
            quantity: parseFloat(itemDiv.querySelector('[data-field="quantity"]').value),
            unit_price: parseFloat(itemDiv.querySelector('[data-field="unit_price"]').value)
        });
    });

    try {
        await API.addPurchaseRecord(data);
        showAlert('进货记录添加成功！', 'success');
        purchaseRecordModal.hide();
        await loadPurchaseRecords();
    } catch (error) {
        showAlert(`添加失败: ${error.message}`, 'danger');
    }
};

const deletePurchaseRecord = async (record) => {
    if (!confirm(`确定要删除进货记录: ID ${record.record_id} 吗？此操作将无法撤销，并可能影响库存数据。`)) {
        return;
    }
    try {
        await API.deletePurchaseRecord(record.record_id);
        showAlert('进货记录删除成功！', 'success');
        await loadPurchaseRecords();
    } catch (error) {
        showAlert(`删除失败: ${error.message}`, 'danger');
    }
};


// --- Sale Record Management ---
let saleProductCounter = 0; // Use a counter to assign unique IDs
const addSaleProductInput = (product = {}) => {
    const container = document.getElementById('saleProductsContainer');
    const div = document.createElement('div');
    div.className = 'product-item';
    div.dataset.index = saleProductCounter++; // Assign a unique index
    div.innerHTML = `
        <input type="number" class="form-control form-control-sm" placeholder="产品ID" value="${product.product_id || ''}" required data-field="product_id">
        <input type="number" step="0.01" min="0" class="form-control form-control-sm" placeholder="数量" value="${product.quantity || ''}" required data-field="quantity">
        <input type="number" step="0.01" min="0" class="form-control form-control-sm" placeholder="单价" value="${product.unit_price || ''}" required data-field="unit_price">
        <button type="button" class="btn btn-danger btn-sm remove-product-btn">移除</button>
    `;
    container.appendChild(div);

    div.querySelector('.remove-product-btn').onclick = () => {
        div.remove();
    };
};

const loadSaleRecords = async () => {
    if (!hasPermission('sale_records', 'GET')) {
        document.getElementById('saleRecordsTableBody').innerHTML = `<tr><td colspan="5" class="text-center text-danger">您没有权限查看销售记录。</td></tr>`;
        return;
    }
    try {
        const records = await API.getSaleRecords();
        const columns = ['record_id', 'date', 'customer_id', 'employee_id'];
        const actions = [
            { label: '查看', type: 'primary', handler: viewSaleRecordDetail, permissionResource: 'sale_records', permissionMethod: 'GET' },
            { label: '删除', type: 'danger', handler: deleteSaleRecord, permissionResource: 'sale_records', permissionMethod: 'DELETE' }
        ];
        renderTable('saleRecordsTableBody', records, columns, actions);
    } catch (error) {
        showAlert(`加载销售记录失败: ${error.message}`, 'danger');
    }
};

const viewSaleRecordDetail = async (record) => {
    // Reset modal state
    document.getElementById('saleRecordForm').classList.add('d-none');
    document.getElementById('saleRecordDetails').classList.remove('d-none');
    document.getElementById('saleRecordModalLabel').textContent = '销售记录详情';

    try {
        const detail = await API.getSaleRecordDetail(record.record_id);
        document.getElementById('detailSaleRecordId').textContent = detail.record_id;
        document.getElementById('detailSaleDate').textContent = detail.date;
        document.getElementById('detailSaleCustomerName').textContent = detail.customer_name;
        document.getElementById('detailSaleCustomerId').textContent = detail.customer_id;
        document.getElementById('detailSaleEmployeeName').textContent = detail.employee_name;
        document.getElementById('detailSaleEmployeeId').textContent = detail.employee_id;

        const products = await API.getSaleProducts(record.record_id);
        const productsTableBody = document.getElementById('detailSaleProductsTableBody');
        productsTableBody.innerHTML = '';
        if (products.length === 0) {
            productsTableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">无产品信息</td></tr>';
        } else {
            products.forEach(prod => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${prod.product_id}</td>
                    <td>${prod.name}</td>
                    <td>${prod.quantity}</td>
                    <td>${prod.unit}</td>
                    <td>${prod.unit_price}</td>
                `;
                productsTableBody.appendChild(row);
            });
        }
        saleRecordModal.show();
    } catch (error) {
        showAlert(`加载销售记录详情失败: ${error.message}`, 'danger');
    }
};

const handleSaleRecordFormSubmit = async (e) => {
    e.preventDefault();
    const data = {
        customer_id: parseInt(document.getElementById('saleCustomerId').value),
        date: document.getElementById('saleDate').value,
        employee_id: parseInt(document.getElementById('saleEmployeeId').value),
        products: []
    };

    document.querySelectorAll('#saleProductsContainer .product-item').forEach(itemDiv => {
        data.products.push({
            product_id: parseInt(itemDiv.querySelector('[data-field="product_id"]').value),
            quantity: parseFloat(itemDiv.querySelector('[data-field="quantity"]').value),
            unit_price: parseFloat(itemDiv.querySelector('[data-field="unit_price"]').value)
        });
    });

    try {
        await API.addSaleRecord(data);
        showAlert('销售记录添加成功！', 'success');
        saleRecordModal.hide();
        await loadSaleRecords();
    } catch (error) {
        showAlert(`添加失败: ${error.message}`, 'danger');
    }
};

const deleteSaleRecord = async (record) => {
    if (!confirm(`确定要删除销售记录: ID ${record.record_id} 吗？此操作将无法撤销，并可能影响库存数据。`)) {
        return;
    }
    try {
        await API.deleteSaleRecord(record.record_id);
        showAlert('销售记录删除成功！', 'success');
        await loadSaleRecords();
    } catch (error) {
        showAlert(`删除失败: ${error.message}`, 'danger');
    }
};

// --- Production Record Management ---
let productionMaterialCounter = 0; // Use a counter to assign unique IDs
const addProductionMaterialInput = (material = {}) => {
    const container = document.getElementById('productionMaterialsContainer');
    const div = document.createElement('div');
    div.className = 'production-material-item';
    div.dataset.index = productionMaterialCounter++; // Assign a unique index
    div.innerHTML = `
        <input type="number" class="form-control form-control-sm" placeholder="原料ID" value="${material.material_id || ''}" required data-field="material_id">
        <input type="number" step="0.01" min="0" class="form-control form-control-sm" placeholder="使用数量" value="${material.quantity || ''}" required data-field="quantity">
        <button type="button" class="btn btn-danger btn-sm remove-production-material-btn">移除</button>
    `;
    container.appendChild(div);

    div.querySelector('.remove-production-material-btn').onclick = () => {
        div.remove();
    };
};

const loadProductionRecords = async () => {
    if (!hasPermission('production_records', 'GET')) {
        document.getElementById('productionRecordsTableBody').innerHTML = `<tr><td colspan="7" class="text-center text-danger">您没有权限查看生产记录。</td></tr>`;
        return;
    }
    try {
        const records = await API.getProductionRecords();
        const columns = ['record_id', 'date', 'product_name', 'line_name', 'theoretical_output', 'actual_output'];
        const actions = [
            { label: '查看', type: 'primary', handler: viewProductionRecordDetail, permissionResource: 'production_records', permissionMethod: 'GET' },
            // No delete production record API in your backend code
        ];
        renderTable('productionRecordsTableBody', records, columns, actions);
    } catch (error) {
        showAlert(`加载生产记录失败: ${error.message}`, 'danger');
    }
};

const viewProductionRecordDetail = async (record) => {
    // Reset modal state
    document.getElementById('productionRecordForm').classList.add('d-none');
    document.getElementById('productionRecordDetails').classList.remove('d-none');
    document.getElementById('productionRecordModalLabel').textContent = '生产记录详情';

    try {
        const detail = await API.getProductionRecordDetail(record.record_id);
        document.getElementById('detailProductionRecordId').textContent = detail.record_id;
        document.getElementById('detailProductionDate').textContent = detail.date;
        document.getElementById('detailProductionProductName').textContent = detail.product_name;
        document.getElementById('detailProductionProductId').textContent = detail.product_id;
        document.getElementById('detailProductionLineName').textContent = detail.line_name;
        document.getElementById('detailProductionLineId').textContent = detail.line_id;
        document.getElementById('detailProductionTheoreticalOutput').textContent = detail.theoretical_output;
        document.getElementById('detailProductionActualOutput').textContent = detail.actual_output;

        const materials = await API.getProductionMaterials(record.record_id);
        const materialsTableBody = document.getElementById('detailProductionMaterialsTableBody');
        materialsTableBody.innerHTML = '';
        if (materials.length === 0) {
            materialsTableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">无原料使用信息</td></tr>';
        } else {
            materials.forEach(mat => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${mat.material_id}</td>
                    <td>${mat.material_name}</td>
                    <td>${mat.quantity_used}</td>
                    <td>${mat.unit}</td>
                `;
                materialsTableBody.appendChild(row);
            });
        }
        productionRecordModal.show();
    } catch (error) {
        showAlert(`加载生产记录详情失败: ${error.message}`, 'danger');
    }
};

const handleProductionRecordFormSubmit = async (e) => {
    e.preventDefault();
    const data = {
        product_id: parseInt(document.getElementById('productionProductId').value),
        line_id: parseInt(document.getElementById('productionLineId').value),
        date: document.getElementById('productionDate').value,
        theoretical_output: parseFloat(document.getElementById('productionTheoreticalOutput').value),
        actual_output: parseFloat(document.getElementById('productionActualOutput').value),
        materials: []
    };

    document.querySelectorAll('#productionMaterialsContainer .production-material-item').forEach(itemDiv => {
        data.materials.push({
            material_id: parseInt(itemDiv.querySelector('[data-field="material_id"]').value),
            quantity: parseFloat(itemDiv.querySelector('[data-field="quantity"]').value)
        });
    });

    try {
        await API.addProductionRecord(data);
        showAlert('生产记录添加成功！', 'success');
        productionRecordModal.hide();
        await loadProductionRecords();
    } catch (error) {
        showAlert(`添加失败: ${error.message}`, 'danger');
    }
};


// --- Event Listeners and Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    // 页面加载时，根据 localStorage 检查登录状态
    updateLoginStatus(); // <-- 此函数现在会根据 localStorage 决定显示登录页或主界面

    // 如果 updateLoginStatus 发现用户已登录，那么 currentUser 将不为 null
    if (currentUser) {
        showView('dashboard'); // <-- 只有在已登录状态下才显示仪表盘
    }
});
// Sidebar toggle for smaller screens
sidebarToggle.addEventListener('click', (e) => {
    e.preventDefault();
    mainAppContainer.classList.toggle('toggled');
});

// Login and Logout
loginForm.addEventListener('submit', handleLogin);
logoutBtn.addEventListener('click', handleLogout);

// Navigation links
document.querySelectorAll('.list-group-item[data-view]').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        showView(link.dataset.view);
    });
});

// Material Modal events
document.getElementById('addMaterialBtn').addEventListener('click', () => {
    materialForm.dataset.mode = 'add';
    document.getElementById('materialModalLabel').textContent = '添加原料';
    materialForm.reset();
    document.getElementById('materialId').value = ''; // Clear ID for add mode
});
materialForm.addEventListener('submit', handleMaterialFormSubmit);

// Product Modal events
document.getElementById('addProductBtn').addEventListener('click', () => {
    productForm.dataset.mode = 'add';
    document.getElementById('productModalLabel').textContent = '添加产品';
    productForm.reset();
    document.getElementById('productId').value = ''; // Clear ID for add mode
});
productForm.addEventListener('submit', handleProductFormSubmit);

// Purchase Record Modal events
document.getElementById('addPurchaseRecordBtn').addEventListener('click', () => {
    purchaseRecordForm.reset();
    document.getElementById('purchaseMaterialsContainer').innerHTML = '';
    purchaseMaterialCounter = 0; // Reset counter
    addPurchaseMaterialInput(); // Add first material input field
    document.getElementById('purchaseRecordForm').classList.remove('d-none');
    document.getElementById('purchaseRecordDetails').classList.add('d-none'); // Hide details view
    document.getElementById('purchaseRecordModalLabel').textContent = '添加进货记录';
});
document.getElementById('addPurchaseMaterialBtn').addEventListener('click', () => addPurchaseMaterialInput());
purchaseRecordForm.addEventListener('submit', handlePurchaseRecordFormSubmit);

// Sale Record Modal events
document.getElementById('addSaleRecordBtn').addEventListener('click', () => {
    saleRecordForm.reset();
    document.getElementById('saleProductsContainer').innerHTML = '';
    saleProductCounter = 0; // Reset counter
    addSaleProductInput(); // Add first product input field
    document.getElementById('saleRecordForm').classList.remove('d-none');
    document.getElementById('saleRecordDetails').classList.add('d-none'); // Hide details view
    document.getElementById('saleRecordModalLabel').textContent = '添加销售记录';
});
document.getElementById('addSaleProductBtn').addEventListener('click', () => addSaleProductInput());
saleRecordForm.addEventListener('submit', handleSaleRecordFormSubmit);

// Production Record Modal events
document.getElementById('addProductionRecordBtn').addEventListener('click', () => {
    productionRecordForm.reset();
    document.getElementById('productionMaterialsContainer').innerHTML = '';
    productionMaterialCounter = 0; // Reset counter
    addProductionMaterialInput(); // Add first material input field
    document.getElementById('productionRecordForm').classList.remove('d-none');
    document.getElementById('productionRecordDetails').classList.add('d-none'); // Hide details view
    document.getElementById('productionRecordModalLabel').textContent = '添加生产记录';
});
document.getElementById('addProductionMaterialBtn').addEventListener('click', () => addProductionMaterialInput());
productionRecordForm.addEventListener('submit', handleProductionRecordFormSubmit);
