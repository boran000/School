from app import app, db
from models import Media, GalleryItem, Banner, Document, PopupBanner
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_directory_exists(directory):
    """Ensure that a directory exists, creating it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def fix_paths():
    with app.app_context():
        logger.info("Checking and fixing file paths...")

        # Create necessary directories if they don't exist
        upload_dirs = ['uploads', 'uploads/gallery', 'uploads/media', 'uploads/thumbnails',
                       'uploads/banners', 'uploads/documents', 'uploads/popups']

        for dir_name in upload_dirs:
            ensure_directory_exists(os.path.join(app.static_folder, dir_name))

        # Fix Media paths
        media_items = Media.query.all()
        logger.info(f"Processing {len(media_items)} media items...")

        for item in media_items:
            # Fix file_url
            if item.file_url:
                if item.video_platform in ['youtube', 'facebook']:
                    # Skip external videos
                    continue

                if item.file_url.startswith('/uploads/'):
                    static_path = os.path.join(app.static_folder, item.file_url.lstrip('/'))
                    if not os.path.exists(static_path):
                        logger.info(f"Media file not found: {static_path}")
                        # Try to determine if it's in a different location
                        filename = os.path.basename(item.file_url)
                        possible_locations = [
                            os.path.join(app.static_folder, 'uploads', 'media', filename),
                            os.path.join(app.static_folder, 'uploads', filename)
                        ]

                        for loc in possible_locations:
                            if os.path.exists(loc):
                                new_url = f"/uploads/media/{filename}" if 'media' in loc else f"/uploads/{filename}"
                                logger.info(f"Updating media URL from {item.file_url} to {new_url}")
                                item.file_url = new_url
                                break

            # Fix thumbnail_url
            if item.thumbnail_url and item.thumbnail_url.startswith('/uploads/'):
                static_path = os.path.join(app.static_folder, item.thumbnail_url.lstrip('/'))
                if not os.path.exists(static_path):
                    filename = os.path.basename(item.thumbnail_url)
                    possible_locations = [
                        os.path.join(app.static_folder, 'uploads', 'thumbnails', filename),
                        os.path.join(app.static_folder, 'uploads', filename)
                    ]

                    for loc in possible_locations:
                        if os.path.exists(loc):
                            new_url = f"/uploads/thumbnails/{filename}" if 'thumbnails' in loc else f"/uploads/{filename}"
                            logger.info(f"Updating thumbnail URL from {item.thumbnail_url} to {new_url}")
                            item.thumbnail_url = new_url
                            break

        # Fix GalleryItem paths
        gallery_items = GalleryItem.query.all()
        logger.info(f"Processing {len(gallery_items)} gallery items...")

        for item in gallery_items:
            if item.image_url:
                # First handle URLs with relative paths
                if item.image_url.startswith('/uploads/'):
                    static_path = os.path.join(app.static_folder, item.image_url.lstrip('/'))
                    if not os.path.exists(static_path):
                        filename = os.path.basename(item.image_url)
                        possible_locations = [
                            os.path.join(app.static_folder, 'uploads', 'gallery', filename),
                            os.path.join(app.static_folder, 'uploads', filename)
                        ]

                        found = False
                        for loc in possible_locations:
                            if os.path.exists(loc):
                                new_url = f"/uploads/gallery/{filename}" if 'gallery' in loc else f"/uploads/{filename}"
                                logger.info(f"Updating gallery image URL from {item.image_url} to {new_url}")
                                item.image_url = new_url
                                found = True
                                break

                        if not found:
                            logger.warning(f"Could not find image file for gallery item {item.id}: {item.title}")

                # Handle URLs without leading slash
                elif not item.image_url.startswith('http') and not item.image_url.startswith('/'):
                    # Add leading slash to make it a proper URL
                    if item.image_url.startswith('uploads/'):
                        item.image_url = f"/{item.image_url}"
                        logger.info(f"Added leading slash to URL: {item.image_url}")

                    # Check if the file exists
                    static_path = os.path.join(app.static_folder, item.image_url.lstrip('/'))
                    if not os.path.exists(static_path):
                        logger.warning(f"Image file does not exist at {static_path} for gallery item {item.id}")
                        # Try to find the file in common locations
                        filename = os.path.basename(item.image_url)
                        possible_locations = [
                            os.path.join(app.static_folder, 'uploads', 'gallery', filename),
                            os.path.join(app.static_folder, 'uploads', filename)
                        ]

                        for loc in possible_locations:
                            if os.path.exists(loc):
                                new_url = f"/uploads/gallery/{filename}" if 'gallery' in loc else f"/uploads/{filename}"
                                logger.info(f"Found and updated gallery image URL to {new_url}")
                                item.image_url = new_url
                                break

        # Fix Banner paths
        banners = Banner.query.all()
        logger.info(f"Processing {len(banners)} banners...")

        for banner in banners:
            if banner.image_url and banner.image_url.startswith('/uploads/'):
                static_path = os.path.join(app.static_folder, banner.image_url.lstrip('/'))
                if not os.path.exists(static_path):
                    filename = os.path.basename(banner.image_url)
                    possible_locations = [
                        os.path.join(app.static_folder, 'uploads', 'banners', filename),
                        os.path.join(app.static_folder, 'uploads', filename)
                    ]

                    for loc in possible_locations:
                        if os.path.exists(loc):
                            new_url = f"/uploads/banners/{filename}" if 'banners' in loc else f"/uploads/{filename}"
                            logger.info(f"Updating banner image URL from {banner.image_url} to {new_url}")
                            banner.image_url = new_url
                            break

        # Fix PopupBanner paths
        popups = PopupBanner.query.all()
        logger.info(f"Processing {len(popups)} popup banners...")

        for popup in popups:
            if popup.image_url and popup.image_url.startswith('/uploads/'):
                static_path = os.path.join(app.static_folder, popup.image_url.lstrip('/'))
                if not os.path.exists(static_path):
                    filename = os.path.basename(popup.image_url)
                    possible_locations = [
                        os.path.join(app.static_folder, 'uploads', 'popups', filename),
                        os.path.join(app.static_folder, 'uploads', filename)
                    ]

                    for loc in possible_locations:
                        if os.path.exists(loc):
                            new_url = f"/uploads/popups/{filename}" if 'popups' in loc else f"/uploads/{filename}"
                            logger.info(f"Updating popup image URL from {popup.image_url} to {new_url}")
                            popup.image_url = new_url
                            break

        # Fix Document paths
        documents = Document.query.all()
        logger.info(f"Processing {len(documents)} documents...")

        for doc in documents:
            if doc.file_url and doc.file_url.startswith('/uploads/'):
                static_path = os.path.join(app.static_folder, doc.file_url.lstrip('/'))
                if not os.path.exists(static_path):
                    filename = os.path.basename(doc.file_url)
                    possible_locations = [
                        os.path.join(app.static_folder, 'uploads', 'documents', filename),
                        os.path.join(app.static_folder, 'uploads', filename)
                    ]

                    for loc in possible_locations:
                        if os.path.exists(loc):
                            new_url = f"/uploads/documents/{filename}" if 'documents' in loc else f"/uploads/{filename}"
                            logger.info(f"Updating document URL from {doc.file_url} to {new_url}")
                            doc.file_url = new_url
                            break

        # Save changes to database
        try:
            db.session.commit()
            logger.info("File path fixes have been applied successfully!")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating database: {str(e)}")


if __name__ == "__main__":
    fix_paths()
