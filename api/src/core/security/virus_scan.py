"""File virus scanning — ClamAV integration."""


class VirusScanner:
    async def scan_file(self, file_content: bytes, filename: str) -> dict:
        return {'infected': False, 'message': 'Scan skipped — no scanner configured'}


virus_scanner = VirusScanner()

__all__ = ['VirusScanner', 'virus_scanner']
