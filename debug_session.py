#!/usr/bin/env python3
"""
سكريبت لاختبار الجلسة الحالية
"""
from app import create_app
from app.models import Cart, CartItem, Product
from app.utils import get_or_create_cart
from flask import session
import requests

app = create_app()

def test_session():
    """اختبار الجلسة عبر طلب HTTP"""
    with app.test_client() as client:
        print("=== اختبار الجلسة عبر HTTP ===")
        
        # اختبار صفحة السلة
        print("1. اختبار صفحة السلة...")
        response = client.get('/cart/cart')
        print(f"   - حالة الاستجابة: {response.status_code}")
        print(f"   - محتوى الجلسة: {dict(session)}")
        
        # اختبار صفحة الدفع
        print("\n2. اختبار صفحة الدفع...")
        response = client.get('/cart/checkout')
        print(f"   - حالة الاستجابة: {response.status_code}")
        if response.status_code == 302:
            print(f"   - إعادة التوجيه إلى: {response.location}")
        
        # اختبار إضافة منتج
        print("\n3. اختبار إضافة منتج...")
        product = Product.query.first()
        if product:
            response = client.post('/cart/add_to_cart', data={
                'product_id': product.id,
                'quantity': 1,
                'size': 'L',
                'color': 'أزرق'
            })
            print(f"   - حالة الاستجابة: {response.status_code}")
            print(f"   - محتوى الجلسة بعد الإضافة: {dict(session)}")
            
            # اختبار صفحة الدفع مرة أخرى
            print("\n4. اختبار صفحة الدفع بعد إضافة المنتج...")
            response = client.get('/cart/checkout')
            print(f"   - حالة الاستجابة: {response.status_code}")
            if response.status_code == 200:
                print("   - نجح الوصول لصفحة الدفع!")
            else:
                print(f"   - فشل الوصول: {response.status_code}")
        else:
            print("   - لا توجد منتجات في قاعدة البيانات")

if __name__ == "__main__":
    with app.app_context():
        test_session() 