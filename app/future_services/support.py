from datetime import datetime
from flask import current_app, render_template
from flask_mail import Message
import json
from app import db
from app.models import User, SupportTicket, TicketResponse
from app.services import mail

class SupportManager:
    @staticmethod
    def create_ticket(data):
        """Create a new support ticket"""
        ticket = SupportTicket(
            ticket_number=f"TKT{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            user_id=data.get('user_id'),
            name=data['name'],
            email=data['email'],
            subject=data['subject'],
            message=data['message'],
            category=data['category']
        )
        
        if data.get('priority'):
            ticket.priority = data['priority']
        
        db.session.add(ticket)
        db.session.commit()
        
        # Send confirmation email
        SupportManager.send_ticket_confirmation(ticket)
        
        return ticket
    
    @staticmethod
    def add_response(ticket_id, message, responder_id=None, is_staff=False):
        """Add response to a ticket"""
        response = TicketResponse(
            ticket_id=ticket_id,
            responder_id=responder_id,
            message=message,
            is_staff=is_staff
        )
        
        ticket = SupportTicket.query.get(ticket_id)
        if is_staff:
            ticket.status = 'in_progress'
        
        db.session.add(response)
        db.session.commit()
        
        # Notify user of response
        if is_staff:
            SupportManager.send_response_notification(ticket, response)
        
        return response
    
    @staticmethod
    def close_ticket(ticket_id):
        """Close a support ticket"""
        ticket = SupportTicket.query.get(ticket_id)
        if ticket:
            ticket.status = 'closed'
            ticket.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Send closure notification
            SupportManager.send_ticket_closure(ticket)
            
            return True
        return False
    
    @staticmethod
    def send_ticket_confirmation(ticket):
        """Send ticket confirmation email"""
        msg = Message(
            f'تأكيد تذكرة الدعم #{ticket.ticket_number}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[ticket.email]
        )
        
        msg.html = f"""
        <h3>تم استلام طلب الدعم الخاص بك</h3>
        <p>رقم التذكرة: {ticket.ticket_number}</p>
        <p>الموضوع: {ticket.subject}</p>
        <p>الحالة: {ticket.status}</p>
        <p>سنقوم بالرد عليك في أقرب وقت ممكن.</p>
        """
        
        mail.send(msg)
    
    @staticmethod
    def send_response_notification(ticket, response):
        """Send notification when staff responds to ticket"""
        msg = Message(
            f'تحديث على تذكرة الدعم #{ticket.ticket_number}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[ticket.email]
        )
        
        msg.html = f"""
        <h3>تم إضافة رد جديد على تذكرة الدعم الخاصة بك</h3>
        <p>رقم التذكرة: {ticket.ticket_number}</p>
        <p>الموضوع: {ticket.subject}</p>
        <p>الرد: {response.message}</p>
        """
        
        mail.send(msg)
    
    @staticmethod
    def send_ticket_closure(ticket):
        """Send ticket closure notification"""
        msg = Message(
            f'إغلاق تذكرة الدعم #{ticket.ticket_number}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[ticket.email]
        )
        
        msg.html = f"""
        <h3>تم إغلاق تذكرة الدعم</h3>
        <p>رقم التذكرة: {ticket.ticket_number}</p>
        <p>الموضوع: {ticket.subject}</p>
        <p>نشكرك على تواصلك معنا.</p>
        """
        
        mail.send(msg)

class FAQ:
    @staticmethod
    def get_all_faqs():
        """Get all FAQs from JSON file"""
        try:
            with open('static/data/faqs.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    @staticmethod
    def search_faqs(query):
        """Search FAQs by keyword"""
        faqs = FAQ.get_all_faqs()
        query = query.lower()
        return [
            faq for faq in faqs
            if query in faq['question'].lower() or query in faq['answer'].lower()
        ]
    
    @staticmethod
    def get_faq_by_category(category):
        """Get FAQs filtered by category"""
        faqs = FAQ.get_all_faqs()
        return [faq for faq in faqs if faq['category'] == category] 