import os
from sloy.api.factory import create_app
from sloy.api.compute import compute_blueprints
from dotenv import load_dotenv

def run_app_dev():
    load_dotenv()
    debug_mode = os.getenv('DEBUG', 'False')
    port = os.getenv('PORT', 8080)

    app = create_app()
    app.register_blueprint(compute_blueprints)

    app.run(debug=debug_mode, port=port)

def run_app():
    load_dotenv()
    port = os.getenv('PORT', 8080)

    app = create_app()
    app.register_blueprint(compute_blueprints)

    from waitress import serve
    serve(app, host="0.0.0.0", port=port)

if __name__ == '__main__':
    run_app()
