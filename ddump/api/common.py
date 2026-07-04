import os
import pathlib
import time

import pandas as pd

from ..common import START_SEP_END, FILE_SUFFIX


def start_end_2_name(start, end):
    """格式化start,end"""
    import datetime

    if isinstance(start, (pd.Timestamp, datetime.datetime)):
        start = f'{start:%Y%m%dT%H%M%S}'
    if isinstance(start, int):
        start = f'{start:020d}'

    if isinstance(end, (pd.Timestamp, datetime.datetime)):
        end = f'{end:%Y%m%dT%H%M%S}'
    if isinstance(end, int):
        end = f'{end:020d}'

    return f'{start}{START_SEP_END}{end}'


def is_remote_path(path) -> bool:
    return '://' in str(path)


def path_join(path, name):
    if is_remote_path(path):
        return f'{str(path).rstrip("/")}/{name}'
    return pathlib.Path(path) / name


def _url_to_fs(path, storage_options=None):
    try:
        import fsspec
    except ImportError as e:
        raise ImportError('Remote paths require fsspec/s3fs: pip install ddump[s3]') from e
    if storage_options is None and str(path).startswith('s3://') and os.getenv('AWS_ENDPOINT_URL_S3'):
        storage_options = {
            'client_kwargs': {'endpoint_url': os.getenv('AWS_ENDPOINT_URL_S3')},
            'config_kwargs': {'s3': {'addressing_style': 'path'}},
        }
    return fsspec.core.url_to_fs(str(path), **(storage_options or {}))


def _mtime_from_info(info):
    mtime = info.get('LastModified') or info.get('mtime') or info.get('updated') or info.get('created')
    if hasattr(mtime, 'timestamp'):
        return mtime.timestamp()
    if mtime is None:
        return time.time()
    return float(mtime)


def path_exists(path, storage_options=None) -> bool:
    if not is_remote_path(path):
        return pathlib.Path(path).exists()
    fs, fs_path = _url_to_fs(path, storage_options)
    return fs.exists(fs_path)


def path_mtime(path, storage_options=None) -> float:
    if not is_remote_path(path):
        return pathlib.Path(path).stat().st_mtime
    fs, fs_path = _url_to_fs(path, storage_options)
    return _mtime_from_info(fs.info(fs_path))


def path_mkdir(path, storage_options=None) -> None:
    if not is_remote_path(path):
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def read_parquet(path, storage_options=None):
    if not is_remote_path(path):
        return pd.read_parquet(path)
    fs, fs_path = _url_to_fs(path, storage_options)
    with fs.open(fs_path, 'rb') as f:
        return pd.read_parquet(f)


def write_parquet(df, path, storage_options=None) -> None:
    if not is_remote_path(path):
        df.to_parquet(path, compression='zstd')
        return
    fs, fs_path = _url_to_fs(path, storage_options)
    with fs.open(fs_path, 'wb') as f:
        df.to_parquet(f, compression='zstd')


def files_to_dataframe(path, suffix=FILE_SUFFIX, storage_options=None):
    """目录中文件转DataFrame

    文件名有格式要求，用分隔符分成前后两个时间。时间为左闭右闭关系。

    Parameters
    ----------
    path: pathlib.Path
    suffix: str
        后缀

    Returns
    -------
    pd.DataFrame

    """
    if is_remote_path(path):
        fs, fs_path = _url_to_fs(path, storage_options)
        files = fs.glob(f'{fs_path.rstrip("/")}/*{suffix}')
        names = [pathlib.PurePosixPath(f).name for f in files]
        mtimes = [_mtime_from_info(fs.info(f)) for f in files]
    else:
        path = pathlib.Path(path)
        files = list(path.glob(f'*{suffix}'))
        names = [f.name for f in files]
        mtimes = [x.stat().st_mtime for x in files]

    df = pd.DataFrame([name.split('.')[0].split(START_SEP_END) for name in names], columns=['start', 'end'])
    # 结束时间
    df['end_s'] = df['end'].apply(lambda x: pd.to_datetime(x).timestamp())
    df['start'] = pd.to_datetime(df['start'])
    df['end'] = pd.to_datetime(df['end'])
    df['path'] = files
    # 文件修改时间
    df['st_mtime'] = mtimes
    # 当前时间，需要立即使用，之后再用就不准了
    df['now'] = time.time()
    return df


def timeout_mtime(path, storage_options=None) -> float:
    """检查文件超时"""
    return time.time() - path_mtime(path, storage_options)


def filter_range_in_dataframe(df, start, end, file_timeout, data_timeout):
    """检查日期是否在某一个文件中

    日期可以跨多个文件

    单日期只是两个日期的特例

    Parameters
    ----------
    df
    start
    end
    file_timeout
    data_timeout

    Returns
    -------
    bool

    """
    if df is None:
        return pd.DataFrame()
    # 找到多条记录
    df = df[(df['start'] <= end) & (start <= df['end'])]
    # 太近了表示存在
    # 太远了，也表示存在
    df = df[(df['now'] - df['st_mtime'] < file_timeout) | (df['now'] - df['end_s'] > data_timeout)]
    return df


def get_last_file(path, suffix):
    """通过最新文件的文件名得到关键参数

    Parameters
    ----------
    path
    suffix

    Returns
    -------
    dt
    id

    """
    path = pathlib.Path(path)
    files = list(path.glob(f'*{suffix}'))
    if len(files) == 0:
        return None
    return files[-1]
