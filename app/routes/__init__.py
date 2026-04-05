def register_routes(app):
    from app.routes.redirect import redirect_bp
    from app.routes.urls import urls_bp
    from app.routes.users import users_bp
    from app.routes.users_crud import users_crud_bp
    from app.routes.events import events_bp

    # users_crud_bp must be registered before redirect_bp so /users/* routes
    # are not captured by the catch-all /<short_code> redirect handler.
    app.register_blueprint(users_crud_bp)
    app.register_blueprint(urls_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(redirect_bp)
