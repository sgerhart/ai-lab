# Design principles

1. **Git is the control plane.** If a host, model, agent, or network exception is real, it is described in this repository.

2. **No secrets in Git.** Names may be documented. Values live in a secret store or a gitignored overlay.

3. **No weights, datasets, or volumes in Git.** Catalogs record identity and location. Blobs stay on disk.

4. **Private by default.** Published ports bind to `127.0.0.1` unless a deploy-time Tailscale address is set. The public Internet is not a transport. Being on a tailnet does not replace application authentication.

5. **Control and compute are separate.** Durable state lives on the M1 mini. The Studio may be restarted or saturated without erasing the work-order queue.

6. **The laptop is not a dependency.** Essential background services must not require the M3 Air to be awake.

7. **Conservative M1 memory.** Design for 16 GB *system* RAM, not 16 GB for Docker. Optional components stay off the default compose file.

8. **Phase-gated deployment.** Repository files for later phases may exist. Applying them to machines requires a human.

9. **Lab is not a product monorepo.** Future applications get their own repositories.

10. **Honest status.** Scaffolded, implemented, and deployed are three different words.

11. **Placeholders until facts are supplied.** Do not invent hostnames, IPs, tailnet names, domains, usernames, or credentials.

12. **Approvals for irreversible actions.** Agents do not silently gain host privileges. Restore scripts do not overwrite live data without confirmation.
