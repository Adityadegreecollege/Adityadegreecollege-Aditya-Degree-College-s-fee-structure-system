from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import mysql.connector
from fpdf import FPDF
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'vishnu@123',
    'database': 'college_fee_management'
}

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user

# Database connection helper
def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

# Initialize database (create tables if they don't exist)
def init_db():
    try:
        conn = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS college_fee_management")
        cursor.close()
        conn.close()
        
        # Now connect to the specific database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create fee_records table with updated schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fee_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_name VARCHAR(100) NOT NULL,
                admission_number VARCHAR(50) NOT NULL,
                student_group VARCHAR(50) NOT NULL,
                semester VARCHAR(20) NOT NULL,
                address TEXT,
                managerial_convener VARCHAR(100),
                tuition_fee DECIMAL(10,2),
                bus_total_fee DECIMAL(10,2),
                bus_paid_fee DECIMAL(10,2),
                bus_pending_fee DECIMAL(10,2),
                practical_fee DECIMAL(10,2),
                university_fee DECIMAL(10,2),
                stationary_fee DECIMAL(10,2),
                internship_fee DECIMAL(10,2),
                viva_fee DECIMAL(10,2),
                total_amount DECIMAL(10,2) NOT NULL,
                discount DECIMAL(10,2) DEFAULT 0,
                paid_amount DECIMAL(10,2) NOT NULL,
                pending_amount DECIMAL(10,2) DEFAULT 0,
                date DATE NOT NULL,
                bill_number VARCHAR(50) NOT NULL,
                class VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create default admin user if not exists
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", 
                         ('admin', 'admin123'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"Error initializing database: {err}")

# Call the init_db function when the app starts
init_db()

# Routes
@app.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and user['password'] == password:
            user_obj = User()
            user_obj.id = username
            login_user(user_obj)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/groups/<class_name>')
@login_required
def groups(class_name):
    return render_template('group.html', class_name=class_name)

@app.route('/fee_table/<class_name>/<group_name>')
@login_required
def fee_table(class_name, group_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all fee records for this class and group
    cursor.execute("""
        SELECT * FROM fee_records 
        WHERE class = %s AND student_group = %s
        ORDER BY student_name
    """, (class_name, group_name))
    records = cursor.fetchall()
    
    # Calculate pending amounts for each record
    for record in records:
        record['pending_amount'] = record['total_amount'] - record['paid_amount']
    
    # Get unique values for filters
    cursor.execute("""
        SELECT DISTINCT semester FROM fee_records 
        WHERE class = %s AND student_group = %s
    """, (class_name, group_name))
    semesters = [s['semester'] for s in cursor.fetchall()]
    
    cursor.execute("""
        SELECT DISTINCT YEAR(date) as year FROM fee_records 
        WHERE class = %s AND student_group = %s
    """, (class_name, group_name))
    years = [y['year'] for y in cursor.fetchall() if y['year']]
    
    cursor.close()
    conn.close()
    
    return render_template('fee_table.html', 
                         records=records,
                         class_name=class_name,
                         group_name=group_name,
                         semesters=semesters,
                         years=years)

@app.route('/add_record/<class_name>/<group_name>', methods=['GET', 'POST'])
@login_required
def add_record(class_name, group_name):
    if request.method == 'POST':
        # Calculate bus fees
        bus_total_fee = float(request.form['bus_total_fee']) if request.form['bus_total_fee'] else 0
        bus_paid_fee = float(request.form['bus_paid_fee']) if request.form['bus_paid_fee'] else 0
        bus_pending_fee = bus_total_fee - bus_paid_fee
        
        # Calculate total amount by summing all fees
        tuition_fee = float(request.form['tuition_fee']) if request.form['tuition_fee'] else 0
        practical_fee = float(request.form['practical_fee']) if request.form['practical_fee'] else 0
        university_fee = float(request.form['university_fee']) if request.form['university_fee'] else 0
        stationary_fee = float(request.form['stationary_fee']) if request.form['stationary_fee'] else 0
        internship_fee = float(request.form['internship_fee']) if request.form['internship_fee'] else 0
        viva_fee = float(request.form['viva_fee']) if request.form['viva_fee'] else 0
        discount = float(request.form['discount']) if request.form['discount'] else 0
        paid_amount = float(request.form['paid_amount']) if request.form['paid_amount'] else 0
        
        total_amount = (tuition_fee + bus_total_fee + practical_fee + 
                       university_fee + stationary_fee + internship_fee + 
                       viva_fee) - discount
        pending_amount = total_amount - paid_amount
        
        # Extract all form data
        data = {
            'student_name': request.form['student_name'],
            'admission_number': request.form['admission_number'],
            'student_group': group_name,
            'semester': request.form['semester'],
            'address': request.form['address'],
            'managerial_convener': request.form['managerial_convener'],
            'tuition_fee': tuition_fee,
            'bus_total_fee': bus_total_fee,
            'bus_paid_fee': bus_paid_fee,
            'bus_pending_fee': bus_pending_fee,
            'practical_fee': practical_fee,
            'university_fee': university_fee,
            'stationary_fee': stationary_fee,
            'internship_fee': internship_fee,
            'viva_fee': viva_fee,
            'total_amount': total_amount,
            'discount': discount,
            'paid_amount': paid_amount,
            'pending_amount': pending_amount,
            'date': request.form['date'],
            'bill_number': request.form['bill_number'],
            'class': class_name
        }
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert the new record
        cursor.execute("""
            INSERT INTO fee_records (
                student_name, admission_number, student_group, semester,
                address, managerial_convener, tuition_fee,
                bus_total_fee, bus_paid_fee, bus_pending_fee, practical_fee, 
                university_fee, stationary_fee, internship_fee, viva_fee, 
                total_amount, discount, paid_amount, pending_amount, date, bill_number, class
            ) VALUES (
                %(student_name)s, %(admission_number)s, %(student_group)s, %(semester)s,
                %(address)s, %(managerial_convener)s, %(tuition_fee)s,
                %(bus_total_fee)s, %(bus_paid_fee)s, %(bus_pending_fee)s, %(practical_fee)s, 
                %(university_fee)s, %(stationary_fee)s, %(internship_fee)s, %(viva_fee)s, 
                %(total_amount)s, %(discount)s, %(paid_amount)s, %(pending_amount)s, %(date)s, %(bill_number)s, %(class)s
            )
        """, data)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Record added successfully!', 'success')
        return redirect(url_for('fee_table', class_name=class_name, group_name=group_name))
    
    return render_template('add_edit.html', 
                         class_name=class_name,
                         group_name=group_name,
                         record=None,
                         action='Add')

@app.route('/edit_record/<class_name>/<group_name>/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_record(class_name, group_name, record_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Calculate bus fees
        bus_total_fee = float(request.form['bus_total_fee']) if request.form['bus_total_fee'] else 0
        bus_paid_fee = float(request.form['bus_paid_fee']) if request.form['bus_paid_fee'] else 0
        bus_pending_fee = bus_total_fee - bus_paid_fee
        
        # Calculate total amount by summing all fees
        tuition_fee = float(request.form['tuition_fee']) if request.form['tuition_fee'] else 0
        practical_fee = float(request.form['practical_fee']) if request.form['practical_fee'] else 0
        university_fee = float(request.form['university_fee']) if request.form['university_fee'] else 0
        stationary_fee = float(request.form['stationary_fee']) if request.form['stationary_fee'] else 0
        internship_fee = float(request.form['internship_fee']) if request.form['internship_fee'] else 0
        viva_fee = float(request.form['viva_fee']) if request.form['viva_fee'] else 0
        discount = float(request.form['discount']) if request.form['discount'] else 0
        paid_amount = float(request.form['paid_amount']) if request.form['paid_amount'] else 0
        
        total_amount = (tuition_fee + bus_total_fee + practical_fee + 
                       university_fee + stationary_fee + internship_fee + 
                       viva_fee) - discount
        pending_amount = total_amount - paid_amount
        
        # Extract all form data
        data = {
            'id': record_id,
            'student_name': request.form['student_name'],
            'admission_number': request.form['admission_number'],
            'student_group': group_name,
            'semester': request.form['semester'],
            'address': request.form['address'],
            'managerial_convener': request.form['managerial_convener'],
            'tuition_fee': tuition_fee,
            'bus_total_fee': bus_total_fee,
            'bus_paid_fee': bus_paid_fee,
            'bus_pending_fee': bus_pending_fee,
            'practical_fee': practical_fee,
            'university_fee': university_fee,
            'stationary_fee': stationary_fee,
            'internship_fee': internship_fee,
            'viva_fee': viva_fee,
            'total_amount': total_amount,
            'discount': discount,
            'paid_amount': paid_amount,
            'pending_amount': pending_amount,
            'date': request.form['date'],
            'bill_number': request.form['bill_number'],
            'class': class_name
        }
        
        # Update the record
        cursor.execute("""
            UPDATE fee_records SET
                student_name = %(student_name)s,
                admission_number = %(admission_number)s,
                student_group = %(student_group)s,
                semester = %(semester)s,
                address = %(address)s,
                managerial_convener = %(managerial_convener)s,
                tuition_fee = %(tuition_fee)s,
                bus_total_fee = %(bus_total_fee)s,
                bus_paid_fee = %(bus_paid_fee)s,
                bus_pending_fee = %(bus_pending_fee)s,
                practical_fee = %(practical_fee)s,
                university_fee = %(university_fee)s,
                stationary_fee = %(stationary_fee)s,
                internship_fee = %(internship_fee)s,
                viva_fee = %(viva_fee)s,
                total_amount = %(total_amount)s,
                discount = %(discount)s,
                paid_amount = %(paid_amount)s,
                pending_amount = %(pending_amount)s,
                date = %(date)s,
                bill_number = %(bill_number)s,
                class = %(class)s
            WHERE id = %(id)s
        """, data)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Record updated successfully!', 'success')
        return redirect(url_for('fee_table', class_name=class_name, group_name=group_name))
    
    # Get the existing record
    cursor.execute("SELECT * FROM fee_records WHERE id = %s", (record_id,))
    record = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not record:
        flash('Record not found!', 'error')
        return redirect(url_for('fee_table', class_name=class_name, group_name=group_name))
    
    return render_template('add_edit.html', 
                         class_name=class_name,
                         group_name=group_name,
                         record=record,
                         action='Edit')

@app.route('/delete_record/<class_name>/<group_name>/<int:record_id>')
@login_required
def delete_record(class_name, group_name, record_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM fee_records WHERE id = %s", (record_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Record deleted successfully!', 'success')
    return redirect(url_for('fee_table', class_name=class_name, group_name=group_name))

@app.route('/download_pdf/<class_name>/<group_name>')
@login_required
def download_pdf(class_name, group_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT * FROM fee_records 
        WHERE class = %s AND student_group = %s
        ORDER BY student_name
    """, (class_name, group_name))
    records = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Calculate pending amounts for each record
    for record in records:
        record['pending_amount'] = record['total_amount'] - record['paid_amount']
    
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.cell(200, 10, txt=f"Fee Records - {class_name} - {group_name}", ln=1, align='C')
    pdf.ln(10)
    
    # Table header
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(60, 10, "Student Name", 1, 0, 'C', True)
    pdf.cell(30, 10, "Admission No", 1, 0, 'C', True)
    pdf.cell(20, 10, "Semester", 1, 0, 'C', True)
    pdf.cell(30, 10, "Total Amount", 1, 0, 'C', True)
    pdf.cell(30, 10, "Paid Amount", 1, 0, 'C', True)
    pdf.cell(30, 10, "Pending Amount", 1, 0, 'C', True)
    pdf.cell(20, 10, "Date", 1, 1, 'C', True)
    
    # Table data
    pdf.set_fill_color(255, 255, 255)
    for record in records:
        pdf.cell(60, 10, record['student_name'], 1)
        pdf.cell(30, 10, record['admission_number'], 1)
        pdf.cell(20, 10, record['semester'], 1)
        pdf.cell(30, 10, str(record['total_amount']), 1)
        pdf.cell(30, 10, str(record['paid_amount']), 1)
        pdf.cell(30, 10, str(record['pending_amount']), 1)
        pdf.cell(20, 10, str(record['date']), 1)
        pdf.ln()
    
    # Save PDF to temporary file
    pdf_path = f"temp_fee_report_{class_name}_{group_name}.pdf"
    pdf.output(pdf_path)
    
    # Send file and then delete it
    response = send_file(pdf_path, as_attachment=True)
    
    # Schedule file deletion after response is sent
    @response.call_on_close
    def remove_file():
        try:
            os.remove(pdf_path)
        except:
            pass
    
    return response

@app.route('/download_record_pdf/<int:record_id>')
@login_required
def download_record_pdf(record_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM fee_records WHERE id = %s", (record_id,))
    record = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not record:
        flash('Record not found!', 'error')
        return redirect(url_for('home'))

    # Calculate pending amount
    record['pending_amount'] = record['total_amount'] - record['paid_amount']

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.cell(200, 10, txt=f"Fee Receipt - {record['student_name']}", ln=1, align='C')
    pdf.ln(10)
    
    # Student Info
    pdf.cell(50, 10, "Student Name:", 0)
    pdf.cell(0, 10, record['student_name'], 0, 1)
    pdf.cell(50, 10, "Admission Number:", 0)
    pdf.cell(0, 10, record['admission_number'], 0, 1)
    pdf.cell(50, 10, "Class:", 0)
    pdf.cell(0, 10, record['class'], 0, 1)
    pdf.cell(50, 10, "Group:", 0)
    pdf.cell(0, 10, record['student_group'], 0, 1)
    pdf.cell(50, 10, "Semester:", 0)
    pdf.cell(0, 10, record['semester'], 0, 1)
    pdf.ln(10)
    
    # Fee Details
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(100, 10, "Fee Component", 1, 0, 'C', True)
    pdf.cell(50, 10, "Amount", 1, 1, 'C', True)
    
    pdf.set_fill_color(255, 255, 255)
    
    # Safe way to check and display fees
    def add_fee_row(label, fee_key):
        if fee_key in record and record[fee_key]:
            pdf.cell(100, 10, label, 1)
            pdf.cell(50, 10, str(record[fee_key]), 1, 1)
    
    add_fee_row("Tuition Fee", 'tuition_fee')
    add_fee_row("Bus Total Fee", 'bus_total_fee')
    add_fee_row("Bus Paid Fee", 'bus_paid_fee')
    add_fee_row("Bus Pending Fee", 'bus_pending_fee')
    add_fee_row("Practical Fee", 'practical_fee')
    add_fee_row("University Fee", 'university_fee')
    add_fee_row("Stationary Fee", 'stationary_fee')
    add_fee_row("Internship Fee", 'internship_fee')
    add_fee_row("Viva Fee", 'viva_fee')
    
    pdf.ln(5)
    pdf.cell(100, 10, "Total Amount:", 0, 0, 'R')
    pdf.cell(50, 10, str(record.get('total_amount', 0)), 0, 1)
    
    pdf.cell(100, 10, "Discount:", 0, 0, 'R')
    pdf.cell(50, 10, str(record.get('discount', 0)), 0, 1)
    
    pdf.cell(100, 10, "Paid Amount:", 0, 0, 'R')
    pdf.cell(50, 10, str(record.get('paid_amount', 0)), 0, 1)
    
    pdf.cell(100, 10, "Remaining Balance:", 0, 0, 'R')
    pdf.cell(50, 10, str(record.get('pending_amount', 0)), 0, 1)
    
    pdf.ln(10)
    pdf.cell(0, 10, f"Bill Number: {record.get('bill_number', '')}", 0, 1)
    pdf.cell(0, 10, f"Date: {record.get('date', '')}", 0, 1)
    
    # Save PDF to temporary file
    pdf_path = f"temp_fee_receipt_{record_id}.pdf"
    pdf.output(pdf_path)
    
    # Send file and then delete it
    response = send_file(
        pdf_path, 
        as_attachment=True, 
        download_name=f"fee_receipt_{record['student_name']}.pdf"
    )
    
    # Schedule file deletion after response is sent
    @response.call_on_close
    def remove_file():
        try:
            os.remove(pdf_path)
        except:
            pass
    
    return response

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))