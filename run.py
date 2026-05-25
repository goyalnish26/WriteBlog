import logging
import os
import sys


def _quiet_werkzeug_dev_warning():
    """Flask prints a dev-server WARNING to stderr; PowerShell shows that as a red error."""
    import werkzeug.serving

    original_log = werkzeug.serving._log

    def filtered_log(type, message, *args, **kwargs):
        if type == 'warning' and 'development server' in message:
            return
        original_log(type, message, *args, **kwargs)

    werkzeug.serving._log = filtered_log


_quiet_werkzeug_dev_warning()
logging.getLogger('werkzeug').setLevel(logging.ERROR)

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))

    print(f'Starting WriteBlog at http://127.0.0.1:{port}')
    print('Press Ctrl+C to stop.\n')

    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True,
            use_reloader=False,
        )
    except OSError as exc:
        win_err = getattr(exc, 'winerror', None)
        if win_err == 10048 or exc.errno in (48, 98, 10048):
            print(f'Port {port} is already in use.')
            print('Stop the other server (Ctrl+C in that terminal), then run: python run.py')
            print(f'Or use another port:  $env:PORT=5001; python run.py')
            sys.exit(1)
        raise
