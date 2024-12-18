import contextlib
import typing

from parrot_api.core import create_server

from startup import *

app = create_server(
    spec_dir=os.path.join(current_directory, './schemas/'),
    debug=app_settings['environment'] not in {'qa', 'prod'},
    app_settings=app_settings,
)
