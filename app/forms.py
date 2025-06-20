from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, BooleanField, TextAreaField, IntegerField, SelectField, FileField, SelectMultipleField, RadioField, widgets, DateTimeField, HiddenField, DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional, ValidationError
from flask_wtf.file import FileAllowed
from datetime import datetime
from pytz import timezone

def AtLeastOneSelected(form, field):
    if not field.data or len(field.data) == 0:
        raise ValidationError('يجب اختيار خيار واحد على الأقل.')

class ProductForm(FlaskForm):
    name = StringField('اسم المنتج', validators=[DataRequired(), Length(min=2, max=100)], render_kw={"class": "form-control"})
    description = TextAreaField('الوصف', validators=[Optional(), Length(max=1000)], render_kw={"class": "form-control", "rows": 5})
    features = TextAreaField('المميزات (ميزة في كل سطر)', validators=[Optional()], render_kw={"class": "form-control", "rows": 5, "placeholder": "قطن 100% عالي الجودة\nطباعة عالية الجودة بألوان ثابتة"})
    price = FloatField('السعر', validators=[DataRequired(), NumberRange(min=0)], render_kw={"class": "form-control", "required": True})
    sizes = SelectMultipleField('المقاسات', choices=[('S','S'),('M','M'),('L','L'),('XL','XL')], 
                                validators=[AtLeastOneSelected], 
                                option_widget=widgets.CheckboxInput(), 
                                widget=widgets.ListWidget(prefix_label=False),
                                render_kw={})
    colors = SelectMultipleField('الألوان', choices=[
        ('white','أبيض'),
        ('black','أسود'),
        ('red','أحمر'),
        ('blue','أزرق'),
        ('green','أخضر'),
        ('yellow','أصفر'),
        ('beige','بيج'),
        ('gray','رمادي'),
        ('navy','كحلي'),
        ('pink','وردي'),
        ('purple','بنفسجي'),
        ('brown','بني'),
        ('orange','برتقالي'),
    ], validators=[AtLeastOneSelected],
       option_widget=widgets.CheckboxInput(), 
       widget=widgets.ListWidget(prefix_label=False),
       render_kw={})
    material = StringField('الخامة', validators=[Optional(), Length(max=100)], render_kw={"class": "form-control"})
    featured = BooleanField('مميز', render_kw={"class": "form-check-input"})
    image = FileField('صورة المنتج', render_kw={"class": "form-control", "accept": "image/*"})
    in_stock = BooleanField('متوفر في المخزون', default=True, render_kw={"class": "form-check-input"})
    category = StringField('الفئة', validators=[Optional(), Length(max=100)], render_kw={"class": "form-control", "placeholder": "مثال: تيشيرتات، فلسطين، صيف 2024"})
    is_palestine = BooleanField('عرض هذا المنتج ضمن قسم فلسطين', render_kw={"class": "form-check-input"})
    submit = SubmitField('حفظ', render_kw={"class": "btn btn-primary w-100"})

class ContactForm(FlaskForm):
    name = StringField('الاسم', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    phone = StringField('رقم الهاتف', validators=[Optional(), Length(min=6, max=20)])
    message = TextAreaField('الرسالة', validators=[DataRequired(), Length(min=10, max=2000)])
    submit = SubmitField('إرسال')

class AdminLoginForm(FlaskForm):
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    submit = SubmitField('تسجيل الدخول')

class GovernorateForm(FlaskForm):
    name = StringField('اسم المحافظة', validators=[DataRequired(), Length(min=2, max=100)], render_kw={"class": "form-control"})
    delivery_fee = FloatField('رسوم التوصيل', validators=[DataRequired(), NumberRange(min=0)], render_kw={"class": "form-control"})
    submit = SubmitField('حفظ', render_kw={"class": "btn btn-primary"})

class CheckoutForm(FlaskForm):
    name = StringField('الاسم الكامل', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email(message="الرجاء إدخال بريد إلكتروني صالح.")])
    phone = StringField('رقم الهاتف', validators=[DataRequired(), Length(min=6, max=20)])
    governorate_id = SelectField('المحافظة', validators=[DataRequired(message="الرجاء اختيار المحافظة.")], render_kw={"class": "form-control"})
    address = TextAreaField('العنوان بالتفصيل (الشارع، رقم المنزل، علامة مميزة)', validators=[DataRequired(), Length(min=10, max=500)])
    payment_method = RadioField('طريقة الدفع', choices=[
        ('cod', 'الدفع عند الاستلام')
    ], validators=[DataRequired()])
    csrf_token = HiddenField()
    submit = SubmitField('إتمام الطلب')

class OrderStatusForm(FlaskForm):
    status = SelectField('حالة الطلب الجديدة', choices=[
        ('pending', 'قيد الانتظار'),
        ('processing', 'قيد التجهيز'),
        ('printing', 'قيد الطباعة'),
        ('shipped', 'تم الشحن'),
        ('out_for_delivery', 'خارج للتوصيل'),
        ('delivered', 'تم التوصيل'),
        ('cancelled', 'ملغي'),
        ('refunded', 'تم استرداد المبلغ'),
    ], validators=[DataRequired()])
    notes = TextAreaField('ملاحظات (اختياري)')
    submit = SubmitField('تحديث الحالة')

class SettingsForm(FlaskForm):
    """نموذج لتعديل إعدادات الموقع"""
    hero_title = StringField('العنوان الرئيسي للهيرو', 
                           validators=[Optional(), Length(max=200)], 
                           render_kw={"class": "form-control"},
                           description="العنوان الكبير الذي يظهر في أعلى الصفحة الرئيسية.")
    hero_subtitle = TextAreaField('العنوان الفرعي للهيرو', 
                                render_kw={"class": "form-control", "rows": 2},
                                description="النص الأصغر الذي يظهر تحت العنوان الرئيسي.")
    hero_button_text = StringField('نص زر الهيرو',
                                   validators=[Optional(), Length(max=50)],
                                   render_kw={"class": "form-control"},
                                   description="النص الذي يظهر على الزر في قسم الهيرو.")
    hero_image = FileField('صورة الهيرو الرئيسية', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'الصور فقط!')])
    hero_height = IntegerField('ارتفاع قسم الهيرو (vh)', 
                             validators=[Optional(), NumberRange(min=30, max=100)], 
                             description="أدخل رقمًا بين 30 و 100. هذا يمثل النسبة المئوية لارتفاع الشاشة.",
                             default=75)
    homepage_about_us_content = TextAreaField('محتوى "من نحن" في الصفحة الرئيسية', 
                                             render_kw={"class": "form-control", "rows": 4},
                                             description='محتوى يظهر تحت قسم الهيرو للتعريف بالمتجر.')
    homepage_about_products_content = TextAreaField('محتوى "عن منتجاتنا" في الصفحة الرئيسية', 
                                                   render_kw={"class": "form-control", "rows": 4},
                                                   description='محتوى يظهر في قسم خاص للحديث عن جودة المنتجات.')
    footer_about_us_content = TextAreaField('نبذة "من نحن" في الفوتر', 
                                              render_kw={"class": "form-control", "rows": 3}, 
                                              description='محتوى مختصر يظهر في الفوتر أسفل اسم المتجر.')
    contact_email = StringField('البريد الإلكتروني للتواصل')
    phone_number = StringField('رقم الهاتف')
    address = StringField('العنوان')
    facebook_url = StringField('رابط فيسبوك')
    instagram_url = StringField('رابط انستغرام')
    tiktok_url = StringField('رابط تيكتوك')
    whatsapp_number = StringField('رقم واتساب')
    header_scripts = TextAreaField('أكواد إضافية في الهيدر (Header Scripts)', 
                                 render_kw={"class": "form-control", "rows": 5},
                                 description="أضف هنا أي أكواد تتبع مثل Google Analytics أو Facebook Pixel. سيتم إضافتها قبل إغلاق وسم </head>.")
    submit = SubmitField('حفظ الإعدادات')

class PageForm(FlaskForm):
    """نموذج لتعديل صفحات المحتوى"""
    title = StringField('عنوان الصفحة', validators=[DataRequired(), Length(min=2, max=255)], render_kw={"class": "form-control"})
    slug = StringField('الرابط (Slug)', validators=[DataRequired(), Length(min=2, max=255)], 
                       render_kw={"class": "form-control", "placeholder": "example: about-us"},
                       description="هذا هو الجزء الذي يظهر في رابط الصفحة. استخدم الحروف الإنجليزية الصغيرة والشرطات فقط.")
    content = TextAreaField('المحتوى', render_kw={"class": "form-control", "rows": 15, "id": "editor"})
    meta_title = StringField('عنوان Meta', validators=[Optional(), Length(max=255)], render_kw={"class": "form-control"})
    meta_description = TextAreaField('وصف Meta', validators=[Optional(), Length(max=500)], render_kw={"class": "form-control", "rows": 3})
    is_published = BooleanField('منشور', default=True, render_kw={"class": "form-check-input"})
    submit = SubmitField('حفظ التغييرات', render_kw={"class": "btn btn-primary"})

class AnnouncementForm(FlaskForm):
    """نموذج لإضافة أو تعديل إعلان"""
    text = TextAreaField('نص الإعلان', validators=[DataRequired(), Length(min=5, max=500)], render_kw={"class": "form-control", "rows": 3})
    is_active = BooleanField('نشط', default=True, render_kw={"class": "form-check-input"})
    submit = SubmitField('حفظ الإعلان', render_kw={"class": "btn btn-primary"})

class FAQForm(FlaskForm):
    """نموذج لإدارة الأسئلة الشائعة"""
    question = StringField('السؤال', validators=[DataRequired(), Length(max=500)], render_kw={"class": "form-control"})
    answer = TextAreaField('الإجابة', validators=[DataRequired()], render_kw={"class": "form-control", "rows": 5})
    is_active = BooleanField('عرض هذا السؤال في الموقع', default=True, render_kw={"class": "form-check-input"})
    display_order = IntegerField('ترتيب العرض', default=0, render_kw={"class": "form-control"}, description="الأرقام الأقل تظهر أولاً.")
    submit = SubmitField('حفظ', render_kw={"class": "btn btn-primary"})

class PromoCodeForm(FlaskForm):
    """نموذج إدارة أكواد الخصم"""
    code = StringField('كود الخصم', validators=[
        DataRequired(message='يرجى إدخال كود الخصم'),
        Length(min=3, max=50, message='يجب أن يكون طول الكود بين 3 و 50 حرفاً')
    ])
    discount_percentage = FloatField('نسبة الخصم (%)', validators=[
        DataRequired(message='يرجى إدخال نسبة الخصم'),
        NumberRange(min=0, max=100, message='يجب أن تكون نسبة الخصم بين 0 و 100')
    ])
    max_uses = IntegerField('الحد الأقصى للاستخدام', validators=[
        Optional(),
        NumberRange(min=1, message='يجب أن يكون الحد الأقصى للاستخدام أكبر من 0')
    ])
    expiration_date = DateField('تاريخ انتهاء الصلاحية', validators=[DataRequired(message='يرجى تحديد تاريخ انتهاء الصلاحية')], format='%Y-%m-%d')
    is_active = BooleanField('نشط')

    def validate_code(self, code):
        """التحقق من عدم تكرار الكود"""
        from app.models import PromoCode
        promo_code = PromoCode.query.filter_by(code=code.data).first()
        if promo_code and promo_code.id != getattr(self, '_id', None):
            raise ValidationError('هذا الكود مستخدم بالفعل')

    def validate_expiration_date(self, expiration_date):
        """التحقق من أن تاريخ انتهاء الصلاحية في المستقبل (بتوقيت مصر)"""
        egypt = timezone('Africa/Cairo')
        now_egypt = datetime.now(egypt).date()
        if expiration_date.data <= now_egypt:
            raise ValidationError('يجب أن يكون تاريخ انتهاء الصلاحية بعد اليوم')