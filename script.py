#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "aiohttp",
#     "boto3",
#     "requests",
# ]
# ///
""" Main script to push to maven.mozilla.org"""
import argparse
import asyncio
import aiohttp
import pathlib
import tempfile

from context import Context
from utils import (
    load_json_or_yaml, setup_mimetypes, _handle_asyncio_loop,
    upload_to_s3, raise_future_exceptions
)
from zip import (
    download_zip_archive,
    check_extract_and_delete_zip_archive,
)

CHUNK_SIZE = 1024 * 1024

MOZSEARCH_PACKAGES = [
    'semanticdb-kotlinc'
]

BASE_URL = "https://jitpack.io"
BASE_PATH = "com/github/mozsearch/semanticdb-kotlinc"


async def download_file(context, url):
    resp = await context.session.get(url)
    resp.raise_for_status()
    filename = f"{context.tmpdir}{resp.url.path}"
    pathlib.Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, 'wb') as fd:
        async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
            fd.write(chunk)
    return resp.url.path


async def download_from_index(context, url):
    headers = [("User-Agent", "curl")]
    index = await context.session.get(url, headers=headers)
    index.raise_for_status()
    files = (await index.text()).splitlines()
    downloads = []
    for f in files:
        if not f.endswith((".jar", ".pom", ".module")):
            continue
        downloads.append(download_file(context, f"{url}{f}"))
        downloads.append(download_file(context, f"{url}{f}.md5"))
        downloads.append(download_file(context, f"{url}{f}.sha1"))
    return downloads


async def download_artifacts(context):
    url = f"{BASE_URL}/{BASE_PATH}/{context.version}/"
    downloads = await download_from_index(context, url)
    for package in MOZSEARCH_PACKAGES:
        url = f"{BASE_URL}/{BASE_PATH}/{package}/{context.version}/"
        downloads += await download_from_index(context, url)
    context.extracted_files = await asyncio.gather(*downloads)


async def move_beets(context):
    """TODO"""
    uploads = []
    for path in context.extracted_files:
        local_path = f"{context.tmpdir}{path}"
        destination = f"maven2{path}"
        uploads.append(
            asyncio.ensure_future(
                upload_to_s3(context=context, s3_key=destination, path=local_path)
            )
        )

        await raise_future_exceptions(uploads)


async def async_main(context):
    """TODO"""
    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        context.session = session
        # download the artifacts from jitpack.io
        context.downloaded_files = await download_artifacts(context)
        # and upload them to maven
        await move_beets(context)


def sync_main(async_main, tmpdir, script_config,
              bucket, version, dry_run):
    """TODO"""
    context = Context()
    context.tmpdir = tmpdir
    context.bucket = bucket
    context.version = version
    context.dry_run = dry_run

    context.config = {}
    context.config.update(load_json_or_yaml(script_config, is_path=True))

    setup_mimetypes()

    asyncio.run(_handle_asyncio_loop(async_main, context))


def main():
    """TODO"""
    parser = argparse.ArgumentParser(description='semanticdb-kotlinc upload')
    parser.add_argument('--script-config', dest='script_config',
                        action='store', required=True)
    parser.add_argument('--bucket', dest='bucket',
                        action='store', required=True)
    parser.add_argument('--version', dest='version',
                        action='store', required=True)
    parser.add_argument('--dry-run', default=False,
                        action='store_true')

    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmpdir:
        sync_main(async_main, tmpdir,
                  args.script_config, args.bucket, args.version,
                  args.dry_run)


__name__ == '__main__' and main()
