"""File virus scanning — magic-byte validation + size enforcement."""

_MAX_UPLOAD_BYTES = 50 * 1024 * 1024

_RISKY_MAGIC_PATTERNS: list[tuple[bytes, str]] = [
    (b'MZ', 'Windows executable (PE)'),
    (b'\x7fELF', 'Linux executable (ELF)'),
    (b'\xca\xfe\xba\xbe', 'Java class'),
    (b'\xcf\xfa\xed\xfe', 'Mach-O (macOS)'),
    (b'\xce\xfa\xed\xfe', 'Mach-O (macOS)'),
    (b'#!/', 'Unix script (shebang)'),
    (b'#!', 'Script with shebang'),
    (b'<script', 'Embedded script tag'),
    (b'<?php', 'PHP script'),
    (b'PK\x03\x04', 'ZIP/DOCX/XLSX/PPTX/JAR archive'),
    (b'Rar!\x1a\x07', 'RAR archive'),
    (b'\x1f\x8b', 'GZip archive'),
    (b'\x42\x5a\x68', 'BZip2 archive'),
]


class VirusScanner:
    async def scan_file(self, file_content: bytes, filename: str) -> dict:
        if len(file_content) > _MAX_UPLOAD_BYTES:
            return {'infected': True, 'message': f'File exceeds {_MAX_UPLOAD_BYTES // (1024*1024)} MB limit'}

        if len(file_content) < 4:
            return {'infected': False, 'message': 'File too small for magic-byte scan'}

        for sig, desc in _RISKY_MAGIC_PATTERNS:
            if file_content[:len(sig)] == sig:
                safe_extensions = {'.zip', '.docx', '.xlsx', '.pptx', '.jar', '.gz', '.bz2', '.epub', '.odt', '.ods', '.odp'}
                ext = (filename or '').rsplit('.', 1)[-1].lower() if '.' in (filename or '') else ''
                full_ext = f'.{ext}' if ext else ''
                if full_ext not in safe_extensions:
                    return {'infected': True, 'message': f'Blocked by magic-byte check: {desc}'}

        return {'infected': False, 'message': 'Magic-byte scan passed'}


virus_scanner = VirusScanner()

__all__ = ['VirusScanner', 'virus_scanner']
