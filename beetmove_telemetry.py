import argparse
import os
import requests
import zipfile

ZIP_MAX_SIZE_IN_MB = 1

def download_zip_archive(url, zip_path):
    # switch to asyncio
    ret = requests.get(url)

    # FIXME: switch to NamedTemporaryFile here
    with open(zip_path, 'wb') as f:
        f.write(ret.content)


def check_archive_itself(zip_path):
    zip_size = os.path.getsize(zip_path)
    zip_size_in_mb = zip_size // (1024 * 1024)

    if zip_size_in_mb > ZIP_MAX_SIZE_IN_MB:
        raise Exception(
            f"Archive {zip_path} is too big. Max accepted size (in MB): {zip_size_in_mb}"
        )

    if not zipfile.is_zipfile(zip_path):
        raise Exception(
            f"Archive {zip_path} is not a valid zip file"
        )


def _fetch_zip_metadata(zip_file):
    return {
        info.filename: {
            'compress_size': info.compress_size,
            'file_size': info.file_size,
        }
        for info in zip_file.infolist() if not info.is_dir()
    }


def extract_and_check_output_files(zip_file, relative_paths_in_archive):
    zip_path = zip_file.filename
    if not os.path.isabs(zip_path):
        raise Exception(f'Archive {zip_path} is not absolute path')

    extract_to = '{}.out'.format(zip_path)
    expected_full_paths_per_relative_path = {
        path_in_archive: os.path.join(extract_to, path_in_archive)
        for path_in_archive in relative_paths_in_archive
    }
    zip_file.extractall(extract_to)
    return expected_full_paths_per_relative_path


def check_extract_and_delete_zip_archive(zip_path):
    # sanity check the archive itself
    check_archive_itself(zip_path)

    with zipfile.ZipFile(zip_path) as zip_file:
        zip_metadata = _fetch_zip_metadata(zip_file)
        relative_paths_in_archive = list(zip_metadata.keys())

        # TODO: add ensure_files_in_archive_have_decent_sizes
        # TODO: ensure_all_expected_files_are_present_in_archive

        extracted_files = extract_and_check_output_files(zip_file, relative_paths_in_archive)
    # TODO: to uncomment this to remove the archive in the end
    # os.remove(zip_path)
    return extracted_files


def main(release_url, zip_path):
    # download the release archive from Github
    download_zip_archive(release_url, zip_path)

    # explode zip archive
    check_extract_and_delete_zip_archive(zip_path)

    # transfer files to S3


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Telemetry upload')
    parser.add_argument('--release-url', dest='release_url',
                        action='store', required=True)

    args = parser.parse_args()
    if not args.release_url:
        exit(1)

    zip_path = '/tmp/target.zip'
    main(args.release_url, zip_path)