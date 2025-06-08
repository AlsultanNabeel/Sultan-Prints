import click
from flask.cli import with_appcontext
from .extensions import db
from .models import Setting, Page

@click.command('seed')
@with_appcontext
def seed_command():
    """Seeds the database with initial settings and pages."""
    print("Starting database seeding...")

    # 1. Initialize Settings
    default_settings = {
        'contact_email': 'admin@example.com',
        'phone_number': '+1234567890',
        'address': '123 Main Street, Anytown, USA',
        'facebook_url': 'https://facebook.com',
        'instagram_url': 'https://instagram.com',
        'twitter_url': 'https://twitter.com',
        'whatsapp_number': '+1234567890',
        'hero_image': 'images/hero-palestine.jpg'
    }
    for key, value in default_settings.items():
        if not Setting.query.filter_by(key=key).first():
            db.session.add(Setting(key=key, value=value))
            print(f"  - Added setting: {key}")

    # 2. Initialize Pages
    default_pages = [
        {'slug': 'about-us', 'title': 'من نحن', 'content': '<p>محتوى صفحة "من نحن" يكتب هنا. يمكنك تعديله من لوحة التحكم.</p>'},
        {'slug': 'contact-us', 'title': 'تواصل معنا', 'content': '<p>محتوى صفحة "تواصل معنا" يكتب هنا.</p>'},
        {'slug': 'privacy-policy', 'title': 'سياسة الخصوصية', 'content': '<p>محتوى صفحة "سياسة الخصوصية" يكتب هنا.</p>'},
        {'slug': 'terms-and-conditions', 'title': 'الشروط والأحكام', 'content': '<p>محتوى صفحة "الشروط والأحكام" يكتب هنا.</p>'}
    ]
    for page_data in default_pages:
        if not Page.query.filter_by(slug=page_data['slug']).first():
            db.session.add(Page(**page_data))
            print(f"  - Added page: {page_data['title']}")
            
    db.session.commit()
    print("Database seeding completed successfully.")

def init_app(app):
    """Register database functions with the Flask app. This is called by the application factory."""
    app.cli.add_command(seed_command) 