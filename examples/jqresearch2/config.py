import pathlib
from pprint import pprint

from jupyter_data_fetch.auth import parse_joinquant_cookie
from jupyter_kernel_client import KernelClient

COOKIE = 'user-12345678901=2|1:0|10:1784880677|16:user-12345678901|48:MTY2YmVjYzctZDUwOS00ZTMyLWEwMDYtNWExMmM3YzVmYmQ0|b16b2eb1a44f0c378133df1ad8453e1e08f6fbd4c5e31b86ce760b762c0e4719; uid=wKgyrWpFsz1+TAXEuiVIAg==; _xsrf=2|596e71d1|ddc54c7ec6cee0b5a79f19e0191a98a3|1782953117; token=b91dfb5d0a450ec31ef78b0741d8726f25795565; PHPSESSID=732pgsm005e5eimo4koitaf5a0'
SERVER_URL, HEADERS, UID = parse_joinquant_cookie(COOKIE)

DATA_ROOT = pathlib.Path(r'D:\data\jqresearch')
DATA_ROOT_AKSHARE = pathlib.Path(r'D:\data\akshare')

# 未指定kernel_id时，获取!pwd是/，导致导入工作目录下库失败
with KernelClient(server_url=SERVER_URL, token=None, headers=HEADERS) as kernel:
    pprint(kernel.list_kernels())
    KERNEL_ID = kernel.list_kernels()[0]['id']
