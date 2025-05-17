from PyQt5.QtCore import QThread, pyqtSignal
from PIL import Image, ImageOps
import piexif
import os
import concurrent.futures

from .utils import calculate_dimensions


class ProcessWorker(QThread):
    """Thread worker that processes a list of images."""

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str, str)

    def __init__(self, images, output_dir, settings):
        super().__init__()
        self.images = images
        self.output_dir = output_dir
        self.settings = settings
        self.should_stop = False

    def run(self):
        errors = []
        try:
            # Ensure at least one worker to avoid ThreadPoolExecutor ValueError
            max_workers = max(1, min(os.cpu_count() or 1, len(self.images)))

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for i, image_path in enumerate(self.images):
                    if self.should_stop:
                        break
                    future = executor.submit(
                        self.process_single_image,
                        image_path,
                        i,
                        len(self.images),
                    )
                    futures.append(future)

                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    if self.should_stop:
                        break
                    try:
                        error = future.result()
                        if error:
                            errors.append(error)
                    except Exception as e:
                        errors.append(f"Unexpected error: {str(e)}")
                    self.progress.emit(i + 1, f"Processed {i + 1} of {len(self.images)} images")

        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
        finally:
            self.finished.emit(errors)

    def process_single_image(self, image_path, index, total):
        try:
            if self.should_stop:
                return None
            base_filename = self.settings['base_filename']
            aspect_ratio = self.settings['aspect_ratio']
            border_size = self.settings['border_size']
            save_format = self.settings['save_format']
            quality = self.settings['quality']
            preserve_metadata = self.settings['preserve_metadata']
            border_color = self.settings['border_color']

            with Image.open(image_path) as img:
                icc_profile = img.info.get('icc_profile')

                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, border_color)
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[3])
                    else:
                        background.paste(img, mask=img.split()[1])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                orig_width, orig_height = img.size
                target_width, target_height = calculate_dimensions(
                    orig_width, orig_height, border_size, aspect_ratio
                )

                if border_size > 0:
                    img = ImageOps.expand(img, border=border_size, fill=border_color)

                current_width, current_height = img.size
                if (target_width, target_height) != (current_width, current_height):
                    result = Image.new('RGB', (target_width, target_height), border_color)
                    paste_x = (target_width - current_width) // 2
                    paste_y = (target_height - current_height) // 2
                    result.paste(img, (paste_x, paste_y))
                else:
                    result = img

                if base_filename:
                    if total > 1:
                        base_name = f"{base_filename}_{index+1}"
                    else:
                        base_name = base_filename
                else:
                    original_name = os.path.basename(image_path)
                    base_name = os.path.splitext(original_name)[0] + "_processed"

                if save_format == "JPEG":
                    ext = ".jpg"
                elif save_format == "TIFF":
                    ext = ".tiff"
                elif save_format == "PNG":
                    ext = ".png"
                else:
                    ext = ".heif"

                output_path = os.path.join(self.output_dir, base_name + ext)

                exif_bytes = None
                if preserve_metadata:
                    try:
                        exif_dict = piexif.load(image_path)
                        gps_dict = exif_dict.get('GPS', {})
                        new_exif = {'GPS': gps_dict}
                        exif_bytes = piexif.dump(new_exif)
                    except Exception:
                        pass

                save_args = {'format': save_format}
                if icc_profile:
                    save_args['icc_profile'] = icc_profile

                if save_format == "JPEG":
                    save_args.update({
                        'quality': quality,
                        'exif': exif_bytes,
                        'optimize': True,
                        'subsampling': 0,
                    })
                elif save_format == "HEIF":
                    save_args.update({'quality': quality})
                elif save_format == "PNG":
                    save_args.update({'optimize': True})

                result.save(output_path, **save_args)

                return None

        except Exception as e:
            return f"Error processing {os.path.basename(image_path)}: {str(e)}"

    def stop(self):
        self.should_stop = True
