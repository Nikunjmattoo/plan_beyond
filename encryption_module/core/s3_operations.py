"""S3 operations for encrypted vault files."""
import boto3
from botocore.exceptions import ClientError
from typing import Optional
import logging

from .config import S3_BUCKET_NAME, AWS_REGION, S3_PRESIGNED_URL_EXPIRY
from ..exceptions import (
    S3UploadException,
    S3DownloadException,
    S3DeleteException,
    S3AccessDeniedException,
    FileNotFoundException
)

logger = logging.getLogger(__name__)


class S3Operations:
    """Handles S3 operations for encrypted vault files."""
    
    def __init__(self):
        try:
            self.s3 = boto3.client('s3', region_name=AWS_REGION)
            self.bucket = S3_BUCKET_NAME
        except Exception as e:
            logger.exception("Failed to initialize S3 client")
            raise S3UploadException(
                "Failed to initialize S3 client",
                details={"error": str(e), "region": AWS_REGION}
            )
    
    def upload_encrypted_file(
        self,
        encrypted_data: bytes,
        file_id: str,
        user_id: str,
        file_type: str = 'source'
    ) -> str:
        """
        Upload encrypted file to S3.
        
        Args:
            encrypted_data: Encrypted file bytes
            file_id: Unique file identifier
            user_id: Owner user ID
            file_type: 'source' for source files
            
        Returns:
            str: S3 key (path) where file is stored
            
        Raises:
            S3UploadException: If upload fails
            S3AccessDeniedException: If access denied
        """
        if not encrypted_data:
            raise S3UploadException(
                "Cannot upload empty file",
                details={"file_id": file_id, "data_length": 0}
            )
        
        s3_key = f"vault_files/{user_id}/{file_id}/{file_type}.bin"
        
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=encrypted_data,
                ServerSideEncryption='AES256',
                Metadata={
                    'user_id': user_id,
                    'file_id': file_id,
                    'encryption': 'AES-256-GCM'
                }
            )
            logger.info(f"Successfully uploaded encrypted file to S3: {s3_key}")
            return s3_key
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.exception(f"S3 upload failed for file {file_id}")
            
            # Handle specific S3 errors
            if error_code == 'AccessDenied':
                raise S3AccessDeniedException(
                    "Access denied to S3 bucket",
                    details={
                        "bucket": self.bucket,
                        "s3_key": s3_key,
                        "aws_error_code": error_code,
                        "file_id": file_id,
                        "user_id": user_id
                    }
                )
            
            raise S3UploadException(
                "Failed to upload encrypted file to S3",
                details={
                    "bucket": self.bucket,
                    "s3_key": s3_key,
                    "aws_error_code": error_code,
                    "error_message": str(e),
                    "file_id": file_id,
                    "user_id": user_id,
                    "data_size_bytes": len(encrypted_data)
                }
            )
        except Exception as e:
            logger.exception(f"Unexpected error during S3 upload for file {file_id}")
            raise S3UploadException(
                "Unexpected error during S3 upload",
                details={
                    "error": str(e),
                    "file_id": file_id,
                    "s3_key": s3_key
                }
            )
    
    def download_encrypted_file(self, s3_key: str) -> bytes:
        """
        Download encrypted file from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            bytes: Encrypted file data
            
        Raises:
            S3DownloadException: If download fails
            FileNotFoundException: If file doesn't exist in S3
            S3AccessDeniedException: If access denied
        """
        if not s3_key:
            raise S3DownloadException(
                "S3 key cannot be empty",
                details={"s3_key": s3_key}
            )
        
        try:
            response = self.s3.get_object(
                Bucket=self.bucket,
                Key=s3_key
            )
            data = response['Body'].read()
            logger.info(f"Successfully downloaded encrypted file from S3: {s3_key}")
            return data
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.exception(f"S3 download failed for key {s3_key}")
            
            # Handle specific S3 errors
            if error_code == 'NoSuchKey':
                raise FileNotFoundException(
                    "Encrypted file not found in S3",
                    details={
                        "bucket": self.bucket,
                        "s3_key": s3_key,
                        "aws_error_code": error_code
                    }
                )
            
            if error_code == 'AccessDenied':
                raise S3AccessDeniedException(
                    "Access denied to S3 object",
                    details={
                        "bucket": self.bucket,
                        "s3_key": s3_key,
                        "aws_error_code": error_code
                    }
                )
            
            raise S3DownloadException(
                "Failed to download encrypted file from S3",
                details={
                    "bucket": self.bucket,
                    "s3_key": s3_key,
                    "aws_error_code": error_code,
                    "error_message": str(e)
                }
            )
        except Exception as e:
            logger.exception(f"Unexpected error during S3 download for key {s3_key}")
            raise S3DownloadException(
                "Unexpected error during S3 download",
                details={
                    "error": str(e),
                    "s3_key": s3_key
                }
            )
    
    def generate_presigned_download_url(
        self,
        s3_key: str,
        expiry: int = S3_PRESIGNED_URL_EXPIRY
    ) -> str:
        """
        Generate temporary download URL for encrypted file.
        
        Args:
            s3_key: S3 object key
            expiry: URL expiration time in seconds (default 1 hour)
            
        Returns:
            str: Presigned URL valid for expiry seconds
            
        Raises:
            S3DownloadException: If URL generation fails
        """
        if not s3_key:
            raise S3DownloadException(
                "S3 key cannot be empty",
                details={"s3_key": s3_key}
            )
        
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': s3_key
                },
                ExpiresIn=expiry
            )
            logger.info(f"Generated presigned URL for S3 key: {s3_key}")
            return url
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.exception(f"Failed to generate presigned URL for key {s3_key}")
            raise S3DownloadException(
                "Failed to generate presigned download URL",
                details={
                    "bucket": self.bucket,
                    "s3_key": s3_key,
                    "expiry_seconds": expiry,
                    "aws_error_code": error_code,
                    "error_message": str(e)
                }
            )
        except Exception as e:
            logger.exception(f"Unexpected error generating presigned URL for key {s3_key}")
            raise S3DownloadException(
                "Unexpected error generating presigned URL",
                details={
                    "error": str(e),
                    "s3_key": s3_key
                }
            )
    
    def delete_encrypted_file(self, s3_key: str):
        """
        Delete encrypted file from S3.
        
        Args:
            s3_key: S3 object key
            
        Raises:
            S3DeleteException: If deletion fails
            S3AccessDeniedException: If access denied
        """
        if not s3_key:
            raise S3DeleteException(
                "S3 key cannot be empty",
                details={"s3_key": s3_key}
            )
        
        try:
            self.s3.delete_object(
                Bucket=self.bucket,
                Key=s3_key
            )
            logger.info(f"Successfully deleted encrypted file from S3: {s3_key}")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.exception(f"S3 delete failed for key {s3_key}")
            
            # Handle specific S3 errors
            if error_code == 'AccessDenied':
                raise S3AccessDeniedException(
                    "Access denied to delete S3 object",
                    details={
                        "bucket": self.bucket,
                        "s3_key": s3_key,
                        "aws_error_code": error_code
                    }
                )
            
            raise S3DeleteException(
                "Failed to delete encrypted file from S3",
                details={
                    "bucket": self.bucket,
                    "s3_key": s3_key,
                    "aws_error_code": error_code,
                    "error_message": str(e)
                }
            )
        except Exception as e:
            logger.exception(f"Unexpected error during S3 delete for key {s3_key}")
            raise S3DeleteException(
                "Unexpected error during S3 delete",
                details={
                    "error": str(e),
                    "s3_key": s3_key
                }
            )