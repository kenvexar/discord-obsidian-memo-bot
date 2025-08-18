"""
GitHub-based Obsidian vault synchronization system
"""

import asyncio
import os
import subprocess
from datetime import datetime
from typing import Any

from ..config.settings import get_settings
from ..utils.mixins import LoggerMixin


class GitHubSyncError(Exception):
    """GitHub 同期エラー"""

    pass


class GitHubObsidianSync(LoggerMixin):
    """GitHub を使用した Obsidian vault の永続化システム"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.vault_path = self.settings.obsidian_vault_path
        self.github_token = (
            str(self.settings.github_token.get_secret_value())
            if self.settings.github_token
            else os.getenv("GITHUB_TOKEN")
        )
        self.github_repo_url = self.settings.obsidian_backup_repo or os.getenv(
            "OBSIDIAN_BACKUP_REPO"
        )
        self.github_branch = self.settings.obsidian_backup_branch or os.getenv(
            "OBSIDIAN_BACKUP_BRANCH", "main"
        )

        # Git 設定
        self.git_user_name = self.settings.git_user_name or os.getenv(
            "GIT_USER_NAME", "ObsidianBot"
        )
        self.git_user_email = self.settings.git_user_email or os.getenv(
            "GIT_USER_EMAIL", "bot@example.com"
        )

        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """設定の検証"""
        if not self.github_token:
            self.logger.warning("GITHUB_TOKEN not set, GitHub sync disabled")
            return

        if not self.github_repo_url:
            self.logger.warning("OBSIDIAN_BACKUP_REPO not set, GitHub sync disabled")
            return

        self.logger.info("GitHub sync configuration validated")

    @property
    def is_configured(self) -> bool:
        """GitHub 同期が設定されているかチェック"""
        return bool(self.github_token and self.github_repo_url)

    async def setup_git_repository(self) -> bool:
        """Git リポジトリの初期化"""
        if not self.is_configured:
            self.logger.error("GitHub sync not configured")
            return False

        try:
            # Vault ディレクトリが存在しない場合は作成
            self.vault_path.mkdir(parents=True, exist_ok=True)

            # Git リポジトリの初期化
            if not (self.vault_path / ".git").exists():
                await self._run_git_command(["init"])
                self.logger.info("Git repository initialized")

            # リモートリポジトリの設定
            await self._setup_remote_repository()

            # Git ユーザー設定
            await self._configure_git_user()

            # .gitignore の設定
            await self._setup_gitignore()

            self.logger.info("Git repository setup completed")
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup Git repository: {e}")
            return False

    async def _setup_remote_repository(self) -> None:
        """リモートリポジトリの設定"""
        try:
            # 既存のリモートをチェック
            result = await self._run_git_command(
                ["remote", "get-url", "origin"], check=False
            )

            if result.returncode != 0:
                # リモートが存在しない場合は追加
                repo_url_with_token = self._get_authenticated_repo_url()
                await self._run_git_command(
                    ["remote", "add", "origin", repo_url_with_token]
                )
                self.logger.info("Remote repository added")
            else:
                # 既存のリモートを更新
                repo_url_with_token = self._get_authenticated_repo_url()
                await self._run_git_command(
                    ["remote", "set-url", "origin", repo_url_with_token]
                )
                self.logger.info("Remote repository URL updated")

        except Exception as e:
            self.logger.error(f"Failed to setup remote repository: {e}")
            raise GitHubSyncError(f"Remote repository setup failed: {e}") from e

    async def _configure_git_user(self) -> None:
        """Git ユーザー設定"""
        await self._run_git_command(["config", "user.name", self.git_user_name])
        await self._run_git_command(["config", "user.email", self.git_user_email])
        self.logger.debug("Git user configuration set")

    async def _setup_gitignore(self) -> None:
        """.gitignore の設定"""
        gitignore_path = self.vault_path / ".gitignore"
        if not gitignore_path.exists():
            gitignore_content = """
# Obsidian workspace files
.obsidian/workspace*
.obsidian/hotkeys.json
.obsidian/core-plugins-migration.json

# System files
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
*~
""".strip()
            gitignore_path.write_text(gitignore_content)
            self.logger.info("Created .gitignore file")

    def _get_authenticated_repo_url(self) -> str:
        """認証トークン付きのリポジトリ URL を取得"""
        if self.github_repo_url is None:
            raise GitHubSyncError("GitHub repository URL is not configured")

        if self.github_repo_url.startswith("https://github.com/"):
            # HTTPS URL の場合はトークンを挿入
            return self.github_repo_url.replace(
                "https://github.com/", f"https://{self.github_token}@github.com/"
            )
        return self.github_repo_url

    async def sync_to_github(self, commit_message: str | None = None) -> bool:
        """Obsidian vault を GitHub に同期"""
        if not self.is_configured:
            self.logger.warning("GitHub sync not configured, skipping sync")
            return False

        try:
            # 変更があるかチェック
            if not await self._has_changes():
                self.logger.debug("No changes to sync")
                return True

            # ステージング
            await self._run_git_command(["add", "."])

            # コミット
            message = commit_message or f"Auto-sync: {datetime.now().isoformat()}"
            await self._run_git_command(["commit", "-m", message])

            # プッシュ
            await self._run_git_command(["push", "origin", self.github_branch])

            self.logger.info("Successfully synced vault to GitHub")
            return True

        except Exception as e:
            self.logger.error(f"Failed to sync to GitHub: {e}")
            return False

    async def sync_from_github(self) -> bool:
        """GitHub から Obsidian vault を同期"""
        if not self.is_configured:
            self.logger.warning("GitHub sync not configured, skipping sync")
            return False

        try:
            # リポジトリが存在するかチェック
            if not (self.vault_path / ".git").exists():
                # 初回クローン
                return await self._clone_repository()

            # 既存リポジトリの場合はプル
            await self._run_git_command(["fetch", "origin"])
            await self._run_git_command(
                ["reset", "--hard", f"origin/{self.github_branch}"]
            )

            self.logger.info("Successfully synced vault from GitHub")
            return True

        except Exception as e:
            self.logger.error(f"Failed to sync from GitHub: {e}")
            return False

    async def _clone_repository(self) -> bool:
        """リポジトリをクローン"""
        try:
            # 既存のディレクトリを削除（空でない場合）
            if self.vault_path.exists():
                import shutil

                shutil.rmtree(self.vault_path)

            # 親ディレクトリを作成
            self.vault_path.parent.mkdir(parents=True, exist_ok=True)

            # クローン
            repo_url_with_token = self._get_authenticated_repo_url()
            process = await asyncio.create_subprocess_exec(
                "git",
                "clone",
                repo_url_with_token,
                str(self.vault_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.vault_path.parent,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise GitHubSyncError(f"Clone failed: {stderr.decode()}")

            self.logger.info("Repository cloned successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to clone repository: {e}")
            return False

    async def _has_changes(self) -> bool:
        """変更があるかチェック"""
        try:
            result = await self._run_git_command(
                ["status", "--porcelain"], capture_output=True
            )
            return bool(result.stdout.strip())
        except Exception:
            return False

    async def _run_git_command(
        self, args: list[str], capture_output: bool = False, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        """Git コマンドを実行"""
        cmd = ["git", "-C", str(self.vault_path)] + args

        try:
            if capture_output:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.vault_path.parent
                    if not self.vault_path.exists()
                    else None,
                )
                stdout, stderr = await process.communicate()

                result = subprocess.CompletedProcess(
                    cmd, process.returncode or 0, stdout.decode(), stderr.decode()
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=self.vault_path.parent
                    if not self.vault_path.exists()
                    else None,
                )
                returncode = await process.wait()

                result = subprocess.CompletedProcess(cmd, returncode or 0, "", "")

            if check and result.returncode != 0:
                raise GitHubSyncError(
                    f"Git command failed: {' '.join(cmd)}\n{result.stderr}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Git command failed: {' '.join(cmd)}, error: {e}")
            raise

    async def get_sync_status(self) -> dict[str, Any]:
        """同期ステータスを取得"""
        if not self.is_configured:
            return {"configured": False, "status": "GitHub sync not configured"}

        try:
            has_changes = await self._has_changes()

            # 最新コミット情報を取得
            result = await self._run_git_command(
                ["log", "-1", "--format=%H|%s|%ci"], capture_output=True
            )

            commit_info = (
                result.stdout.strip().split("|")
                if result.stdout.strip()
                else ["", "", ""]
            )

            return {
                "configured": True,
                "has_changes": has_changes,
                "last_commit_hash": commit_info[0],
                "last_commit_message": commit_info[1],
                "last_commit_date": commit_info[2],
                "repository_url": self.github_repo_url,
                "branch": self.github_branch,
            }

        except Exception as e:
            return {"configured": True, "status": f"Error getting sync status: {e}"}

    async def force_reset_from_github(self) -> bool:
        """GitHub からの強制リセット"""
        if not self.is_configured:
            self.logger.warning("GitHub sync not configured")
            return False

        try:
            self.logger.warning(
                "Performing force reset from GitHub - local changes will be lost"
            )

            # ローカルの変更を破棄
            await self._run_git_command(["reset", "--hard", "HEAD"])
            await self._run_git_command(["clean", "-fd"])

            # リモートから強制プル
            await self._run_git_command(["fetch", "origin"])
            await self._run_git_command(
                ["reset", "--hard", f"origin/{self.github_branch}"]
            )

            self.logger.info("Force reset from GitHub completed")
            return True

        except Exception as e:
            self.logger.error(f"Force reset failed: {e}")
            return False
