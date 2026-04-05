def register_routes(app):
    from app.routes.users_crud import users_crud_bp
    from app.routes.urls_crud import urls_crud_bp
    from app.routes.events_crud import events_crud_bp
    from app.routes.urls import urls_bp
    from app.routes.users import users_bp
    from app.routes.events import events_bp
    from app.routes.redirect import redirect_bp

    # Specific blueprints must be registered before redirect_bp.
    # The redirect handler uses /<short_code> which would otherwise
    # swallow /users, /urls, and /events requests.
    app.register_blueprint(users_crud_bp)
    app.register_blueprint(urls_crud_bp)
    app.register_blueprint(events_crud_bp)
    app.register_blueprint(urls_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(redirect_bp)
