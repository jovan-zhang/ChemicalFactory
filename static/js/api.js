// js/api.js

const BASE_URL = 'http://127.0.0.1:5000'; // 后端Flask服务器地址，本地测试不修改此项

let authToken = localStorage.getItem('authToken') || null;

export const setAuthToken = (token) => {
    authToken = token;
    if (token) {
        localStorage.setItem('authToken', token);
    } else {
        localStorage.removeItem('authToken');
    }
};

export const getAuthToken = () => authToken;

export const fetchAPI = async (endpoint, method = 'GET', data = null) => {
    const url = `${BASE_URL}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
    };

    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }

    const options = {
        method,
        headers,
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        const responseData = await response.json();

        if (!response.ok) {
            // Check for specific error messages from backend
            let errorMessage = responseData.message || responseData.error || '未知错误';
            throw new Error(`Error ${response.status}: ${errorMessage}`);
        }

        return responseData;

    } catch (error) {
        console.error('API请求失败:', error);
        throw error; // Re-throw to be caught by the calling function
    }
};

// Export all API endpoints for use in app.js
export const API = {
    // Auth
    login: (username, password) => fetchAPI('/login', 'POST', { username, password }),

    // Materials
    getMaterials: () => fetchAPI('/materials', 'GET'),
    getMaterial: (id) => fetchAPI(`/materials/${id}`, 'GET'),
    addMaterial: (data) => fetchAPI('/materials', 'POST', data),
    updateMaterial: (id, data) => fetchAPI(`/materials/${id}`, 'PUT', data),
    deleteMaterial: (id) => fetchAPI(`/materials/${id}`, 'DELETE'),

    // Products
    getProducts: () => fetchAPI('/products', 'GET'),
    getProduct: (id) => fetchAPI(`/products/${id}`, 'GET'),
    addProduct: (data) => fetchAPI('/products', 'POST', data),
    updateProduct: (id, data) => fetchAPI(`/products/${id}`, 'PUT', data),
    deleteProduct: (id) => fetchAPI(`/products/${id}`, 'DELETE'),

    // Purchase Records
    getPurchaseRecords: () => fetchAPI('/purchase_records', 'GET'),
    getPurchaseRecordDetail: (id) => fetchAPI(`/purchase_records/${id}`, 'GET'),
    getPurchaseMaterials: (id) => fetchAPI(`/purchase_records/${id}/materials`, 'GET'),
    addPurchaseRecord: (data) => fetchAPI('/purchase_records', 'POST', data),
    deletePurchaseRecord: (id) => fetchAPI(`/purchase_records/${id}`, 'DELETE'),

    // Sale Records
    getSaleRecords: () => fetchAPI('/sale_records', 'GET'),
    getSaleRecordDetail: (id) => fetchAPI(`/sale_records/${id}`, 'GET'),
    getSaleProducts: (id) => fetchAPI(`/sale_records/${id}/products`, 'GET'),
    addSaleRecord: (data) => fetchAPI('/sale_records', 'POST', data),
    deleteSaleRecord: (id) => fetchAPI(`/sale_records/${id}`, 'DELETE'),

    // Production Records
    getProductionRecords: () => fetchAPI('/production_records', 'GET'),
    getProductionRecordDetail: (id) => fetchAPI(`/production_records/${id}`, 'GET'),
    getProductionMaterials: (id) => fetchAPI(`/production_records/${id}/materials`, 'GET'),
    addProductionRecord: (data) => fetchAPI('/production_records', 'POST', data),
    // Note: API doc doesn't have a DELETE for production records, so we won't implement it on frontend.
    // deleteProductionRecord: (id) => fetchAPI(`/production_records/${id}`, 'DELETE'),
};
