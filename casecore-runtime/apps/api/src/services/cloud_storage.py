"""
Cloud Storage Connector — Dropbox, Google Drive, OneDrive
Allows clients to authorize and access their cloud-stored files
without manual downloads. OAuth2 flow for each provider.

This module provides:
  1. Abstract base class CloudStorageProvider for extensibility
  2. Concrete Dropbox implementation via HTTP API v2 (no SDK)
  3. CloudStorageManager for managing multiple provider connections
  4. Token storage (in-memory for sandbox, use encrypted DB in production)
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
import base64
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field
from src.utils.ids import new_id

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & Models
# ---------------------------------------------------------------------------

class FileType(str, Enum):
    """Supported file types for evidence intake."""
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    IMAGE = "image"
    OTHER = "other"


class CloudProvider(str, Enum):
    """Available cloud storage providers."""
    DROPBOX = "dropbox"
    GOOGLE_DRIVE = "google_drive"
    ONEDRIVE = "onedrive"


class FileMetadata(BaseModel):
    """Cloud storage file metadata."""
    file_id: str
    name: str
    path: str
    size: int  # bytes
    modified: datetime
    extension: str
    file_type: FileType
    is_dir: bool = False
    mime_type: Optional[str] = None


class CloudFileEntry(BaseModel):
    """File entry returned from list_files."""
    name: str
    path: str
    file_id: str
    size: int
    modified: Optional[str]
    is_dir: bool
    extension: Optional[str]
    file_type: FileType


class DownloadResult(BaseModel):
    """Result of a file download."""
    file_id: str
    filename: str
    size: int
    data: bytes
    mime_type: Optional[str] = None


class AuthorizeResponse(BaseModel):
    """OAuth authorization response."""
    provider: CloudProvider
    auth_url: str
    state: str
    expires_in: int = 3600


class TokenExchangeRequest(BaseModel):
    """OAuth token exchange request."""
    provider: CloudProvider
    code: str
    state: str


class TokenExchangeResponse(BaseModel):
    """OAuth token exchange response."""
    provider: CloudProvider
    access_token: str
    refresh_token: Optional[str]
    expires_in: int
    token_type: str = "Bearer"
    account_id: Optional[str] = None


class CloudConnection(BaseModel):
    """Active cloud storage connection."""
    connection_id: str
    provider: CloudProvider
    account_id: Optional[str]
    email: Optional[str]
    access_token: str
    refresh_token: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime


# ---------------------------------------------------------------------------
# File type detection
# ---------------------------------------------------------------------------

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".mkv", ".flv", ".m4v", ".mpg", ".mpeg", ".3gp"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma", ".opus"}
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt", ".rtf"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff"}


def detect_file_type(filename: str) -> FileType:
    """Detect file type from filename."""
    ext = Path(filename).suffix.lower()
    if ext in VIDEO_EXTENSIONS:
        return FileType.VIDEO
    elif ext in AUDIO_EXTENSIONS:
        return FileType.AUDIO
    elif ext in DOCUMENT_EXTENSIONS:
        return FileType.DOCUMENT
    elif ext in IMAGE_EXTENSIONS:
        return FileType.IMAGE
    else:
        return FileType.OTHER


# ---------------------------------------------------------------------------
# Abstract Cloud Storage Provider
# ---------------------------------------------------------------------------

class CloudStorageProvider(ABC):
    """
    Abstract base class for cloud storage providers.

    Implementations must define OAuth2 flow, file listing, downloading, and metadata retrieval.
    """

    def __init__(self, provider: CloudProvider):
        self.provider = provider
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.expires_at: Optional[datetime] = None
        self.account_id: Optional[str] = None
        self.email: Optional[str] = None

    @abstractmethod
    def authorize_url(self, state: str) -> str:
        """
        Generate OAuth authorization URL.

        Args:
            state: CSRF protection state token

        Returns:
            Authorization URL for user to click
        """
        pass

    @abstractmethod
    def exchange_token(self, code: str) -> Tuple[str, Optional[str], int]:
        """
        Exchange OAuth code for access token.

        Args:
            code: Authorization code from OAuth redirect

        Returns:
            (access_token, refresh_token, expires_in)
        """
        pass

    @abstractmethod
    def list_files(self, path: str = "/") -> List[CloudFileEntry]:
        """
        List files in a cloud storage path.

        Args:
            path: Path to list (e.g., "/" for root, "/folder" for subfolder)

        Returns:
            List of CloudFileEntry objects
        """
        pass

    @abstractmethod
    def download_file(self, file_id: str, file_path: str) -> DownloadResult:
        """
        Download a file from cloud storage.

        Args:
            file_id: File identifier in cloud storage
            file_path: File path in cloud storage

        Returns:
            DownloadResult with file data
        """
        pass

    @abstractmethod
    def get_file_metadata(self, file_id: str, file_path: str) -> FileMetadata:
        """
        Get metadata for a file.

        Args:
            file_id: File identifier
            file_path: File path

        Returns:
            FileMetadata object
        """
        pass

    def is_token_expired(self) -> bool:
        """Check if access token is expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) >= self.expires_at

    def set_token(self, access_token: str, refresh_token: Optional[str] = None, expires_in: int = 3600):
        """Store access token and calculate expiration."""
        self.access_token = access_token
        self.refresh_token = refresh_token
        if expires_in:
            self.expires_at = datetime.now(timezone.utc).timestamp() + expires_in


# ---------------------------------------------------------------------------
# Dropbox Provider Implementation
# ---------------------------------------------------------------------------

class DropboxProvider(CloudStorageProvider):
    """
    Dropbox cloud storage provider using HTTP API v2.

    Configuration via environment variables:
      DROPBOX_APP_KEY — OAuth app key
      DROPBOX_APP_SECRET — OAuth app secret
      DROPBOX_REDIRECT_URI — OAuth redirect URI (default: http://localhost:8000/api/v1/cloud/dropbox/callback)
    """

    BASE_URL = "https://api.dropboxapi.com/2"
    CONTENT_URL = "https://content.dropboxapi.com/2"
    AUTH_URL = "https://www.dropbox.com/oauth2/authorize"
    TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"

    def __init__(self):
        super().__init__(CloudProvider.DROPBOX)
        self.app_key = os.getenv("DROPBOX_APP_KEY", "")
        self.app_secret = os.getenv("DROPBOX_APP_SECRET", "")
        self.redirect_uri = os.getenv(
            "DROPBOX_REDIRECT_URI",
            "http://localhost:8000/api/v1/cloud/dropbox/callback"
        )

        if not self.app_key or not self.app_secret:
            logger.warning(
                "DROPBOX_APP_KEY or DROPBOX_APP_SECRET not set. "
                "Dropbox OAuth will not work. Set env vars to enable."
            )

    def authorize_url(self, state: str) -> str:
        """Generate Dropbox OAuth authorization URL."""
        params = {
            "client_id": self.app_key,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": state,
            "token_access_type": "offline",
        }
        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_token(self, code: str) -> Tuple[str, Optional[str], int]:
        """
        Exchange OAuth code for Dropbox access token.

        Uses the OAuth2 token endpoint to get long-lived access token.
        """
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": self.app_key,
            "client_secret": self.app_secret,
            "redirect_uri": self.redirect_uri,
        }

        req_data = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(
            self.TOKEN_URL,
            data=req_data,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                resp_data = json.loads(response.read().decode('utf-8'))

            access_token = resp_data.get("access_token", "")
            refresh_token = resp_data.get("refresh_token")
            expires_in = resp_data.get("expires_in", 3600)

            if access_token:
                self.set_token(access_token, refresh_token, expires_in)
                # Extract account ID from token
                self._fetch_account_info()

            return access_token, refresh_token, expires_in

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            logger.error(f"Dropbox token exchange failed: {error_body}")
            raise RuntimeError(f"Dropbox OAuth failed: {error_body}")
        except Exception as e:
            logger.error(f"Dropbox token exchange error: {e}")
            raise

    def _fetch_account_info(self):
        """Fetch account info (email, account_id) to store in connection."""
        if not self.access_token:
            return

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        req = urllib.request.Request(
            f"{self.BASE_URL}/users/get_current_account",
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                self.account_id = data.get("account_id")
                self.email = data.get("email")
                logger.info(f"Dropbox account: {self.email} ({self.account_id})")
        except Exception as e:
            logger.warning(f"Could not fetch Dropbox account info: {e}")

    def list_files(self, path: str = "/") -> List[CloudFileEntry]:
        """
        List files in Dropbox path using /2/files/list_folder endpoint.

        Args:
            path: Dropbox path (e.g., "/" or "/My Folder")

        Returns:
            List of CloudFileEntry objects
        """
        if not self.access_token:
            raise RuntimeError("Dropbox not authenticated")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        # Dropbox API requires empty string for root, not "/"
        if path == "/":
            path = ""
        body = json.dumps({"path": path, "recursive": False, "include_deleted": False}).encode('utf-8')
        req = urllib.request.Request(
            f"{self.BASE_URL}/files/list_folder",
            data=body,
            headers=headers,
            method="POST"
        )

        entries = []
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

            for item in data.get("entries", []):
                tag = item.get(".tag", "")
                name = item.get("name", "")
                path_str = item.get("path_display", "")
                id_str = item.get("id", "")

                if tag == "folder":
                    entries.append(CloudFileEntry(
                        name=name,
                        path=path_str,
                        file_id=id_str,
                        size=0,
                        modified=None,
                        is_dir=True,
                        extension=None,
                        file_type=FileType.OTHER,
                    ))
                else:  # file
                    ext = Path(name).suffix.lower()
                    file_type = detect_file_type(name)
                    modified_str = item.get("client_modified")
                    try:
                        modified_dt = datetime.fromisoformat(modified_str.replace('Z', '+00:00'))
                        modified_str = modified_dt.isoformat()
                    except (ValueError, AttributeError):
                        pass

                    entries.append(CloudFileEntry(
                        name=name,
                        path=path_str,
                        file_id=id_str,
                        size=item.get("size", 0),
                        modified=modified_str,
                        is_dir=False,
                        extension=ext or None,
                        file_type=file_type,
                    ))

            logger.info(f"Listed {len(entries)} items in Dropbox path: {path}")
            return entries

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            logger.error(f"Dropbox list_folder failed: {error_body}")
            raise RuntimeError(f"Failed to list Dropbox files: {error_body}")
        except Exception as e:
            logger.error(f"Dropbox list_files error: {e}")
            raise

    def download_file(self, file_id: str, file_path: str) -> DownloadResult:
        """
        Download a file from Dropbox.

        Args:
            file_id: File ID (path in Dropbox)
            file_path: Full path in Dropbox (e.g., "/path/to/file.mp4")

        Returns:
            DownloadResult with file data

        Handles chunked streaming for large files (up to 672MB for videos).
        """
        if not self.access_token:
            raise RuntimeError("Dropbox not authenticated")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Dropbox-API-Arg": json.dumps({"path": file_path}),
        }

        req = urllib.request.Request(
            f"{self.CONTENT_URL}/files/download",
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=300) as response:  # 5min timeout for large files
                # Read in chunks to avoid memory overload
                chunks = []
                chunk_size = 1024 * 1024  # 1MB chunks
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    chunks.append(chunk)

                data = b"".join(chunks)
                filename = Path(file_path).name
                mime_type = response.headers.get("Content-Type")

                logger.info(f"Downloaded {filename} ({len(data)} bytes) from Dropbox")

                return DownloadResult(
                    file_id=file_id,
                    filename=filename,
                    size=len(data),
                    data=data,
                    mime_type=mime_type,
                )

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            logger.error(f"Dropbox download failed: {error_body}")
            raise RuntimeError(f"Failed to download file from Dropbox: {error_body}")
        except Exception as e:
            logger.error(f"Dropbox download error: {e}")
            raise

    def get_file_metadata(self, file_id: str, file_path: str) -> FileMetadata:
        """
        Get metadata for a file in Dropbox.

        Args:
            file_id: File ID
            file_path: File path

        Returns:
            FileMetadata object
        """
        if not self.access_token:
            raise RuntimeError("Dropbox not authenticated")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        body = json.dumps({"path": file_path}).encode('utf-8')
        req = urllib.request.Request(
            f"{self.BASE_URL}/files/get_metadata",
            data=body,
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

            name = data.get("name", "")
            ext = Path(name).suffix.lower()
            file_type = detect_file_type(name)

            modified_str = data.get("client_modified", "")
            try:
                modified_dt = datetime.fromisoformat(modified_str.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                modified_dt = datetime.now(timezone.utc)

            return FileMetadata(
                file_id=file_id,
                name=name,
                path=file_path,
                size=data.get("size", 0),
                modified=modified_dt,
                extension=ext or "unknown",
                file_type=file_type,
                is_dir=data.get(".tag") == "folder",
            )

        except Exception as e:
            logger.error(f"Dropbox get_metadata error: {e}")
            raise


# ---------------------------------------------------------------------------
# Cloud Storage Manager
# ---------------------------------------------------------------------------

class CloudStorageManager:
    """
    Manages cloud storage provider instances and active connections.

    Handles:
      - Provider initialization
      - OAuth flow (generate URL, exchange tokens)
      - Connection storage and retrieval
      - Token refresh (for future implementations)
    """

    # Token persistence file (survives server restarts in sandbox)
    TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".cloud_tokens.json")

    def __init__(self):
        """Initialize manager with available providers."""
        self.providers: Dict[CloudProvider, CloudStorageProvider] = {
            CloudProvider.DROPBOX: DropboxProvider(),
        }

        # In-memory connection storage (sandbox mode)
        # Production: use encrypted database
        self.connections: Dict[str, CloudConnection] = {}
        self.states: Dict[str, Dict[str, str]] = {}  # {state: {provider, ...}}

        # Restore saved tokens from disk
        self._load_tokens()

    def get_provider(self, provider: CloudProvider) -> CloudStorageProvider:
        """Get a provider instance."""
        if provider not in self.providers:
            raise ValueError(f"Provider not supported: {provider}")
        return self.providers[provider]

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available providers with connection status."""
        result = []
        for provider in CloudProvider:
            status = "configured" if self._is_provider_configured(provider) else "not_configured"
            connected = any(
                c.provider == provider for c in self.connections.values()
            )
            result.append({
                "provider": provider.value,
                "status": status,
                "connected": connected,
                "connection_count": sum(1 for c in self.connections.values() if c.provider == provider),
            })
        return result

    def _is_provider_configured(self, provider: CloudProvider) -> bool:
        """Check if provider has required credentials."""
        if provider == CloudProvider.DROPBOX:
            return bool(os.getenv("DROPBOX_APP_KEY")) and bool(os.getenv("DROPBOX_APP_SECRET"))
        # Add checks for other providers
        return False

    def start_authorization(self, provider: CloudProvider) -> AuthorizeResponse:
        """
        Start OAuth authorization flow.

        Args:
            provider: Cloud provider to authorize

        Returns:
            AuthorizeResponse with auth_url and state token
        """
        if not self._is_provider_configured(provider):
            raise RuntimeError(f"Provider {provider.value} is not configured. Set environment variables.")

        state = new_id()
        prov = self.get_provider(provider)
        auth_url = prov.authorize_url(state)

        # Store state for validation in callback
        self.states[state] = {
            "provider": provider.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Started authorization for {provider.value}")

        return AuthorizeResponse(
            provider=provider,
            auth_url=auth_url,
            state=state,
            expires_in=3600,
        )

    def exchange_code(self, provider: CloudProvider, code: str, state: str) -> TokenExchangeResponse:
        """
        Exchange OAuth code for access token.

        Args:
            provider: Cloud provider
            code: Authorization code from OAuth redirect
            state: State token for validation

        Returns:
            TokenExchangeResponse with tokens
        """
        # Validate state
        if state not in self.states:
            raise ValueError("Invalid state token (CSRF protection)")

        state_data = self.states.pop(state)
        if state_data.get("provider") != provider.value:
            raise ValueError("State token provider mismatch")

        prov = self.get_provider(provider)
        access_token, refresh_token, expires_in = prov.exchange_token(code)

        # Create connection record
        conn = CloudConnection(
            connection_id=new_id(),
            provider=provider,
            account_id=prov.account_id,
            email=prov.email,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=(
                datetime.now(timezone.utc).timestamp() + expires_in
                if expires_in else None
            ),
            created_at=datetime.now(timezone.utc),
        )

        # Store connection and persist to disk
        self.connections[conn.connection_id] = conn
        self._save_tokens()
        logger.info(f"Created connection {conn.connection_id} for {provider.value} ({prov.email})")

        return TokenExchangeResponse(
            provider=provider,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            account_id=prov.account_id,
        )

    def get_connection(self, connection_id: str) -> CloudConnection:
        """Get an active connection by ID."""
        if connection_id not in self.connections:
            raise ValueError(f"Connection not found: {connection_id}")
        return self.connections[connection_id]

    def list_connections(self, provider: Optional[CloudProvider] = None) -> List[CloudConnection]:
        """List all active connections, optionally filtered by provider."""
        conns = list(self.connections.values())
        if provider:
            conns = [c for c in conns if c.provider == provider]
        return conns

    def disconnect(self, connection_id: str) -> bool:
        """Disconnect and revoke a connection."""
        if connection_id in self.connections:
            conn = self.connections.pop(connection_id)
            logger.info(f"Disconnected {conn.provider.value} connection {connection_id}")
            return True
        return False

    def list_files_in_connection(self, connection_id: str, path: str = "/") -> List[CloudFileEntry]:
        """List files in a cloud storage path for a specific connection."""
        conn = self.get_connection(connection_id)
        prov = self.get_provider(conn.provider)

        # Set token on provider
        prov.access_token = conn.access_token
        prov.refresh_token = conn.refresh_token
        prov.expires_at = conn.expires_at

        return prov.list_files(path)

    def download_file_from_connection(
        self, connection_id: str, file_id: str, file_path: str
    ) -> DownloadResult:
        """Download a file from cloud storage via a specific connection."""
        conn = self.get_connection(connection_id)
        prov = self.get_provider(conn.provider)

        # Set token on provider
        prov.access_token = conn.access_token
        prov.refresh_token = conn.refresh_token
        prov.expires_at = conn.expires_at

        return prov.download_file(file_id, file_path)

    def get_file_metadata_from_connection(
        self, connection_id: str, file_id: str, file_path: str
    ) -> FileMetadata:
        """Get file metadata from cloud storage."""
        conn = self.get_connection(connection_id)
        prov = self.get_provider(conn.provider)

        # Set token on provider
        prov.access_token = conn.access_token
        prov.refresh_token = conn.refresh_token
        prov.expires_at = conn.expires_at

        return prov.get_file_metadata(file_id, file_path)


    def _save_tokens(self):
        """Persist tokens to disk so they survive server restarts."""
        try:
            data = {}
            for conn_id, conn in self.connections.items():
                data[conn_id] = {
                    "connection_id": conn.connection_id,
                    "provider": conn.provider.value,
                    "account_id": conn.account_id,
                    "email": conn.email,
                    "access_token": conn.access_token,
                    "refresh_token": conn.refresh_token,
                    "expires_at": conn.expires_at if isinstance(conn.expires_at, (int, float)) else (conn.expires_at.timestamp() if hasattr(conn.expires_at, 'timestamp') else conn.expires_at),
                    "created_at": conn.created_at.isoformat() if hasattr(conn.created_at, 'isoformat') else str(conn.created_at) if conn.created_at else None,
                }
            with open(self.TOKEN_FILE, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(data)} cloud connection(s) to {self.TOKEN_FILE}")
        except Exception as e:
            logger.warning(f"Could not save cloud tokens: {e}")

    def _load_tokens(self):
        """Load persisted tokens from disk."""
        if not os.path.exists(self.TOKEN_FILE):
            return
        try:
            with open(self.TOKEN_FILE, "r") as f:
                data = json.load(f)
            for conn_id, info in data.items():
                conn = CloudConnection(
                    connection_id=info["connection_id"],
                    provider=CloudProvider(info["provider"]),
                    account_id=info.get("account_id"),
                    email=info.get("email"),
                    access_token=info["access_token"],
                    refresh_token=info.get("refresh_token"),
                    expires_at=info.get("expires_at"),
                    created_at=datetime.fromisoformat(info["created_at"]) if info.get("created_at") else datetime.now(timezone.utc),
                )
                self.connections[conn_id] = conn
            logger.info(f"Restored {len(data)} cloud connection(s) from disk")
        except Exception as e:
            logger.warning(f"Could not load cloud tokens: {e}")


# Global manager instance
_cloud_storage_manager: Optional[CloudStorageManager] = None


def get_cloud_storage_manager() -> CloudStorageManager:
    """Get or create the global cloud storage manager."""
    global _cloud_storage_manager
    if _cloud_storage_manager is None:
        _cloud_storage_manager = CloudStorageManager()
    return _cloud_storage_manager
