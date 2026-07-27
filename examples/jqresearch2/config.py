import pathlib
from pprint import pprint

from jupyter_data_fetch.auth import parse_joinquant_cookie
from jupyter_kernel_client import JupyterKernelClient

COOKIE = 'user-12345678901=2|1:0|10:1785114012|16:user-12345678901|48:NzBjNTIxYzgtMjk3Zi00NTYxLWE1NzQtNGJjZGY5NjBlOWJj|356fef5a1cd2211020b910136ebf8adeb4e1c8f3827064bc2f5450ec68f6c1ad; uid=wKgyrWpFsz1+TAXEuiVIAg==; _xsrf=2|596e71d1|ddc54c7ec6cee0b5a79f19e0191a98a3|1782953117; token=711e6ebbc9f3d7043fb9f429b14d9a9282d6e023; PHPSESSID=uhuojfninksi1gld6deo4pj023'
SERVER_URL, HEADERS, UID = parse_joinquant_cookie(COOKIE)

DATA_ROOT = pathlib.Path(r'D:\data\jqresearch')
DATA_ROOT_AKSHARE = pathlib.Path(r'D:\data\akshare')

# 未指定kernel_id时，获取!pwd是/，导致导入工作目录下库失败
with JupyterKernelClient(server_url=SERVER_URL, token=None, headers=HEADERS) as kernel:
    pprint(kernel.list_kernels())
    KERNEL_ID = kernel.list_kernels()[0]['id']
