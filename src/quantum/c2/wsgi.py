"""quantum.c2.wsgi — production WSGI chain (waitress -> gunicorn -> dev)."""
from __future__ import annotations

from quantum.core.logging import log


def run_c2(app, host="0.0.0.0", port=8443):
    """V3 production WSGI: waitress (all OS) -> gunicorn (POSIX) -> Flask dev
    server as last resort only."""
    try:
        import waitress
        log(f"C2 served by WAITRESS (production WSGI) on {host}:{port}", "C2")
        waitress.serve(app, host=host, port=port, threads=16, channel_timeout=30)
        return
    except ImportError:
        pass
    try:
        import gunicorn.app.base
        class Standalone(gunicorn.app.base.BaseApplication):
            def load_config(self):
                self.cfg.set("bind", f"{host}:{port}")
                self.cfg.set("workers", 4)
            def load(self): return app
        log(f"C2 served by GUNICORN (production WSGI) on {host}:{port}", "C2")
        Standalone().run(); return
    except ImportError:
        log("waitress/gunicorn missing — falling back to Flask dev server "
            "(NOT production-recommended; pip install waitress)", "WARN")
    app.run(host=host, port=port, threaded=True)
