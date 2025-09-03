from flask import Flask, render_template
import os
from routes.business_auth import business_auth_bp
from routes.referral_auth import referral_auth_bp
from routes.business_product import product_bp
from routes.referral_request_bus import referrals_bp as ref_req_bus
from routes.referral_products import referral_bp as referral_product


app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'static/uploads/products'

app.register_blueprint(business_auth_bp)
app.register_blueprint(referral_auth_bp)
app.register_blueprint(product_bp)
app.register_blueprint(ref_req_bus)
app.register_blueprint(referral_product)

@app.route('/')
def api_index():
    return render_template('start_page.html')

@app.route('/start_menu')
def start_menu():
    return render_template('api_index.html')

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=8002, debug=True)