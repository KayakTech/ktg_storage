##

# `ktg_storage` Installation & Usage

## Installation

To install or upgrade the latest version:

```bash
pip install git+https://github.com/KayakTech/ktg_storage.git
```

### Specific Branch Installation

To install from a specific branch:

```bash
pip install git+https://github.com/KayakTech/ktg_storage.git@branch_name

```

# To Uninstall

```bash
pip uninstall ktg_storage
```

## Usage

```python
from ktg_storage.models import Storage



# THIS SEEETING MUST BE IN THE settings.py file

AWS_ACCESS_KEY_ID = "q4f24ebdtbe'wrg"
AWS_SECRET_ACCESS_KEY = '2423f3g34422'
AWS_S3_REGION_NAME = "eu-west-3"
AWS_STORAGE_BUCKET_NAME = name_of_bucket
AWS_DEFAULT_ACL='public-read'
AWS_PRESIGNED_EXPIRY = 10
FILE_MAX_SIZE = 10000
ALLOW_AUTHENTICATION = True
FILE_UPLOAD_STORAGE =  s3
MEDIA_LOCATION "media"

APP_DOMAIN = "localhost"
IS_USING_LOCAL_STORAGE = FILE_UPLOAD_STORAGE == "local"


FILE_MAX_SIZE = 1024
FILE_UPLOAD_STORAGE =s3

IS_USING_LOCAL_STORAGE = FILE_UPLOAD_STORAGE == "local"


# Use the client as needed
```

---
