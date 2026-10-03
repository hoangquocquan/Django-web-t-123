# Docker Desktop / WSL 2 Diagnostic Report

Initial diagnosis: 2026-09-09 (Asia/Tokyo)  
Authorized inference-settings repair: 2026-09-10 (Asia/Tokyo)  
Scope: host-environment diagnosis and only the recovery actions expressly allowed by the task  
Current final verdict: `OWNER_ACTION_REQUIRED_REMOVE_STALE_ENDPOINT`

## 1. Project isolation evidence

- Working directory: `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO`
- Git root: `C:/Users/hoang/Documents/ChatGPT/WEB Ô TÔ DJANGO`
- Remote: `origin https://github.com/hoangquocquan/Django-web-t-123.git`
- Branch: `codex/demo-database-validation`
- `django_backend/`: present
- `figma_make_frontend/`: present
- Repository identity, branch, backend, and frontend all matched the required project.
- `AI FACTORY N8N` was not read or modified.

## 2. Initial Git state

```text
 M django_backend/apps/business_core/models.py
 M django_backend/apps/sales/models.py
?? PHASE_3A_SCHEMA_AND_MIGRATION_PLAN_R2_REPORT.md
?? PHASE_3A_SCHEMA_AND_MIGRATION_PLAN_REPORT.md
?? PHASE_3B_MASTER_DATA_RFQ_IMPLEMENTATION_REPORT.md
?? PHASE_3B_POSTGRESQL_VALIDATION_CLOSURE_REPORT.md
?? django_backend/apps/business_core/business_numbers.py
?? django_backend/apps/business_core/migrations/0003_businessmaterial_businessnumbersequence_and_more.py
?? django_backend/apps/business_core/migrations/0004_mark_existing_master_rows_legacy.py
?? django_backend/apps/business_core/migrations/0005_phase3b_master_constraints.py
?? django_backend/apps/business_core/tests/test_phase3b_master_models.py
?? django_backend/apps/foundation/migrations/0007_define_phase3b_permissions.py
?? django_backend/apps/sales/migrations/0002_salesrfq_salesrfqline_salesrfqdocument_and_more.py
?? django_backend/apps/sales/tests/test_phase3b_rfq_models.py
?? django_backend/tests/test_phase3b_migrations.py
?? docs/database/
```

All pre-existing tracked and untracked files were preserved.

## 3. Execution identity

Normal Codex execution identity:

```text
quanpc\codexsandboxoffline
```

Relevant groups included `QUANPC\CodexSandboxUsers`, `BUILTIN\Users`, `NT AUTHORITY\INTERACTIVE`, and `NT AUTHORITY\Authenticated Users`; the identity was not a member of `docker-users` or Administrators in the reported token.

Approved Owner-context read-only checks ran as:

```text
quanpc\hoang
```

## 4. Docker service and process state

Initial Windows service state:

```text
Name      : com.docker.service
Status    : Running
StartType : Manual
```

Owner-context CIM evidence:

```text
Name      : com.docker.service
State     : Running
StartMode : Manual
StartName : LocalSystem
ExitCode  : 0
```

Docker Desktop UI, two `com.docker.backend` processes, and several stale Docker CLI processes were initially visible. Visible/responding processes did not constitute a healthy engine. After the targeted close/relaunch, fresh UI and backend processes started at 11:55:13, but the backend immediately returned to its crash/error state.

## 5. WSL version, status, and distributions

```text
WSL version: 2.7.3.0
Kernel version: 6.6.114.1-1
WSLg version: 1.0.73
Windows version: 10.0.26200.9168
Default distribution: docker-desktop
Default version: 2
```

Before recovery:

```text
NAME              STATE    VERSION
* docker-desktop  Stopped  2
```

After relaunch:

```text
NAME              STATE    VERSION
* docker-desktop  Stopped  2
```

There were no non-Docker WSL distributions listed and no unrelated WSL workload running. No global `wsl --shutdown` was used. The distro was already stopped, so it was not terminated.

The Codex sandbox could run `wsl --version`, but `wsl --status` and `wsl -l -v` returned `Wsl/EnumerateDistros/Service/E_ACCESSDENIED`. Owner-context queries succeeded.

## 6. Windows features and virtualization

- Direct `Get-WindowsOptionalFeature` queries for `Microsoft-Windows-Subsystem-Linux` and `VirtualMachinePlatform` required elevation and were not changed.
- Owner-context `Get-CimInstance Win32_Processor` reported `VirtualizationFirmwareEnabled=False` and `VMMonitorModeExtensions=False`.
- Independent `systeminfo` evidence reported: `A hypervisor has been detected. Features required for Hyper-V will not be displayed.`
- Docker backend state reported `HasNoVirtualization:false` and `WslUpdateRequired:false`.
- WSL 2.7.3 successfully enumerated a version-2 `docker-desktop` distribution.
- `bcdedit /enum "{current}"` did not return usable configuration (`specified entry type is invalid`), so no boot-setting conclusion was inferred from it.

Because an active hypervisor and functioning WSL 2 installation were independently evidenced, the processor CIM booleans alone are insufficient evidence that BIOS virtualization is disabled. No Windows feature, BIOS, boot, update, or reboot change was performed.

## 7. Docker context and endpoint

Owner context:

```text
NAME              DESCRIPTION                               DOCKER ENDPOINT
default           Current DOCKER_HOST based configuration   npipe:////./pipe/docker_engine
desktop-linux *   Docker Desktop                            npipe:////./pipe/dockerDesktopLinuxEngine
```

The Owner context was already correctly set to `desktop-linux`; it was not changed.

The Codex sandbox could not read `C:\Users\hoang\.docker\config.json` or `C:\Users\hoang\.docker\contexts`, so it fell back to `default`. Initially, Docker-related named pipes including `docker_engine` and `dockerDesktopLinuxEngine` existed, but Codex received named-pipe permission denial. After the reproduced backend crash, the final Codex check reported that `docker_engine` no longer existed. No pipe ACL was changed.

## 8. Relevant log and filesystem evidence

Docker Desktop 4.74.0 backend log, initial startup:

```text
received state {Docker:stopped DockerAPI:stopped HasNoVirtualization:false ... Mode:linux ... WslUpdateRequired:false}
backend cancelling with error: starting services: initializing Inference manager:
listening on unix://<HOME>\AppData\Local\Docker\run\dockerInference:
remove <HOME>\AppData\Local\Docker\run\dockerInference:
The file cannot be accessed by the system.
(listener: The filename, directory name, or volume label syntax is incorrect.)
```

The log then recorded all local engines being stopped and the backend crashing. The targeted relaunch reproduced the same error at `2026-09-09T14:55:14Z` before WSL/Docker Engine started.

Read-only endpoint inspection showed:

```text
Path:          C:\Users\hoang\AppData\Local\Docker\run\dockerInference
Exists:        True
Type:          file-like reparse point
Length:        0
Created:       2026-05-24 00:24:39
Last written:  2026-08-23 13:21:40
ACL query:     The file cannot be accessed by the system
```

The containing `run` directory is a normal directory and grants `QUANPC\hoang` full control. This makes the stale/inaccessible `dockerInference` reparse-point runtime endpoint the evidenced startup blocker.

## 9. Diagnostic executable and timeouts

`C:\Program Files\Docker\Docker\resources\com.docker.diagnose.exe` was present. Its non-uploading `check` command was invoked and returned:

```text
The 'check' command is deprecated. Please use 'gather' to generate a diagnostics bundle.
```

No diagnostic was uploaded. A bundle was not gathered because the root cause was already present in the minimal recent backend log and a bundle was unnecessary for classification.

Recorded timeouts (each bounded to 30 seconds):

- Owner `docker version` before recovery: timed out/no usable Server result.
- Owner `docker info` before recovery: timed out/no usable Server result.
- Supported `docker desktop restart`: exceeded 30 seconds; its command session was terminated.
- Owner `docker version`/`docker info` after recovery: failed to yield usable engine output within their bounded run; the one remaining task-started `docker.exe` PID 1240 was explicitly terminated.

Codex-context Docker and WSL probes that returned did so within 30 seconds. No PowerShell job created by this task was left running.

## 10. Root-cause classification

Primary evidenced cause: **another evidenced cause from Docker logs** — Docker Desktop backend startup aborts while initializing its inference manager because the stale `dockerInference` reparse-point runtime endpoint cannot be removed or accessed. The abort occurs before the WSL Linux engine starts, leaving `docker-desktop` stopped.

Secondary execution-context limitation: the Codex sandbox cannot read the Owner's Docker configuration or access Owner WSL enumeration and Docker named pipes. However, this is not merely `DOCKER_HOST_HEALTHY_CODEX_ACCESS_BLOCKED`, because Owner-context checks also failed and the backend logs prove the host engine is stopped.

Rejected by evidence:

- Service stopped: service is running with exit code 0.
- Wrong Docker context: Owner context is correctly `desktop-linux`.
- WSL version too old: 2.7.3; Docker reports `WslUpdateRequired:false`.
- Demonstrated WSL hang: Owner WSL enumeration completes and shows the Docker distro stopped.
- Demonstrated feature/BIOS/hypervisor failure: system reports an active hypervisor and Docker reports `HasNoVirtualization:false`.

## 11. Safe recovery actions performed

1. Read-only checks under both Codex and approved Owner context.
2. Invoked the supported `docker desktop restart`; it timed out at 30 seconds and its command session was terminated.
3. Verified `docker-desktop` was stopped and that no unrelated WSL distribution was running.
4. Closed only the verified Docker Desktop UI and `com.docker.backend` processes from `C:\Program Files\Docker\Docker\` (two backend PIDs and four UI PIDs).
5. Relaunched `C:\Program Files\Docker\Docker\Docker Desktop.exe`.
6. Verified that the identical inference-endpoint crash recurred and that `docker-desktop` remained stopped.

No further mutation was attempted because deleting the stale endpoint is not one of this task's enumerated reversible recovery actions.

## 12. Before-and-after health checks

Before, Codex `docker version` returned Client 29.4.3 only and failed with permission denied on `npipe:////./pipe/docker_engine`; `docker info` returned client/plugin data but no usable Server section. Owner health checks did not complete successfully within their bounded attempts.

After relaunch, final Codex checks returned within 30 seconds but failed:

```text
docker version: Client 29.4.3 only; exit 1
docker info: client/plugin data and empty Server heading; exit 1
error: failed to connect to npipe:////./pipe/docker_engine:
       The system cannot find the file specified.
```

The success criteria are not met: no healthy Server section, no successful Linux Engine information, and the commands do not work from the Phase 3B execution context.

## 13. Remaining Owner action

Docker Desktop must be fully quit, and the single stale runtime endpoint below must be removed by the Owner before relaunching Docker Desktop:

```text
C:\Users\hoang\AppData\Local\Docker\run\dockerInference
```

This is a zero-byte runtime socket/reparse point, not a container, image, volume, database, WSL distribution, or Docker data directory. Its removal was deliberately not performed because it falls outside the task's closed list of permitted recovery actions. The safest next step is a narrowly scoped Owner-approved follow-up that removes only this endpoint while Docker Desktop is stopped, relaunches Docker Desktop, and repeats the bounded success checks. Do not use Reset to factory defaults.

## 14. Preservation confirmation

No container, image, network, volume, database, WSL distribution, Docker data directory, Django source file, frontend file, or AI FACTORY content was deleted or modified. No database connection was attempted. No Windows feature, BIOS setting, boot setting, named-pipe ACL, user/group membership, or security control was changed. No commit, push, branch switch, stash, reset, Phase 3B test, PostgreSQL-container creation, or Phase 3C work was performed.

## 15. Final Git status

The final Git state is the initial state plus this report:

```text
 M django_backend/apps/business_core/models.py
 M django_backend/apps/sales/models.py
?? DOCKER_DESKTOP_WSL_DIAGNOSTIC_REPORT.md
?? PHASE_3A_SCHEMA_AND_MIGRATION_PLAN_R2_REPORT.md
?? PHASE_3A_SCHEMA_AND_MIGRATION_PLAN_REPORT.md
?? PHASE_3B_MASTER_DATA_RFQ_IMPLEMENTATION_REPORT.md
?? PHASE_3B_POSTGRESQL_VALIDATION_CLOSURE_REPORT.md
?? django_backend/apps/business_core/business_numbers.py
?? django_backend/apps/business_core/migrations/0003_businessmaterial_businessnumbersequence_and_more.py
?? django_backend/apps/business_core/migrations/0004_mark_existing_master_rows_legacy.py
?? django_backend/apps/business_core/migrations/0005_phase3b_master_constraints.py
?? django_backend/apps/business_core/tests/test_phase3b_master_models.py
?? django_backend/apps/foundation/migrations/0007_define_phase3b_permissions.py
?? django_backend/apps/sales/migrations/0002_salesrfq_salesrfqline_salesrfqdocument_and_more.py
?? django_backend/apps/sales/tests/test_phase3b_rfq_models.py
?? django_backend/tests/test_phase3b_migrations.py
?? docs/database/
```

## 16. Final verdict

`BLOCKED_DOCKER_ENGINE_UNHEALTHY`

The Docker host engine is not healthy. Recovery is blocked by the stale/inaccessible `dockerInference` runtime endpoint, which lies outside the task's permitted recovery mutations.

## 17. Authorized inference-settings repair (2026-09-10)

### Isolation and initial state

The repair task repeated the isolation checks before host modification:

```text
Working directory: C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO
Git root:          C:/Users/hoang/Documents/ChatGPT/WEB Ô TÔ DJANGO
Remote:            https://github.com/hoangquocquan/Django-web-t-123.git
Branch:            codex/demo-database-validation
django_backend/:   present
figma_make_frontend/: present
```

The initial Git state for the repair was the final state in section 15. No repository file other than this existing diagnostic report was changed by the repair task. AI FACTORY was not read or modified.

### Exact error being repaired

```text
starting services: initializing Inference manager:
listening on unix://C:\Users\hoang\AppData\Local\Docker\run\dockerInference:
remove C:\Users\hoang\AppData\Local\Docker\run\dockerInference:
The file cannot be accessed by the system.
(listener: The filename, directory name, or volume label syntax is incorrect.)
```

### Settings path and preconditions

- Docker Desktop UI/backend processes were confirmed closed before the settings file was read or changed.
- Resolved Owner settings path: `C:\Users\hoang\AppData\Roaming\Docker\settings-store.json`
- The settings file existed and parsed successfully as JSON.
- No unrelated setting values or secrets were printed.

### Backup and integrity verification

```text
Backup: C:\Users\hoang\AppData\Roaming\Docker\settings-store.json.backup.20260910-000043
Original SHA-256: C77DA1403A005423F7E426476C1EF3DDC44BC2B7BD724C0945B67EF002085E8D
Backup SHA-256:   C77DA1403A005423F7E426476C1EF3DDC44BC2B7BD724C0945B67EF002085E8D
Hash match:       true
```

The backup remains beside the original settings file.

### Settings changed

Only these three top-level properties were added/set. All three were absent before the repair, so no pre-repair Boolean value existed:

| Setting | Existed before | Before | After |
|---|---:|---:|---:|
| `enableInference` | false | `<missing>` | `false` |
| `enableInferenceTCP` | false | `<missing>` | `false` |
| `enableInferenceGPUVariant` | false | `<missing>` | `false` |

The full existing JSON object was parsed, the three fields were changed in memory, and all unrelated JSON properties were verified as deeply equal before writing. The generated JSON and the temporary file were parsed and validated. The final settings file was installed by a same-directory temporary-file rename with overwrite and then parsed again; all three final values were verified as Boolean `false`.

Two implementation attempts safely aborted before replacement: one temporary-file Boolean accessor was invalid, and this runtime rejected a null backup argument to `File.Replace`. Before each retry, the original still matched the verified backup. Temporary files were removed. The successful attempt used the validated same-directory `File.Move(..., overwrite: true)` rename.

### Restart actions

- Owner identity: `QUANPC\hoang`.
- Owner token Administrator status: `false`.
- `com.docker.service` was already `Running`; it was not restarted because Administrator authority was unavailable and no service start was necessary.
- Docker Desktop was launched normally from `C:\Program Files\Docker\Docker\Docker Desktop.exe`.
- Fresh Docker Desktop UI/backend processes started.
- Owner `wsl -l -v` completed and showed `docker-desktop` still `Stopped`, version 2.
- No unrelated WSL distribution was present or terminated.

### Post-repair error and health results

The previous error **returned**. Fresh backend log evidence at `2026-09-09T15:01:46.868391700Z` recorded the same inference-manager cancellation, followed by the backend crash at `15:02:18.880621700Z`:

```text
backend cancelling with error: starting services: initializing Inference manager:
listening on unix://<HOME>\AppData\Local\Docker\run\dockerInference:
remove <HOME>\AppData\Local\Docker\run\dockerInference:
The file cannot be accessed by the system.
(listener: The filename, directory name, or volume label syntax is incorrect.)
```

Bounded Owner health checks:

```text
docker version: no usable result within 30 seconds; task-started CLI process did not remain running
docker info:    no usable result within 30 seconds; task-started CLI process did not remain running
```

Final Codex-context checks completed within 30 seconds but were not healthy (unrelated plugin detail omitted):

```text
docker version: exit 1; Client 29.4.3 only; Context default
docker info:    exit 1; Client/plugin information; no usable Server information
error: permission denied while trying to connect to npipe:////./pipe/docker_engine
```

The Owner's Docker context had already been verified as `desktop-linux`, and the fresh backend state remained `Mode:linux`, but no Linux Docker Server became available. This is not `DOCKER_HOST_HEALTHY_CODEX_ACCESS_BLOCKED`, because the Owner checks also failed and the host backend reproduced its crash.

### Preservation confirmation

- The `dockerInference` path was not manually deleted.
- `%LOCALAPPDATA%\Docker` and `%APPDATA%\Docker` were not deleted.
- No Docker container, image, network, volume, database, WSL distribution, or Docker data was removed.
- `daemon.json`, Docker named-pipe ACLs, group membership, Windows features, BIOS/virtualization settings, and security controls were not modified.
- No PostgreSQL container was created and no PostgreSQL validation was started.
- No Django source, frontend file, or AI FACTORY content was changed.
- No commit or push was performed.

### Repair verdict

`BLOCKED_DOCKER_ENGINE_UNHEALTHY`

The three requested inference flags are now explicitly `false`, but Docker Desktop 4.74.0 still initializes the inference manager and crashes on the pre-existing inaccessible `dockerInference` reparse point. The Engine therefore remains unavailable for Phase 3B PostgreSQL work.

## 18. Authorized stale-endpoint quarantine attempt (2026-09-10)

### Isolation and pre-action state

The repository isolation checks again matched `hoangquocquan/Django-web-t-123`, branch `codex/demo-database-validation`, with both `django_backend/` and `figma_make_frontend/` present. The complete diagnostic report was read before the endpoint action. AI FACTORY was not read or modified.

Docker Desktop UI and `com.docker.backend` processes were confirmed absent before target validation. No unrelated process was stopped.

### Exact target validation

```text
Normalized target: C:\Users\hoang\AppData\Local\Docker\run\dockerInference
Normalized parent: C:\Users\hoang\AppData\Local\Docker\run
Is directory:      false
Length:            0
Attributes:        Archive, ReparsePoint
Is reparse point:  true
```

The normalized target and parent matched the Owner-authorized paths exactly. The reparse point was not followed or enumerated.

### Quarantine and removal result

The recoverable same-directory rename to `dockerInference.stale.<timestamp>` was attempted first, using a literal validated path, no wildcard, no recursion, and no overwrite. It failed with:

```text
The file cannot be accessed by the system.
```

No quarantine path was created and the original endpoint remained in place.

The fallback exact removal was prepared only after repeating the strict target validations. Execution outside the Codex sandbox was denied by the host approval system because the account had reached its usage limit. The removal was not attempted through another mechanism, and no security boundary was bypassed.

Final read-only verification still showed the exact endpoint as a zero-byte `Archive, ReparsePoint` object, with Docker Desktop UI/backend processes absent.

### Owner action required

Open **PowerShell as Administrator**, ensure Docker Desktop is fully quit, and run only:

```powershell
Remove-Item -LiteralPath 'C:\Users\hoang\AppData\Local\Docker\run\dockerInference' -Force
```

Then verify only that exact active path is absent:

```powershell
Test-Path -LiteralPath 'C:\Users\hoang\AppData\Local\Docker\run\dockerInference'
```

Expected result: `False`. Do not target the parent `run` directory, use a wildcard, add `-Recurse`, or delete any quarantine/data path.

Docker Desktop was not relaunched and Docker/WSL health checks were not rerun because the stale active endpoint remains present.

### Preservation confirmation

No Docker directory, container, image, network, volume, database, WSL distribution, settings file, named-pipe ACL, or project data was removed or modified during this attempt. No PostgreSQL or Phase 3C work was started. The only repository modification was appending this report section.

Final Git status remained the pre-existing worktree state listed in section 15, with `DOCKER_DESKTOP_WSL_DIAGNOSTIC_REPORT.md` still the only diagnostic-task repository artifact. No source or frontend status entry changed during this attempt.

### Quarantine-attempt verdict

`OWNER_ACTION_REQUIRED_REMOVE_STALE_ENDPOINT`

### Continuation on 2026-09-12

The endpoint and Docker process state were rechecked before continuing:

```text
Endpoint:      C:\Users\hoang\AppData\Local\Docker\run\dockerInference
Is directory: false
Length:       0
Attributes:   Archive, ReparsePoint
Docker Desktop UI/backend processes: absent
com.docker.service: Stopped (Manual)
```

The endpoint timestamps were newer than the earlier observation (`CreationTime` 2026-09-10 21:57:09; `LastWriteTime` 2026-09-11 23:48:02), so no stale identity assumption was reused. The target, exact parent, non-directory status, zero length, and reparse-point attribute were revalidated in the same command immediately before each attempted mutation.

An Owner-context exact removal using literal-path `Remove-Item -Force`, without wildcard or recursion, failed:

```text
The file cannot be accessed by the system.
```

The Windows reparse-point-specific mechanism was then tried on only the same validated endpoint:

```text
fsutil reparsepoint delete C:\Users\hoang\AppData\Local\Docker\run\dockerInference
Error 1920: The file cannot be accessed by the system.
```

Because removal of the reparse metadata failed, the follow-up ordinary-file deletion was not attempted. The endpoint remains present and unchanged. No parent directory or other Docker path was touched.

Docker Desktop was not relaunched and health checks were not run because the required precondition—removal of the active stale endpoint—was not achieved. Administrator/Owner action remains required. The current final verdict remains:

`OWNER_ACTION_REQUIRED_REMOVE_STALE_ENDPOINT`
