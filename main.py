import os
import re
import exifread
import piexif
from datetime import datetime
from pathlib import Path
from piexif._exceptions import InvalidImageDataError

MONTHS = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December'
}

DELETE_THESE_EXTENSIONS = (
    'json',
    'ini',
    'db'
)

def organize_photos(folder_dir, output_dir=""):
    def _filename_date(file_name):
        re_dates = re.compile(r'.*((19|20)\d{2})([0|1]\d)([0-3]\d)\D?([0-2]\d)?([0-5]\d)?([0-5]\d)?.*')
        mo = re_dates.search(file_name)


        try:
            mg = mo.groups()
        except AttributeError:
            return None

        try:
            return datetime(int(mg[0]), int(mg[2]), int(mg[3]), int(mg[4]), int(mg[5]), int(mg[6]))
        except TypeError:
            pass

        try:
            return datetime(int(mg[0]), int(mg[2]), int(mg[3]), 0, 0, 0)
        except ValueError as e:
            return None

    def _photo_date(file_path):
        with open(file_path, 'rb') as fh:
            tags = exifread.process_file(fh, stop_tag="EXIF DateTimeOriginal")
            try:
                dateTaken = tags["EXIF DateTimeOriginal"]
                dateTaken = datetime.strptime(dateTaken.values, '%Y:%m:%d %H:%M:%S')
                return dateTaken

            except KeyError:
                return None

            except ValueError:
                return None

    def _update_jpeg_date(file_path, new_date):
        exif_dict = piexif.load(file_path)
        exif_dict['Exif'] = {piexif.ExifIFD.DateTimeOriginal: new_date.strftime('%Y:%m:%d %H:%M:%S')}
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, file_path)

    def disneyland_resort_photo(file_name):
        dlr_file_names = [
            'dca_',
            'dlpca_',
            'pixiehallow',
            'plazainn'
            'wdw'
        ]
        for dlr_file_name in dlr_file_names:
            if dlr_file_name in file_name.lower():
                return True
        return False

    if len(output_dir) == 0:
        output_dir = folder_dir

    for folder_name, subfolders, file_names in os.walk(folder_dir):
        for file_name in file_names:
            full_path = os.path.join(folder_name, file_name)
            file_name, file_extension = os.path.splitext(file_name.lower())
            if file_extension == '.jpeg':
                file_extension = '.jpg'

            filename_date = _filename_date(file_name)
            photo_date = _photo_date(full_path)

            if file_extension[1:] in DELETE_THESE_EXTENSIONS:
                os.remove(full_path)
                print(f'Deleted file:\n\t{full_path}\n')
                continue

            elif "screenshot" in file_name:
                new_dir = os.path.join(output_dir, 'screenshots')
                new_filename = file_name

            elif 'fb_img' in file_name:
                new_dir = os.path.join(output_dir, 'facebook')
                new_filename = file_name

            elif 'snapchat' in file_name:
                new_dir = os.path.join(output_dir, 'gif')
                new_filename = file_name

            elif 'received' in file_name:
                new_dir = os.path.join(output_dir, 'received')
                new_filename = file_name

            elif disneyland_resort_photo(file_name):

                if photo_date is None:
                    use_date = filename_date
                else:
                    use_date = photo_date

                year = use_date.strftime('%Y')
                month = int(use_date.strftime('%m'))
                month = f'{month:0>2d} - {MONTHS[month]}'

                new_dir = os.path.join(output_dir, year, month, 'Disneyland Resort Photopass')
                photo_location = '_'.join(file_name.split("_")[:2]).upper()
                new_filename = f"{use_date.strftime('%Y%m%d_%H%M%S')}_{photo_location}"

            elif filename_date is not None:
                year = filename_date.strftime('%Y')
                month = int(filename_date.strftime('%m'))
                month = f'{month:0>2d} - {MONTHS[month]}'

                new_dir = os.path.join(output_dir, year)
                if 'school photo' in file_name:
                    new_filename = f'{year} School Photo'

                else:
                    new_filename = filename_date.strftime('%Y%m%d_%H%M%S')
                    new_dir = os.path.join(new_dir, month)



                try:
                    dates_dont_match = photo_date.date() != filename_date.date()
                except AttributeError:
                    dates_dont_match = True

                if dates_dont_match:
                    funcs = {
                        'jpg': _update_jpeg_date,
                        'jpeg': _update_jpeg_date,
                        # 'gif': _update_jpeg_date,
                    }
                    try:
                        funcs[file_extension[1:]](full_path, filename_date)

                    except KeyError:
                        new_dir = os.path.join(output_dir, file_extension[1:], year, month)
                        # new_filename = file_name

                    except InvalidImageDataError:
                        # possible corrupted image
                        new_dir = os.path.join(output_dir, 'Possible Corrupted files', year, month)
                        # new_filename = file_name

            elif photo_date is not None:
                year = photo_date.strftime('%Y')
                month = int(photo_date.strftime('%m'))
                month = f'{month:0>2d} - {MONTHS[month]}'

                new_dir = os.path.join(output_dir, year, month)
                new_filename = photo_date.strftime('%Y%m%d_%H%M%S')

            else:
                new_dir = os.path.join(output_dir, 'unknown', os.path.basename(folder_name))
                new_filename = file_name

            if not os.path.exists(full_path):
                continue


            # Move File
            Path(new_dir).mkdir(parents=True, exist_ok=True)
            new_path = os.path.join(new_dir, f'{new_filename}{file_extension}')

            i = 1
            while os.path.exists(new_path):
                i += 1
                new_path = os.path.join(new_dir, f'{new_filename}_{i:0>3d}{file_extension}')

            print(f'{full_path:<80}\t->\t{new_path}')
            assert not os.path.exists(new_path)
            os.rename(full_path, new_path)

        else:
            try:
                os.rmdir(folder_name)
                print(f'Removed Empty Folder:\n\t{folder_name}\n')
            except OSError as e:
                if e.args[1] == 'The directory is not empty':
                    pass
                elif e.args[1] == 'Access is denied':
                    pass
                else:
                    raise e

    else:
        for folder_name, subfolders, file_names in os.walk(folder_dir):
            try:
                os.rmdir(folder_name)
                print(f'Removed Empty Folder:\n\t{folder_name}\n')
            except OSError as e:
                if e.args[1] == 'The directory is not empty':
                    pass
                else:
                    raise e


if __name__ == '__main__':
    current_folder = r'F:\Pictures\unknown\Scanned'
    output_folder = r"F:\Pictures"
    organize_photos(current_folder, output_folder)
