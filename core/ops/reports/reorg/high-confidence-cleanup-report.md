# High-Confidence Cleanup Report

Generated at: `2026-07-04T08:16:07.328589+00:00`

## Scope and Safety

- Cleanup constrained to broken symlinks in approved archive/test scopes and regenerable caches.
- No repo roots, active source trees, or runtime/model stores were deleted.
- `.ollama`/`.lmstudio` model-related cache names were explicitly protected/skipped.

## Disk Usage Before/After

- Pre-clean `df -h /`: `/dev/disk3s1s1 228Gi used=16Gi avail=1.9Gi capacity=90%`
- Post-clean `df -h /`: `/dev/disk3s1s1 228Gi used=16Gi avail=6.6Gi capacity=71%`
- Reclaimed by measured deletions: `4781396105 bytes` (4.45 GiB)

## Exact Deletions Performed

- Broken symlinks deleted: `3`
  - `/Users/ajoxendine68/Desktop/Xoras_Workspace/Backups_and_Configs/_Archive/History/github_audits/xoras-sentry/tests/spectrum-sandbox/tunnel_link` (100 bytes)
  - `/Users/ajoxendine68/Desktop/Xoras_Workspace/Backups_and_Configs/_Archive/History/github_audits/sovra-core-lighthouse/aux/mac-jarvis` (47 bytes)
  - `/Users/ajoxendine68/Desktop/Xoras_Workspace/Backups_and_Configs/_Archive/History/github_audits/sovra-core-lighthouse/aux/gate_keeper` (48 bytes)

- Cache entries deleted: `83`
  - `/Users/ajoxendine68/Library/Caches/.DS_Store` (6148 bytes)
  - `/Users/ajoxendine68/Library/Caches/.wasm-pack` (0 bytes)
  - `/Users/ajoxendine68/Library/Caches/AtomicJar` (13551 bytes)
  - `/Users/ajoxendine68/Library/Caches/Codex` (1994890 bytes)
  - `/Users/ajoxendine68/Library/Caches/Docker Desktop` (147 bytes)
  - `/Users/ajoxendine68/Library/Caches/GameKit` (47499 bytes)
  - `/Users/ajoxendine68/Library/Caches/GeoServices` (68097812 bytes)
  - `/Users/ajoxendine68/Library/Caches/Google` (668372918 bytes)
  - `/Users/ajoxendine68/Library/Caches/Homebrew` (21391784 bytes)
  - `/Users/ajoxendine68/Library/Caches/PassKit` (2325214 bytes)
  - `/Users/ajoxendine68/Library/Caches/Zed` (0 bytes)
  - `/Users/ajoxendine68/Library/Caches/antigravity-updater` (317245157 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.anthropic.claudefordesktop` (123152 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.anthropic.claudefordesktop.ShipIt` (2879 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.AMPLibraryAgent` (2797619 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.AppleMediaServices` (18186169 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.AssistantServices` (0 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.AuthenticationServicesCore.AuthenticationServicesAgent` (143752 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.AvatarKit` (0 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.CloudTelemetry` (33183194 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.Family-Settings.extension` (642272 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.FeatureAccessAgent` (868872 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.SoftwareUpdateNotificationManager` (139632 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.Spotlight` (64 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.akd` (848614 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.amsaccountsd` (959716 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.amsengagementd` (1053177 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.appleaccountd` (287952 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.appstoreagent` (1623760 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.askpermissiond` (189072 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.assistantd` (0 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.betaenrollmentagent` (156112 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.bird` (764411 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.businessservicesd` (0 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.cache_delete` (122877 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.chrono` (5984 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.commerce` (424 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.ctcategories.service` (2421219 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.dataaccess.dataaccessd` (144016 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.duetexpertd` (256 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.e5rt.e5bundlecache` (0 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.feedbacklogger` (91808 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.gamed` (288 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.geoanalyticsd` (255256 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.helpd` (14875956 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.iCloudNotificationAgent` (559872 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.iTunes` (790592 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.iTunesCloud` (0 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.itunescloudd` (1535737 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.managedappdistributionagent` (423912 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.nbagent` (423912 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.nsservicescache.plist` (14771 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.nsurlsessiond` (0 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.parsecd` (17139984 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.passd` (4350319 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.preferencepanes.usercache` (881 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.proactive.eventtracker` (227226 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.python` (6550577 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.remindd` (147283 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.siri.bundleservicecache.plist` (9624 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.siri.transformationplugincache.plist` (4334 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.sirittsd` (524961 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.storekitagent` (489832 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.systemsettings.menucache` (3054 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.tipsd` (634032 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.tiswitcher.cache` (0 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.apple.translationd` (244313 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.google.GoogleUpdater` (81920 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.google.antigravity` (81920 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.google.antigravity.ShipIt` (2709 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.openai.codex` (656664 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.openai.sky.CUAService` (164352 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.todesktop.230313mzl4w4u92` (123152 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.todesktop.230313mzl4w4u92.ShipIt` (3176 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.vercel.cli` (1116 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.xoras.commanddeck` (16 bytes)
  - `/Users/ajoxendine68/Library/Caches/com.xoras.sovereign` (671962 bytes)
  - `/Users/ajoxendine68/Library/Caches/docker-secrets-engine` (0 bytes)
  - `/Users/ajoxendine68/Library/Caches/ms-playwright` (563522583 bytes)
  - `/Users/ajoxendine68/Library/Caches/ms-playwright-go` (128969322 bytes)
  - `/Users/ajoxendine68/Library/Caches/node-gyp` (117845304 bytes)
  - `/Users/ajoxendine68/Library/Caches/pip` (38623138 bytes)
  - `/Users/ajoxendine68/Library/Application Support/interpreter` (2737189737 bytes)

## Skipped Items and Why

- `/Users/ajoxendine68/Library/Caches/CloudKit` - delete_failed: [Errno 1] Operation not permitted: PosixPath('/Users/ajoxendine68/Library/Caches/CloudKit')
- `/Users/ajoxendine68/Library/Caches/FamilyCircle` - delete_failed: [Errno 1] Operation not permitted: PosixPath('/Users/ajoxendine68/Library/Caches/FamilyCircle')
- `/Users/ajoxendine68/Library/Caches/com.apple.HomeKit` - delete_failed: [Errno 1] Operation not permitted: PosixPath('/Users/ajoxendine68/Library/Caches/com.apple.HomeKit')
- `/Users/ajoxendine68/Library/Caches/com.apple.Safari` - delete_failed: [Errno 1] Operation not permitted: PosixPath('/Users/ajoxendine68/Library/Caches/com.apple.Safari')
- `/Users/ajoxendine68/Library/Caches/com.apple.Safari.SafeBrowsing` - delete_failed: [Errno 1] Operation not permitted: PosixPath('/Users/ajoxendine68/Library/Caches/com.apple.Safari.SafeBrowsing')
- `/Users/ajoxendine68/Library/Caches/com.apple.ap.adprivacyd` - delete_failed: [Errno 1] Operation not permitted: PosixPath('/Users/ajoxendine68/Library/Caches/com.apple.ap.adprivacyd')
- `/Users/ajoxendine68/Library/Caches/com.apple.containermanagerd` - delete_failed: [Errno 1] Operation not permitted: PosixPath('/Users/ajoxendine68/Library/Caches/com.apple.containermanagerd')
- `/Users/ajoxendine68/Library/Caches/com.apple.homed` - delete_failed: [Errno 1] Operation not permitted: PosixPath('/Users/ajoxendine68/Library/Caches/com.apple.homed')
- `/Users/ajoxendine68/Library/Caches/com.electron.ollama` - protected model-related name
- `/Users/ajoxendine68/Library/Caches/familycircled` - delete_failed: [Errno 1] Operation not permitted: PosixPath('/Users/ajoxendine68/Library/Caches/familycircled')
- `/Users/ajoxendine68/Library/Caches/ollama` - protected model-related name

## Next Safe Cleanup Tranche (Recommendations)

- Run a targeted stale build-artifact pass (`**/dist`, `**/build`, `**/.pytest_cache`, `**/__pycache__`) only outside active repos or via per-repo approval.
- Trim package manager caches with freshness checks (e.g., last access >30 days) if you want an even safer, incremental pass.
- Review operation-not-permitted cache directories manually in System Settings privacy-protected areas before attempting another deletion pass.

