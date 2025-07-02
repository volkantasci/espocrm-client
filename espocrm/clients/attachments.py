"""EspoCRM Attachment operasyonları client'ı.

Bu modül EspoCRM API'nin attachment (dosya) yönetimi operasyonlarını gerçekleştiren
AttachmentClient sınıfını içerir. File upload, download, validation ve bulk operations sağlar.
"""

import base64
import hashlib
import io
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, BinaryIO, Callable, Dict, List, Optional, Union
from urllib.parse import urljoin

from ..exceptions import (
    EspoCRMError, 
    EspoCRMValidationError, 
    EspoCRMConnectionError,
    EspoCRMNotFoundError
)
from ..models.attachments import (
    Attachment,
    AttachmentUploadRequest,
    AttachmentDownloadRequest,
    BulkAttachmentUploadRequest,
    FileValidationConfig,
    FileValidationError,
    SecurityValidationError,
    AttachmentRole,
    AttachmentFieldType,
    create_file_upload_request,
    create_attachment_upload_request,
    create_attachment_from_bytes
)
from ..models.responses import (
    EntityResponse,
    ListResponse,
    BulkOperationResult,
    parse_entity_response,
    parse_list_response
)
from ..utils.helpers import timing_decorator
from ..logging import get_logger


class ProgressCallback:
    """Progress tracking için callback sınıfı."""
    
    def __init__(self, callback: Optional[Callable[[int, int], None]] = None):
        """Progress callback'i başlatır.
        
        Args:
            callback: Progress callback fonksiyonu (current, total)
        """
        self.callback = callback
        self.current = 0
        self.total = 0
        self._lock = threading.Lock()
    
    def set_total(self, total: int):
        """Toplam boyutu ayarlar."""
        with self._lock:
            self.total = total
            self.current = 0
    
    def update(self, increment: int):
        """Progress'i günceller."""
        with self._lock:
            self.current += increment
            if self.callback:
                self.callback(self.current, self.total)
    
    def complete(self):
        """Progress'i tamamlar."""
        with self._lock:
            self.current = self.total
            if self.callback:
                self.callback(self.current, self.total)


class StreamingUploader:
    """Streaming file upload için sınıf."""
    
    def __init__(self, file_data: bytes, chunk_size: int = 8192):
        """Streaming uploader'ı başlatır.
        
        Args:
            file_data: Upload edilecek dosya verisi
            chunk_size: Chunk boyutu
        """
        self.file_data = file_data
        self.chunk_size = chunk_size
        self.position = 0
    
    def read(self, size: int = -1) -> bytes:
        """Dosyadan veri okur."""
        if size == -1:
            size = len(self.file_data) - self.position
        
        chunk = self.file_data[self.position:self.position + size]
        self.position += len(chunk)
        return chunk
    
    def __len__(self) -> int:
        """Dosya boyutunu döndürür."""
        return len(self.file_data)


class AttachmentClient:
    """EspoCRM Attachment operasyonları için client sınıfı.
    
    Bu sınıf EspoCRM API'nin attachment operasyonlarını sağlar:
    - File upload (File field ve Attachment-Multiple field)
    - File download
    - File validation ve security checks
    - Bulk file operations
    - Progress tracking
    - Streaming upload/download
    """
    
    def __init__(self, main_client):
        """Attachment client'ı başlatır.
        
        Args:
            main_client: Ana EspoCRM client instance'ı
        """
        self.client = main_client
        self.logger = get_logger(f"{__name__}.AttachmentClient")
        
        # Default validation config
        self.validation_config = FileValidationConfig()
        
        # Temporary file management
        self._temp_files = []
        self._temp_lock = threading.Lock()
    
    def set_validation_config(self, config: FileValidationConfig):
        """File validation konfigürasyonunu ayarlar.
        
        Args:
            config: Validation konfigürasyonu
        """
        self.validation_config = config
        self.logger.info("File validation config updated")
    
    @timing_decorator
    def upload_file(
        self,
        file_path: Union[str, Path],
        related_type: str,
        field: str = "file",
        mime_type: Optional[str] = None,
        validate: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        **kwargs
    ) -> EntityResponse:
        """File field için dosya yükler.
        
        Args:
            file_path: Yüklenecek dosya yolu
            related_type: Related entity türü (Document için)
            field: Field adı (default: "file")
            mime_type: MIME type (otomatik detect edilir)
            validate: Dosya validation yapılsın mı
            progress_callback: Progress callback fonksiyonu
            **kwargs: Ek request parametreleri
            
        Returns:
            Upload edilen attachment response'u
            
        Raises:
            FileNotFoundError: Dosya bulunamadı
            FileValidationError: Validation hatası
            SecurityValidationError: Güvenlik hatası
            EspoCRMError: API hatası
            
        Example:
            >>> response = attachment_client.upload_file(
            ...     "/path/to/document.pdf",
            ...     related_type="Document",
            ...     field="file"
            ... )
            >>> attachment_id = response.get_id()
        """
        self.logger.info(
            "Uploading file",
            file_path=str(file_path),
            related_type=related_type,
            field=field
        )
        
        try:
            # Upload request oluştur
            upload_request = create_file_upload_request(
                file_path=file_path,
                related_type=related_type,
                field=field,
                mime_type=mime_type
            )
            
            # Validation
            if validate:
                self.validation_config.validate_file(upload_request)
            
            # Progress tracking
            progress = ProgressCallback(progress_callback)
            if progress_callback:
                progress.set_total(upload_request.get_file_size())
            
            # API request
            response_data = self.client.post(
                "Attachment",
                data=upload_request.to_api_dict(),
                **kwargs
            )
            
            # Progress complete
            if progress_callback:
                progress.complete()
            
            # Response parse et
            entity_response = parse_entity_response(response_data, "Attachment")
            
            self.logger.info(
                "File uploaded successfully",
                attachment_id=entity_response.get_id(),
                file_name=upload_request.name,
                file_size=upload_request.get_file_size()
            )
            
            return entity_response
            
        except Exception as e:
            self.logger.error(
                "Failed to upload file",
                file_path=str(file_path),
                error=str(e)
            )
            raise
    
    @timing_decorator
    def upload_attachment(
        self,
        file_path: Union[str, Path],
        parent_type: str,
        mime_type: Optional[str] = None,
        validate: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        **kwargs
    ) -> EntityResponse:
        """Attachment-Multiple field için dosya yükler.
        
        Args:
            file_path: Yüklenecek dosya yolu
            parent_type: Parent entity türü (Note, Email vb.)
            mime_type: MIME type (otomatik detect edilir)
            validate: Dosya validation yapılsın mı
            progress_callback: Progress callback fonksiyonu
            **kwargs: Ek request parametreleri
            
        Returns:
            Upload edilen attachment response'u
            
        Example:
            >>> response = attachment_client.upload_attachment(
            ...     "/path/to/image.jpg",
            ...     parent_type="Note"
            ... )
        """
        self.logger.info(
            "Uploading attachment",
            file_path=str(file_path),
            parent_type=parent_type
        )
        
        try:
            # Upload request oluştur
            upload_request = create_attachment_upload_request(
                file_path=file_path,
                parent_type=parent_type,
                mime_type=mime_type
            )
            
            # Validation
            if validate:
                self.validation_config.validate_file(upload_request)
            
            # Progress tracking
            progress = ProgressCallback(progress_callback)
            if progress_callback:
                progress.set_total(upload_request.get_file_size())
            
            # API request
            response_data = self.client.post(
                "Attachment",
                data=upload_request.to_api_dict(),
                **kwargs
            )
            
            # Progress complete
            if progress_callback:
                progress.complete()
            
            # Response parse et
            entity_response = parse_entity_response(response_data, "Attachment")
            
            self.logger.info(
                "Attachment uploaded successfully",
                attachment_id=entity_response.get_id(),
                file_name=upload_request.name,
                file_size=upload_request.get_file_size()
            )
            
            return entity_response
            
        except Exception as e:
            self.logger.error(
                "Failed to upload attachment",
                file_path=str(file_path),
                error=str(e)
            )
            raise
    
    @timing_decorator
    def upload_from_bytes(
        self,
        file_data: bytes,
        filename: str,
        field_type: AttachmentFieldType = AttachmentFieldType.ATTACHMENTS,
        related_type: Optional[str] = None,
        parent_type: Optional[str] = None,
        field: str = "attachments",
        mime_type: Optional[str] = None,
        validate: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        **kwargs
    ) -> EntityResponse:
        """Bytes veriden dosya yükler.
        
        Args:
            file_data: Dosya verisi
            filename: Dosya adı
            field_type: Field türü (FILE veya ATTACHMENTS)
            related_type: Related entity türü (File field için)
            parent_type: Parent entity türü (Attachment-Multiple field için)
            field: Field adı
            mime_type: MIME type
            validate: Dosya validation yapılsın mı
            progress_callback: Progress callback fonksiyonu
            **kwargs: Ek request parametreleri
            
        Returns:
            Upload edilen attachment response'u
        """
        self.logger.info(
            "Uploading from bytes",
            filename=filename,
            size=len(file_data),
            field_type=field_type.value
        )
        
        try:
            # Upload request oluştur
            upload_request = create_attachment_from_bytes(
                file_data=file_data,
                filename=filename,
                mime_type=mime_type
            )
            
            # Field type'a göre parametreleri ayarla
            if field_type == AttachmentFieldType.FILE:
                if not related_type:
                    raise EspoCRMValidationError("File field için related_type gereklidir")
                upload_request.related_type = related_type
                upload_request.field = field
            else:
                if not parent_type:
                    raise EspoCRMValidationError("Attachment-Multiple field için parent_type gereklidir")
                upload_request.parent_type = parent_type
                upload_request.field = "attachments"
            
            # Validation
            if validate:
                self.validation_config.validate_file(upload_request)
            
            # Progress tracking
            progress = ProgressCallback(progress_callback)
            if progress_callback:
                progress.set_total(len(file_data))
            
            # API request
            response_data = self.client.post(
                "Attachment",
                data=upload_request.to_api_dict(),
                **kwargs
            )
            
            # Progress complete
            if progress_callback:
                progress.complete()
            
            # Response parse et
            entity_response = parse_entity_response(response_data, "Attachment")
            
            self.logger.info(
                "Upload from bytes completed successfully",
                attachment_id=entity_response.get_id(),
                filename=filename,
                size=len(file_data)
            )
            
            return entity_response
            
        except Exception as e:
            self.logger.error(
                "Failed to upload from bytes",
                filename=filename,
                error=str(e)
            )
            raise
    
    @timing_decorator
    def download_file(
        self,
        attachment_id: str,
        save_path: Optional[Union[str, Path]] = None,
        overwrite: bool = False,
        validate_checksum: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        **kwargs
    ) -> Path:
        """Attachment dosyasını indirir.
        
        Args:
            attachment_id: Attachment ID'si
            save_path: Dosyanın kaydedileceği yol (opsiyonel)
            overwrite: Mevcut dosyanın üzerine yazılsın mı
            validate_checksum: Checksum doğrulaması yapılsın mı
            progress_callback: Progress callback fonksiyonu
            **kwargs: Ek request parametreleri
            
        Returns:
            İndirilen dosyanın yolu
            
        Raises:
            EspoCRMNotFoundError: Attachment bulunamadı
            FileExistsError: Dosya zaten mevcut ve overwrite=False
            EspoCRMError: API hatası
            
        Example:
            >>> file_path = attachment_client.download_file(
            ...     "507f1f77bcf86cd799439011",
            ...     save_path="/downloads/"
            ... )
            >>> print(f"Downloaded: {file_path}")
        """
        self.logger.info(
            "Downloading file",
            attachment_id=attachment_id,
            save_path=str(save_path) if save_path else None
        )
        
        try:
            # Önce attachment bilgilerini al
            attachment_info = self.get_attachment(attachment_id, **kwargs)
            attachment = attachment_info.get_entity(Attachment)
            
            # Download URL oluştur
            download_endpoint = f"Attachment/file/{attachment_id}"
            
            # Progress tracking
            progress = ProgressCallback(progress_callback)
            if progress_callback:
                progress.set_total(attachment.size)
            
            # Dosyayı indir
            response = self.client.http_client.get(download_endpoint, stream=True)
            
            # Save path belirle
            if save_path:
                save_path = Path(save_path)
                if save_path.is_dir():
                    final_path = save_path / attachment.name
                else:
                    final_path = save_path
            else:
                final_path = Path(attachment.name)
            
            # Dosya mevcut mu kontrol et
            if final_path.exists() and not overwrite:
                raise FileExistsError(f"Dosya zaten mevcut: {final_path}")
            
            # Dosyayı kaydet
            final_path.parent.mkdir(parents=True, exist_ok=True)
            
            downloaded_size = 0
            checksum_hash = hashlib.md5() if validate_checksum else None
            
            with open(final_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if checksum_hash:
                            checksum_hash.update(chunk)
                        
                        if progress_callback:
                            progress.update(len(chunk))
            
            # Checksum validation
            if validate_checksum and checksum_hash:
                calculated_checksum = checksum_hash.hexdigest()
                # EspoCRM'den checksum bilgisi alınabilirse karşılaştır
                # Şimdilik sadece boyut kontrolü yap
                if downloaded_size != attachment.size:
                    raise EspoCRMError(
                        f"Dosya boyutu uyuşmuyor. Beklenen: {attachment.size}, "
                        f"İndirilen: {downloaded_size}"
                    )
            
            # Progress complete
            if progress_callback:
                progress.complete()
            
            self.logger.info(
                "File downloaded successfully",
                attachment_id=attachment_id,
                file_path=str(final_path),
                size=downloaded_size
            )
            
            return final_path
            
        except Exception as e:
            self.logger.error(
                "Failed to download file",
                attachment_id=attachment_id,
                error=str(e)
            )
            raise
    
    @timing_decorator
    def download_to_bytes(
        self,
        attachment_id: str,
        validate_checksum: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        **kwargs
    ) -> bytes:
        """Attachment dosyasını bytes olarak indirir.
        
        Args:
            attachment_id: Attachment ID'si
            validate_checksum: Checksum doğrulaması yapılsın mı
            progress_callback: Progress callback fonksiyonu
            **kwargs: Ek request parametreleri
            
        Returns:
            Dosya verisi (bytes)
        """
        self.logger.info(
            "Downloading file to bytes",
            attachment_id=attachment_id
        )
        
        try:
            # Önce attachment bilgilerini al
            attachment_info = self.get_attachment(attachment_id, **kwargs)
            attachment = attachment_info.get_entity(Attachment)
            
            # Download URL oluştur
            download_endpoint = f"Attachment/file/{attachment_id}"
            
            # Progress tracking
            progress = ProgressCallback(progress_callback)
            if progress_callback:
                progress.set_total(attachment.size)
            
            # Dosyayı indir
            response = self.client.http_client.get(download_endpoint, stream=True)
            
            # Bytes buffer
            file_data = io.BytesIO()
            downloaded_size = 0
            checksum_hash = hashlib.md5() if validate_checksum else None
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file_data.write(chunk)
                    downloaded_size += len(chunk)
                    
                    if checksum_hash:
                        checksum_hash.update(chunk)
                    
                    if progress_callback:
                        progress.update(len(chunk))
            
            # Checksum validation
            if validate_checksum and checksum_hash:
                if downloaded_size != attachment.size:
                    raise EspoCRMError(
                        f"Dosya boyutu uyuşmuyor. Beklenen: {attachment.size}, "
                        f"İndirilen: {downloaded_size}"
                    )
            
            # Progress complete
            if progress_callback:
                progress.complete()
            
            file_bytes = file_data.getvalue()
            
            self.logger.info(
                "File downloaded to bytes successfully",
                attachment_id=attachment_id,
                size=len(file_bytes)
            )
            
            return file_bytes
            
        except Exception as e:
            self.logger.error(
                "Failed to download file to bytes",
                attachment_id=attachment_id,
                error=str(e)
            )
            raise
    
    @timing_decorator
    def get_attachment(
        self,
        attachment_id: str,
        **kwargs
    ) -> EntityResponse:
        """Attachment bilgilerini getirir.
        
        Args:
            attachment_id: Attachment ID'si
            **kwargs: Ek request parametreleri
            
        Returns:
            Attachment entity response'u
        """
        self.logger.info(
            "Getting attachment info",
            attachment_id=attachment_id
        )
        
        try:
            # API request
            endpoint = f"Attachment/{attachment_id}"
            response_data = self.client.get(endpoint, **kwargs)
            
            # Response parse et
            entity_response = parse_entity_response(response_data, "Attachment")
            
            self.logger.info(
                "Attachment info retrieved successfully",
                attachment_id=attachment_id
            )
            
            return entity_response
            
        except Exception as e:
            self.logger.error(
                "Failed to get attachment info",
                attachment_id=attachment_id,
                error=str(e)
            )
            raise
    
    @timing_decorator
    def list_attachments(
        self,
        parent_type: Optional[str] = None,
        parent_id: Optional[str] = None,
        field: Optional[str] = None,
        offset: int = 0,
        max_size: int = 20,
        **kwargs
    ) -> ListResponse:
        """Attachment listesini getirir.
        
        Args:
            parent_type: Parent entity türü
            parent_id: Parent entity ID'si
            field: Field adı
            offset: Başlangıç offset'i
            max_size: Maksimum kayıt sayısı
            **kwargs: Ek request parametreleri
            
        Returns:
            Attachment listesi
        """
        self.logger.info(
            "Listing attachments",
            parent_type=parent_type,
            parent_id=parent_id,
            field=field
        )
        
        try:
            # Query parameters
            params = {
                "offset": offset,
                "maxSize": max_size
            }
            
            # Filtreleme parametreleri
            where_clauses = []
            if parent_type:
                where_clauses.append({
                    "type": "equals",
                    "attribute": "parentType",
                    "value": parent_type
                })
            
            if parent_id:
                where_clauses.append({
                    "type": "equals",
                    "attribute": "parentId",
                    "value": parent_id
                })
            
            if field:
                where_clauses.append({
                    "type": "equals",
                    "attribute": "field",
                    "value": field
                })
            
            if where_clauses:
                params["where"] = where_clauses
            
            # API request
            response_data = self.client.get("Attachment", params=params, **kwargs)
            
            # Response parse et
            list_response = parse_list_response(response_data, "Attachment")
            
            self.logger.info(
                "Attachments listed successfully",
                total=list_response.total,
                count=len(list_response.list)
            )
            
            return list_response
            
        except Exception as e:
            self.logger.error(
                "Failed to list attachments",
                error=str(e)
            )
            raise
    
    @timing_decorator
    def delete_attachment(
        self,
        attachment_id: str,
        **kwargs
    ) -> bool:
        """Attachment'ı siler.
        
        Args:
            attachment_id: Attachment ID'si
            **kwargs: Ek request parametreleri
            
        Returns:
            Silme işlemi başarılı ise True
        """
        self.logger.info(
            "Deleting attachment",
            attachment_id=attachment_id
        )
        
        try:
            # API request
            endpoint = f"Attachment/{attachment_id}"
            self.client.delete(endpoint, **kwargs)
            
            self.logger.info(
                "Attachment deleted successfully",
                attachment_id=attachment_id
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to delete attachment",
                attachment_id=attachment_id,
                error=str(e)
            )
            raise
    
    @timing_decorator
    def bulk_upload(
        self,
        upload_request: BulkAttachmentUploadRequest,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        **kwargs
    ) -> BulkOperationResult:
        """Bulk dosya yükleme.
        
        Args:
            upload_request: Bulk upload request'i
            progress_callback: Progress callback fonksiyonu
            **kwargs: Ek request parametreleri
            
        Returns:
            Bulk operasyon sonucu
        """
        self.logger.info(
            "Starting bulk upload",
            file_count=upload_request.get_file_count(),
            total_size=upload_request.get_total_size()
        )
        
        results = []
        successful = 0
        failed = 0
        errors = []
        
        # Progress tracking
        progress = ProgressCallback(progress_callback)
        if progress_callback:
            progress.set_total(upload_request.get_file_count())
        
        for i, file_request in enumerate(upload_request.files):
            try:
                # Validation
                if upload_request.validate_files:
                    self.validation_config.validate_file(file_request)
                
                # Upload
                response = self.client.post(
                    "Attachment",
                    data=file_request.to_api_dict(),
                    **kwargs
                )
                
                entity_response = parse_entity_response(response, "Attachment")
                
                results.append({
                    "index": i,
                    "success": True,
                    "id": entity_response.get_id(),
                    "filename": file_request.name,
                    "size": file_request.get_file_size()
                })
                successful += 1
                
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "filename": file_request.name,
                    "error": str(e)
                })
                failed += 1
                errors.append({
                    "index": i,
                    "filename": file_request.name,
                    "message": str(e)
                })
            
            # Progress update
            if progress_callback:
                progress.update(1)
        
        bulk_result = BulkOperationResult(
            success=failed == 0,
            total=upload_request.get_file_count(),
            successful=successful,
            failed=failed,
            results=results,
            errors=errors if errors else None
        )
        
        self.logger.info(
            "Bulk upload completed",
            total=bulk_result.total,
            successful=bulk_result.successful,
            failed=bulk_result.failed
        )
        
        return bulk_result
    
    @timing_decorator
    def bulk_download(
        self,
        attachment_ids: List[str],
        download_dir: Union[str, Path],
        overwrite: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        **kwargs
    ) -> BulkOperationResult:
        """Bulk dosya indirme.
        
        Args:
            attachment_ids: İndirilecek attachment ID'leri
            download_dir: İndirme dizini
            overwrite: Mevcut dosyaların üzerine yazılsın mı
            progress_callback: Progress callback fonksiyonu
            **kwargs: Ek request parametreleri
            
        Returns:
            Bulk operasyon sonucu
        """
        self.logger.info(
            "Starting bulk download",
            attachment_count=len(attachment_ids),
            download_dir=str(download_dir)
        )
        
        download_dir = Path(download_dir)
        download_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        successful = 0
        failed = 0
        errors = []
        
        # Progress tracking
        progress = ProgressCallback(progress_callback)
        if progress_callback:
            progress.set_total(len(attachment_ids))
        
        for i, attachment_id in enumerate(attachment_ids):
            try:
                # Download
                file_path = self.download_file(
                    attachment_id=attachment_id,
                    save_path=download_dir,
                    overwrite=overwrite,
                    **kwargs
                )
                
                results.append({
                    "index": i,
                    "success": True,
                    "id": attachment_id,
                    "file_path": str(file_path)
                })
                successful += 1
                
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "id": attachment_id,
                    "error": str(e)
                })
                failed += 1
                errors.append({
                    "index": i,
                    "attachment_id": attachment_id,
                    "message": str(e)
                })
            
            # Progress update
            if progress_callback:
                progress.update(1)
        
        bulk_result = BulkOperationResult(
            success=failed == 0,
            total=len(attachment_ids),
            successful=successful,
            failed=failed,
            results=results,
            errors=errors if errors else None
        )
        
        self.logger.info(
            "Bulk download completed",
            total=bulk_result.total,
            successful=bulk_result.successful,
            failed=bulk_result.failed
        )
        
        return bulk_result
    
    def validate_file_security(self, file_data: bytes, filename: str) -> bool:
        """Dosya güvenlik kontrolü yapar.
        
        Args:
            file_data: Dosya verisi
            filename: Dosya adı
            
        Returns:
            Güvenli ise True
            
        Raises:
            SecurityValidationError: Güvenlik hatası
        """
        # File header kontrolü
        if len(file_data) < 4:
            raise SecurityValidationError("Dosya çok küçük")
        
        # Executable file kontrolü
        executable_signatures = [
            b'\x4d\x5a',  # PE executable (Windows)
            b'\x7f\x45\x4c\x46',  # ELF executable (Linux)
            b'\xfe\xed\xfa\xce',  # Mach-O executable (macOS)
            b'\xfe\xed\xfa\xcf',  # Mach-O executable (macOS)
        ]
        
        for signature in executable_signatures:
            if file_data.startswith(signature):
                
                raise SecurityValidationError(f"Executable dosya türü tespit edildi: {filename}")
        
        # Script file kontrolü
        script_extensions = ['.sh', '.bat', '.cmd', '.ps1', '.vbs', '.js', '.php', '.asp', '.jsp']
        file_ext = Path(filename).suffix.lower()
        if file_ext in script_extensions:
            raise SecurityValidationError(f"Script dosya türü yasaklıdır: {file_ext}")
        
        # Malicious content patterns
        malicious_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'<?php',
            b'<%',
        ]
        
        file_content_lower = file_data[:1024].lower()  # İlk 1KB kontrol et
        for pattern in malicious_patterns:
            if pattern in file_content_lower:
                raise SecurityValidationError(f"Şüpheli içerik tespit edildi: {filename}")
        
        return True
    
    def create_temp_file(self, file_data: bytes, suffix: str = "") -> Path:
        """Geçici dosya oluşturur.
        
        Args:
            file_data: Dosya verisi
            suffix: Dosya uzantısı
            
        Returns:
            Geçici dosya yolu
        """
        with self._temp_lock:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.write(file_data)
            temp_file.close()
            
            temp_path = Path(temp_file.name)
            self._temp_files.append(temp_path)
            
            return temp_path
    
    def cleanup_temp_files(self):
        """Geçici dosyaları temizler."""
        with self._temp_lock:
            for temp_file in self._temp_files:
                try:
                    if temp_file.exists():
                        temp_file.unlink()
                except Exception as e:
                    self.logger.warning(f"Geçici dosya silinemedi: {temp_file}, hata: {e}")
            
            self._temp_files.clear()
    
    def get_file_info(self, attachment_id: str, **kwargs) -> Dict[str, Any]:
        """Dosya bilgilerini getirir.
        
        Args:
            attachment_id: Attachment ID'si
            **kwargs: Ek request parametreleri
            
        Returns:
            Dosya bilgileri
        """
        attachment_response = self.get_attachment(attachment_id, **kwargs)
        attachment = attachment_response.get_entity(Attachment)
        
        return {
            "id": attachment.id,
            "name": attachment.name,
            "type": attachment.type,
            "size": attachment.size,
            "role": attachment.role,
            "parent_type": attachment.parent_type,
            "parent_id": attachment.parent_id,
            "related_type": attachment.related_type,
            "related_id": attachment.related_id,
            "field": attachment.field,
            "created_at": attachment.created_at,
            "modified_at": attachment.modified_at,
            "metadata": attachment.metadata,
            "is_image": attachment.is_image(),
            "is_safe": attachment.is_safe_file_type(),
            "download_url": attachment.get_download_url(self.client.base_url)
        }
    
    def copy_attachment(
        self,
        source_attachment_id: str,
        target_parent_type: Optional[str] = None,
        target_parent_id: Optional[str] = None,
        target_field: Optional[str] = None,
        **kwargs
    ) -> EntityResponse:
        """Attachment'ı kopyalar.
        
        Args:
            source_attachment_id: Kaynak attachment ID'si
            target_parent_type: Hedef parent entity türü
            target_parent_id: Hedef parent entity ID'si
            target_field: Hedef field adı
            **kwargs: Ek request parametreleri
            
        Returns:
            Kopyalanan attachment response'u
        """
        self.logger.info(
            "Copying attachment",
            source_id=source_attachment_id,
            target_parent_type=target_parent_type,
            target_parent_id=target_parent_id
        )
        
        try:
            # Kaynak attachment'ı indir
            file_data = self.download_to_bytes(source_attachment_id, **kwargs)
            
            # Kaynak attachment bilgilerini al
            source_info = self.get_file_info(source_attachment_id, **kwargs)
            
            # Yeni attachment oluştur
            if target_parent_type:
                field_type = AttachmentFieldType.ATTACHMENTS
                parent_type = target_parent_type
                related_type = None
                field = target_field or "attachments"
            else:
                field_type = AttachmentFieldType.FILE
                parent_type = None
                related_type = target_parent_type
                field = target_field or "file"
            
            response = self.upload_from_bytes(
                file_data=file_data,
                filename=source_info["name"],
                field_type=field_type,
                related_type=related_type,
                parent_type=parent_type,
                field=field,
                mime_type=source_info["type"],
                **kwargs
            )
            
            self.logger.info(
                "Attachment copied successfully",
                source_id=source_attachment_id,
                target_id=response.get_id()
            )
            
            return response
            
        except Exception as e:
            self.logger.error(
                "Failed to copy attachment",
                source_id=source_attachment_id,
                error=str(e)
            )
            raise
    
    def __del__(self):
        """Destructor - geçici dosyaları temizle."""
        try:
            self.cleanup_temp_files()
        except Exception:
            pass


# Export edilecek sınıflar
__all__ = [
    "AttachmentClient",
    "ProgressCallback",
    "StreamingUploader",
]