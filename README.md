##

# `ktg_chat_sdk` Installation & Usage

## Installation

To install or upgrade the latest version:

```bash
pip install --upgrade git+https://github.com/KayakTech/ktg_chat_sdk
```

### Specific Branch Installation

To install from a specific branch:

```bash
pip install git+https://github.com/KayakTech/ktg_chat_sdk@branch_name
```

# To Uninstall

```bash
pip uninstall ktg_chat_sdk
```

## Usage

```python
from chat_sdk.ktg_chat_client import ChatClientConfig, ChatClient

TOKEN = "YOUR_ORG_TOKEN"
BASE_URL = "https://api.tuulbox.app"

# Initialize config and client
config = ChatClientConfig(BASE_URL, TOKEN)
client = ChatClient(config)

# Use the client as needed
```

# Documentation

For more detailed information, check the official documentation:

[official documentation](https://chat.tuulbox.app/docs)

---
