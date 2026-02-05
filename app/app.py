from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func, extract
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    expenses = db.relationship('Expense', backref='category', lazy=True, cascade='all, delete-orphan')

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize database
with app.app_context():
    db.create_all()
    # Add default categories if none exist
    if Category.query.count() == 0:
        default_categories = ['Birthday', 'Anniversary', 'Christmas', 'Trip', 'Other Holiday']
        for cat_name in default_categories:
            category = Category(name=cat_name)
            db.session.add(category)
        db.session.commit()

@app.route('/')
def index():
    categories = Category.query.all()
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    return render_template('index.html', categories=categories, expenses=expenses)

@app.route('/api/expenses', methods=['GET', 'POST'])
def handle_expenses():
    if request.method == 'POST':
        data = request.json
        try:
            expense = Expense(
                description=data['description'],
                amount=float(data['amount']),
                date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
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
            expense.category_id = int(data['category_id'])
            expense.notes = data.get('notes', '')
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/categories', methods=['GET', 'POST'])
def handle_categories():
    if request.method == 'POST':
        data = request.json
        try:
            category = Category(name=data['name'])
            db.session.add(category)
            db.session.commit()
            return jsonify({'success': True, 'id': category.id})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    categories = Category.query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in categories])

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/analytics')
def analytics():
    category_id = request.args.get('category_id', type=int)
    
    # Get yearly totals by category
    query = db.session.query(
        extract('year', Expense.date).label('year'),
        Category.name,
        func.sum(Expense.amount).label('total')
    ).join(Category).group_by('year', Category.name).order_by('year', Category.name)
    
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    
    results = query.all()
    
    # Format data
    data = {}
    for year, category, total in results:
        year = int(year)
        if year not in data:
            data[year] = {}
        data[year][category] = float(total)
    
    # Get monthly breakdown for current year
    current_year = datetime.now().year
    monthly_query = db.session.query(
        extract('month', Expense.date).label('month'),
        Category.name,
        func.sum(Expense.amount).label('total')
    ).join(Category).filter(
        extract('year', Expense.date) == current_year
    ).group_by('month', Category.name).order_by('month')
    
    if category_id:
        monthly_query = monthly_query.filter(Expense.category_id == category_id)
    
    monthly_results = monthly_query.all()
    
    monthly_data = {}
    for month, category, total in monthly_results:
        month = int(month)
        if month not in monthly_data:
            monthly_data[month] = {}
        monthly_data[month][category] = float(total)
    
    return jsonify({
        'yearly': data,
        'monthly': monthly_data
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
