from app import create_app, db
from app.models import Product, Design, Banner, Category
import json
import os

app = create_app()

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if there are already products
        if Product.query.count() == 0:
            # Add some example products
            products = [
                {
                    'name': 'قميص أبيض كلاسيكي',
                    'description': 'قميص أبيض كلاسيكي مصنوع من القطن عالي الجودة، مناسب للإرتداء اليومي.',
                    'price': 199.99,
                    'image_path': 'images/products/tshirt_white.jpg',
                    'category': 'tshirts',
                    'is_trending': True,
                    'colors': 'white,black,gray',
                    'featured': True,
                    'sizes': json.dumps(['S', 'M', 'L', 'XL']),
                    'material': 'قطن'
                },
                {
                    'name': 'قميص فلسطين',
                    'description': 'قميص مطبوع بتصميم فلسطيني رائع، مصنوع من القطن الممتاز.',
                    'price': 249.99,
                    'image_path': 'images/products/tshirt_palestine.jpg',
                    'category': 'tshirts',
                    'is_palestine': True,
                    'is_trending': True,
                    'colors': 'white,black',
                    'featured': True,
                    'sizes': json.dumps(['S', 'M', 'L', 'XL']),
                    'material': 'قطن'
                },
                {
                    'name': 'قميص رياضي',
                    'description': 'قميص رياضي مريح مناسب للتمارين والأنشطة الرياضية.',
                    'price': 179.99,
                    'image_path': 'images/products/tshirt_sport.jpg',
                    'category': 'tshirts',
                    'is_trending': False,
                    'colors': 'red,blue,black',
                    'featured': True,
                    'sizes': json.dumps(['M', 'L', 'XL']),
                    'material': 'بوليستر'
                }
            ]
            
            for product_data in products:
                product = Product(**product_data)
                db.session.add(product)
            
            # Add default designs
            designs = [
                {
                    'name': 'تصميم فلسطين',
                    'description': 'تصميم يظهر علم فلسطين',
                    'image_path': 'images/designs/palestine_flag.png',
                    'is_default': True
                },
                {
                    'name': 'تصميم كلاسيكي',
                    'description': 'تصميم كلاسيكي بسيط',
                    'image_path': 'images/designs/classic.png',
                    'is_default': True
                },
                {
                    'name': 'تصميم مصر',
                    'description': 'تصميم يظهر علم مصر',
                    'image_path': 'images/designs/egypt_flag.png',
                    'is_default': True
                }
            ]
            
            # Make sure the designs directory exists
            os.makedirs('static/images/designs', exist_ok=True)
            os.makedirs('static/images/products', exist_ok=True)
            
            for design_data in designs:
                design = Design(**design_data)
                db.session.add(design)
            
            # Add default and main categories
            categories_to_add = [
                {"name": "فئة افتراضية", "description": "فئة افتراضية للمنتجات"},
                {"name": "بلايز رجالي", "description": "تشكيلة متنوعة من البلايز الرجالية"},
                {"name": "بلايز نسائي", "description": "تشكيلة متنوعة من البلايز النسائية"},
                {"name": "بلايز أطفال", "description": "تشكيلة متنوعة من بلايز الأطفال"}
            ]

            for cat_data in categories_to_add:
                existing_cat = Category.query.filter_by(name=cat_data["name"]).first()
                if not existing_cat:
                    category = Category(name=cat_data["name"], description=cat_data["description"])
                    db.session.add(category)
            
            db.session.commit()
            print("✅ تم تهيئة قاعدة البيانات وإضافة بيانات العرض التوضيحي")
        else:
            print("ℹ️ قاعدة البيانات تحتوي بالفعل على بيانات")

if __name__ == '__main__':
    init_db()
