from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this for production

# Helper function to get DB connection
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Home page
@app.route('/')
def index():
    conn = get_db()
    products = conn.execute('SELECT * FROM products LIMIT 6').fetchall()  # Featured products
    conn.close()
    return render_template('index.html', products=products)

# Categories page
@app.route('/categories')
def categories():
    category = request.args.get('category', '')
    conn = get_db()
    if category:
        products = conn.execute('SELECT * FROM products WHERE category = ?', (category,)).fetchall()
    else:
        products = conn.execute('SELECT * FROM products').fetchall()
    categories = conn.execute('SELECT DISTINCT category FROM products').fetchall()
    conn.close()
    return render_template('categories.html', products=products, categories=categories, selected_category=category)

# Add to cart
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'cart' not in session:
        session['cart'] = []
    
    product_id = request.form['product_id']
    quantity = int(request.form.get('quantity', 1))
    
    conn = get_db()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    
    if product:
        # Check if already in cart
        for item in session['cart']:
            if item['id'] == product_id:
                item['quantity'] += quantity
                break
        else:
            session['cart'].append({
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'quantity': quantity,
                'image': product['image']
            })
        session.modified = True
        flash('Product added to cart!', 'success')
    
    return redirect(url_for('index' if request.referrer == url_for('index') else 'categories'))

# Cart page
@app.route('/cart')
def cart():
    if 'cart' not in session:
        session['cart'] = []
    total = sum(item['quantity'] * item['price'] for item in session['cart'])
    return render_template('cart.html', cart=session['cart'], total=total)

# Remove from cart
@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if item['id'] != product_id]
        session.modified = True
        flash('Product removed from cart!', 'info')
    return redirect(url_for('cart'))

# Update cart quantity (AJAX-friendly)
@app.route('/update_cart', methods=['POST'])
def update_cart():
    product_id = request.json['product_id']
    new_quantity = int(request.json['quantity'])
    
    if 'cart' in session:
        for item in session['cart']:
            if item['id'] == product_id:
                item['quantity'] = new_quantity
                if new_quantity == 0:
                    session['cart'].remove(item)
                break
        session.modified = True
    
    total = sum(item['quantity'] * item['price'] for item in session['cart'])
    return jsonify({'total': total})

# Search (simple keyword search)
@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    conn = get_db()
    products = conn.execute('SELECT * FROM products WHERE name LIKE ? OR description LIKE ?', (f'%{query}%', f'%{query}%')).fetchall()
    conn.close()
    return render_template('index.html', products=products, search_query=query)

if __name__ == '__main__':
    app.run(debug=True)