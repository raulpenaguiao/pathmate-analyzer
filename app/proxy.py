class ReverseProxied:
    """Make the app aware it's mounted under a path prefix (e.g. /pathmate-analyzer)
    by an nginx reverse proxy. Reads the X-Script-Name / X-Forwarded-Proto headers
    nginx sends, matching the convention already used by the other apps on this
    VPS, so url_for()/redirect() produce correctly prefixed, correctly-schemed URLs
    instead of ones rooted at the domain.
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get("HTTP_X_SCRIPT_NAME", "")
        if script_name:
            environ["SCRIPT_NAME"] = script_name
            path_info = environ.get("PATH_INFO", "")
            if path_info.startswith(script_name):
                stripped = path_info[len(script_name):]
                # Hitting the bare mount point (no trailing slash, nothing after
                # it) strips to an empty string, which Flask's router does not
                # treat the same as "/" - force it back to "/" so the root
                # route still matches.
                environ["PATH_INFO"] = stripped or "/"

        scheme = environ.get("HTTP_X_FORWARDED_PROTO", "")
        if scheme:
            environ["wsgi.url_scheme"] = scheme

        return self.app(environ, start_response)
