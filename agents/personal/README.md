# Personal agent

**Status:** Read-only memory and notes, web lookup, and research reports (IWO-095, IWO-097, IWO-098, IWO-101). Sidebar chat is IWO-099. Thread memory is IWO-100. Not autonomous. The research tools are not on the mini yet.

The studio sidebar **Personal agent** button starts this agent. A follow-up in that chat sees the earlier lines. Ask it to research a question and it gathers up to five public pages, files the sources, and can write a markdown report under `~/.ai-lab/reports`. A later message can send it deeper or ask it to revise that report. **New chat** stays a conversation and does not use these tools.

Talks with the operator and looks up a markdown vault under `~/.ai-lab/memory`.
Each run starts with a dated brief: identity, open work, and whether today's
note exists. Search memory with `vault_grep`, then `vault_read`. Notes in
`~/.ai-lab/files` use `files_grep` and `files_read`. A factual question can
use `web_search`. The lab picks the page. Those tools may run again with
different arguments until the step budget ends.

The answering model cannot write the vault or the notes folder. Each scheduler tick files personal-agent chats from finished UTC days into `timeline/daily/YYYY-MM-DD.md` (IWO-096). It does not rewrite people, preferences, or decisions. Today's chats wait until that UTC day is over. Ordinary Studio chat is not filed.
