"""
WSGI Entry Point para Deploy em Produção
Render.com e outros provedores usam este arquivo
"""

from app_multi_tenant import app

if __name__ == "__main__":
    app.run()
