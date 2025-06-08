from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, BooleanField, TextAreaField, IntegerField, SelectField, FileField, SelectMultipleField, RadioField, widgets
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional, ValidationError
from flask_wtf.file import FileAllowed

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
    submit = SubmitField('حفظ', render_kw={"class": "btn btn-primary w-100"})

class ContactForm(FlaskForm):
    name = StringField('الاسم', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    phone = StringField('رقم الهاتف', validators=[Optional(), Length(min=6, max=20)])
    message = TextAreaField('الرسالة', validators=[DataRequired(), Length(min=10, max=2000)])
    submit = SubmitField('إرسال')

class DiscountForm(FlaskForm):
    code = StringField('كود الخصم', validators=[DataRequired(), Length(min=2, max=20)])
    type = SelectField('نوع الخصم', choices=[('percentage','نسبة مئوية'),('fixed','قيمة ثابتة')], validators=[DataRequired()])
    value = FloatField('قيمة الخصم', validators=[DataRequired(), NumberRange(min=0)])
    min_purchase = FloatField('الحد الأدنى للطلب', validators=[Optional(), NumberRange(min=0)])
    max_discount = FloatField('الحد الأقصى للخصم', validators=[Optional(), NumberRange(min=0)])
    usage_limit = IntegerField('عدد مرات الاستخدام', validators=[Optional(), NumberRange(min=1)])
    start_date = StringField('تاريخ البداية', validators=[DataRequired()])
    end_date = StringField('تاريخ النهاية', validators=[DataRequired()])
    is_active = BooleanField('نشط', default=True)
    submit = SubmitField('حفظ')

class AdminLoginForm(FlaskForm):
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    submit = SubmitField('تسجيل الدخول')

class CheckoutForm(FlaskForm):
    name = StringField('الاسم الكامل', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('رقم الهاتف', validators=[DataRequired(), Length(min=6, max=20)])
    address = TextAreaField('العنوان بالتفصيل', validators=[DataRequired(), Length(min=10, max=500)])
    payment_method = RadioField('طريقة الدفع', choices=[
        ('cod', 'الدفع عند الاستلام'),
        ('vodafone_cash', 'فودافون كاش')
    ], validators=[DataRequired()])
    vodafone_receipt = FileField('إيصال الدفع (لفودافون كاش فقط)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'الصور فقط مسموح بها!')
    ])
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
    hero_image = FileField('صورة الهيرو الرئيسية', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'الصور فقط!')])
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
    twitter_url = StringField('رابط تويتر')
    whatsapp_number = StringField('رقم واتساب')
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