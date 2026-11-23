from pathlib import Path
from urllib.parse import urlsplit
import cv2

#Required extensions and its image size bytes
ALLOWED_IMAGE_EXTENSIONS={".png",".jpg",".jpeg",".bmp",".webp"}
MAX_IMAGE_SIZE_BYTES=10*1024*1024          #10 MB

#URL Validation
def _is_http_url(value:str)->bool:                  #It will return True or False
    if not value or value!=value.strip() or any(ch.isspace() for ch in value):
        return False
    try:
        parsed=urlsplit(value)
        if parsed.scheme.lower() not in {"http", "https"}:
            return False
        if not parsed.hostname:
            return False
        if parsed.port is not None and not (1<parsed.port<=65535):
            return False
        if parsed.username is not None or parsed.password is not None:
            return False
        return True
    except Exception:
        return False
def decode_qr_code(image_path:str)->dict:
    '''It will decode a qrcode from an image file
    Returns a dictionary that are containing
    success, decoded_text, url, is_url, and its message'''
    if not isinstance(image_path,(str,Path)) or not str(image_path).strip():
        return {
            "success": False, "decoded_text": None, "url": None,
            "is_url": False, "message": "Please provide the valid image file path."
        }
    path=Path(image_path).expanduser()           #Stores the image file actual path
    if not path.exists() or not path.is_file():
        return {
            "success": False, "decoded_text": None, "url": None,
            "is_url": False, "message": "Image file was not found."
        }
    if path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        return {
            "success": False, "decoded_text": None, "url": None,
            "is_url": False, "message": "Unsupported image file extensions. Use .png,.jpg,.jpeg,.bmp,.webp format..."
        }
    try:
        if path.stat().st_size>MAX_IMAGE_SIZE_BYTES:
            return {
                "success": False, "decoded_text": None, "url": None,
                "is_url": False, "message": "The Image is too large to support. Maximum size allowed is 10 MB."
            }
        image=cv2.imread(str(path),cv2.IMREAD_COLOR)
        if image is None:
            return {
                "success": False, "decoded_text": None, "url": None,
                "is_url": False, "message": "The image couldn't be read. Please double check that it is valid image or not"
            }
        detector=cv2.QRCodeDetector()
        decoded_text,points,_=detector.detectAndDecode(image)
        if not decoded_text:
            return {
                "success": False, "decoded_text": None, "url": None,
                "is_url": False, "message": "No readable QRCode is found in the image."
            }
        decoded_text=decoded_text.strip()
        is_url=_is_http_url(decoded_text)
        return {
            "success": True, "decoded_text": decoded_text, "url": decoded_text if is_url else None,
            "is_url": is_url, "message": (
                "QR code decoded successfully. URL is ready for security analysis."
                if is_url else
                "QR code decoded, but its content is not a valid HTTP/HTTPS URL."
            )
        }
    except (OSError,cv2.error) as exc:
        return {
            "success": False, "decoded_text": None, "url": None,
            "is_url": False, "message": f"Couldn't process the given QR image {exc}"
        }
if __name__=="__main__":
    enterqr=input("Enter QR Image path or Name: ")
    result=decode_qr_code(enterqr)
    print("\n===== PHISHGUARD AI QRCODE DETECTOR=====\n")
    for key,value in result.items():
        print(f"{key} : {value}")
    if result["is_url"]:
        print("\nThe extracted URL is ready for your ML/DNS analysis pipeline.")
        print("Safety reminder: The decoded URL has NOT been opened or visited.")
