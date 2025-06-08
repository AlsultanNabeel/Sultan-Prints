from app import create_app, db
from app.utils import cleanup_old_uploads, log_event
from app.models import Page
import sys
import click
from sqlalchemy import text

app = create_app()

@app.cli.command("seed-db")
def seed_db_command():
    """Seeds the database with initial data."""
    with app.app_context():
        # --- Create About Us page ---
        about_page = Page.query.filter_by(slug='about-us').first()
        if not about_page:
            about_page = Page(
                title='من نحن',
                slug='about-us',
                content='<p>هنا تكتب قصة متجرك. من أنتم؟ ما الذي يميزكم؟</p>',
                is_published=True
            )
            db.session.add(about_page)
            click.echo('Created "About Us" page.')

        # --- Create Contact Us page ---
        contact_page = Page.query.filter_by(slug='contact-us').first()
        if not contact_page:
            contact_page = Page(
                title='تواصل معنا',
                slug='contact-us',
                content='<p>يمكنك تعديل هذا المحتوى من لوحة التحكم.</p>',
                is_published=True
            )
            db.session.add(contact_page)
            click.echo('Created "Contact Us" page.')
            
        db.session.commit()
        click.echo('Database has been seeded.')


if __name__ == '__main__':
    # تهيئة سجل الأحداث عند بدء التشغيل
    log_event("Application starting up...", level='info')
    
    # جدولة مهمة التنظيف (يمكن استخدام مكتبة مثل APScheduler في تطبيق حقيقي)
    # هذا مجرد مثال بسيط
    # cleanup_old_uploads(app)
    
    app.run(debug=True, port=5002) 