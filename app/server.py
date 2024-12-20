from connexion import AsyncApp
from startup import current_directory
import os
app = AsyncApp(__name__)
app.add_api(specification= os.path.join(current_directory, 'schemas/v1.yaml'))
