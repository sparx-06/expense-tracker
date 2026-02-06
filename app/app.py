from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func, extract
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///expenses.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class EventType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    events = db.relationship('Event', backref='event_type', lazy=True)

class ExpenseCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    expenses = db.relationship('Expense', backref='category', lazy=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    event_type_id = db.Column(db.Integer, db.ForeignKey('event_type.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expenses = db.relationship('Expense', backref='event', lazy=True, cascade='all, delete-orphan')

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_category.id'), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize database
with app.app_context():
    db.create_all()
    
    # Add default event types if none exist
    if EventType.query.count() == 0:
        default_event_types = ['Birthday', 'Anniversary', 'Trip', 'Christmas', 'Wedding', 
                               'Thanksgiving', 'Easter', 'Graduation', 'Baby Shower', 'Other']
        for type_name in default_event_types:
            event_type = EventType(name=type_name)
            db.session.add(event_type)
        db.session.commit()
    
    # Add default expense categories if none exist
    if ExpenseCategory.query.count() == 0:
        default_categories = [
            'Gifts', 'Food & Dining', 'Transportation', 'Accommodation', 'Entertainment',
            'Decorations', 'Supplies', 'Clothing', 'Activities', 'Services', 'Other'
        ]
        for cat_name in default_categories:
            category = ExpenseCategory(name=cat_name)
            db.session.add(category)
        db.session.commit()

@app.route('/')
def index():
    event_types = EventType.query.all()
    expense_categories = ExpenseCategory.query.all()
    events = Event.query.order_by(Event.date.desc()).all()
    return render_template('index.html', 
                         event_types=event_types, 
                         expense_categories=expense_categories,
                         events=events)

# Event endpoints
@app.route('/api/events', methods=['GET', 'POST'])
def handle_events():
    if request.method == 'POST':
        data = request.json
        try:
            event = Event(
                name=data['name'],
                event_type_id=int(data['event_type_id']),
                date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
                notes=data.get('notes', '')
            )
            db.session.add(event)
            db.session.commit()
            return jsonify({'success': True, 'id': event.id})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    # GET request
    events = Event.query.order_by(Event.date.desc()).all()
    return jsonify([{
        'id': e.id,
        'name': e.name,
        'event_type': e.event_type.name,
        'event_type_id': e.event_type_id,
        'date': e.date.strftime('%Y-%m-%d'),
        'notes': e.notes,
        'total_expenses': sum(exp.amount for exp in e.expenses)
    } for e in events])

@app.route('/api/events/<int:event_id>', methods=['GET', 'DELETE', 'PUT'])
def handle_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': event.id,
            'name': event.name,
            'event_type_id': event.event_type_id,
            'date': event.date.strftime('%Y-%m-%d'),
            'notes': event.notes,
            'expenses': [{
                'id': exp.id,
                'description': exp.description,
                'amount': exp.amount,
                'date': exp.date.strftime('%Y-%m-%d'),
                'category': exp.category.name,
                'category_id': exp.category_id,
                'notes': exp.notes
            } for exp in event.expenses]
        })
    
    if request.method == 'DELETE':
        db.session.delete(event)
        db.session.commit()
        return jsonify({'success': True})
    
    if request.method == 'PUT':
        data = request.json
        try:
            event.name = data['name']
            event.event_type_id = int(data['event_type_id'])
            event.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            event.notes = data.get('notes', '')
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

# Expense endpoints
@app.route('/api/expenses', methods=['GET', 'POST'])
def handle_expenses():
    if request.method == 'POST':
        data = request.json
        try:
            expense = Expense(
                description=data['description'],
                amount=float(data['amount']),
                date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
                event_id=int(data['event_id']),
                category_id=int(data['category_id']),
                notes=data.get('notes', '')
            )
            db.session.add(expense)
            db.session.commit()
            return jsonify({'success': True, 'id': expense.id})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    # GET request
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    return jsonify([{
        'id': e.id,
        'description': e.description,
        'amount': e.amount,
        'date': e.date.strftime('%Y-%m-%d'),
        'event': e.event.name,
        'event_id': e.event_id,
        'category': e.category.name,
        'category_id': e.category_id,
        'notes': e.notes
    } for e in expenses])

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE', 'PUT'])
def handle_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    
    if request.method == 'DELETE':
        db.session.delete(expense)
        db.session.commit()
        return jsonify({'success': True})
    
    if request.method == 'PUT':
        data = request.json
        try:
            expense.description = data['description']
            expense.amount = float(data['amount'])
            expense.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            expense.event_id = int(data['event_id'])
            expense.category_id = int(data['category_id'])
            expense.notes = data.get('notes', '')
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

# Event Type endpoints
@app.route('/api/event-types', methods=['GET', 'POST'])
def handle_event_types():
    if request.method == 'POST':
        data = request.json
        try:
            event_type = EventType(name=data['name'])
            db.session.add(event_type)
            db.session.commit()
            return jsonify({'success': True, 'id': event_type.id})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    event_types = EventType.query.all()
    return jsonify([{'id': et.id, 'name': et.name} for et in event_types])

# Expense Category endpoints
@app.route('/api/expense-categories', methods=['GET', 'POST'])
def handle_expense_categories():
    if request.method == 'POST':
        data = request.json
        try:
            category = ExpenseCategory(name=data['name'])
            db.session.add(category)
            db.session.commit()
            return jsonify({'success': True, 'id': category.id})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    categories = ExpenseCategory.query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in categories])

@app.route('/api/analytics')
def analytics():
    event_type_id = request.args.get('event_type_id', type=int)
    
    # Get yearly totals by event type
    query = db.session.query(
        extract('year', Event.date).label('year'),
        EventType.name,
        func.sum(Expense.amount).label('total')
    ).join(Event).join(Expense).group_by('year', EventType.name).order_by('year', EventType.name)
    
    if event_type_id:
        query = query.filter(Event.event_type_id == event_type_id)
    
    results = query.all()
    
    # Format data
    yearly_data = {}
    for year, event_type, total in results:
        year = int(year)
        if year not in yearly_data:
            yearly_data[year] = {}
        yearly_data[year][event_type] = float(total)
    
    # Get event breakdown
    event_query = db.session.query(
        Event.id,
        Event.name,
        Event.date,
        EventType.name.label('event_type'),
        func.sum(Expense.amount).label('total')
    ).join(EventType).join(Expense).group_by(Event.id).order_by(Event.date.desc())
    
    if event_type_id:
        event_query = event_query.filter(Event.event_type_id == event_type_id)
    
    event_results = event_query.all()
    
    events_data = [{
        'id': e.id,
        'name': e.name,
        'date': e.date.strftime('%Y-%m-%d'),
        'event_type': e.event_type,
        'total': float(e.total)
    } for e in event_results]
    
    # Get category breakdown
    category_query = db.session.query(
        ExpenseCategory.name,
        func.sum(Expense.amount).label('total')
    ).join(Expense).group_by(ExpenseCategory.name).order_by(func.sum(Expense.amount).desc())
    
    if event_type_id:
        category_query = category_query.join(Event).filter(Event.event_type_id == event_type_id)
    
    category_results = category_query.all()
    
    category_data = {cat: float(total) for cat, total in category_results}
    
    return jsonify({
        'yearly': yearly_data,
        'events': events_data,
        'categories': category_data
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
