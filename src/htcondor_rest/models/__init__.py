from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class CondorSubmit(BaseModel):
    model_config = ConfigDict(extra="allow")
    jobbatchname: Optional[str] = Field(None, description="Desired job batch name")
    executable: Optional[str] = Field(
        None, description="Path to the executable (relative to the submit directory)."
    )
    arguments: Optional[str] = Field(
        None,
        description=("Command-line arguments space seperated"),
    )
    environment: Optional[str] = Field(
        None,
        description="Environment variables",
    )
    error: Optional[str] = Field(
        None,
        description="File that receives the job's *stderr* (defaults to /dev/null on Unix).",
    )
    input: Optional[str] = Field(
        None,
        description="File that provides *stdin* to the job (defaults to /dev/null on Unix).",
    )
    output: Optional[str] = Field(
        None,
        description="File that receives the job's *stdout* (defaults to /dev/null on Unix).",
    )
    log: Optional[str] = Field(
        None,
        description="Event-log file for the whole cluster.",
    )
    log_xml: Optional[bool] = Field(
        None,
        description="If true, the event log is written in ClassAd XML.",
    )
    priority: Optional[int | str] = Field(
        None,
        description="Job priority (integer, default 0).",
    )
    request_cpus: Optional[int | str] = Field(
        None,
        description="Number of CPU cores requested (default 1).",
    )
    request_memory: Optional[str] = Field(
        None,
        description="Memory request - stored internally as KiB.  Accepts int (KiB) or str with units.",
    )
    request_disk: Optional[str] = Field(
        None,
        description="Disk request - stored internally as KiB.  Accepts int or unit string.",
    )
    request_gpus: Optional[int | str] = Field(
        None,
        description="Number of GPUs requested.",
    )
    require_gpus: Optional[str] = Field(
        None,
        description="GPU constraint expression.",
    )
    request_custom: Dict[str, int] = Field(
        None,
        description="Custom resources: ``request_<name> = <quantity>``.",
    )
    model_config = {
        "json_schema_extra": {
            "example": {
                "executable": "/usr/bin/echo",
                "arguments": "Hello World",
                "output": "/tmp/out",
                "error": "/tmp/err",
                "log": "/tmp/log",
                "request_cpus": "1",
                "request_memory": "1",
                "request_disk": "1",
            }
        }
    }


class CondorJob(BaseModel):
    # ------------------------------------------------------------------
    # Core scalar fields (most of them are directly convertible)
    # ------------------------------------------------------------------
    JobBatchName: Optional[str] = Field(None, alias="JobBatchName")
    In: Optional[str] = Field(None, alias="In")
    Cmd: Optional[str] = Field(None, alias="Cmd")
    Err: Optional[str] = Field(None, alias="Err")
    Iwd: Optional[str] = Field(None, alias="Iwd")
    Out: Optional[str] = Field(None, alias="Out")
    Args: Optional[str] = Field(None, alias="Args")
    Rank: Optional[float | str] = Field(None, alias="Rank")
    User: Optional[str] = Field(None, alias="User")
    Owner: Optional[str] = Field(None, alias="Owner")
    QDate: Optional[int | str] = Field(None, alias="QDate")
    MyType: Optional[str] = Field(None, alias="MyType")
    ProcId: Optional[int | str] = Field(None, alias="ProcId")
    JobPrio: Optional[int | str] = Field(None, alias="JobPrio")
    UserLog: Optional[str] = Field(None, alias="UserLog")
    ExitCode: Optional[int | str] = Field(None, alias="ExitCode")
    MaxHosts: Optional[int | str] = Field(None, alias="MaxHosts")
    MinHosts: Optional[int | str] = Field(None, alias="MinHosts")
    NumCkpts: Optional[int | str] = Field(None, alias="NumCkpts")
    BytesSent: Optional[float | str] = Field(None, alias="BytesSent")
    ClusterId: Optional[int | str] = Field(None, alias="ClusterId")
    DiskUsage: Optional[int | str] = Field(None, alias="DiskUsage")
    ImageSize: Optional[int | str] = Field(None, alias="ImageSize")
    JobStatus: Optional[int | str] = Field(None, alias="JobStatus")
    StreamErr: Optional[bool] = Field(None, alias="StreamErr")
    StreamOut: Optional[bool] = Field(None, alias="StreamOut")
    BlockReads: Optional[int | str] = Field(None, alias="BlockReads")
    BytesRecvd: Optional[float | str] = Field(None, alias="BytesRecvd")
    ExitStatus: Optional[int | str] = Field(None, alias="ExitStatus")
    TargetType: Optional[str] = Field(None, alias="TargetType")
    TransferIn: Optional[bool] = Field(None, alias="TransferIn")
    BlockWrites: Optional[int | str] = Field(None, alias="BlockWrites")
    Environment: Optional[str] = Field(None, alias="Environment")
    GlobalJobId: Optional[str] = Field(None, alias="GlobalJobId")
    JobRunCount: Optional[int | str] = Field(None, alias="JobRunCount")
    JobUniverse: Optional[int | str] = Field(None, alias="JobUniverse")
    MemoryUsage: Optional[float | str] = Field(None, alias="MemoryUsage")
    NumRestarts: Optional[int | str] = Field(None, alias="NumRestarts")
    RequestCpus: Optional[int | str] = Field(None, alias="RequestCpus")
    RequestDisk: Optional[int | str] = Field(None, alias="RequestDisk")
    CurrentHosts: Optional[int | str] = Field(None, alias="CurrentHosts")
    ExitBySignal: Optional[bool] = Field(None, alias="ExitBySignal")
    JobStartDate: Optional[int | str] = Field(None, alias="JobStartDate")
    NumCkpts_RAW: Optional[int | str] = Field(None, alias="NumCkpts_RAW")
    NumJobStarts: Optional[int | str] = Field(None, alias="NumJobStarts")
    OrigMaxHosts: Optional[int | str] = Field(None, alias="OrigMaxHosts")
    RemoteSysCpu: Optional[float | str] = Field(None, alias="RemoteSysCpu")
    Requirements: Optional[str] = Field(None, alias="Requirements")
    CommittedTime: Optional[int | str] = Field(None, alias="CommittedTime")
    CondorVersion: Optional[str] = Field(None, alias="CondorVersion")
    DiskUsage_RAW: Optional[int | str] = Field(None, alias="DiskUsage_RAW")
    ImageSize_RAW: Optional[int | str] = Field(None, alias="ImageSize_RAW")
    LastJobStatus: Optional[int | str] = Field(None, alias="LastJobStatus")
    LastMatchTime: Optional[int | str] = Field(None, alias="LastMatchTime")
    NumJobMatches: Optional[int | str] = Field(None, alias="NumJobMatches")
    RemoteUserCpu: Optional[float | str] = Field(None, alias="RemoteUserCpu")
    RequestMemory: Optional[int | str] = Field(None, alias="RequestMemory")
    CompletionDate: Optional[int | str] = Field(None, alias="CompletionDate")
    CondorPlatform: Optional[str] = Field(None, alias="CondorPlatform")
    ExecutableSize: Optional[int | str] = Field(None, alias="ExecutableSize")
    LastRemoteHost: Optional[str] = Field(None, alias="LastRemoteHost")
    NumSystemHolds: Optional[int | str] = Field(None, alias="NumSystemHolds")
    BlockReadKbytes: Optional[int | str] = Field(None, alias="BlockReadKbytes")
    CpusProvisioned: Optional[int | str] = Field(None, alias="CpusProvisioned")
    DiskProvisioned: Optional[int | str] = Field(None, alias="DiskProvisioned")
    GPUsProvisioned: Optional[int | str] = Field(None, alias="GPUsProvisioned")
    JobNotification: Optional[int | str] = Field(None, alias="JobNotification")
    JobSubmitMethod: Optional[int | str] = Field(None, alias="JobSubmitMethod")
    LeaveJobInQueue: Optional[bool] = Field(None, alias="LeaveJobInQueue")
    NumShadowStarts: Optional[int | str] = Field(None, alias="NumShadowStarts")
    ResidentSetSize: Optional[int | str] = Field(None, alias="ResidentSetSize")
    StartdPrincipal: Optional[str] = Field(None, alias="StartdPrincipal")
    BlockWriteKbytes: Optional[int | str] = Field(None, alias="BlockWriteKbytes")
    FileSystemDomain: Optional[str] = Field(None, alias="FileSystemDomain")
    JobLeaseDuration: Optional[int | str] = Field(None, alias="JobLeaseDuration")
    MachineAttrCpus0: Optional[int | str] = Field(None, alias="MachineAttrCpus0")
    RecentBlockReads: Optional[int | str] = Field(None, alias="RecentBlockReads")
    TotalSubmitProcs: Optional[int | str] = Field(None, alias="TotalSubmitProcs")
    TotalSuspensions: Optional[int | str] = Field(None, alias="TotalSuspensions")
    CommittedSlotTime: Optional[float | str] = Field(None, alias="CommittedSlotTime")
    FirstJobMatchDate: Optional[int | str] = Field(None, alias="FirstJobMatchDate")
    LastPublicClaimId: Optional[str] = Field(None, alias="LastPublicClaimId")
    MemoryProvisioned: Optional[int | str] = Field(None, alias="MemoryProvisioned")
    NumJobCompletions: Optional[int | str] = Field(None, alias="NumJobCompletions")
    RecentBlockWrites: Optional[int | str] = Field(None, alias="RecentBlockWrites")
    ActivationDuration: Optional[int | str] = Field(None, alias="ActivationDuration")
    CumulativeSlotTime: Optional[float | str] = Field(None, alias="CumulativeSlotTime")
    ExecutableSize_RAW: Optional[int | str] = Field(None, alias="ExecutableSize_RAW")
    LastSuspensionTime: Optional[int | str] = Field(None, alias="LastSuspensionTime")
    TerminationPending: Optional[bool] = Field(None, alias="TerminationPending")
    TransferInputStats: Dict = Field(default_factory=dict, alias="TransferInputStats")
    InitialWaitDuration: Optional[int | str] = Field(None, alias="InitialWaitDuration")
    JobCurrentStartDate: Optional[int | str] = Field(None, alias="JobCurrentStartDate")
    JobFinishedHookDone: Optional[int | str] = Field(None, alias="JobFinishedHookDone")
    LastJobLeaseRenewal: Optional[int | str] = Field(None, alias="LastJobLeaseRenewal")
    RemoteWallClockTime: Optional[float | str] = Field(
        None, alias="RemoteWallClockTime"
    )
    ResidentSetSize_RAW: Optional[int | str] = Field(None, alias="ResidentSetSize_RAW")
    ShouldTransferFiles: Optional[str] = Field(None, alias="ShouldTransferFiles")
    TransferInputSizeMB: Optional[int | str] = Field(None, alias="TransferInputSizeMB")
    TransferOutputStats: Dict = Field(default_factory=dict, alias="TransferOutputStats")
    EnteredCurrentStatus: Optional[int | str] = Field(
        None, alias="EnteredCurrentStatus"
    )
    StatsLifetimeStarter: Optional[int | str] = Field(
        None, alias="StatsLifetimeStarter"
    )
    WhenToTransferOutput: Optional[str] = Field(None, alias="WhenToTransferOutput")
    RecentBlockReadKbytes: Optional[int | str] = Field(
        None, alias="RecentBlockReadKbytes"
    )
    CumulativeRemoteSysCpu: Optional[float | str] = Field(
        None, alias="CumulativeRemoteSysCpu"
    )
    ExecuteDirWasEncrypted: Optional[bool] = Field(None, alias="ExecuteDirWasEncrypted")
    MachineAttrSlotWeight0: Optional[int | str] = Field(
        None, alias="MachineAttrSlotWeight0"
    )
    RecentBlockWriteKbytes: Optional[int | str] = Field(
        None, alias="RecentBlockWriteKbytes"
    )
    ActivationSetupDuration: Optional[int | str] = Field(
        None, alias="ActivationSetupDuration"
    )
    CommittedSuspensionTime: Optional[int | str] = Field(
        None, alias="CommittedSuspensionTime"
    )
    CumulativeRemoteUserCpu: Optional[float | str] = Field(
        None, alias="CumulativeRemoteUserCpu"
    )
    LastRemoteWallClockTime: Optional[float | str] = Field(
        None, alias="LastRemoteWallClockTime"
    )
    TransferInputFileCounts: Dict[str, int] = Field(
        default_factory=dict, alias="TransferInputFileCounts"
    )
    CumulativeSuspensionTime: Optional[int | str] = Field(
        None, alias="CumulativeSuspensionTime"
    )
    ActivationTeardownDuration: Optional[int | str] = Field(
        None, alias="ActivationTeardownDuration"
    )
    JobCurrentReconnectAttempt: Optional[None] = Field(
        None, alias="JobCurrentReconnectAttempt"
    )
    RecentStatsLifetimeStarter: Optional[int | str] = Field(
        None, alias="RecentStatsLifetimeStarter"
    )
    ActivationExecutionDuration: Optional[int | str] = Field(
        None, alias="ActivationExecutionDuration"
    )
    JobCurrentStartExecutingDate: Optional[int | str] = Field(
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
    def _try_float(cls, v: Any) -> Optional[float | str]:
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
    def _boolify(cls, v: Any) -> Optional[bool]:
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
    def _intify(cls, v: Any) -> Optional[int | str]:
        if v is None:
            return None
        if isinstance(v, int):
            return v
        try:
            return int(v)
        except ValueError:
            return None


class CondorSubmitResults(BaseModel):
    cluster: Optional[str | int] = Field(
        None,
        description=("Cluster ID"),
    )
    clusterad: Optional[str | CondorJob] = Field(
        None,
        description=("CondorJob definition from submission"),
    )
    first_proc: Optional[str | int] = Field(
        None,
        description=("First Proc"),
    )
    num_procs: Optional[str | int] = Field(
        None,
        description=("Number of Proc"),
    )
    submit_script: Optional[str] = Field(
        None,
        description=("Rendered Submit Script"),
    )
