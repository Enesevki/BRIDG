# games/security.py

import os
import re
import math
import zipfile
import logging
from pathlib import Path
from collections import Counter
from django.core.exceptions import ValidationError
from django.conf import settings

logger = logging.getLogger(__name__)

# =============================================================================
# File Upload Security Configuration
# =============================================================================

# Allowed file types (MIME types)
ALLOWED_MIME_TYPES = {
    'application/zip',
    'application/x-zip-compressed',
    'application/x-zip',
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.zip'}

# Dangerous file extensions (blocked inside ZIP)
DANGEROUS_EXTENSIONS = {
    # Executables
    '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.vb', '.jar',
    '.msi', '.dll', '.sys', '.app', '.deb', '.rpm', '.dmg', '.pkg',
    
    # Scripts (excluding .js for WebGL games)
    '.sh', '.bash', '.zsh', '.ps1', '.psm1', '.psd1', '.php', '.asp', '.aspx',
    '.jsp', '.pl', '.py', '.rb', '.lua', '.tcl',
    
    # Archives (nested archives)
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz',
    
    # Documents with macros
    '.doc', '.docm', '.xls', '.xlsm', '.ppt', '.pptm',
    
    # Note: .js files are allowed for WebGL games but will be content-scanned
}

# Unity WebGL whitelist patterns - these are safe Unity patterns
UNITY_WEBGL_SAFE_PATTERNS = [
    # Unity loader.js specific patterns that are safe
    rb'unityFramework\s*=',
    rb'Module\[.*\]\s*=.*unityLoader',
    rb'UnityLoader\.instantiate',
    rb'createUnityInstance',
    rb'gameInstance\s*=.*createUnityInstance',
    rb'HEAP8\s*=\s*new Int8Array',
    rb'HEAPU8\s*=\s*new Uint8Array',
    rb'Unity WebGL Player',
    rb'buildUrl\s*\+\s*.*\.wasm',
    rb'companyName\s*:\s*.*productName\s*:',
    rb'unity-container',
    rb'#unity-canvas',
]

# Suspicious file patterns (more specific now)
DANGEROUS_PATTERNS = [
    # Clearly malicious patterns (not Unity-related)
    rb'<script[^>]*src=["\']https?://(?!localhost|127\.0\.0\.1)[^"\']*(?:evil|malware|virus)[^"\']*',  # External malicious scripts
    rb'javascript:.*[;,].*(?:system|shell|cmd|exec)\s*\(',  # JavaScript with system calls
    rb'vbscript:',
    rb'onload\s*=.*(?:system|shell|cmd|exec)\s*\(',        # Dangerous onload handlers
    rb'onerror\s*=.*(?:system|shell|cmd|exec)\s*\(',       # Dangerous onerror handlers
    
    # Server-side code
    rb'<\?php',
    rb'<%@\s*page',
    rb'<%\s*eval',
    
    # Clearly malicious shell commands
    rb'system\s*\(\s*["\'].*(?:rm\s+-rf|del\s+/q|format)',  # Destructive commands
    rb'exec\s*\(\s*["\'].*(?:rm\s+-rf|del\s+/q|format)',   # Destructive commands
    rb'cmd\.exe.*(?:del|format|rd)',
    rb'/bin/(?:sh|bash).*(?:rm\s+-rf)',
    
    # SQL injection patterns
    rb'DROP\s+TABLE',
    rb'DELETE\s+FROM.*WHERE.*1\s*=\s*1',
    rb'UNION\s+SELECT.*FROM',
    
    # Dangerous decoders
    rb'base64_decode\s*\(',
    rb'eval\s*\(\s*atob\s*\(',     # eval(atob()) - base64 decode + eval
    
    # External malicious URLs (not local/CDN)
    rb'src\s*=\s*["\']https?://(?!(?:cdn\.|assets\.|static\.)[a-zA-Z0-9.-]+|localhost|127\.0\.0\.1)[^"\']*\.(?:exe|bat|scr|vbs)',
]

# File size limits
MAX_FILE_SIZE = getattr(settings, 'MAX_GAME_ZIP_SIZE_MB', 50) * 1024 * 1024  # 50MB default
MAX_FILES_IN_ZIP = 1000  # Maximum files in ZIP
MAX_FILENAME_LENGTH = 255
MAX_TOTAL_EXTRACTED_SIZE = MAX_FILE_SIZE * 3  # 150MB max extracted

# =============================================================================
# WebGL Validation Classes
# =============================================================================

class WebGLStructureValidator:
    """Validates Unity WebGL game structure"""
    
    def __init__(self, zip_file):
        self.zip_file = zip_file
        self.file_list = [f.filename for f in zip_file.infolist() if not f.is_dir()]
        self.issues = []
    
    def validate(self):
        """Validate WebGL game structure"""
        self._check_required_files()
        self._check_structure_patterns()
        
        if self.issues:
            raise FileSecurityError(f"WebGL structure validation failed: {'; '.join(self.issues)}")
    
    def _check_required_files(self):
        """Check for required WebGL files"""
        # Check for index.html (can be in root or Build folder)
        index_files = [f for f in self.file_list if f.lower().endswith('index.html')]
        
        if not index_files:
            self.issues.append("Missing index.html - WebGL games require an HTML entry point")
            return
        
        # Check for Unity build files
        has_loader = any('loader.js' in f.lower() for f in self.file_list)
        has_wasm = any(f.lower().endswith('.wasm') or f.lower().endswith('.wasm.br') for f in self.file_list)
        has_data = any(f.lower().endswith('.data') or f.lower().endswith('.data.br') for f in self.file_list)
        
        if not has_loader:
            self.issues.append("Missing Unity loader.js file")
        
        if not (has_wasm or has_data):
            self.issues.append("Missing Unity runtime files (.wasm or .data files)")
    
    def _check_structure_patterns(self):
        """Check for valid WebGL structure patterns"""
        # Pattern 1: Files in root (Build/, TemplateData/, index.html)
        # Pattern 2: Files in subfolder (SomeFolder/Build/, SomeFolder/TemplateData/, SomeFolder/index.html)
        
        build_folders = [f for f in self.file_list if '/build/' in f.lower() or f.lower().startswith('build/')]
        template_folders = [f for f in self.file_list if '/templatedata/' in f.lower() or f.lower().startswith('templatedata/')]
        
        # At least one structure should exist
        if not build_folders and not template_folders:
            # Maybe it's a custom structure, check for Unity files
            unity_files = [f for f in self.file_list if any(pattern in f.lower() for pattern in ['loader.js', '.wasm', '.data', 'unity'])]
            if not unity_files:
                self.issues.append("No Unity WebGL structure detected (missing Build/ or TemplateData/ folders)")


# =============================================================================
# File Validation Classes
# =============================================================================

class FileSecurityError(ValidationError):
    """Custom exception for file security violations"""
    pass


class FileTypeValidator:
    """Validates file types using multiple methods"""
    
    @staticmethod
    def validate_extension(filename):
        """Check file extension"""
        file_ext = Path(filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise FileSecurityError(f"File extension '{file_ext}' not allowed. Only .zip files are permitted.")
    
    @staticmethod
    def validate_mime_type(file):
        """Check MIME type using python-magic fallback"""
        try:
            # Try to get MIME type from uploaded file
            import magic
            
            # Read first chunk to determine type
            file.seek(0)
            first_chunk = file.read(1024)
            file.seek(0)
            
            mime_type = magic.from_buffer(first_chunk, mime=True)
            
            if mime_type not in ALLOWED_MIME_TYPES:
                raise FileSecurityError(f"File type '{mime_type}' not allowed. Only ZIP files are permitted.")
                
        except ImportError:
            # Fallback: Check magic bytes manually
            FileTypeValidator._validate_zip_magic_bytes(file)
    
    @staticmethod
    def _validate_zip_magic_bytes(file):
        """Fallback ZIP validation using magic bytes"""
        file.seek(0)
        header = file.read(4)
        file.seek(0)
        
        # ZIP file signatures
        zip_signatures = [
            b'PK\x03\x04',  # Standard ZIP
            b'PK\x05\x06',  # Empty ZIP
            b'PK\x07\x08',  # Spanned ZIP
        ]
        
        if not any(header.startswith(sig) for sig in zip_signatures):
            raise FileSecurityError("File is not a valid ZIP archive.")


class ZipSecurityAnalyzer:
    """Analyzes ZIP file contents for security threats"""
    
    def __init__(self, zip_path):
        self.zip_path = zip_path
        self.threats_found = []
        self.total_extracted_size = 0
        self.file_count = 0
    
    def analyze(self):
        """Perform comprehensive ZIP security analysis"""
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_file:
                # First validate WebGL structure
                webgl_validator = WebGLStructureValidator(zip_file)
                webgl_validator.validate()
                
                # Then check security
                self._check_zip_structure(zip_file)
                self._scan_file_contents(zip_file)
                self._check_compression_bomb(zip_file)
                
        except zipfile.BadZipFile:
            raise FileSecurityError("Corrupted or invalid ZIP file.")
        except FileSecurityError:
            raise  # Re-raise WebGL and security errors
        except Exception as e:
            logger.error(f"ZIP analysis error: {e}")
            raise FileSecurityError(f"Failed to analyze ZIP file: {str(e)}")
        
        if self.threats_found:
            threat_summary = "; ".join(self.threats_found)
            raise FileSecurityError(f"Security threats detected: {threat_summary}")
    
    def _check_zip_structure(self, zip_file):
        """Check ZIP file structure and file paths"""
        self.file_count = len(zip_file.infolist())
        
        if self.file_count > MAX_FILES_IN_ZIP:
            self.threats_found.append(f"Too many files ({self.file_count} > {MAX_FILES_IN_ZIP})")
        
        for file_info in zip_file.infolist():
            filename = file_info.filename
            
            # Skip __MACOSX folders (Mac metadata - harmless)
            if '__MACOSX' in filename or filename.startswith('._'):
                continue
            
            # Check for path traversal
            if '../' in filename or '..\\' in filename:
                self.threats_found.append(f"Path traversal attempt: {filename}")
            
            # Check for absolute paths
            if filename.startswith('/') or (len(filename) > 1 and filename[1] == ':'):
                self.threats_found.append(f"Absolute path not allowed: {filename}")
            
            # Check filename length
            if len(filename) > MAX_FILENAME_LENGTH:
                self.threats_found.append(f"Filename too long: {filename[:50]}...")
            
            # Check for dangerous extensions
            file_ext = Path(filename).suffix.lower()
            if file_ext in DANGEROUS_EXTENSIONS:
                self.threats_found.append(f"Dangerous file type: {filename}")
            
            # Check for suspicious hidden files (but allow common ones)
            if filename.startswith('.') and file_ext not in {'.html', '.css', '.js', '.json', '.txt', '.gitignore', '.htaccess'}:
                # Skip Mac metadata files
                if not filename.startswith('._'):
                    self.threats_found.append(f"Suspicious hidden file: {filename}")
    
    def _scan_file_contents(self, zip_file):
        """Scan file contents for malicious patterns (improved for Unity)"""
        for file_info in zip_file.infolist():
            if file_info.is_dir():
                continue
            
            # Skip __MACOSX files
            if '__MACOSX' in file_info.filename or file_info.filename.startswith('._'):
                continue
            
            try:
                # Only scan text-like files to avoid false positives
                filename = file_info.filename.lower()
                scannable_extensions = {'.html', '.css', '.js', '.json', '.txt', '.xml', '.svg'}
                
                if not any(filename.endswith(ext) for ext in scannable_extensions):
                    continue
                
                # Read file content
                with zip_file.open(file_info) as f:
                    # Only read first 64KB to avoid memory issues
                    content = f.read(65536)
                    
                    # Special handling for Unity loader.js files
                    if 'loader.js' in filename:
                        # Check if it's a genuine Unity loader by looking for Unity patterns
                        is_unity_loader = any(re.search(pattern, content, re.IGNORECASE) for pattern in UNITY_WEBGL_SAFE_PATTERNS)
                        
                        if is_unity_loader:
                            # Skip dangerous pattern check for Unity loaders
                            logger.debug(f"Unity loader.js detected and whitelisted: {file_info.filename}")
                            continue
                    
                    # Check for dangerous patterns
                    for pattern in DANGEROUS_PATTERNS:
                        if re.search(pattern, content, re.IGNORECASE):
                            self.threats_found.append(f"Suspicious content in {file_info.filename}")
                            break
                    
                    # Check file entropy (possible encryption/obfuscation) - but be lenient for .js files
                    if len(content) > 1024:  # Only for files > 1KB
                        entropy = self._calculate_entropy(content)
                        # Higher threshold for .js files (Unity can be complex)
                        threshold = 8.0 if filename.endswith('.js') else 7.5
                        if entropy > threshold:
                            self.threats_found.append(f"High entropy file (possible encryption): {file_info.filename}")
            
            except Exception as e:
                logger.warning(f"Failed to scan {file_info.filename}: {e}")
                # Don't fail the entire upload for individual file scan errors
    
    def _check_compression_bomb(self, zip_file):
        """Check for ZIP bombs (excessive compression ratio)"""
        for file_info in zip_file.infolist():
            if file_info.is_dir():
                continue
            
            # Skip __MACOSX files
            if '__MACOSX' in file_info.filename:
                continue
            
            compressed_size = file_info.compress_size
            uncompressed_size = file_info.file_size
            
            # Check individual file expansion ratio (more lenient for Unity files)
            if compressed_size > 0:
                ratio = uncompressed_size / compressed_size
                # Unity .wasm and .data files can have high compression ratios
                max_ratio = 1000 if any(ext in file_info.filename.lower() for ext in ['.wasm', '.data', '.br']) else 100
                if ratio > max_ratio:
                    self.threats_found.append(f"Suspicious compression ratio in {file_info.filename}")
            
            self.total_extracted_size += uncompressed_size
        
        # Check total extracted size
        if self.total_extracted_size > MAX_TOTAL_EXTRACTED_SIZE:
            self.threats_found.append(f"Total extracted size too large ({self.total_extracted_size} bytes)")
    
    @staticmethod
    def _calculate_entropy(data):
        """Calculate Shannon entropy of data"""
        if len(data) == 0:
            return 0
        
        # Count byte frequencies
        byte_counts = Counter(data)
        data_len = len(data)
        
        # Calculate entropy
        entropy = 0
        for count in byte_counts.values():
            p = count / data_len
            if p > 0:
                entropy -= p * math.log2(p)
        
        return entropy


class FileNameSanitizer:
    """Sanitizes and validates file names"""
    
    # Dangerous characters in filenames
    DANGEROUS_CHARS = r'[<>:"/\\|?*\x00-\x1f]'
    
    # Reserved names (Windows)
    RESERVED_NAMES = {
        'con', 'prn', 'aux', 'nul',
        'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
        'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
    }
    
    @classmethod
    def sanitize_filename(cls, filename):
        """Sanitize filename for safe storage"""
        if not filename:
            raise FileSecurityError("Filename cannot be empty")
        
        # Remove dangerous characters
        sanitized = re.sub(cls.DANGEROUS_CHARS, '_', filename)
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Check for reserved names
        name_without_ext = Path(sanitized).stem.lower()
        if name_without_ext in cls.RESERVED_NAMES:
            sanitized = f"file_{sanitized}"
        
        # Limit length
        if len(sanitized) > MAX_FILENAME_LENGTH:
            name, ext = os.path.splitext(sanitized)
            max_name_len = MAX_FILENAME_LENGTH - len(ext)
            sanitized = name[:max_name_len] + ext
        
        return sanitized
    
    @classmethod
    def validate_filename(cls, filename):
        """Validate filename without modification"""
        if not filename:
            raise FileSecurityError("Filename cannot be empty")
        
        # Check for dangerous characters
        if re.search(cls.DANGEROUS_CHARS, filename):
            raise FileSecurityError("Filename contains invalid characters")
        
        # Check length
        if len(filename) > MAX_FILENAME_LENGTH:
            raise FileSecurityError(f"Filename too long (max {MAX_FILENAME_LENGTH} characters)")
        
        # Check for reserved names
        name_without_ext = Path(filename).stem.lower()
        if name_without_ext in cls.RESERVED_NAMES:
            raise FileSecurityError(f"Filename '{filename}' is reserved")


# =============================================================================
# Main Security Validator
# =============================================================================

class GameFileSecurityValidator:
    """Main file security validator for game uploads"""
    
    def __init__(self, uploaded_file):
        self.uploaded_file = uploaded_file
        self.temp_path = None
    
    def validate(self):
        """Perform complete security validation"""
        try:
            # 1. File size check
            self._check_file_size()
            
            # 2. Filename validation
            filename = self.uploaded_file.name
            FileNameSanitizer.validate_filename(filename)
            FileTypeValidator.validate_extension(filename)
            
            # 3. File type validation
            FileTypeValidator.validate_mime_type(self.uploaded_file)
            
            # 4. Save temporarily for ZIP analysis
            self._save_temp_file()
            
            # 5. ZIP structure and content analysis
            analyzer = ZipSecurityAnalyzer(self.temp_path)
            analyzer.analyze()
            
            # 6. Log successful validation
            logger.info(f"File security validation passed for: {filename}")
            
        except FileSecurityError:
            raise  # Re-raise our custom errors
        except Exception as e:
            logger.error(f"Unexpected error during file validation: {e}")
            raise FileSecurityError(f"File validation failed: {str(e)}")
        finally:
            self._cleanup_temp_file()
    
    def _check_file_size(self):
        """Check if file size is within limits"""
        if self.uploaded_file.size > MAX_FILE_SIZE:
            size_mb = self.uploaded_file.size / (1024 * 1024)
            max_mb = MAX_FILE_SIZE / (1024 * 1024)
            raise FileSecurityError(f"File too large ({size_mb:.1f}MB > {max_mb}MB)")
    
    def _save_temp_file(self):
        """Save uploaded file temporarily for analysis"""
        import tempfile
        
        # Create temporary file
        fd, self.temp_path = tempfile.mkstemp(suffix='.zip')
        
        try:
            with os.fdopen(fd, 'wb') as tmp_file:
                # Reset file pointer
                self.uploaded_file.seek(0)
                
                # Copy file in chunks
                for chunk in self.uploaded_file.chunks():
                    tmp_file.write(chunk)
                
                # Reset file pointer for further use
                self.uploaded_file.seek(0)
        except Exception as e:
            os.close(fd)
            raise e
    
    def _cleanup_temp_file(self):
        """Clean up temporary file"""
        if self.temp_path and os.path.exists(self.temp_path):
            try:
                os.remove(self.temp_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {self.temp_path}: {e}")


# =============================================================================
# Utility Functions
# =============================================================================

def validate_game_upload(uploaded_file):
    """
    Main function to validate uploaded game files.
    
    Args:
        uploaded_file: Django UploadedFile object
    
    Raises:
        FileSecurityError: If file fails security validation
    """
    validator = GameFileSecurityValidator(uploaded_file)
    validator.validate()


def get_security_summary():
    """Get summary of security measures"""
    return {
        'max_file_size_mb': MAX_FILE_SIZE / (1024 * 1024),
        'allowed_extensions': list(ALLOWED_EXTENSIONS),
        'blocked_extensions': list(DANGEROUS_EXTENSIONS),
        'max_files_in_zip': MAX_FILES_IN_ZIP,
        'pattern_checks': len(DANGEROUS_PATTERNS),
        'features': [
            'File type validation',
            'ZIP structure analysis',
            'Content pattern scanning',
            'Path traversal protection',
            'Compression bomb detection',
            'Filename sanitization',
            'Entropy analysis',
        ]
    } 