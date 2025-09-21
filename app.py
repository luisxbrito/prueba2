import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'restaurant.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key' # Change this in a real app
db = SQLAlchemy(app)

# Association table for the many-to-many relationship between Order and MenuItem
order_items = db.Table('order_items',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), primary_key=True),
    db.Column('menu_item_id', db.Integer, db.ForeignKey('menu_item.id'), primary_key=True)
)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<MenuItem {self.name}>'

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False, default='pending') # pending, in_progress, completed, cancelled
    items = db.relationship('MenuItem', secondary=order_items, lazy='subquery',
        backref=db.backref('orders', lazy=True))

    def __repr__(self):
        return f'<Order {self.id}>'


@app.route('/')
def hello_restaurant():
    return 'Hello, Restaurant!'

@app.route('/menu')
def menu():
    menu_items = MenuItem.query.all()
    return render_template('menu.html', menu_items=menu_items)

@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        item_ids = request.form.getlist('menu_items')
        if not item_ids:
            flash('Please select at least one item to order.', 'warning')
            return redirect(url_for('order'))

        new_order = Order()
        db.session.add(new_order)
        for item_id in item_ids:
            item = db.session.get(MenuItem, item_id)
            if item:
                new_order.items.append(item)

        db.session.commit()
        flash('Your order has been placed successfully!', 'success')
        return redirect(url_for('menu'), code=303)

    # For GET request
    menu_items = MenuItem.query.all()
    return render_template('order.html', menu_items=menu_items)

@app.route('/kitchen')
def kitchen():
    orders = Order.query.order_by(Order.id.desc()).all()
    statuses = ['pending', 'in_progress', 'completed', 'cancelled']
    return render_template('kitchen.html', orders=orders, statuses=statuses)

@app.route('/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"success": False, "error": "Order not found"}), 404

    new_status = request.form.get('status')
    if not new_status:
        return jsonify({"success": False, "error": "Status not provided"}), 400

    order.status = new_status
    db.session.commit()
    return jsonify({"success": True, "new_status": new_status})

@app.route('/bill/<int:order_id>')
def bill(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return "Order not found", 404

    total_price = sum(item.price for item in order.items)

    return render_template('bill.html', order=order, total_price=total_price)


if __name__ == '__main__':
    app.run(debug=True)
