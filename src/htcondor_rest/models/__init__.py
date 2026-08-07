from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CondorStatus(BaseModel):
    model_config = ConfigDict(extra="allow")


class CondorSubmit(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "executable": "/usr/bin/echo",
                "arguments": "Hello World",
                "count": 1,
                "output": "/tmp/out",
                "error": "/tmp/err",
                "log": "/tmp/log",
                "request_cpus": "1",
                "request_memory": "1",
                "request_disk": "1",
            }
        },
    )
    count: int = Field(
        1,
        description="Number of processes (procs) to submit for this cluster.",
    )
    spool: bool = Field(
        False,
        description=(
            "If true, submit the job(s) on hold so their input files can later "
            "be uploaded to the schedd's SPOOL directory via /condor_spool."
        ),
    )
    jobbatchname: str | None = Field(
        None,
        description="Desired job batch name",
    )
    executable: str | None = Field(
        None,
        description="Path to the executable (relative to the submit directory).",
    )
    arguments: str | None = Field(
        None,
        description=("Command-line arguments space separated"),
    )
    environment: str | None = Field(
        None,
        description="Environment variables",
    )
    error: str | None = Field(
        None,
        description="File that receives the job's *stderr* (defaults to /dev/null on Unix).",
    )
    input: str | None = Field(
        None,
        description="File that provides *stdin* to the job (defaults to /dev/null on Unix).",
    )
    output: str | None = Field(
        None,
        description="File that receives the job's *stdout* (defaults to /dev/null on Unix).",
    )
    log: str | None = Field(
        None,
        description="Event-log file for the whole cluster.",
    )
    log_xml: bool | None = Field(
        None,
        description="If true, the event log is written in ClassAd XML.",
    )
    priority: int | str | None = Field(
        None,
        description="Job priority (integer, default 0).",
    )
    request_cpus: int | str | None = Field(
        None,
        description="Number of CPU cores requested (default 1).",
    )
    request_memory: str | None = Field(
        None,
        description="Memory request - stored internally as KiB.  Accepts int (KiB) or str with units.",
    )
    request_disk: str | None = Field(
        None,
        description="Disk request - stored internally as KiB.  Accepts int or unit string.",
    )
    request_gpus: int | str | None = Field(
        None,
        description="Number of GPUs requested.",
    )
    require_gpus: str | None = Field(
        None,
        description="GPU constraint expression.",
    )
    request_custom: dict[str, int] | None = Field(
        None,
        description="Custom resources: ``request_<name> = <quantity>``.",
    )


class CondorJob(BaseModel):
    # ------------------------------------------------------------------
    # Core scalar fields (most of them are directly convertible)
    # ------------------------------------------------------------------
    JobBatchName: str | None = Field(None, alias="JobBatchName")
    In: str | None = Field(None, alias="In")
    Cmd: str | None = Field(None, alias="Cmd")
    Err: str | None = Field(None, alias="Err")
    Iwd: str | None = Field(None, alias="Iwd")
    Out: str | None = Field(None, alias="Out")
    Args: str | None = Field(None, alias="Args")
    Rank: float | str | None = Field(None, alias="Rank")
    User: str | None = Field(None, alias="User")
    Owner: str | None = Field(None, alias="Owner")
    Name: str | None = Field(None, alias="Name")
    QDate: int | str | None = Field(None, alias="QDate")
    MyType: str | None = Field(None, alias="MyType")
    ProcId: int | str | None = Field(None, alias="ProcId")
    JobPrio: int | str | None = Field(None, alias="JobPrio")
    UserLog: str | None = Field(None, alias="UserLog")
    ExitCode: int | str | None = Field(None, alias="ExitCode")
    MaxHosts: int | str | None = Field(None, alias="MaxHosts")
    MinHosts: int | str | None = Field(None, alias="MinHosts")
    NumCkpts: int | str | None = Field(None, alias="NumCkpts")
    BytesSent: float | str | None = Field(None, alias="BytesSent")
    ClusterId: int | str | None = Field(None, alias="ClusterId")
    DiskUsage: int | str | None = Field(None, alias="DiskUsage")
    ImageSize: int | str | None = Field(None, alias="ImageSize")
    JobStatus: int | str | None = Field(None, alias="JobStatus")
    StreamErr: bool | None = Field(None, alias="StreamErr")
    StreamOut: bool | None = Field(None, alias="StreamOut")
    BlockReads: int | str | None = Field(None, alias="BlockReads")
    BytesRecvd: float | str | None = Field(None, alias="BytesRecvd")
    ExitStatus: int | str | None = Field(None, alias="ExitStatus")
    TargetType: str | None = Field(None, alias="TargetType")
    TransferIn: bool | None = Field(None, alias="TransferIn")
    BlockWrites: int | str | None = Field(None, alias="BlockWrites")
    Environment: str | None = Field(None, alias="Environment")
    GlobalJobId: str | None = Field(None, alias="GlobalJobId")
    JobRunCount: int | str | None = Field(None, alias="JobRunCount")
    JobUniverse: int | str | None = Field(None, alias="JobUniverse")
    MemoryUsage: float | str | None = Field(None, alias="MemoryUsage")
    NumRestarts: int | str | None = Field(None, alias="NumRestarts")
    RequestCpus: int | str | None = Field(None, alias="RequestCpus")
    RequestDisk: int | str | None = Field(None, alias="RequestDisk")
    RequestGpus: int | str | None = Field(None, alias="RequestGpus")
    CurrentHosts: int | str | None = Field(None, alias="CurrentHosts")
    runtime_minutes: int | str | None = Field(None, alias="runtime_minutes")
    ExitBySignal: bool | None = Field(None, alias="ExitBySignal")
    JobStartDate: int | str | None = Field(None, alias="JobStartDate")
    NumCkpts_RAW: int | str | None = Field(None, alias="NumCkpts_RAW")
    NumJobStarts: int | str | None = Field(None, alias="NumJobStarts")
    OrigMaxHosts: int | str | None = Field(None, alias="OrigMaxHosts")
    RemoteSysCpu: float | str | None = Field(None, alias="RemoteSysCpu")
    Requirements: str | None = Field(None, alias="Requirements")
    CommittedTime: int | str | None = Field(None, alias="CommittedTime")
    CondorVersion: str | None = Field(None, alias="CondorVersion")
    DiskUsage_RAW: int | str | None = Field(None, alias="DiskUsage_RAW")
    ImageSize_RAW: int | str | None = Field(None, alias="ImageSize_RAW")
    LastJobStatus: int | str | None = Field(None, alias="LastJobStatus")
    LastMatchTime: int | str | None = Field(None, alias="LastMatchTime")
    NumJobMatches: int | str | None = Field(None, alias="NumJobMatches")
    RemoteUserCpu: float | str | None = Field(None, alias="RemoteUserCpu")
    RequestMemory: int | str | None = Field(None, alias="RequestMemory")
    CompletionDate: int | str | None = Field(None, alias="CompletionDate")
    CondorPlatform: str | None = Field(None, alias="CondorPlatform")
    ExecutableSize: int | str | None = Field(None, alias="ExecutableSize")
    LastRemoteHost: str | None = Field(None, alias="LastRemoteHost")
    NumSystemHolds: int | str | None = Field(None, alias="NumSystemHolds")
    BlockReadKbytes: int | str | None = Field(None, alias="BlockReadKbytes")
    CpusProvisioned: int | str | None = Field(None, alias="CpusProvisioned")
    DiskProvisioned: int | str | None = Field(None, alias="DiskProvisioned")
    GPUsProvisioned: int | str | None = Field(None, alias="GPUsProvisioned")
    JobNotification: int | str | None = Field(None, alias="JobNotification")
    JobSubmitMethod: int | str | None = Field(None, alias="JobSubmitMethod")
    LeaveJobInQueue: bool | None = Field(None, alias="LeaveJobInQueue")
    NumShadowStarts: int | str | None = Field(None, alias="NumShadowStarts")
    ResidentSetSize: int | str | None = Field(None, alias="ResidentSetSize")
    StartdPrincipal: str | None = Field(None, alias="StartdPrincipal")
    BlockWriteKbytes: int | str | None = Field(None, alias="BlockWriteKbytes")
    FileSystemDomain: str | None = Field(None, alias="FileSystemDomain")
    JobLeaseDuration: int | str | None = Field(None, alias="JobLeaseDuration")
    MachineAttrCpus0: int | str | None = Field(None, alias="MachineAttrCpus0")
    RecentBlockReads: int | str | None = Field(None, alias="RecentBlockReads")
    TotalSubmitProcs: int | str | None = Field(None, alias="TotalSubmitProcs")
    TotalSuspensions: int | str | None = Field(None, alias="TotalSuspensions")
    CommittedSlotTime: float | str | None = Field(None, alias="CommittedSlotTime")
    FirstJobMatchDate: int | str | None = Field(None, alias="FirstJobMatchDate")
    LastPublicClaimId: str | None = Field(None, alias="LastPublicClaimId")
    MemoryProvisioned: int | str | None = Field(None, alias="MemoryProvisioned")
    NumJobCompletions: int | str | None = Field(None, alias="NumJobCompletions")
    RecentBlockWrites: int | str | None = Field(None, alias="RecentBlockWrites")
    ActivationDuration: int | str | None = Field(None, alias="ActivationDuration")
    CumulativeSlotTime: float | str | None = Field(None, alias="CumulativeSlotTime")
    ExecutableSize_RAW: int | str | None = Field(None, alias="ExecutableSize_RAW")
    LastSuspensionTime: int | str | None = Field(None, alias="LastSuspensionTime")
    TerminationPending: bool | None = Field(None, alias="TerminationPending")
    TransferInputStats: dict = Field(default_factory=dict, alias="TransferInputStats")
    InitialWaitDuration: int | str | None = Field(None, alias="InitialWaitDuration")
    JobCurrentStartDate: int | str | None = Field(None, alias="JobCurrentStartDate")
    JobFinishedHookDone: int | str | None = Field(None, alias="JobFinishedHookDone")
    LastJobLeaseRenewal: int | str | None = Field(None, alias="LastJobLeaseRenewal")
    RemoteWallClockTime: float | str | None = Field(None, alias="RemoteWallClockTime")
    ResidentSetSize_RAW: int | str | None = Field(None, alias="ResidentSetSize_RAW")
    ShouldTransferFiles: str | None = Field(None, alias="ShouldTransferFiles")
    TransferInputSizeMB: int | str | None = Field(None, alias="TransferInputSizeMB")
    TransferOutputStats: dict = Field(default_factory=dict, alias="TransferOutputStats")
    EnteredCurrentStatus: int | str | None = Field(None, alias="EnteredCurrentStatus")
    StatsLifetimeStarter: int | str | None = Field(None, alias="StatsLifetimeStarter")
    WhenToTransferOutput: str | None = Field(None, alias="WhenToTransferOutput")
    RecentBlockReadKbytes: int | str | None = Field(None, alias="RecentBlockReadKbytes")
    CumulativeRemoteSysCpu: float | str | None = Field(
        None, alias="CumulativeRemoteSysCpu"
    )
    ExecuteDirWasEncrypted: bool | None = Field(None, alias="ExecuteDirWasEncrypted")
    MachineAttrSlotWeight0: int | str | None = Field(
        None, alias="MachineAttrSlotWeight0"
    )
    RecentBlockWriteKbytes: int | str | None = Field(
        None, alias="RecentBlockWriteKbytes"
    )
    ActivationSetupDuration: int | str | None = Field(
        None, alias="ActivationSetupDuration"
    )
    CommittedSuspensionTime: int | str | None = Field(
        None, alias="CommittedSuspensionTime"
    )
    CumulativeRemoteUserCpu: float | str | None = Field(
        None, alias="CumulativeRemoteUserCpu"
    )
    LastRemoteWallClockTime: float | str | None = Field(
        None, alias="LastRemoteWallClockTime"
    )
    TransferInputFileCounts: dict[str, int] = Field(
        default_factory=dict, alias="TransferInputFileCounts"
    )
    CumulativeSuspensionTime: int | str | None = Field(
        None, alias="CumulativeSuspensionTime"
    )
    ActivationTeardownDuration: int | str | None = Field(
        None, alias="ActivationTeardownDuration"
    )
    JobCurrentReconnectAttempt: None = Field(None, alias="JobCurrentReconnectAttempt")
    RecentStatsLifetimeStarter: int | str | None = Field(
        None, alias="RecentStatsLifetimeStarter"
    )
    ActivationExecutionDuration: int | str | None = Field(
        None, alias="ActivationExecutionDuration"
    )
    JobCurrentStartExecutingDate: int | str | None = Field(
        None, alias="JobCurrentStartExecutingDate"
    )

    @field_validator(
        "Rank",
        "BytesSent",
        "BytesRecvd",
        "RemoteSysCpu",
        "RemoteUserCpu",
        "MemoryUsage",
        "CommittedSlotTime",
        "CumulativeSlotTime",
        "RemoteWallClockTime",
        "CumulativeRemoteSysCpu",
        "CumulativeRemoteUserCpu",
    )
    def _try_float(cls, v: Any) -> float | str | None:
        if v is None:
            return None
        elif isinstance(v, (int, float)):
            return float(v)
        else:
            return 0.0

    @field_validator(
        "StreamErr",
        "StreamOut",
        "TransferIn",
        "ExitBySignal",
        "LeaveJobInQueue",
        "TerminationPending",
        "ExecuteDirWasEncrypted",
    )
    def _boolify(cls, v: Any) -> bool | None:
        if v is None:
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            lowered = v.lower()
            if lowered in {"true", "yes", "1"}:
                return True
            if lowered in {"false", "no", "0"}:
                return False
        return None

    @field_validator(
        "QDate",
        "JobStartDate",
        "CompletionDate",
        "FirstJobMatchDate",
        "LastMatchTime",
        "LastPublicClaimId",
        "JobCurrentStartDate",
        "JobFinishedHookDone",
        "LastJobLeaseRenewal",
        "EnteredCurrentStatus",
        "JobCurrentStartExecutingDate",
    )
    def _intify(cls, v: Any) -> int | str | None:
        if v is None:
            return None
        if isinstance(v, int):
            return v
        try:
            return int(v)
        except ValueError:
            return None


class CondorSubmitResults(BaseModel):
    cluster: str | int | None = Field(
        None,
        description=("Cluster ID"),
    )
    clusterad: str | CondorJob | None = Field(
        None,
        description=("CondorJob definition from submission"),
    )
    first_proc: str | int | None = Field(
        None,
        description=("First Proc"),
    )
    num_procs: str | int | None = Field(
        None,
        description=("Number of Proc"),
    )
    submit_script: str | None = Field(
        None,
        description=("Rendered Submit Script"),
    )


class CondorSubmitText(BaseModel):
    submit_text: str = Field(
        ...,
        description=(
            "A complete job submit description in the condor_submit language, "
            "including any queue statement."
        ),
    )
    count: int = Field(
        0,
        description=(
            "Number of procs to submit; 0 uses the count from the queue "
            "statement in the submit text."
        ),
    )
    spool: bool = Field(
        False,
        description=(
            "If true, submit the job(s) on hold so their input files can later "
            "be uploaded to the schedd's SPOOL directory via /condor_spool."
        ),
    )


class CondorJobAction(BaseModel):
    job_ids: list[str] | None = Field(
        None,
        description=(
            "Job IDs to act on, e.g. ``['123.0', '123.1']`` or ``['123']`` "
            "for a whole cluster.  Mutually exclusive with ``constraint``."
        ),
    )
    constraint: str | None = Field(
        None,
        description=(
            "ClassAd expression selecting which jobs to act on, e.g. "
            '``Owner == "somebody"``.  Mutually exclusive with ``job_ids``.'
        ),
    )
    reason: str | None = Field(
        None,
        description="Free-form justification for the action.",
    )


class CondorEdit(BaseModel):
    job_ids: list[str] | None = Field(
        None,
        description="Job IDs to edit.  Mutually exclusive with ``constraint``.",
    )
    constraint: str | None = Field(
        None,
        description="ClassAd expression selecting which jobs to edit.",
    )
    attr: str = Field(
        ...,
        description="ClassAd attribute to change.",
    )
    value: str = Field(
        ...,
        description="New value for the attribute (string form of a ClassAd expression).",
    )


class CondorExport(BaseModel):
    job_ids: list[str] | None = Field(
        None,
        description="Job IDs to export.  Mutually exclusive with ``constraint``.",
    )
    constraint: str | None = Field(
        None,
        description="ClassAd expression selecting which jobs to export.",
    )
    export_dir: str = Field(
        ...,
        description="Write the exported job(s) into this directory.",
    )
    new_spool_dir: str = Field(
        ...,
        description="The IWD of the exported job(s).",
    )


class CondorImport(BaseModel):
    import_dir: str = Field(
        ...,
        description="Read the imported jobs from this directory.",
    )


class CondorUnexport(BaseModel):
    job_ids: list[str] | None = Field(
        None,
        description="Job IDs to unexport.  Mutually exclusive with ``constraint``.",
    )
    constraint: str | None = Field(
        None,
        description="ClassAd expression selecting which jobs to unexport.",
    )


class CondorJobSpec(BaseModel):
    """Select a set of jobs by explicit IDs or by a constraint expression."""

    job_ids: list[str] | None = Field(
        None,
        description="Job IDs, e.g. ``['123.0', '123.1']``.  Mutually exclusive with ``constraint``.",
    )
    constraint: str | None = Field(
        None,
        description="ClassAd expression selecting which jobs to act on.",
    )


class CondorRecAction(BaseModel):
    """Act on user or project accounting records."""

    spec: str | list[str] | None = Field(
        None,
        description=(
            "Record name(s): a single name, a list of names, or for updates "
            "a list of ClassAd-style dicts.  Mutually exclusive with ``constraint``."
        ),
    )
    constraint: str | None = Field(
        None,
        description="ClassAd expression selecting which records to act on.",
    )
    reason: str | None = Field(
        None,
        description="Free-form justification for the action.",
    )


class CondorRecUpdate(BaseModel):
    """Update user or project accounting records."""

    ads: list[dict[str, Any]] = Field(
        ...,
        description=(
            "List of ClassAd-style dicts with the new attribute values.  Each "
            "ad must identify the record(s) to update (e.g. via a Name/User or "
            "Requirements attribute)."
        ),
    )


class CondorRefreshGSIProxy(BaseModel):
    cluster: int = Field(..., description="The job's cluster ID.")
    proc: int = Field(..., description="The job's proc ID.")
    proxy_filename: str = Field(
        ..., description="The name of the file containing the refreshed proxy."
    )
    lifetime: int = Field(
        -1,
        description=(
            "Desired lifetime (seconds) of the refreshed proxy.  0 keeps the "
            "current lifetime; -1 uses DELEGATE_JOB_GSI_CREDENTIALS_LIFETIME."
        ),
    )


class CondorOCU(BaseModel):
    """One-Click-University claim request, expressed as a ClassAd."""

    request: dict[str, Any] = Field(
        ...,
        description=(
            "ClassAd representing the OCU claim request (must contain Owner and "
            "RequestCpus/RequestMemory; query requests may be empty)."
        ),
    )


class CondorAdvertise(BaseModel):
    ads: list[dict[str, Any]] = Field(
        ...,
        description="ClassAd(s) to advertise to the collector.",
    )
    command: str = Field(
        "UPDATE_AD_GENERIC",
        description=(
            "The 'advertise command' specifying which kind of ad is being "
            "added; see the condor_advertise manpage for valid values."
        ),
    )
    use_tcp: bool = Field(
        True,
        description="Never set this to false.",
    )
