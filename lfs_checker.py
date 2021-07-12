import os
from typing import (
    Dict,
    List,
    NamedTuple,
    Set,
    Tuple,
)

from discord_webhook import (
    DiscordEmbed,
    DiscordWebhook,
)
from git import Repo


REPO_DIR = os.getenv("REPO_DIR")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")


class GitLock(NamedTuple):
    file: str
    user: str
    id: str


class DiscordManager:

    added_locks: List[GitLock]
    removed_locks: List[GitLock]

    def __init__(
        self,
        added_locks: List[GitLock],
        removed_locks: List[GitLock],
    ) -> None:
        self.added_locks = added_locks
        self.removed_locks = removed_locks

    def publish(self):
        webhook = DiscordWebhook(url=WEBHOOK_URL)
        embed = DiscordEmbed()

        embed.set_color("ffff00" if self.added_locks else "00ff00")
        self.create_added_fields(embed)
        self.create_removed_fields(embed)

        webhook.add_embed(embed)
        webhook.execute()

    def create_added_fields(self, embed: DiscordEmbed) -> None:
        self.create_generic_fields(embed=embed, title="Locked:", locks=self.added_locks)

    def create_removed_fields(self, embed: DiscordEmbed) -> None:
        self.create_generic_fields(embed=embed, title="Unlocked:", locks=self.removed_locks)

    @staticmethod
    def create_generic_fields(
        embed: DiscordEmbed,
        title: str,
        locks: List[GitLock],
    ) -> None:
        if not locks:
            return

        embed.add_embed_field(
            name=title,
            value="\n".join([
                f"{lock.file}, by {lock.user}"
                for lock in locks
            ]),
            inline=False,
        )


class GitLockManager:

    repo: Repo
    locks: Dict[str, GitLock]

    def __init__(self, repo_dir: str = REPO_DIR) -> None:
        self.repo = Repo(repo_dir)
        self.locks = self.load_locks()

    def load_locks(self) -> Dict[str, GitLock]:
        raw_locks: str = self.repo.git.lfs("locks")
        locks = self._parse_raw_locks(raw_locks)
        return locks

    def compare_lock_set(self, new_locks: Dict[str, GitLock]) -> Tuple[Set[str], Set[str]]:
        old_lock_ids = self.locks.keys()
        new_lock_ids = new_locks.keys()

        removed_locks = old_lock_ids - new_lock_ids
        added_locks = new_lock_ids - old_lock_ids

        return removed_locks, added_locks

    def check_locks(self):
        new_locks = self.load_locks()
        removed_locks, added_locks = self.compare_lock_set(new_locks)

        if removed_locks or added_locks:
            print("Publishing changes")
            discord_manager = DiscordManager(
                added_locks=[
                    new_locks[added_lock_id]
                    for added_lock_id in added_locks
                ],
                removed_locks=[
                    self.locks[removed_lock_id]
                    for removed_lock_id in removed_locks
                ],
            )
            discord_manager.publish()
            print("Published changes")
        else:
            print("No changes")

        self.locks = new_locks

    @staticmethod
    def _parse_raw_locks(raw_locks: str) -> Dict[str, GitLock]:
        locks: Dict[str, GitLock] = {}
        for lock_line in raw_locks.splitlines():
            file, user, id = lock_line.split("\t")
            lock = GitLock(
                file=file.strip(),
                user=user.strip(),
                id=id.strip(),
            )
            locks[lock.id] = lock
        return locks


if __name__ == "__main__":
    import time

    print("Loading repo")
    glm = GitLockManager()
    print("Repo loaded")

    retry_time = 5 * 60

    run = True
    while run:
        try:
            glm.check_locks()
            time.sleep(retry_time)
        except KeyboardInterrupt:
            print("Stopping")
            run = False
    print("Stopped, bye bye!")
