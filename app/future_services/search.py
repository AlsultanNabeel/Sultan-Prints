from models import Product, db
from sqlalchemy import or_, and_

class ProductSearch:
    @staticmethod
    def search(query_params):
        """
        Advanced product search with multiple filters
        """
        filters = []
        
        # Text search
        if query_params.get('q'):
            search_term = f"%{query_params['q']}%"
            filters.append(or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            ))
        
        # Price range
        if query_params.get('min_price'):
            filters.append(Product.price >= float(query_params['min_price']))
        if query_params.get('max_price'):
            filters.append(Product.price <= float(query_params['max_price']))
        
        # Size filter
        if query_params.get('size'):
            filters.append(Product.available_sizes.contains(query_params['size']))
        
        # Color filter
        if query_params.get('color'):
            filters.append(Product.available_colors.contains(query_params['color']))
        
        # Category filter
        if query_params.get('category'):
            filters.append(Product.category == query_params['category'])
        
        # Stock status
        if query_params.get('in_stock'):
            filters.append(Product.stock > 0)
        
        # Sort options
        sort_field = query_params.get('sort', 'created_at')
        sort_order = query_params.get('order', 'desc')
        
        # Build query
        query = Product.query
        if filters:
            query = query.filter(and_(*filters))
        
        # Apply sorting
        if sort_order == 'desc':
            query = query.order_by(getattr(Product, sort_field).desc())
        else:
            query = query.order_by(getattr(Product, sort_field).asc())
        
        # Pagination
        page = int(query_params.get('page', 1))
        per_page = int(query_params.get('per_page', 12))
        
        return query.paginate(page=page, per_page=per_page)
    
    @staticmethod
    def get_filter_options():
        """
        Get available filter options for the search form
        """
        return {
            'sizes': ['S', 'M', 'L', 'XL', 'XXL'],
            'colors': ['أبيض', 'أسود', 'أحمر', 'أزرق', 'رمادي'],
            'categories': ['رجالي', 'حريمي', 'أطفال'],
            'sort_options': [
                {'value': 'created_at', 'label': 'الأحدث'},
                {'value': 'price', 'label': 'السعر'},
                {'value': 'name', 'label': 'الاسم'},
                {'value': 'popularity', 'label': 'الأكثر مبيعاً'}
            ]
        } 