import os
import logging
from app import app, db
from models import GalleryItem, GalleryCategory, Media
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_gallery_paths():
    with app.app_context():
        # Fix GalleryItem paths
        items = GalleryItem.query.all()
        logger.info(f"Found {len(items)} gallery items to process")

        for item in items:
            if not item.image_url.startswith('/uploads/gallery/') and not item.image_url.startswith('http'):
                logger.info(f"Processing item {item.id}: {item.title}")

                # Get category
                category = GalleryCategory.query.get(item.category_id)
                if not category:
                    logger.warning(f"No category found for item {item.id}")
                    continue

                folder_name = secure_filename(category.name.lower().replace(' ', '_'))

                # Extract filename from existing path
                old_filename = os.path.basename(item.image_url)

                # Update path in database
                new_path = f'/uploads/gallery/{folder_name}/{old_filename}'
                logger.info(f"Updating path from {item.image_url} to {new_path}")

                # Check if the file exists
                try:
                    old_path = os.path.join(app.static_folder, item.image_url.lstrip('/'))
                    new_full_path = os.path.join(app.static_folder, 'uploads/gallery', folder_name)

                    # Create folder if it doesn't exist
                    os.makedirs(new_full_path, exist_ok=True)

                    # Move file if it exists
                    if os.path.exists(old_path):
                        new_file_path = os.path.join(new_full_path, old_filename)
                        try:
                            os.rename(old_path, new_file_path)
                            logger.info(f"Moved file from {old_path} to {new_file_path}")
                        except Exception as e:
                            logger.error(f"Error moving file: {str(e)}")

                    # Update database
                    item.image_url = new_path
                    db.session.commit()
                    logger.info(f"Updated database record for item {item.id}")

                except Exception as e:
                    logger.error(f"Error processing item {item.id}: {str(e)}")
                    db.session.rollback()

        # Fix Media paths
        media_items = Media.query.all()
        logger.info(f"Found {len(media_items)} media items to process")

        for media in media_items:
            if (media.file_url.startswith('/uploads/media/') and '/' not in media.file_url.replace('/uploads/media/',
                                                                                                   '')) or \
                    (media.thumbnail_url and media.thumbnail_url.startswith(
                        '/uploads/thumbnails/') and '/' not in media.thumbnail_url.replace('/uploads/thumbnails/', '')):

                logger.info(f"Processing media {media.id}: {media.title}")

                # Get category or use 'other' if not set
                category_name = media.gallery_category or 'other'
                folder_name = secure_filename(category_name.lower().replace(' ', '_'))

                # Update file_url
                if media.file_url and media.file_url.startswith('/uploads/media/'):
                    old_filename = os.path.basename(media.file_url)
                    new_path = f'/uploads/media/{folder_name}/{old_filename}'

                    # Move file if it exists
                    try:
                        old_path = os.path.join(app.static_folder, media.file_url.lstrip('/'))
                        new_full_path = os.path.join(app.static_folder, 'uploads/media', folder_name)

                        # Create folder if it doesn't exist
                        os.makedirs(new_full_path, exist_ok=True)

                        if os.path.exists(old_path):
                            new_file_path = os.path.join(new_full_path, old_filename)
                            try:
                                os.rename(old_path, new_file_path)
                                logger.info(f"Moved file from {old_path} to {new_file_path}")
                            except Exception as e:
                                logger.error(f"Error moving file: {str(e)}")

                        media.file_url = new_path
                        logger.info(f"Updated file_url from {media.file_url} to {new_path}")
                    except Exception as e:
                        logger.error(f"Error updating file_url for media {media.id}: {str(e)}")

                # Update thumbnail_url
                if media.thumbnail_url and media.thumbnail_url.startswith('/uploads/thumbnails/'):
                    old_thumb_filename = os.path.basename(media.thumbnail_url)
                    new_thumb_path = f'/uploads/thumbnails/{folder_name}/{old_thumb_filename}'

                    # Move file if it exists
                    try:
                        old_thumb_path = os.path.join(app.static_folder, media.thumbnail_url.lstrip('/'))
                        new_thumb_full_path = os.path.join(app.static_folder, 'uploads/thumbnails', folder_name)

                        # Create folder if it doesn't exist
                        os.makedirs(new_thumb_full_path, exist_ok=True)

                        if os.path.exists(old_thumb_path):
                            new_thumb_file_path = os.path.join(new_thumb_full_path, old_thumb_filename)
                            try:
                                os.rename(old_thumb_path, new_thumb_file_path)
                                logger.info(f"Moved thumbnail from {old_thumb_path} to {new_thumb_file_path}")
                            except Exception as e:
                                logger.error(f"Error moving thumbnail: {str(e)}")

                        media.thumbnail_url = new_thumb_path
                        logger.info(f"Updated thumbnail_url from {media.thumbnail_url} to {new_thumb_path}")
                    except Exception as e:
                        logger.error(f"Error updating thumbnail_url for media {media.id}: {str(e)}")

                # Commit changes
                try:
                    db.session.commit()
                    logger.info(f"Updated database record for media {media.id}")
                except Exception as e:
                    logger.error(f"Error committing changes for media {media.id}: {str(e)}")
                    db.session.rollback()


if __name__ == "__main__":
    logger.info("Starting gallery path fixing script")
    fix_gallery_paths()
    logger.info("Completed gallery path fixing")
