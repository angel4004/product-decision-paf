#!/usr/bin/env python3
"""Reference filesystem host adapter for versioned PAF hypothesis state.

The adapter uses only the Python standard library. It never chooses a storage
root, calls a network service, or writes inside the skill package. A caller must
provide an explicit proposal-intent file for read-only intent validation, or an
absolute state root and explicit change-set file for persistence.
"""

from __future__ import annotations

import argparse
import copy
import errno
import hashlib
import json
import math
import os
import re
import secrets
import socket
import stat
import sys
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = PACKAGE_ROOT / "assets"
BUNDLE_FILENAME = "hypothesis-state-bundle.json"
LOCK_FILENAME = "hypothesis-state.lock"
LOCK_GATE_FILENAME = ".hypothesis-state.lock.gate"
MAX_BUNDLE_BYTES = 32 * 1024 * 1024
MAX_CHANGE_SET_BYTES = 36 * 1024 * 1024
MAX_PROPOSAL_INTENT_BYTES = 1024 * 1024
MAX_LOCK_BYTES = 4096
MAX_JSON_DEPTH = 128
MAX_REVISION_COUNT = 10_000
MAX_SAFE_INTEGER = 9_007_199_254_740_991

WORKSPACE_SCHEMA = "hypothesis-workspace-state.schema.json"
CHANGE_SET_SCHEMA = "hypothesis-change-set.schema.json"
PROPOSAL_INTENT_SCHEMA = "hypothesis-proposal-intent.schema.json"
RECEIPT_SCHEMA = "persistence-receipt.schema.json"
BUNDLE_SCHEMA = "hypothesis-state-bundle.schema.json"

STABLE_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
TERMINAL_STATES = {"closed", "cancelled", "superseded"}
RUNNABLE_STATES = {"ready_to_run", "running", "ready_for_review", "closed"}
ALLOWED_TRANSITIONS = {
    "framing": {
        "blocked_upstream",
        "awaiting_owner_rule",
        "ready_to_run",
        "cancelled",
        "superseded",
    },
    "blocked_upstream": {
        "framing",
        "awaiting_owner_rule",
        "cancelled",
        "superseded",
    },
    "awaiting_owner_rule": {
        "framing",
        "ready_to_run",
        "cancelled",
        "superseded",
    },
    "ready_to_run": {"running", "cancelled", "superseded"},
    "running": {"ready_for_review", "cancelled"},
    "ready_for_review": {"running", "closed"},
    "closed": set(),
    "cancelled": set(),
    "superseded": set(),
}

SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", re.I),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{16,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}\b", re.I),
    re.compile(r"(?i)(?:[A-Z]:[\\/]+Users[\\/]+)[^\\/\s`\"'<>]+"),
    re.compile(
        r"(?i)(?:"
        + "|".join(
            re.escape(root)
            for root in ("/" + "Users" + "/", "/" + "home" + "/")
        )
        + r")[^/\s`\"'<>]+"
    ),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    re.compile(
        r"(?<![A-Za-z0-9])(?:\+?\d[\s().-]*){10,15}(?![A-Za-z0-9])"
    ),
    re.compile(
        r"\b(?:raw\s+transcript|private\s+message\s+follows|"
        r"сырая\s+расшифровка|личное\s+сообщение)\b",
        re.I,
    ),
)

SUPPORTED_SCHEMA_KEYWORDS = {
    "$schema",
    "$id",
    "$ref",
    "$defs",
    "title",
    "description",
    "type",
    "additionalProperties",
    "required",
    "properties",
    "const",
    "enum",
    "anyOf",
    "allOf",
    "if",
    "then",
    "else",
    "items",
    "uniqueItems",
    "minItems",
    "minLength",
    "maxLength",
    "minimum",
    "maximum",
    "pattern",
    "format",
}


class AdapterError(Exception):
    """Safe adapter error whose message contains no state payload."""


class OutcomeUnknownError(AdapterError):
    """The atomic replace may have committed, but verification was interrupted."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_bytes(value: object) -> bytes:
    def validate_text(child: str, label: str) -> None:
        if unicodedata.normalize("NFC", child) != child:
            raise AdapterError(f"{label} must use Unicode NFC")
        try:
            child.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise AdapterError(
                f"{label} contains an unpaired Unicode surrogate"
            ) from exc

    def validate_portable_json(child: object) -> None:
        if isinstance(child, dict):
            for key, nested in child.items():
                if not isinstance(key, str):
                    raise AdapterError("JSON object keys must be strings")
                validate_text(key, "JSON object keys")
                validate_portable_json(nested)
        elif isinstance(child, list):
            for nested in child:
                validate_portable_json(nested)
        elif isinstance(child, str):
            validate_text(child, "JSON strings")
        elif isinstance(child, bool) or child is None:
            return
        elif isinstance(child, int):
            if abs(child) > MAX_SAFE_INTEGER:
                raise AdapterError(
                    "JSON integers must fit the interoperable safe range"
                )
        elif isinstance(child, float):
            raise AdapterError(
                "JSON floating-point numbers are not portable; use canonical decimal strings"
            )

    def order_by_utf16(child: object) -> object:
        if isinstance(child, dict):
            return {
                key: order_by_utf16(child[key])
                for key in sorted(
                    child,
                    key=lambda item: item.encode("utf-16-be"),
                )
            }
        if isinstance(child, list):
            return [order_by_utf16(nested) for nested in child]
        return child

    validate_portable_json(value)
    try:
        serialized = json.dumps(
            order_by_utf16(value),
            ensure_ascii=False,
            sort_keys=False,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise AdapterError("value cannot be represented as strict JSON") from exc
    return serialized.encode("utf-8")


def pretty_bytes(value: object) -> bytes:
    try:
        serialized = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise AdapterError("value cannot be represented as strict JSON") from exc
    return (serialized + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def strict_json_loads(text: str) -> object:
    def reject_constant(value: str) -> object:
        raise ValueError(f"non-standard numeric constant {value}")

    def unique_object(pairs: list[tuple[str, object]]) -> dict:
        result: dict = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate object key {key}")
            result[key] = value
        return result

    return json.loads(
        text,
        parse_constant=reject_constant,
        object_pairs_hook=unique_object,
    )


def ensure_json_depth(value: object, label: str) -> None:
    stack: list[tuple[object, int]] = [(value, 1)]
    while stack:
        child, depth = stack.pop()
        if depth > MAX_JSON_DEPTH:
            raise AdapterError(
                f"{label} exceeds the maximum JSON nesting depth"
            )
        if isinstance(child, dict):
            stack.extend((nested, depth + 1) for nested in child.values())
        elif isinstance(child, list):
            stack.extend((nested, depth + 1) for nested in child)


def load_json(
    path: Path,
    label: str,
    *,
    max_bytes: int = MAX_BUNDLE_BYTES,
) -> object:
    try:
        if is_reparse_point(path):
            raise AdapterError(
                f"{label} must not be a symlink or reparse point"
            )
        metadata = path.stat()
        if not stat.S_ISREG(metadata.st_mode):
            raise AdapterError(f"{label} is not a regular file")
        if metadata.st_size > max_bytes:
            raise AdapterError(f"{label} exceeds its bounded size limit")
        with path.open("rb") as handle:
            raw = handle.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise AdapterError(f"{label} exceeds its bounded size limit")
        loaded = strict_json_loads(raw.decode("utf-8-sig"))
        ensure_json_depth(loaded, label)
        return loaded
    except FileNotFoundError as exc:
        raise AdapterError(f"{label} does not exist") from exc
    except UnicodeDecodeError as exc:
        raise AdapterError(f"{label} is not UTF-8 JSON") from exc
    except json.JSONDecodeError as exc:
        raise AdapterError(
            f"{label} is invalid JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    except ValueError as exc:
        raise AdapterError(f"{label} is not strict JSON") from exc
    except RecursionError as exc:
        raise AdapterError(
            f"{label} exceeds the maximum JSON nesting depth"
        ) from exc
    except OSError as exc:
        raise AdapterError(f"{label} could not be read") from exc


def ensure_state_root(raw_root: Path, *, create: bool) -> Path:
    if not raw_root.is_absolute():
        raise AdapterError("state root must be an absolute path selected by the user")
    if os.name == "nt" and (
        str(raw_root).startswith("\\\\")
        or raw_root.drive.startswith("\\\\")
    ):
        raise AdapterError(
            "reference adapter requires a single-host local filesystem root"
        )
    root = raw_root.resolve()
    if root == PACKAGE_ROOT or root.is_relative_to(PACKAGE_ROOT):
        raise AdapterError("state root must be outside the skill package")
    if create:
        root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
        raise AdapterError("state root does not exist or is not a directory")
    return root


def is_reparse_point(path: Path) -> bool:
    try:
        attributes = path.lstat().st_file_attributes
    except AttributeError:
        return path.is_symlink()
    except FileNotFoundError:
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def checked_child_path(root: Path, filename: str) -> Path:
    path = root / filename
    if path.parent.resolve() != root:
        raise AdapterError("adapter path escapes the selected state root")
    if (path.exists() or path.is_symlink()) and is_reparse_point(path):
        raise AdapterError("adapter refuses a symlink or reparse-point state file")
    return path


def bundle_temp_filename(lock_token: str) -> str:
    return f".{BUNDLE_FILENAME}.{lock_token}.tmp"


def lock_owner_filename(lock_token: str) -> str:
    return f".{LOCK_FILENAME}.{lock_token}.owner"


@contextmanager
def lock_operation_gate(root: Path):
    """Serialize main-lock publication and dead-lock recovery.

    The short-lived advisory lock is released by the operating system when the
    process exits. The one-byte gate file remains for reuse and contains no
    runtime payload.
    """

    gate_path = checked_child_path(root, LOCK_GATE_FILENAME)
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(gate_path, flags, 0o600)
    except OSError as exc:
        raise AdapterError("cannot open the lock-operation gate safely") from exc
    locked = False
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise AdapterError("lock-operation gate is not a regular file")
        if is_reparse_point(gate_path):
            raise AdapterError(
                "adapter refuses a symlink or reparse-point lock-operation gate"
            )
        if metadata.st_size == 0:
            os.write(descriptor, b"\0")
            os.fsync(descriptor)
        elif metadata.st_size != 1:
            raise AdapterError("lock-operation gate is malformed")
        os.lseek(descriptor, 0, os.SEEK_SET)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(
                    descriptor,
                    fcntl.LOCK_EX | fcntl.LOCK_NB,
                )
        except OSError as exc:
            raise AdapterError(
                "another lock operation is already in progress"
            ) from exc
        locked = True
        yield
    finally:
        if locked:
            os.lseek(descriptor, 0, os.SEEK_SET)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def atomic_write(path: Path, data: bytes, *, lock_token: str) -> None:
    if not path.parent.is_dir():
        raise AdapterError("atomic-write parent is not a directory")
    temporary_path = checked_child_path(
        path.parent,
        bundle_temp_filename(lock_token),
    )
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        descriptor = os.open(temporary_path, flags, 0o600)
    except FileExistsError as exc:
        raise AdapterError(
            "lock-owned bundle staging file already exists"
        ) from exc
    replaced = False
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        replaced = True
        if os.name != "nt":
            directory_descriptor = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
    except OSError as exc:
        if replaced:
            raise OutcomeUnknownError(
                "bundle replace completed but filesystem durability verification is unknown"
            ) from exc
        raise
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def warn_lock_cleanup_incomplete(lock_token: str, stage: str) -> None:
    """Report stale-lock risk without changing the authoritative command result."""

    warning = {
        "authoritative_result_unchanged": True,
        "lock_id": lock_token,
        "next_step": "inspect-lock_then_recover-if-owner-dead",
        "stage": stage,
        "warning": "lock_cleanup_required",
    }
    try:
        print(
            json.dumps(warning, ensure_ascii=False, sort_keys=True),
            file=sys.stderr,
        )
    except (OSError, ValueError):
        # A diagnostic failure must not replace an already-known persistence
        # outcome with a misleading command failure.
        pass


@contextmanager
def exclusive_lock(root: Path):
    lock_path = checked_child_path(root, LOCK_FILENAME)
    lock_token = secrets.token_hex(16)
    owner_path = checked_child_path(root, lock_owner_filename(lock_token))
    payload = {
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "token": lock_token,
        "created_at": utc_now(),
        "purpose": "product-decision-paf-state-commit",
        "bundle_temp_filename": bundle_temp_filename(lock_token),
        "owner_filename": owner_path.name,
    }
    owner_data = pretty_bytes(payload)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        with lock_operation_gate(root):
            try:
                descriptor = os.open(owner_path, flags, 0o600)
            except FileExistsError as exc:
                raise AdapterError(
                    "lock owner staging record already exists"
                ) from exc
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(owner_data)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(owner_path, lock_path)
            except FileExistsError as exc:
                raise AdapterError(
                    "state root is locked; inspect the existing lock before retrying"
                ) from exc
            owner_path.unlink()
        yield payload
    finally:
        try:
            owner_path.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            warn_lock_cleanup_incomplete(lock_token, "owner_record_remove")
        try:
            raw = lock_path.read_bytes()
        except FileNotFoundError:
            raw = None
        except OSError:
            warn_lock_cleanup_incomplete(lock_token, "lock_record_read")
            raw = None
        if raw is not None:
            try:
                current = strict_json_loads(raw.decode("utf-8-sig"))
            except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
                current = None
            if isinstance(current, dict) and current.get("token") == lock_token:
                try:
                    lock_path.unlink()
                except FileNotFoundError:
                    pass
                except OSError:
                    warn_lock_cleanup_incomplete(
                        lock_token,
                        "lock_record_remove",
                    )


def read_lock(root: Path) -> tuple[Path, bytes, dict]:
    lock_path = checked_child_path(root, LOCK_FILENAME)
    try:
        metadata = lock_path.stat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_size > MAX_LOCK_BYTES
        ):
            raise AdapterError("lock file is malformed; recovery is not safe")
        with lock_path.open("rb") as handle:
            raw = handle.read(MAX_LOCK_BYTES + 1)
        if len(raw) > MAX_LOCK_BYTES:
            raise AdapterError("lock file is malformed; recovery is not safe")
    except FileNotFoundError as exc:
        raise AdapterError("state root is not locked") from exc
    try:
        payload = strict_json_loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise AdapterError("lock file is malformed; recovery is not safe") from exc
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("pid"), int)
        or isinstance(payload.get("pid"), bool)
        or payload["pid"] <= 0
        or payload.get("host") != socket.gethostname()
        or not isinstance(payload.get("token"), str)
        or re.fullmatch(r"[a-f0-9]{32}", payload["token"]) is None
        or not isinstance(payload.get("created_at"), str)
        or payload.get("purpose") != "product-decision-paf-state-commit"
        or payload.get("bundle_temp_filename")
        != bundle_temp_filename(payload["token"])
        or payload.get("owner_filename")
        != lock_owner_filename(payload["token"])
    ):
        raise AdapterError("lock file is malformed; recovery is not safe")
    return lock_path, raw, payload


def process_liveness(pid: int) -> str:
    if os.name == "nt":
        import ctypes

        process_query_limited_information = 0x1000
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.OpenProcess(
            process_query_limited_information,
            False,
            pid,
        )
        if handle:
            kernel32.CloseHandle(handle)
            return "alive"
        error = ctypes.get_last_error()
        if error in {87, 1168}:
            return "dead"
        if error == 5:
            return "alive"
        return "unknown"
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return "dead"
    except PermissionError:
        return "alive"
    except OSError as exc:
        if exc.errno == errno.ESRCH or getattr(exc, "winerror", None) == 87:
            return "dead"
        return "unknown"
    return "alive"


class SchemaRegistry:
    """Small JSON Schema 2020-12 evaluator for this package's schema subset."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.documents: dict[str, dict] = {}
        for name in (
            WORKSPACE_SCHEMA,
            CHANGE_SET_SCHEMA,
            PROPOSAL_INTENT_SCHEMA,
            RECEIPT_SCHEMA,
            BUNDLE_SCHEMA,
        ):
            document = load_json(root / name, f"schema {name}")
            if not isinstance(document, dict):
                raise AdapterError(f"schema {name} root must be an object")
            self._assert_supported_schema(document, f"schema:{name}")
            self.documents[name] = document

    def _assert_supported_schema(self, schema: dict, path: str) -> None:
        unsupported = sorted(set(schema) - SUPPORTED_SCHEMA_KEYWORDS)
        if unsupported:
            raise AdapterError(
                f"{path} uses unsupported schema keyword {unsupported[0]}"
            )
        if "$ref" in schema and len(schema) != 1:
            raise AdapterError(f"{path} uses unsupported $ref siblings")
        schema_type = schema.get("type")
        if schema_type is not None and schema_type not in {
            "object",
            "array",
            "string",
            "integer",
            "number",
            "boolean",
            "null",
        }:
            raise AdapterError(f"{path} uses an unsupported type declaration")
        schema_format = schema.get("format")
        if schema_format is not None and schema_format != "date-time":
            raise AdapterError(f"{path} uses an unsupported format")
        pattern = schema.get("pattern")
        if pattern is not None:
            if not isinstance(pattern, str):
                raise AdapterError(f"{path}.pattern must be a string")
            try:
                re.compile(pattern)
            except re.error as exc:
                raise AdapterError(f"{path} contains an invalid pattern") from exc
        additional = schema.get("additionalProperties")
        if additional is not None and not isinstance(additional, bool):
            raise AdapterError(
                f"{path} uses unsupported additionalProperties semantics"
            )

        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for name, child in properties.items():
                if not isinstance(child, dict):
                    raise AdapterError(f"{path}.properties.{name} must be an object")
                self._assert_supported_schema(child, f"{path}.properties.{name}")

        definitions = schema.get("$defs", {})
        if isinstance(definitions, dict):
            for name, child in definitions.items():
                if not isinstance(child, dict):
                    raise AdapterError(f"{path}.$defs.{name} must be an object")
                self._assert_supported_schema(child, f"{path}.$defs.{name}")

        for keyword in ("items", "if", "then", "else"):
            child = schema.get(keyword)
            if child is not None:
                if not isinstance(child, dict):
                    raise AdapterError(f"{path}.{keyword} must be an object")
                self._assert_supported_schema(child, f"{path}.{keyword}")

        for keyword in ("anyOf", "allOf"):
            branches = schema.get(keyword, [])
            if not isinstance(branches, list):
                raise AdapterError(f"{path}.{keyword} must be an array")
            for index, child in enumerate(branches):
                if not isinstance(child, dict):
                    raise AdapterError(f"{path}.{keyword}[{index}] must be an object")
                self._assert_supported_schema(child, f"{path}.{keyword}[{index}]")

    def validate(self, value: object, schema_name: str) -> list[str]:
        errors: list[str] = []
        self._validate(value, self.documents[schema_name], schema_name, "$", errors)
        return errors[:50]

    def _resolve_ref(self, reference: str, current_name: str) -> tuple[dict, str]:
        file_part, separator, fragment = reference.partition("#")
        target_name = file_part or current_name
        if target_name not in self.documents:
            raise AdapterError("schema contains an unsupported reference")
        target: object = self.documents[target_name]
        if separator and fragment:
            if not fragment.startswith("/"):
                raise AdapterError("schema contains an unsupported fragment")
            for raw_part in fragment[1:].split("/"):
                part = raw_part.replace("~1", "/").replace("~0", "~")
                if not isinstance(target, dict) or part not in target:
                    raise AdapterError("schema reference does not resolve")
                target = target[part]
        if not isinstance(target, dict):
            raise AdapterError("schema reference does not resolve to an object")
        return target, target_name

    @staticmethod
    def _matches_type(value: object, expected: str) -> bool:
        if expected == "object":
            return isinstance(value, dict)
        if expected == "array":
            return isinstance(value, list)
        if expected == "string":
            return isinstance(value, str)
        if expected == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected == "number":
            return (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(value)
            )
        if expected == "boolean":
            return isinstance(value, bool)
        if expected == "null":
            return value is None
        raise AdapterError("schema contains an unsupported type")

    @staticmethod
    def _valid_datetime(value: str) -> bool:
        candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            return False
        return parsed.tzinfo is not None

    def _branch_valid(
        self,
        value: object,
        schema: dict,
        schema_name: str,
        path: str,
    ) -> bool:
        branch_errors: list[str] = []
        self._validate(value, schema, schema_name, path, branch_errors)
        return not branch_errors

    def _validate(
        self,
        value: object,
        schema: dict,
        schema_name: str,
        path: str,
        errors: list[str],
    ) -> None:
        if len(errors) >= 50:
            return

        reference = schema.get("$ref")
        if isinstance(reference, str):
            target, target_name = self._resolve_ref(reference, schema_name)
            self._validate(value, target, target_name, path, errors)
            return

        any_of = schema.get("anyOf")
        if isinstance(any_of, list) and not any(
            self._branch_valid(value, branch, schema_name, path)
            for branch in any_of
        ):
            errors.append(f"{path}: does not match any allowed schema")
            return

        all_of = schema.get("allOf")
        if isinstance(all_of, list):
            for branch in all_of:
                self._validate(value, branch, schema_name, path, errors)

        conditional = schema.get("if")
        if isinstance(conditional, dict):
            selected = (
                schema.get("then")
                if self._branch_valid(value, conditional, schema_name, path)
                else schema.get("else")
            )
            if isinstance(selected, dict):
                self._validate(value, selected, schema_name, path, errors)

        expected_type = schema.get("type")
        if isinstance(expected_type, str):
            if not self._matches_type(value, expected_type):
                errors.append(f"{path}: expected {expected_type}")
                return

        if "const" in schema and value != schema["const"]:
            errors.append(f"{path}: value does not match required constant")
        if "enum" in schema and value not in schema["enum"]:
            errors.append(f"{path}: value is not in the allowed enum")

        if isinstance(value, dict):
            required = schema.get("required", [])
            if isinstance(required, list):
                for key in required:
                    if key not in value:
                        errors.append(f"{path}: missing required field {key}")
            properties = schema.get("properties", {})
            if isinstance(properties, dict):
                for key, child_schema in properties.items():
                    if key in value and isinstance(child_schema, dict):
                        self._validate(
                            value[key],
                            child_schema,
                            schema_name,
                            f"{path}.{key}",
                            errors,
                        )
                if schema.get("additionalProperties") is False:
                    for key in sorted(set(value) - set(properties)):
                        errors.append(f"{path}: unknown field {key}")

        if isinstance(value, list):
            minimum_items = schema.get("minItems")
            if isinstance(minimum_items, int) and len(value) < minimum_items:
                errors.append(f"{path}: fewer than {minimum_items} items")
            if schema.get("uniqueItems") is True:
                serialized = [canonical_bytes(item) for item in value]
                if len(serialized) != len(set(serialized)):
                    errors.append(f"{path}: items must be unique")
            item_schema = schema.get("items")
            if isinstance(item_schema, dict):
                for index, item in enumerate(value):
                    self._validate(
                        item,
                        item_schema,
                        schema_name,
                        f"{path}[{index}]",
                        errors,
                    )

        if isinstance(value, str):
            minimum_length = schema.get("minLength")
            maximum_length = schema.get("maxLength")
            if isinstance(minimum_length, int) and len(value) < minimum_length:
                errors.append(f"{path}: string is shorter than {minimum_length}")
            if isinstance(maximum_length, int) and len(value) > maximum_length:
                errors.append(f"{path}: string is longer than {maximum_length}")
            pattern = schema.get("pattern")
            if isinstance(pattern, str) and re.search(pattern, value) is None:
                errors.append(f"{path}: string does not match required pattern")
            if schema.get("format") == "date-time" and not self._valid_datetime(value):
                errors.append(f"{path}: invalid date-time")

        minimum = schema.get("minimum")
        if (
            isinstance(minimum, (int, float))
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
            and value < minimum
        ):
            errors.append(f"{path}: number is below minimum {minimum}")
        maximum = schema.get("maximum")
        if (
            isinstance(maximum, (int, float))
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
            and value > maximum
        ):
            errors.append(f"{path}: number is above maximum {maximum}")


def iter_strings(value: object):
    if isinstance(value, dict):
        for child in value.values():
            yield from iter_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_strings(child)
    elif isinstance(value, str):
        yield value


def validate_sensitive_data(value: object) -> list[str]:
    for text in iter_strings(value):
        if re.fullmatch(r"[a-f0-9]{64}", text):
            continue
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            return [
                "payload failed the bounded sensitive-data pattern scan"
            ]
    return []


def validate_proposal_intent_semantics(intent: dict) -> list[str]:
    errors: list[str] = []
    known = intent["known_bindings"]
    requested = intent["requested_change"]
    unresolved = set(intent["unresolved_bindings"])
    operation = intent["requested_operation"]

    binding_values = {
        "workspace_id": known["workspace_id"],
        "product_ref": known["product_ref"],
        "decision_scope": known["decision_scope_id"],
        "owner_tenure": known["owner_tenure_id"],
        "hypothesis_id": known["hypothesis_id"],
        "hypothesis_statement": requested["hypothesis_statement"],
        "hypothesis_class": requested["hypothesis_class"],
        "lifecycle_context": (
            requested["lifecycle_context"]
            if requested["lifecycle_context"]
            else None
        ),
        "segment": requested["segment"],
        "validation_design": requested["validation_design_ref"],
        "write_authority": (
            True if known["write_authority"] is True else None
        ),
        "state_root_or_host_adapter": (
            known["state_root_or_host_adapter_ref"]
        ),
    }
    for binding, value in binding_values.items():
        is_missing = value is None
        is_listed = binding in unresolved
        if is_missing and not is_listed:
            errors.append(
                f"proposal intent omits unresolved binding {binding}"
            )
        elif not is_missing and is_listed:
            errors.append(
                f"proposal intent lists resolved binding {binding} as unresolved"
            )

    expected_revision = known["expected_workspace_revision"]
    candidate_revision = known["candidate_workspace_revision"]
    snapshot_ref = known["current_workspace_snapshot_ref"]
    receipt_ref = known["matching_accepted_receipt_ref"]
    if operation == "create":
        if expected_revision is not None or candidate_revision != 0:
            errors.append(
                "create proposal intent requires expected revision null and "
                "candidate revision 0"
            )
        if snapshot_ref is not None or receipt_ref is not None:
            errors.append(
                "create proposal intent must not bind a prior snapshot or receipt"
            )
        for binding in (
            "current_workspace_snapshot",
            "matching_accepted_receipt",
        ):
            if binding in unresolved:
                errors.append(
                    f"create proposal intent must not require {binding}"
                )
    elif operation == "replace":
        if (
            expected_revision is None
            or candidate_revision is None
            or candidate_revision != expected_revision + 1
        ):
            errors.append(
                "replace proposal intent requires candidate revision exactly "
                "one greater than expected revision"
            )
    else:
        if expected_revision is not None or candidate_revision is not None:
            errors.append(
                "undetermined proposal intent requires both revisions to be null"
            )

    if operation != "create":
        for binding, value in (
            ("current_workspace_snapshot", snapshot_ref),
            ("matching_accepted_receipt", receipt_ref),
        ):
            is_missing = value is None
            is_listed = binding in unresolved
            if is_missing and not is_listed:
                errors.append(
                    f"proposal intent omits unresolved binding {binding}"
                )
            elif not is_missing and is_listed:
                errors.append(
                    f"proposal intent lists resolved binding {binding} as unresolved"
                )

    candidate_state_bindings = {
        "workspace_id",
        "product_ref",
        "current_workspace_snapshot",
        "matching_accepted_receipt",
        "decision_scope",
        "owner_tenure",
        "hypothesis_id",
        "hypothesis_statement",
        "hypothesis_class",
        "lifecycle_context",
        "segment",
        "validation_design",
    }
    if not (unresolved & candidate_state_bindings):
        errors.append(
            "proposal intent requires at least one unresolved candidate-state binding"
        )

    required_materialization = {
        "resolved_bindings",
        "schema_valid_change_set",
        "authorized_host_adapter",
        "write_authority",
    }
    declared_materialization = set(
        intent["materialization_contract"]["required_to_commit"]
    )
    missing_materialization = sorted(
        required_materialization - declared_materialization
    )
    if missing_materialization:
        errors.append(
            "proposal intent materialization contract omits "
            + ", ".join(missing_materialization)
        )
    return errors


def require_unique_ids(items: list[dict], field: str, label: str) -> list[str]:
    values = [item[field] for item in items]
    if len(values) != len(set(values)):
        return [f"{label} contains duplicate {field} values"]
    return []


def require_increasing_sequences(items: list[dict], label: str) -> list[str]:
    sequences = [item["sequence"] for item in items]
    if sequences != sorted(sequences) or len(sequences) != len(set(sequences)):
        return [f"{label} sequence values must be unique and increasing"]
    return []


def dependency_cycles(hypotheses: list[dict]) -> list[list[str]]:
    hypothesis_ids = {
        record["hypothesis_id"] for record in hypotheses
    }
    graph = {
        record["hypothesis_id"]: [
            dependency["hypothesis_id"]
            for dependency in record["upstream_dependencies"]
            if dependency["hypothesis_id"] in hypothesis_ids
        ]
        for record in hypotheses
    }
    visited: set[str] = set()
    active: set[str] = set()
    stack: list[str] = []
    cycles: list[list[str]] = []

    def visit(hypothesis_id: str) -> None:
        if hypothesis_id in visited:
            return
        visited.add(hypothesis_id)
        active.add(hypothesis_id)
        stack.append(hypothesis_id)
        for upstream_id in graph[hypothesis_id]:
            if upstream_id not in visited:
                visit(upstream_id)
            elif upstream_id in active:
                cycle_start = stack.index(upstream_id)
                cycles.append(stack[cycle_start:] + [upstream_id])
        stack.pop()
        active.remove(hypothesis_id)

    for hypothesis_id in graph:
        visit(hypothesis_id)
    return cycles


def relation_cycles(hypotheses: list[dict]) -> list[list[str]]:
    hypothesis_ids = {
        record["hypothesis_id"] for record in hypotheses
    }
    graph: dict[str, list[str]] = {}
    for record in hypotheses:
        relations = record["relations"]
        targets = list(relations["based_on_hypothesis_ids"])
        replacement = relations["replaces_hypothesis_id"]
        if replacement is not None:
            targets.append(replacement)
        graph[record["hypothesis_id"]] = [
            target for target in targets if target in hypothesis_ids
        ]

    visited: set[str] = set()
    active: set[str] = set()
    stack: list[str] = []
    cycles: list[list[str]] = []

    def visit(hypothesis_id: str) -> None:
        if hypothesis_id in visited:
            return
        visited.add(hypothesis_id)
        active.add(hypothesis_id)
        stack.append(hypothesis_id)
        for target in graph[hypothesis_id]:
            if target not in visited:
                visit(target)
            elif target in active:
                start = stack.index(target)
                cycles.append(stack[start:] + [target])
        stack.pop()
        active.remove(hypothesis_id)

    for hypothesis_id in graph:
        visit(hypothesis_id)
    return cycles


def active_blocked_claim_ids(claim_log: list[dict]) -> list[str]:
    latest_by_claim: dict[str, dict] = {}
    for event in claim_log:
        latest_by_claim[event["claim_id"]] = event
    return sorted(
        claim_id
        for claim_id, event in latest_by_claim.items()
        if event["status"] == "blocked"
    )


def active_usable_evidence_ids(evidence_log: list[dict]) -> list[str]:
    superseded_ids = {
        evidence_id
        for entry in evidence_log
        for evidence_id in entry["supersedes_evidence_ids"]
    }
    return [
        entry["evidence_id"]
        for entry in evidence_log
        if entry["evidence_id"] not in superseded_ids
        and entry["status"] in {"supported", "partial", "contradictory"}
    ]


def active_nexus_entry_ids(nexus_entries: list[dict]) -> list[str]:
    superseded_ids = {
        entry_id
        for entry in nexus_entries
        for entry_id in entry["supersedes_entry_ids"]
    }
    return [
        entry["entry_id"]
        for entry in nexus_entries
        if entry["entry_id"] not in superseded_ids
    ]


def nexus_entry_descends_from(
    entry_id: str,
    ancestor_ids: set[str],
    nexus_by_id: dict[str, dict],
) -> bool:
    pending = [entry_id]
    visited: set[str] = set()
    while pending:
        current_id = pending.pop()
        if current_id in ancestor_ids:
            return True
        if current_id in visited:
            continue
        visited.add(current_id)
        current = nexus_by_id.get(current_id)
        if current is not None:
            pending.extend(current["supersedes_entry_ids"])
    return False


def nexus_decision_subject_sha256(entry: dict, workspace_id: str) -> str:
    authority = entry["decision_authority"]
    if not isinstance(authority, dict):
        raise AdapterError("Nexus decision lacks an authority contract")
    payload = {
        "contract": "product-decision-paf/nexus-decision-subject/v1",
        "workspace_id": workspace_id,
        "entry_id": entry["entry_id"],
        "sequence": entry["sequence"],
        "kind": entry["kind"],
        "statement": entry["statement"],
        "evidence_ids": entry["evidence_ids"],
        "supersedes_entry_ids": entry["supersedes_entry_ids"],
        "status": entry["status"],
        "valid_as_of": entry["valid_as_of"],
        "decision_scope_id": authority["decision_scope_id"],
        "owner_ref": authority["owner_ref"],
        "owner_tenure_id": authority["owner_tenure_id"],
        "decided_at": authority["decided_at"],
        "reversibility": authority["reversibility"],
    }
    return sha256_bytes(canonical_bytes(payload))


def validate_evidence_status_binding(
    *,
    label: str,
    status: str,
    evidence_ids: list[str],
    evidence_by_id: dict[str, dict],
) -> list[str]:
    errors: list[str] = []
    resolved = [
        evidence_by_id[evidence_id]
        for evidence_id in evidence_ids
        if evidence_id in evidence_by_id
    ]
    if status == "not_applicable":
        return [f"{label} cannot use not_applicable evidence status"]
    if status == "missing":
        if resolved and not any(
            item["status"] == "missing" for item in resolved
        ):
            errors.append(f"{label} missing status is not evidence-bound")
        return errors
    if not evidence_ids:
        return [f"{label} {status} status lacks evidence"]
    if len(resolved) != len(evidence_ids):
        return errors
    statuses = {item["status"] for item in resolved}
    if status == "supported" and statuses != {"supported"}:
        errors.append(f"{label} supported status cites weaker evidence")
    elif status == "partial" and "partial" not in statuses:
        errors.append(f"{label} partial status lacks partial evidence")
    elif status == "contradictory" and "contradictory" not in statuses:
        errors.append(
            f"{label} contradictory status lacks contradictory evidence"
        )
    elif status == "stale" and "stale" not in statuses:
        errors.append(f"{label} stale status lacks stale evidence")
    return errors


def without_approval_status(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: without_approval_status(child)
            for key, child in value.items()
            if key != "approval_status"
        }
    if isinstance(value, list):
        return [without_approval_status(child) for child in value]
    return value


def frozen_test_contract(record: dict) -> dict:
    return {
        "origin": record["origin"],
        "hypothesis_class": record["hypothesis_class"],
        "lifecycle_context": record["lifecycle_context"],
        "statement": record["statement"],
        "segment": record["segment"],
        "situation": record["situation"],
        "rationale": record["rationale"],
        "upstream_dependencies": record["upstream_dependencies"],
        "validation": record["validation"],
    }


def approval_subject(
    record: dict,
    scope: str,
    workspace_id: str,
    owner_tenure_id: str,
    subject_revision: int | None = None,
) -> dict:
    bound_revision = (
        record["revision"] if subject_revision is None else subject_revision
    )
    if scope == "decision_rule":
        subject = without_approval_status(frozen_test_contract(record))
    elif scope == "proposed_assumption":
        validation = record["validation"]
        subject = {
            "metrics": [
                {
                    "metric_id": metric["metric_id"],
                    "criterion": metric["criterion"],
                    "criterion_provenance": metric["criterion_provenance"],
                }
                for metric in validation["metrics"]
                if metric["criterion_provenance"] == "proposed_assumption"
            ],
            "sample": (
                without_approval_status(validation["sample"])
                if validation["sample"]["provenance"] == "proposed_assumption"
                else None
            ),
            "time_window": (
                without_approval_status(validation["time_window"])
                if validation["time_window"]["provenance"]
                == "proposed_assumption"
                else None
            ),
        }
    elif scope == "state_transition":
        subject = {
            "state": record["state"],
            "execution_ref": record["execution_ref"],
        }
    elif scope == "terminal_verdict":
        result = copy.deepcopy(record["result"])
        result.pop("decision_owner_acceptance_ref", None)
        subject = {
            "state": record["state"],
            "verdict": record["verdict"],
            "evidence_ids": record["evidence_ids"],
            "result": result,
        }
    else:
        raise AdapterError("unknown owner approval scope")
    return {
        "contract": "product-decision-paf/owner-approval-subject/v1",
        "workspace_id": workspace_id,
        "hypothesis_id": record["hypothesis_id"],
        "decision_scope_id": record["decision_scope_id"],
        "owner_tenure_id": owner_tenure_id,
        "subject_revision": bound_revision,
        "scope": scope,
        "subject": subject,
    }


def approval_subject_sha256(
    record: dict,
    scope: str,
    workspace_id: str,
    owner_tenure_id: str,
    subject_revision: int | None = None,
) -> str:
    return sha256_bytes(
        canonical_bytes(
            approval_subject(
                record,
                scope,
                workspace_id,
                owner_tenure_id,
                subject_revision,
            )
        )
    )


def approval_matches_current_subject(
    record: dict,
    approval: dict,
    workspace_id: str,
) -> bool:
    scope = approval["scope"]
    expected = approval_subject_sha256(
        record,
        scope,
        workspace_id,
        approval["owner_tenure_id"],
        approval["subject_revision"],
    )
    if approval["subject_sha256"] != expected:
        return False
    if scope in {"state_transition", "terminal_verdict"}:
        return approval["subject_revision"] == record["revision"]
    return approval["subject_revision"] <= record["revision"]


def current_approval(
    record: dict,
    scope: str,
    workspace_id: str,
    owner_tenure_id: str | None = None,
) -> dict | None:
    matches = [
        approval
        for approval in record["owner_approvals"]
        if approval["scope"] == scope
        and (
            owner_tenure_id is None
            or approval["owner_tenure_id"] == owner_tenure_id
        )
        and approval_matches_current_subject(record, approval, workspace_id)
    ]
    if not matches or matches[-1]["decision"] != "approved":
        return None
    return matches[-1]


def has_current_approval(
    record: dict,
    scope: str,
    workspace_id: str,
    owner_tenure_id: str | None = None,
) -> bool:
    return (
        current_approval(
            record,
            scope,
            workspace_id,
            owner_tenure_id,
        )
        is not None
    )


def validate_result_gates(
    record: dict,
    evidence_by_id: dict[str, dict],
) -> list[str]:
    errors: list[str] = []
    hypothesis_id = record["hypothesis_id"]
    state = record["state"]
    result = record["result"]

    if state in {
        "framing",
        "blocked_upstream",
        "awaiting_owner_rule",
        "ready_to_run",
        "running",
    }:
        expected_empty = {
            "observations": [],
            "interpretation": None,
            "validity_status": "not_reviewed",
            "metric_results": [],
            "new_nexus_entry_ids": [],
            "external_outcome_status": "not_verified",
            "outcome_evidence_ids": [],
            "external_outcome_receipt_ref": None,
            "decision_taken": None,
            "decision_owner_acceptance_ref": None,
        }
        if result != expected_empty:
            errors.append(
                f"hypothesis {hypothesis_id} has premature result claims"
            )

    if state in {"ready_for_review", "closed"}:
        if not record["evidence_ids"] or not result["observations"]:
            errors.append(
                f"hypothesis {hypothesis_id} has no reviewable result evidence"
            )
        metric_results = result["metric_results"]
        errors.extend(
            require_unique_ids(
                metric_results,
                "metric_id",
                f"metric results for {hypothesis_id}",
            )
        )
        metric_ids = {
            metric["metric_id"]
            for metric in record["validation"]["metrics"]
        }
        primary_metric_ids = {
            metric["metric_id"]
            for metric in record["validation"]["metrics"]
            if metric["role"] == "primary"
        }
        result_by_metric = {
            item["metric_id"]: item for item in metric_results
        }
        if not primary_metric_ids.issubset(result_by_metric):
            errors.append(
                f"hypothesis {hypothesis_id} lacks a result for every primary metric"
            )
        if not set(result_by_metric).issubset(metric_ids):
            errors.append(
                f"hypothesis {hypothesis_id} has a result for an unknown metric"
            )
        for metric_result in metric_results:
            result_evidence_ids = metric_result["evidence_ids"]
            if not result_evidence_ids:
                errors.append(
                    f"hypothesis {hypothesis_id} metric result lacks evidence"
                )
            if not set(result_evidence_ids).issubset(
                set(record["evidence_ids"])
            ):
                errors.append(
                    f"hypothesis {hypothesis_id} metric result uses evidence outside the run"
                )
            if not set(result_evidence_ids).issubset(evidence_by_id):
                errors.append(
                    f"hypothesis {hypothesis_id} metric result has unknown evidence"
                )
    if state in {"cancelled", "superseded"} and (
        result["observations"]
        or result["interpretation"] is not None
        or result["new_nexus_entry_ids"]
        or result["validity_status"] != "not_reviewed"
    ):
        if not record["evidence_ids"] or not result["observations"]:
            errors.append(
                f"hypothesis {hypothesis_id} terminal learning lacks evidence"
            )

    if state != "closed" and result["decision_owner_acceptance_ref"] is not None:
        errors.append(
            f"hypothesis {hypothesis_id} has premature owner acceptance"
        )
    if state != "closed" and result["decision_taken"] is not None:
        errors.append(
            f"hypothesis {hypothesis_id} has a premature decision"
        )
    if state == "closed":
        if result["interpretation"] is None or result["decision_taken"] is None:
            errors.append(
                f"hypothesis {hypothesis_id} closed without interpretation or decision"
            )
        if not result["new_nexus_entry_ids"]:
            errors.append(
                f"hypothesis {hypothesis_id} closed without returning learning to Nexus"
            )
        if result["validity_status"] == "invalid" and record["verdict"] != "unresolved":
            errors.append(
                f"hypothesis {hypothesis_id} invalid result requires unresolved verdict"
            )
        primary_results = [
            item
            for item in result["metric_results"]
            if item["metric_id"]
            in {
                metric["metric_id"]
                for metric in record["validation"]["metrics"]
                if metric["role"] == "primary"
            }
        ]
        if record["verdict"] in {"confirmed", "disconfirmed"}:
            cited_evidence = [
                evidence_by_id[evidence_id]
                for evidence_id in record["evidence_ids"]
                if evidence_id in evidence_by_id
            ]
            if (
                not cited_evidence
                or any(
                    evidence["status"] != "supported"
                    for evidence in cited_evidence
                )
            ):
                errors.append(
                    f"hypothesis {hypothesis_id} terminal verdict lacks supported evidence"
                )
            if (
                result["validity_status"] != "adequate"
                or any(
                    item["validity_status"] != "adequate"
                    for item in primary_results
                )
            ):
                errors.append(
                    f"hypothesis {hypothesis_id} terminal verdict lacks adequate validity"
                )
        if record["verdict"] == "confirmed" and any(
            item["criterion_evaluation"] != "met"
            for item in primary_results
        ):
            errors.append(
                f"hypothesis {hypothesis_id} confirmed verdict conflicts with its primary criteria"
            )
        if record["verdict"] == "disconfirmed" and (
            not primary_results
            or not any(
                item["criterion_evaluation"] == "not_met"
                for item in primary_results
            )
            or any(
                item["criterion_evaluation"] == "indeterminate"
                for item in primary_results
            )
        ):
            errors.append(
                f"hypothesis {hypothesis_id} disconfirmed verdict conflicts with its primary criteria"
            )

    if result["external_outcome_status"] in {
        "observed",
        "attribution_limited",
        "verified",
    } and not result["outcome_evidence_ids"]:
        errors.append(
            f"hypothesis {hypothesis_id} external outcome lacks evidence"
        )
    if result["external_outcome_status"] in {
        "observed",
        "attribution_limited",
    }:
        outcome_evidence = [
            evidence_by_id[evidence_id]
            for evidence_id in result["outcome_evidence_ids"]
            if evidence_id in evidence_by_id
        ]
        if (
            len(outcome_evidence) != len(result["outcome_evidence_ids"])
            or not outcome_evidence
            or any(
                evidence["status"] not in {"supported", "partial"}
                for evidence in outcome_evidence
            )
        ):
            errors.append(
                f"hypothesis {hypothesis_id} observed outcome cites unusable evidence"
            )
    if (
        result["external_outcome_status"] == "verified"
        and result["external_outcome_receipt_ref"] is None
    ):
        errors.append(
            f"hypothesis {hypothesis_id} verified outcome lacks host receipt"
        )
    if result["external_outcome_status"] == "verified":
        outcome_evidence = [
            evidence_by_id[evidence_id]
            for evidence_id in result["outcome_evidence_ids"]
            if evidence_id in evidence_by_id
        ]
        if (
            not outcome_evidence
            or any(
                evidence["status"] != "supported"
                for evidence in outcome_evidence
            )
        ):
            errors.append(
                f"hypothesis {hypothesis_id} verified outcome lacks supported evidence"
            )
    if (
        result["external_outcome_status"] != "verified"
        and result["external_outcome_receipt_ref"] is not None
    ):
        errors.append(
            f"hypothesis {hypothesis_id} has a premature outcome receipt"
        )
    return errors


def validate_owner_gates(
    record: dict,
    owner_tenures: dict[str, dict],
    active_owner_tenure_id: str,
    workspace_id: str,
) -> list[str]:
    errors: list[str] = []
    state = record["state"]
    hypothesis_id = record["hypothesis_id"]

    for approval in record["owner_approvals"]:
        tenure = owner_tenures.get(approval["owner_tenure_id"])
        if tenure is None:
            errors.append(
                f"hypothesis {hypothesis_id} approval has unknown owner tenure"
            )
        elif approval["owner_ref"] != tenure["owner_ref"]:
            errors.append(
                f"hypothesis {hypothesis_id} approval owner does not match tenure"
            )
        if approval["subject_revision"] > record["revision"]:
            errors.append(
                f"hypothesis {hypothesis_id} approval targets a future revision"
            )
        if approval["subject_revision"] == record["revision"]:
            expected_hash = approval_subject_sha256(
                record,
                approval["scope"],
                workspace_id,
                approval["owner_tenure_id"],
                approval["subject_revision"],
            )
            if approval["subject_sha256"] != expected_hash:
                errors.append(
                    f"hypothesis {hypothesis_id} approval subject hash does not match"
                )

    if state in {
        "framing",
        "blocked_upstream",
        "awaiting_owner_rule",
        "ready_to_run",
    }:
        if record["execution_ref"] is not None:
            errors.append(
                f"hypothesis {hypothesis_id} has premature execution evidence"
            )
    elif state in {"running", "ready_for_review", "closed"}:
        if record["execution_ref"] is None:
            errors.append(
                f"hypothesis {hypothesis_id} lacks host execution evidence"
            )

    unresolved = [
        dependency
        for dependency in record["upstream_dependencies"]
        if dependency["mode"] == "prerequisite"
        and dependency["evidence_status"] != "supported"
    ]
    if state == "blocked_upstream" and not unresolved:
        errors.append(
            f"hypothesis {hypothesis_id} is blocked without an unresolved dependency"
        )
    if state in {"cancelled", "superseded"} and not has_current_approval(
        record, "state_transition", workspace_id
    ):
        errors.append(
            f"hypothesis {hypothesis_id} lacks terminal transition approval"
        )

    if state not in RUNNABLE_STATES:
        return errors

    required_tenure_id = (
        None if state == "closed" else active_owner_tenure_id
    )
    if not has_current_approval(
        record,
        "decision_rule",
        workspace_id,
        required_tenure_id,
    ):
        errors.append(
            f"hypothesis {hypothesis_id} requires approved decision rules"
        )

    validation = record["validation"]
    metrics = validation["metrics"]
    primary_metrics = [
        metric for metric in metrics if metric["role"] == "primary"
    ]
    if not primary_metrics:
        errors.append(
            f"hypothesis {hypothesis_id} has no primary decision metric"
        )
    assumption_pending = False
    for metric in metrics:
        if metric["criterion"] is None and metric["role"] == "primary":
            errors.append(
                f"hypothesis {hypothesis_id} primary metric has no criterion"
            )
        if (
            metric["role"] == "primary"
            and (
                metric["criterion_provenance"] == "unset"
                or metric["rationale"] is None
            )
        ):
            errors.append(
                f"hypothesis {hypothesis_id} primary metric contract is incomplete"
            )
        if metric["approval_status"] != "approved":
            errors.append(
                f"hypothesis {hypothesis_id} has an unapproved metric rule"
            )
        if metric["criterion_provenance"] == "proposed_assumption":
            assumption_pending = True

    sample = validation["sample"]
    time_window = validation["time_window"]
    if (
        sample["target_size"] is None
        or sample["rationale"] is None
        or sample["provenance"] == "unset"
    ):
        errors.append(
            f"hypothesis {hypothesis_id} sample contract is incomplete"
        )
    if (
        time_window["definition"] is None
        or time_window["rationale"] is None
        or time_window["provenance"] == "unset"
    ):
        errors.append(
            f"hypothesis {hypothesis_id} time-window contract is incomplete"
        )
    for design in (sample, time_window):
        if design["approval_status"] != "approved":
            errors.append(
                f"hypothesis {hypothesis_id} has an unapproved design rule"
            )
        if design["provenance"] == "proposed_assumption":
            assumption_pending = True

    if assumption_pending and not has_current_approval(
        record,
        "proposed_assumption",
        workspace_id,
        required_tenure_id,
    ):
        errors.append(
            f"hypothesis {hypothesis_id} lacks proposed-assumption approval"
        )

    if unresolved:
        errors.append(
            f"hypothesis {hypothesis_id} has unresolved upstream dependencies"
        )

    if state in {"running", "ready_for_review"} and not has_current_approval(
        record,
        "state_transition",
        workspace_id,
        active_owner_tenure_id,
    ):
        errors.append(
            f"hypothesis {hypothesis_id} lacks execution transition approval"
        )
    if state == "closed":
        terminal_approval = current_approval(
            record, "terminal_verdict", workspace_id
        )
        if terminal_approval is None:
            errors.append(
                f"hypothesis {hypothesis_id} lacks terminal-verdict approval"
            )
        elif (
            record["result"]["decision_owner_acceptance_ref"]
            != terminal_approval["safe_receipt_ref"]
        ):
            errors.append(
                f"hypothesis {hypothesis_id} terminal acceptance ref does not match"
            )
        if record["result"]["decision_owner_acceptance_ref"] is None:
            errors.append(
                f"hypothesis {record['hypothesis_id']} lacks owner acceptance ref"
            )
        if record["result"]["validity_status"] == "not_reviewed":
            errors.append(
                f"hypothesis {record['hypothesis_id']} result was not reviewed"
            )
    return errors


def validate_pending_approvals(
    record: dict,
    owner_tenures: dict[str, dict],
    active_owner_tenure_id: str,
    workspace_id: str,
) -> list[str]:
    errors: list[str] = []
    hypothesis_id = record["hypothesis_id"]
    pending = record["pending_owner_approvals"]
    pending_keys: set[tuple[str, str, int, str]] = set()

    if record["state"] == "awaiting_owner_rule" and not pending:
        errors.append(
            f"hypothesis {hypothesis_id} awaits an undeclared owner approval"
        )
    if record["state"] != "awaiting_owner_rule" and pending:
        errors.append(
            f"hypothesis {hypothesis_id} has pending approvals outside awaiting state"
        )
    for requirement in pending:
        key = (
            requirement["hypothesis_id"],
            requirement["approval_scope"],
            requirement["subject_revision"],
            requirement["subject_sha256"],
        )
        if key in pending_keys:
            errors.append(
                f"hypothesis {hypothesis_id} has duplicate pending approval"
            )
        pending_keys.add(key)
        if requirement["hypothesis_id"] != hypothesis_id:
            errors.append(
                f"hypothesis {hypothesis_id} has a foreign pending approval"
            )
        tenure = owner_tenures.get(requirement["owner_tenure_id"])
        if tenure is None:
            errors.append(
                f"hypothesis {hypothesis_id} pending approval has unknown owner tenure"
            )
        elif requirement["owner_ref"] != tenure["owner_ref"]:
            errors.append(
                f"hypothesis {hypothesis_id} pending owner does not match tenure"
            )
        if requirement["owner_tenure_id"] != active_owner_tenure_id:
            errors.append(
                f"hypothesis {hypothesis_id} pending approval targets an inactive owner tenure"
            )
        if requirement["subject_revision"] != record["revision"]:
            errors.append(
                f"hypothesis {hypothesis_id} pending approval targets another revision"
            )
        expected_hash = approval_subject_sha256(
            record,
            requirement["approval_scope"],
            workspace_id,
            requirement["owner_tenure_id"],
            requirement["subject_revision"],
        )
        if requirement["subject_sha256"] != expected_hash:
            errors.append(
                f"hypothesis {hypothesis_id} pending approval hash does not match"
            )
        if has_current_approval(
            record,
            requirement["approval_scope"],
            workspace_id,
            requirement["owner_tenure_id"],
        ):
            errors.append(
                f"hypothesis {hypothesis_id} pending approval is already resolved"
            )
    return errors


def validate_state_semantics(state: dict) -> list[str]:
    errors: list[str] = []
    evidence = state["evidence_log"]
    hypotheses = state["hypotheses"]
    nexus_entries = state["nexus_entries"]
    claim_log = state["claim_log"]
    outcome_log = state["outcome_log"]
    decision_scopes = state["decision_scope_log"]
    owner_tenures = state["owner_tenure_log"]

    errors.extend(require_unique_ids(evidence, "evidence_id", "evidence_log"))
    errors.extend(require_unique_ids(hypotheses, "hypothesis_id", "hypotheses"))
    errors.extend(require_unique_ids(nexus_entries, "entry_id", "nexus_entries"))
    errors.extend(require_unique_ids(claim_log, "event_id", "claim_log"))
    errors.extend(require_unique_ids(outcome_log, "event_id", "outcome_log"))
    errors.extend(
        require_unique_ids(
            decision_scopes,
            "scope_id",
            "decision_scope_log",
        )
    )
    errors.extend(
        require_unique_ids(
            owner_tenures,
            "tenure_id",
            "owner_tenure_log",
        )
    )
    errors.extend(require_increasing_sequences(nexus_entries, "nexus_entries"))
    errors.extend(require_increasing_sequences(evidence, "evidence_log"))
    errors.extend(require_increasing_sequences(claim_log, "claim_log"))
    errors.extend(require_increasing_sequences(outcome_log, "outcome_log"))
    errors.extend(
        require_increasing_sequences(
            decision_scopes,
            "decision_scope_log",
        )
    )
    errors.extend(
        require_increasing_sequences(
            owner_tenures,
            "owner_tenure_log",
        )
    )

    evidence_ids = {item["evidence_id"] for item in evidence}
    evidence_sequences = {
        item["evidence_id"]: item["sequence"] for item in evidence
    }
    evidence_by_id = {
        item["evidence_id"]: item for item in evidence
    }
    hypothesis_ids = {item["hypothesis_id"] for item in hypotheses}
    hypotheses_by_id = {
        item["hypothesis_id"]: item for item in hypotheses
    }
    nexus_ids = {item["entry_id"] for item in nexus_entries}
    nexus_by_id = {
        item["entry_id"]: item for item in nexus_entries
    }
    nexus_sequences = {
        item["entry_id"]: item["sequence"] for item in nexus_entries
    }
    active_nexus_ids = set(active_nexus_entry_ids(nexus_entries))
    active_usable_evidence_id_set = set(
        active_usable_evidence_ids(evidence)
    )
    active_supported_evidence_ids = {
        item["evidence_id"]
        for item in evidence
        if item["evidence_id"] in active_usable_evidence_id_set
        and item["status"] == "supported"
    }
    approval_ids: set[str] = set()
    pending_resolution_ids: set[str] = set()
    claim_event_ids = {item["event_id"] for item in claim_log}
    claim_event_sequences = {
        item["event_id"]: item["sequence"] for item in claim_log
    }
    claim_ids = {item["claim_id"] for item in claim_log}
    decision_scope_ids = {
        item["scope_id"] for item in decision_scopes
    }
    owner_tenure_by_id = {
        item["tenure_id"]: item for item in owner_tenures
    }
    active_scope_id = state["active_decision_scope_id"]
    active_tenure_id = state["active_owner_tenure_id"]

    if decision_scopes:
        if decision_scopes[0]["predecessor_scope_id"] is not None:
            errors.append("initial decision scope cannot have a predecessor")
        for previous_scope, scope in zip(
            decision_scopes, decision_scopes[1:]
        ):
            if scope["predecessor_scope_id"] != previous_scope["scope_id"]:
                errors.append(
                    "decision-scope lineage must follow the prior scope"
                )
        if active_scope_id != decision_scopes[-1]["scope_id"]:
            errors.append("active decision scope is not the latest scope")
        if state["goal"] != decision_scopes[-1]["goal"]:
            errors.append("current goal does not match active decision scope")
        if any(
            scope["opened_workspace_revision"] > state["revision"]
            for scope in decision_scopes
        ):
            errors.append("decision scope opens in a future revision")
    if owner_tenures:
        if owner_tenures[0]["predecessor_tenure_id"] is not None:
            errors.append("initial owner tenure cannot have a predecessor")
        for previous_tenure, tenure in zip(
            owner_tenures, owner_tenures[1:]
        ):
            if (
                tenure["predecessor_tenure_id"]
                != previous_tenure["tenure_id"]
            ):
                errors.append(
                    "owner-tenure lineage must follow the prior tenure"
                )
        if active_tenure_id != owner_tenures[-1]["tenure_id"]:
            errors.append("active owner tenure is not the latest tenure")
        if state["decision_owner_ref"] != owner_tenures[-1]["owner_ref"]:
            errors.append(
                "current decision owner does not match active tenure"
            )
        if any(
            tenure["effective_workspace_revision"] > state["revision"]
            for tenure in owner_tenures
        ):
            errors.append("owner tenure starts in a future revision")

    focus = state["focus_hypothesis_id"]
    if focus is not None and focus not in hypothesis_ids:
        errors.append("focus_hypothesis_id does not resolve")
    elif focus is not None:
        focused_record = next(
            record for record in hypotheses if record["hypothesis_id"] == focus
        )
        if focused_record["state"] in TERMINAL_STATES:
            errors.append("focus_hypothesis_id points to a terminal hypothesis")
        if focused_record["decision_scope_id"] != active_scope_id:
            errors.append(
                "focus_hypothesis_id belongs to an inactive decision scope"
            )
    has_usable_evidence = bool(active_usable_evidence_ids(evidence))
    if state["base"] == "data_base" and not has_usable_evidence:
        errors.append("data_base requires active usable evidence")
    if state["base"] == "null_base" and has_usable_evidence:
        errors.append("null_base conflicts with active usable evidence")
    for cycle in dependency_cycles(hypotheses):
        errors.append(
            "upstream dependency graph contains a cycle: "
            + " -> ".join(cycle)
        )
    for cycle in relation_cycles(hypotheses):
        errors.append(
            "hypothesis relation graph contains a cycle: "
            + " -> ".join(cycle)
        )

    for entry in evidence:
        if not set(entry["claim_refs"]).issubset(claim_ids):
            errors.append(
                f"evidence entry {entry['evidence_id']} has unknown claim refs"
            )
        superseded = set(entry["supersedes_evidence_ids"])
        if not superseded.issubset(evidence_ids):
            errors.append(
                f"evidence entry {entry['evidence_id']} supersedes an unknown entry"
            )
        if any(
            evidence_sequences[target] >= entry["sequence"]
            for target in superseded
            if target in evidence_sequences
        ):
            errors.append(
                f"evidence entry {entry['evidence_id']} may supersede only earlier entries"
            )

    latest_claim_event: dict[str, dict] = {}
    for event in claim_log:
        event_id = event["event_id"]
        claim_id = event["claim_id"]
        superseded = event["supersedes_event_ids"]
        if not set(superseded).issubset(claim_event_ids):
            errors.append(f"claim event {event_id} supersedes an unknown event")
        if any(
            claim_event_sequences[target] >= event["sequence"]
            for target in superseded
            if target in claim_event_sequences
        ):
            errors.append(
                f"claim event {event_id} may supersede only earlier events"
            )
        prior = latest_claim_event.get(claim_id)
        if prior is None:
            if superseded:
                errors.append(
                    f"first event for claim {claim_id} cannot supersede another event"
                )
            if event["status"] != "blocked":
                errors.append(
                    f"first event for claim {claim_id} must be blocked"
                )
        else:
            if superseded != [prior["event_id"]]:
                errors.append(
                    f"claim event {event_id} must supersede the latest event for its claim"
                )
            if event["claim"] != prior["claim"]:
                errors.append(
                    f"claim event {event_id} rewrites the logical claim"
                )
        if not set(event["resolution_evidence_ids"]).issubset(evidence_ids):
            errors.append(
                f"claim event {event_id} has unknown resolution evidence"
            )
        if event["status"] == "blocked":
            if event["resolution"] is not None:
                errors.append(
                    f"blocked claim {claim_id} has a premature resolution"
                )
            if not event["required_evidence"]:
                errors.append(
                    f"blocked claim {claim_id} lacks required evidence"
                )
            if event["resolution_evidence_ids"]:
                errors.append(
                    f"blocked claim {claim_id} has premature resolution evidence"
                )
        else:
            if event["resolution"] is None:
                errors.append(
                    f"resolved claim {claim_id} lacks a resolution kind"
                )
            if not event["resolution_evidence_ids"]:
                errors.append(
                    f"resolved claim {claim_id} lacks resolution evidence"
                )
            resolved_evidence = [
                evidence_by_id[evidence_id]
                for evidence_id in event["resolution_evidence_ids"]
                if evidence_id in evidence_by_id
            ]
            if (
                event["resolution"] == "supported"
                and resolved_evidence
                and any(
                    evidence["status"] != "supported"
                    for evidence in resolved_evidence
                )
            ):
                errors.append(
                    f"resolved claim {claim_id} is not supported by its resolution evidence"
                )
            if (
                event["resolution"] == "withdrawn"
                and resolved_evidence
                and not any(
                    evidence["status"] == "contradictory"
                    for evidence in resolved_evidence
                )
            ):
                errors.append(
                    f"withdrawn claim {claim_id} lacks contradictory evidence"
                )
        latest_claim_event[claim_id] = event

    outcome_event_ids = {event["event_id"] for event in outcome_log}
    outcome_event_sequences = {
        event["event_id"]: event["sequence"] for event in outcome_log
    }
    latest_outcome_by_hypothesis: dict[str, dict] = {}
    for event in outcome_log:
        event_id = event["event_id"]
        hypothesis_id = event["hypothesis_id"]
        linked_record = hypotheses_by_id.get(hypothesis_id)
        if linked_record is None:
            errors.append(
                f"outcome event {event_id} has an unknown hypothesis"
            )
        else:
            if linked_record["state"] != "closed":
                errors.append(
                    f"outcome event {event_id} targets a hypothesis that is not closed"
                )
            if event["decision_scope_id"] != linked_record["decision_scope_id"]:
                errors.append(
                    f"outcome event {event_id} has the wrong decision scope"
                )
        superseded = event["supersedes_event_ids"]
        if not set(superseded).issubset(outcome_event_ids):
            errors.append(
                f"outcome event {event_id} supersedes an unknown event"
            )
        if any(
            outcome_event_sequences[target] >= event["sequence"]
            for target in superseded
            if target in outcome_event_sequences
        ):
            errors.append(
                f"outcome event {event_id} may supersede only earlier events"
            )
        prior = latest_outcome_by_hypothesis.get(hypothesis_id)
        if prior is None:
            if superseded:
                errors.append(
                    f"first outcome event for {hypothesis_id} cannot supersede another event"
                )
        elif superseded != [prior["event_id"]]:
            errors.append(
                f"outcome event {event_id} must supersede the latest outcome for its hypothesis"
            )
        resolved_evidence = [
            evidence_by_id[evidence_id]
            for evidence_id in event["evidence_ids"]
            if evidence_id in evidence_by_id
        ]
        if len(resolved_evidence) != len(event["evidence_ids"]):
            errors.append(
                f"outcome event {event_id} has unknown evidence"
            )
        statuses = {item["status"] for item in resolved_evidence}
        if not resolved_evidence:
            errors.append(
                f"outcome event {event_id} lacks evidence"
            )
        elif event["status"] in {"observed", "verified"} and statuses != {
            "supported"
        }:
            errors.append(
                f"outcome event {event_id} lacks supported outcome evidence"
            )
        elif event["status"] == "attribution_limited" and not statuses.issubset(
            {"supported", "partial"}
        ):
            errors.append(
                f"outcome event {event_id} cites unusable attribution evidence"
            )
        elif (
            event["status"] == "withdrawn"
            and "contradictory" not in statuses
        ):
            errors.append(
                f"outcome event {event_id} withdrawal lacks contradictory evidence"
            )
        if (
            event["status"] == "attribution_limited"
            and event["attribution_note"] is None
        ):
            errors.append(
                f"outcome event {event_id} lacks an attribution limitation"
            )
        latest_outcome_by_hypothesis[hypothesis_id] = event

    for hypothesis_id, event in latest_outcome_by_hypothesis.items():
        if not set(event["evidence_ids"]).issubset(
            active_usable_evidence_id_set
        ):
            errors.append(
                f"latest outcome for {hypothesis_id} relies on superseded or unusable evidence"
            )

    for entry in nexus_entries:
        if not set(entry["evidence_ids"]).issubset(evidence_ids):
            errors.append(f"nexus entry {entry['entry_id']} has unknown evidence IDs")
        errors.extend(
            validate_evidence_status_binding(
                label=f"nexus entry {entry['entry_id']}",
                status=entry["status"],
                evidence_ids=entry["evidence_ids"],
                evidence_by_id=evidence_by_id,
            )
        )
        if entry["kind"] == "unknown" and entry["status"] == "supported":
            errors.append(
                f"nexus entry {entry['entry_id']} cannot support an unknown"
            )
        authority = entry["decision_authority"]
        if entry["kind"] == "decision":
            if not isinstance(authority, dict):
                errors.append(
                    f"nexus decision {entry['entry_id']} lacks owner authority"
                )
            elif not {
                "owner_ref",
                "owner_tenure_id",
                "decision_scope_id",
                "decided_at",
                "reversibility",
                "safe_receipt_ref",
                "subject_sha256",
            }.issubset(authority):
                errors.append(
                    f"nexus decision {entry['entry_id']} has an incomplete authority contract"
                )
            else:
                tenure = owner_tenure_by_id.get(
                    authority["owner_tenure_id"]
                )
                if (
                    tenure is None
                    or tenure["owner_ref"] != authority["owner_ref"]
                ):
                    errors.append(
                        f"nexus decision {entry['entry_id']} owner does not match tenure"
                    )
                if authority["decision_scope_id"] not in decision_scope_ids:
                    errors.append(
                        f"nexus decision {entry['entry_id']} has an unknown decision scope"
                    )
                if entry["status"] != "supported":
                    errors.append(
                        f"nexus decision {entry['entry_id']} must be supported"
                    )
                if authority["subject_sha256"] != (
                    nexus_decision_subject_sha256(
                        entry,
                        state["workspace_id"],
                    )
                ):
                    errors.append(
                        f"nexus decision {entry['entry_id']} subject hash does not match"
                    )
        elif authority is not None:
            errors.append(
                f"non-decision Nexus entry {entry['entry_id']} has decision authority"
            )
        superseded = set(entry["supersedes_entry_ids"])
        if not superseded.issubset(nexus_ids):
            errors.append(
                f"nexus entry {entry['entry_id']} supersedes an unknown entry"
            )
        if any(
            nexus_sequences[target] >= entry["sequence"]
            for target in superseded
            if target in nexus_sequences
        ):
            errors.append(
                f"nexus entry {entry['entry_id']} may supersede only earlier entries"
            )
    for record in hypotheses:
        hypothesis_id = record["hypothesis_id"]
        if record["decision_scope_id"] not in decision_scope_ids:
            errors.append(
                f"hypothesis {hypothesis_id} has an unknown decision scope"
            )
        if (
            record["state"] not in TERMINAL_STATES
            and record["decision_scope_id"] != active_scope_id
        ):
            errors.append(
                f"active hypothesis {hypothesis_id} belongs to an inactive decision scope"
            )
        errors.extend(
            require_unique_ids(
                record["validation"]["metrics"],
                "metric_id",
                f"metrics for {hypothesis_id}",
            )
        )
        if not set(record["origin"]["originating_entry_ids"]).issubset(nexus_ids):
            errors.append(f"hypothesis {hypothesis_id} has unknown origin entries")
        if record["origin"]["nexus_revision"] > state["revision"]:
            errors.append(
                f"hypothesis {hypothesis_id} origin targets a future Nexus revision"
            )
        if not set(record["evidence_ids"]).issubset(evidence_ids):
            errors.append(f"hypothesis {hypothesis_id} has unknown evidence IDs")
        if not set(record["result"]["outcome_evidence_ids"]).issubset(evidence_ids):
            errors.append(f"hypothesis {hypothesis_id} has unknown outcome evidence")
        if not set(record["result"]["new_nexus_entry_ids"]).issubset(nexus_ids):
            errors.append(f"hypothesis {hypothesis_id} has unknown new Nexus IDs")

        errors.extend(
            require_unique_ids(
                record["upstream_dependencies"],
                "dependency_id",
                f"upstream dependencies for {hypothesis_id}",
            )
        )
        for dependency in record["upstream_dependencies"]:
            dependency_hypothesis = dependency["hypothesis_id"]
            if (
                dependency_hypothesis is not None
                and dependency_hypothesis not in hypothesis_ids
            ):
                errors.append(
                    f"hypothesis {hypothesis_id} has an unknown upstream hypothesis"
                )
            if dependency_hypothesis == hypothesis_id:
                errors.append(
                    f"hypothesis {hypothesis_id} cannot depend on itself"
                )
            linked_record = hypotheses_by_id.get(dependency_hypothesis)
            if (
                dependency["mode"] == "prerequisite"
                and dependency["co_test_plan_ref"] is not None
            ):
                errors.append(
                    f"hypothesis {hypothesis_id} prerequisite has a co-test plan"
                )
            if dependency["mode"] == "co_test":
                if dependency["co_test_plan_ref"] is None:
                    errors.append(
                        f"hypothesis {hypothesis_id} co-test lacks a plan ref"
                    )
                if dependency_hypothesis is None:
                    errors.append(
                        f"hypothesis {hypothesis_id} co-test lacks a linked hypothesis"
                    )
                if dependency["evidence_status"] == "supported":
                    errors.append(
                        f"hypothesis {hypothesis_id} supported dependency must use prerequisite mode"
                    )
            if (
                linked_record is not None
                and linked_record["hypothesis_class"]
                != dependency["required_class"]
            ):
                errors.append(
                    f"hypothesis {hypothesis_id} upstream class does not match"
                )
            if (
                dependency["mode"] == "co_test"
                and linked_record is not None
            ):
                class_pair = frozenset(
                    {
                        record["hypothesis_class"],
                        linked_record["hypothesis_class"],
                    }
                )
                if class_pair not in {
                    frozenset({"value_proposition", "solution"}),
                    frozenset({"solution", "business_model"}),
                }:
                    errors.append(
                        f"hypothesis {hypothesis_id} uses an unsupported PAF co-test pair"
                    )
                if record["state"] in {
                    "ready_to_run",
                    "running",
                    "ready_for_review",
                }:
                    if linked_record["state"] not in RUNNABLE_STATES:
                        errors.append(
                            f"hypothesis {hypothesis_id} co-test peer is not runnable"
                        )
                    if not has_current_approval(
                        linked_record,
                        "decision_rule",
                        state["workspace_id"],
                        active_tenure_id,
                    ):
                        errors.append(
                            f"hypothesis {hypothesis_id} co-test peer lacks separate approved rules"
                        )
                    if (
                        record["state"] == "ready_to_run"
                        and linked_record["state"] != "ready_to_run"
                    ):
                        errors.append(
                            f"hypothesis {hypothesis_id} co-test peers are not jointly ready"
                        )
                    if (
                        record["state"] in {"running", "ready_for_review"}
                        and (
                            linked_record["state"]
                            not in {
                                "running",
                                "ready_for_review",
                                "closed",
                            }
                            or linked_record["execution_ref"]
                            != record["execution_ref"]
                        )
                    ):
                        errors.append(
                            f"hypothesis {hypothesis_id} co-test peers lack shared execution evidence"
                        )
            if not set(dependency["evidence_ids"]).issubset(evidence_ids):
                errors.append(
                    f"hypothesis {hypothesis_id} has unknown upstream evidence"
                )
            if dependency["evidence_status"] == "supported":
                direct_evidence = [
                    evidence_by_id[evidence_id]
                    for evidence_id in dependency["evidence_ids"]
                    if evidence_id in evidence_by_id
                ]
                dependency_evidence_ids = set(dependency["evidence_ids"])
                if (
                    not dependency_evidence_ids
                    or len(direct_evidence) != len(dependency_evidence_ids)
                    or not dependency_evidence_ids.issubset(
                        active_supported_evidence_ids
                    )
                ):
                    errors.append(
                        f"hypothesis {hypothesis_id} upstream support lacks current supported evidence"
                    )
                if linked_record is not None:
                    if not (
                        linked_record["state"] == "closed"
                        and linked_record["verdict"] == "confirmed"
                        and linked_record["result"]["validity_status"]
                        == "adequate"
                    ):
                        errors.append(
                            f"hypothesis {hypothesis_id} upstream support is not a confirmed valid hypothesis"
                        )
                    lineage_roots = set(
                        linked_record["result"]["new_nexus_entry_ids"]
                    )
                    current_authority_entries = [
                        entry
                        for entry in nexus_entries
                        if entry["entry_id"] in active_nexus_ids
                        and entry["status"] == "supported"
                        and nexus_entry_descends_from(
                            entry["entry_id"],
                            lineage_roots,
                            nexus_by_id,
                        )
                    ]
                    if (
                        not lineage_roots
                        or not any(
                            set(entry["evidence_ids"]).issubset(
                                dependency_evidence_ids
                            )
                            for entry in current_authority_entries
                        )
                    ):
                        errors.append(
                            f"hypothesis {hypothesis_id} upstream support lacks current Nexus authority"
                        )
                elif (
                    dependency_hypothesis is None
                    and (
                        not dependency["evidence_ids"]
                        or len(direct_evidence)
                        != len(dependency["evidence_ids"])
                        or any(
                            item["status"] != "supported"
                            for item in direct_evidence
                        )
                    )
                ):
                    errors.append(
                        f"hypothesis {hypothesis_id} upstream support lacks supported direct evidence"
                    )

        relations = record["relations"]
        related_ids = set(relations["based_on_hypothesis_ids"])
        if hypothesis_id in related_ids:
            errors.append(
                f"hypothesis {hypothesis_id} cannot be based on itself"
            )
        if relations["replaces_hypothesis_id"] is not None:
            related_ids.add(relations["replaces_hypothesis_id"])
            replacement_id = relations["replaces_hypothesis_id"]
            if replacement_id == hypothesis_id:
                errors.append(
                    f"hypothesis {hypothesis_id} cannot replace itself"
                )
            replacement_record = hypotheses_by_id.get(replacement_id)
            if (
                replacement_record is not None
                and replacement_record["state"]
                not in {"superseded", "closed"}
            ):
                errors.append(
                    f"hypothesis {hypothesis_id} replacement target is not a closed or superseded record"
                )
        if not related_ids.issubset(hypothesis_ids):
            errors.append(f"hypothesis {hypothesis_id} has unknown relations")

        for approval in record["owner_approvals"]:
            approval_id = approval["approval_id"]
            if approval_id in approval_ids:
                errors.append(f"duplicate owner approval ID {approval_id}")
            approval_ids.add(approval_id)
        for resolution in record["pending_owner_resolutions"]:
            resolution_id = resolution["resolution_id"]
            if resolution_id in pending_resolution_ids:
                errors.append(
                    f"duplicate pending owner resolution ID {resolution_id}"
                )
            pending_resolution_ids.add(resolution_id)
            if resolution["hypothesis_id"] != hypothesis_id:
                errors.append(
                    f"hypothesis {hypothesis_id} has a foreign pending resolution"
                )
            request_tenure = owner_tenure_by_id.get(
                resolution["request_owner_tenure_id"]
            )
            authority_tenure = owner_tenure_by_id.get(
                resolution["authority_tenure_id"]
            )
            if request_tenure is None:
                errors.append(
                    f"pending resolution {resolution_id} has an unknown request tenure"
                )
            if authority_tenure is None:
                errors.append(
                    f"pending resolution {resolution_id} has an unknown authority tenure"
                )
            elif (
                authority_tenure["owner_ref"]
                != resolution["authority_owner_ref"]
            ):
                errors.append(
                    f"pending resolution {resolution_id} authority does not match tenure"
                )
            if resolution["subject_revision"] > record["revision"]:
                errors.append(
                    f"pending resolution {resolution_id} targets a future revision"
                )
            if (
                resolution["resolution"]
                == "invalidated_by_tenure_transition"
                and authority_tenure is not None
                and authority_tenure["predecessor_tenure_id"]
                != resolution["request_owner_tenure_id"]
            ):
                errors.append(
                    f"pending resolution {resolution_id} is not bound to the owner transition"
                )
        errors.extend(
            validate_pending_approvals(
                record,
                owner_tenure_by_id,
                active_tenure_id,
                state["workspace_id"],
            )
        )
        errors.extend(
            validate_owner_gates(
                record,
                owner_tenure_by_id,
                active_tenure_id,
                state["workspace_id"],
            )
        )
        errors.extend(validate_result_gates(record, evidence_by_id))

    errors.extend(validate_sensitive_data(state))
    return errors


def list_suffix_ids(
    previous: list[dict],
    candidate: list[dict],
    id_field: str,
    label: str,
) -> tuple[list[str], list[str]]:
    if len(candidate) < len(previous) or candidate[: len(previous)] != previous:
        return [], [f"{label} must preserve the previous append-only prefix"]
    return [item[id_field] for item in candidate[len(previous) :]], []


def approval_map(state: dict) -> dict[str, dict]:
    return {
        approval["approval_id"]: approval
        for hypothesis in state["hypotheses"]
        for approval in hypothesis["owner_approvals"]
    }


def validate_change_semantics(
    change_set: dict,
    previous: dict | None,
) -> list[str]:
    candidate = change_set["candidate_state"]
    errors = validate_state_semantics(candidate)

    if candidate["workspace_id"] != change_set["workspace_id"]:
        errors.append("candidate workspace_id does not match change set")
    if candidate["revision"] != change_set["candidate_workspace_revision"]:
        errors.append("candidate revision does not match change set")

    operation = change_set["workspace_operation"]
    if operation == "create":
        if previous is not None:
            errors.append("create operation cannot replace an existing workspace")
        if change_set["expected_workspace_revision"] is not None:
            errors.append("create operation must use a null expected revision")
        if candidate["revision"] != 0:
            errors.append("created workspace must start at revision zero")
        previous = {
            "revision": -1,
            "workspace_id": candidate["workspace_id"],
            "base": None,
            "decision_scope_log": [],
            "owner_tenure_log": [],
            "nexus_entries": [],
            "evidence_log": [],
            "claim_log": [],
            "outcome_log": [],
            "hypotheses": [],
            "focus_hypothesis_id": None,
        }
    else:
        if previous is None:
            errors.append("replace operation requires an existing workspace")
            return errors
        if previous["workspace_id"] != change_set["workspace_id"]:
            errors.append("workspace_id does not match the persisted workspace")
        if candidate["revision"] != previous["revision"] + 1:
            errors.append("replacement workspace revision must increase by one")
        for field in (
            "schema_version",
            "data_policy",
            "workspace_id",
            "product_ref",
        ):
            if candidate[field] != previous[field]:
                errors.append(f"workspace field {field} is immutable")
    appended_decision_scopes, log_errors = list_suffix_ids(
        previous["decision_scope_log"],
        candidate["decision_scope_log"],
        "scope_id",
        "decision_scope_log",
    )
    errors.extend(log_errors)
    appended_owner_tenures, log_errors = list_suffix_ids(
        previous["owner_tenure_log"],
        candidate["owner_tenure_log"],
        "tenure_id",
        "owner_tenure_log",
    )
    errors.extend(log_errors)
    if len(appended_decision_scopes) > 1:
        errors.append("one revision may open at most one decision scope")
    if len(appended_owner_tenures) > 1:
        errors.append("one revision may start at most one owner tenure")
    appended_scope_set = set(appended_decision_scopes)
    for scope in candidate["decision_scope_log"]:
        if (
            scope["scope_id"] in appended_scope_set
            and scope["opened_workspace_revision"] != candidate["revision"]
        ):
            errors.append(
                "new decision scope must bind to the current workspace revision"
            )
    appended_tenure_set = set(appended_owner_tenures)
    for tenure in candidate["owner_tenure_log"]:
        if (
            tenure["tenure_id"] in appended_tenure_set
            and tenure["effective_workspace_revision"]
            != candidate["revision"]
        ):
            errors.append(
                "new owner tenure must bind to the current workspace revision"
            )

    appended_nexus, log_errors = list_suffix_ids(
        previous["nexus_entries"],
        candidate["nexus_entries"],
        "entry_id",
        "nexus_entries",
    )
    errors.extend(log_errors)
    appended_evidence, log_errors = list_suffix_ids(
        previous["evidence_log"],
        candidate["evidence_log"],
        "evidence_id",
        "evidence_log",
    )
    errors.extend(log_errors)
    appended_claim_events, log_errors = list_suffix_ids(
        previous["claim_log"],
        candidate["claim_log"],
        "event_id",
        "claim_log",
    )
    errors.extend(log_errors)
    appended_outcome_events, log_errors = list_suffix_ids(
        previous["outcome_log"],
        candidate["outcome_log"],
        "event_id",
        "outcome_log",
    )
    errors.extend(log_errors)

    previous_hypotheses = {
        record["hypothesis_id"]: record for record in previous["hypotheses"]
    }
    candidate_hypotheses = {
        record["hypothesis_id"]: record for record in candidate["hypotheses"]
    }
    if not set(previous_hypotheses).issubset(candidate_hypotheses):
        errors.append("candidate state cannot delete hypothesis records")
    previous_hypothesis_order = [
        record["hypothesis_id"] for record in previous["hypotheses"]
    ]
    candidate_hypothesis_order = [
        record["hypothesis_id"] for record in candidate["hypotheses"]
    ]
    if (
        candidate_hypothesis_order[: len(previous_hypothesis_order)]
        != previous_hypothesis_order
    ):
        errors.append(
            "hypothesis order is append-only and cannot be rewritten"
        )

    creates: list[dict] = []
    updates: list[dict] = []
    appended_pending_resolutions: list[dict] = []
    meaningful_hypothesis_update = False
    candidate_nexus_by_id = {
        entry["entry_id"]: entry for entry in candidate["nexus_entries"]
    }
    candidate_active_nexus_ids = set(
        active_nexus_entry_ids(candidate["nexus_entries"])
    )
    for entry_id in appended_nexus:
        entry = candidate_nexus_by_id[entry_id]
        if entry["kind"] != "decision":
            continue
        authority = entry.get("decision_authority")
        if not isinstance(authority, dict):
            continue
        if (
            authority.get("owner_tenure_id")
            != candidate["active_owner_tenure_id"]
            or authority.get("owner_ref")
            != candidate["decision_owner_ref"]
            or authority.get("decision_scope_id")
            != candidate["active_decision_scope_id"]
        ):
            errors.append(
                f"new Nexus decision {entry_id} does not use the active decision authority"
            )
    for hypothesis_id, record in candidate_hypotheses.items():
        old = previous_hypotheses.get(hypothesis_id)
        if old is None:
            if record["revision"] != 0:
                errors.append(f"new hypothesis {hypothesis_id} must start at revision zero")
            if record["origin"]["nexus_revision"] != candidate["revision"]:
                errors.append(
                    f"new hypothesis {hypothesis_id} origin must bind to its workspace revision"
                )
            if not set(
                record["origin"]["originating_entry_ids"]
            ).issubset(candidate_active_nexus_ids):
                errors.append(
                    f"new hypothesis {hypothesis_id} origin cites superseded Nexus knowledge"
                )
            if (
                record["decision_scope_id"]
                != candidate["active_decision_scope_id"]
            ):
                errors.append(
                    f"new hypothesis {hypothesis_id} must belong to the active decision scope"
                )
            if (
                record["state"] in {"cancelled", "superseded"}
                and record["execution_ref"] is not None
            ):
                errors.append(
                    f"new terminal hypothesis {hypothesis_id} cannot invent execution evidence"
                )
            if record["pending_owner_resolutions"]:
                errors.append(
                    f"new hypothesis {hypothesis_id} cannot contain pending-request resolutions"
                )
            creates.append(
                {"hypothesis_id": hypothesis_id, "candidate_revision": record["revision"]}
            )
            newly_claimed_nexus_ids = record["result"][
                "new_nexus_entry_ids"
            ]
            if not set(newly_claimed_nexus_ids).issubset(appended_nexus):
                errors.append(
                    f"new hypothesis {hypothesis_id} claims Nexus learning from another revision"
                )
            for entry_id in newly_claimed_nexus_ids:
                entry = candidate_nexus_by_id.get(entry_id)
                if entry is not None and (
                    not entry["evidence_ids"]
                    or not set(entry["evidence_ids"]).issubset(
                        record["evidence_ids"]
                    )
                ):
                    errors.append(
                        f"new Nexus learning for {hypothesis_id} is not bound to its run evidence"
                    )
            continue
        if record == old:
            continue
        old_meaningful = copy.deepcopy(old)
        record_meaningful = copy.deepcopy(record)
        for value in (old_meaningful, record_meaningful):
            value.pop("revision", None)
            value.pop("updated_at", None)
        if record_meaningful != old_meaningful:
            meaningful_hypothesis_update = True
        if old["state"] in TERMINAL_STATES:
            errors.append(f"terminal hypothesis {hypothesis_id} is immutable")
            continue
        if record["revision"] != old["revision"] + 1:
            errors.append(f"hypothesis {hypothesis_id} revision must increase by one")
        if record["created_at"] != old["created_at"]:
            errors.append(f"hypothesis {hypothesis_id} created_at is immutable")
        if record["decision_scope_id"] != old["decision_scope_id"]:
            errors.append(
                f"hypothesis {hypothesis_id} decision scope is immutable"
            )
        if record["origin"] != old["origin"]:
            errors.append(f"hypothesis {hypothesis_id} origin is immutable")
        if (
            record["relations"]["replaces_hypothesis_id"]
            != old["relations"]["replaces_hypothesis_id"]
        ):
            errors.append(
                f"hypothesis {hypothesis_id} replacement relation is immutable"
            )
        if old["state"] in {"ready_to_run", "running", "ready_for_review"}:
            if frozen_test_contract(record) != frozen_test_contract(old):
                errors.append(
                    f"hypothesis {hypothesis_id} test contract is frozen"
                )
        if old["state"] in {"running", "ready_for_review"}:
            if record["execution_ref"] != old["execution_ref"]:
                errors.append(
                    f"hypothesis {hypothesis_id} execution ref is immutable after start"
                )
        if record["state"] in {"cancelled", "superseded"}:
            if record["execution_ref"] != old["execution_ref"]:
                errors.append(
                    f"hypothesis {hypothesis_id} terminal transition changed execution ref"
                )
        if (
            len(record["evidence_ids"]) < len(old["evidence_ids"])
            or record["evidence_ids"][: len(old["evidence_ids"])]
            != old["evidence_ids"]
        ):
            errors.append(f"hypothesis {hypothesis_id} evidence IDs are append-only")
        old_new_nexus_ids = old["result"]["new_nexus_entry_ids"]
        current_new_nexus_ids = record["result"]["new_nexus_entry_ids"]
        if (
            len(current_new_nexus_ids) < len(old_new_nexus_ids)
            or current_new_nexus_ids[: len(old_new_nexus_ids)]
            != old_new_nexus_ids
        ):
            errors.append(
                f"hypothesis {hypothesis_id} new Nexus IDs are append-only"
            )
        newly_claimed_nexus_ids = current_new_nexus_ids[
            len(old_new_nexus_ids):
        ]
        if not set(newly_claimed_nexus_ids).issubset(appended_nexus):
            errors.append(
                f"hypothesis {hypothesis_id} claims Nexus learning from another revision"
            )
        for entry_id in newly_claimed_nexus_ids:
            entry = candidate_nexus_by_id.get(entry_id)
            if entry is not None and (
                not entry["evidence_ids"]
                or not set(entry["evidence_ids"]).issubset(
                    record["evidence_ids"]
                )
            ):
                errors.append(
                    f"new Nexus learning for {hypothesis_id} is not bound to its run evidence"
                )
        if (
            len(record["owner_approvals"]) < len(old["owner_approvals"])
            or record["owner_approvals"][: len(old["owner_approvals"])]
            != old["owner_approvals"]
        ):
            errors.append(f"hypothesis {hypothesis_id} approvals are append-only")
        old_resolutions = old["pending_owner_resolutions"]
        current_resolutions = record["pending_owner_resolutions"]
        if (
            len(current_resolutions) < len(old_resolutions)
            or current_resolutions[: len(old_resolutions)]
            != old_resolutions
        ):
            errors.append(
                f"hypothesis {hypothesis_id} pending resolutions are append-only"
            )
        else:
            appended_pending_resolutions.extend(
                current_resolutions[len(old_resolutions):]
            )
        if (
            record["state"] != old["state"]
            and record["state"] not in ALLOWED_TRANSITIONS[old["state"]]
        ):
            errors.append(
                f"hypothesis {hypothesis_id} has an invalid lifecycle transition"
            )
        if record["state"] == "closed":
            for required_scope in ("decision_rule", "terminal_verdict"):
                if not has_current_approval(
                    record,
                    required_scope,
                    candidate["workspace_id"],
                    candidate["active_owner_tenure_id"],
                ):
                    errors.append(
                        f"hypothesis {hypothesis_id} closing decision lacks "
                        f"{required_scope} approval from the active owner tenure"
                    )
        updates.append(
            {
                "hypothesis_id": hypothesis_id,
                "expected_revision": old["revision"],
                "candidate_revision": record["revision"],
                "from_state": old["state"],
                "to_state": record["state"],
            }
        )

    old_approvals = approval_map(previous)
    new_approvals = approval_map(candidate)
    appended_approvals = sorted(set(new_approvals) - set(old_approvals))
    newly_added_approvals = [
        new_approvals[approval_id]
        for approval_id in appended_approvals
    ]
    for hypothesis_id, old_record in previous_hypotheses.items():
        new_record = candidate_hypotheses.get(hypothesis_id)
        if new_record is None:
            continue
        for requirement in old_record["pending_owner_approvals"]:
            if requirement in new_record["pending_owner_approvals"]:
                continue
            resolved = any(
                approval["scope"] == requirement["approval_scope"]
                and approval["owner_ref"] == requirement["owner_ref"]
                and approval["owner_tenure_id"]
                == requirement["owner_tenure_id"]
                and approval["subject_revision"]
                == requirement["subject_revision"]
                and approval["subject_sha256"]
                == requirement["subject_sha256"]
                for approval in newly_added_approvals
            )
            resolved = resolved or any(
                resolution["hypothesis_id"]
                == requirement["hypothesis_id"]
                and resolution["approval_scope"]
                == requirement["approval_scope"]
                and resolution["request_owner_tenure_id"]
                == requirement["owner_tenure_id"]
                and resolution["subject_revision"]
                == requirement["subject_revision"]
                and resolution["subject_sha256"]
                == requirement["subject_sha256"]
                for resolution in appended_pending_resolutions
            )
            if not resolved:
                errors.append(
                    f"pending owner approval for {hypothesis_id} disappeared without a matching decision or resolution"
                )
    prior_pending_requirements = [
        requirement
        for record in previous["hypotheses"]
        for requirement in record["pending_owner_approvals"]
    ]
    appended_tenure_ids = set(appended_owner_tenures)
    for resolution in appended_pending_resolutions:
        if not any(
            resolution["hypothesis_id"] == requirement["hypothesis_id"]
            and resolution["approval_scope"]
            == requirement["approval_scope"]
            and resolution["request_owner_tenure_id"]
            == requirement["owner_tenure_id"]
            and resolution["subject_revision"]
            == requirement["subject_revision"]
            and resolution["subject_sha256"]
            == requirement["subject_sha256"]
            for requirement in prior_pending_requirements
        ):
            errors.append(
                "pending owner resolution does not match a prior pending request"
            )
        if (
            resolution["authority_tenure_id"]
            != candidate["active_owner_tenure_id"]
            or resolution["authority_owner_ref"]
            != candidate["decision_owner_ref"]
        ):
            errors.append(
                "pending owner resolution does not use the active owner authority"
            )
        if (
            resolution["resolution"]
            == "invalidated_by_tenure_transition"
            and resolution["authority_tenure_id"]
            not in appended_tenure_ids
        ):
            errors.append(
                "pending owner invalidation lacks a same-revision owner transition"
            )

    manifest = change_set["change_manifest"]
    if manifest["hypothesis_creates"] != creates:
        errors.append("change manifest does not match hypothesis creates")
    if sorted(manifest["hypothesis_updates"], key=canonical_bytes) != sorted(
        updates, key=canonical_bytes
    ):
        errors.append("change manifest does not match hypothesis updates")
    if manifest["appended_evidence_ids"] != appended_evidence:
        errors.append("change manifest does not match appended evidence")
    if manifest["appended_decision_scope_ids"] != appended_decision_scopes:
        errors.append(
            "change manifest does not match appended decision scopes"
        )
    if manifest["appended_owner_tenure_ids"] != appended_owner_tenures:
        errors.append(
            "change manifest does not match appended owner tenures"
        )
    if manifest["appended_nexus_entry_ids"] != appended_nexus:
        errors.append("change manifest does not match appended Nexus entries")
    if manifest["appended_claim_event_ids"] != appended_claim_events:
        errors.append("change manifest does not match appended claim events")
    if manifest["appended_outcome_event_ids"] != appended_outcome_events:
        errors.append("change manifest does not match appended outcome events")
    if sorted(manifest["new_owner_approval_ids"]) != appended_approvals:
        errors.append("change manifest does not match owner approvals")

    previous_focus = previous["focus_hypothesis_id"]
    candidate_focus = candidate["focus_hypothesis_id"]
    expected_focus_change = (
        None
        if previous_focus == candidate_focus
        else {"from": previous_focus, "to": candidate_focus}
    )
    if manifest["focus_change"] != expected_focus_change:
        errors.append("change manifest does not match focus change")
    expected_base_change = (
        None
        if previous["base"] == candidate["base"]
        else {"from": previous["base"], "to": candidate["base"]}
    )
    if manifest["base_change"] != expected_base_change:
        errors.append("change manifest does not match evidence base change")

    required_approvals = change_set["required_owner_approvals"]
    persisted_pending = [
        requirement
        for record in candidate["hypotheses"]
        for requirement in record["pending_owner_approvals"]
    ]
    if required_approvals != persisted_pending:
        errors.append(
            "required owner approvals do not match persisted pending approvals"
        )
    for record in candidate["hypotheses"]:
        prior_pending = (
            previous_hypotheses[record["hypothesis_id"]][
                "pending_owner_approvals"
            ]
            if record["hypothesis_id"] in previous_hypotheses
            else []
        )
        for requirement in record["pending_owner_approvals"]:
            if requirement in prior_pending:
                continue
            if requirement["source_change_set_id"] != change_set["change_set_id"]:
                errors.append(
                    "new pending owner approval source does not match the "
                    "current change set"
                )
    active_tenure_id = candidate["active_owner_tenure_id"]
    previous_approval_ids = set(old_approvals)
    for record in candidate["hypotheses"]:
        for approval in record["owner_approvals"]:
            if (
                approval["approval_id"] not in previous_approval_ids
                and approval["owner_tenure_id"] != active_tenure_id
            ):
                errors.append(
                    "new owner approval does not use the active owner tenure"
                )
    if not any(
        (
            creates,
            meaningful_hypothesis_update,
            appended_decision_scopes,
            appended_owner_tenures,
            appended_nexus,
            appended_evidence,
            appended_claim_events,
            appended_outcome_events,
            appended_approvals,
            expected_focus_change,
            expected_base_change,
        )
    ):
        errors.append("replacement revision has no substantive state change")
    return errors


def validate_hypothesis_transition(previous: dict, candidate: dict) -> list[str]:
    errors: list[str] = []
    hypothesis_id = candidate["hypothesis_id"]
    if previous["state"] in TERMINAL_STATES:
        errors.append(f"hypothesis history mutated terminal {hypothesis_id}")
        return errors
    if candidate["revision"] != previous["revision"] + 1:
        errors.append(f"hypothesis history skipped revision for {hypothesis_id}")
    if candidate["created_at"] != previous["created_at"]:
        errors.append(f"hypothesis history changed created_at for {hypothesis_id}")
    if candidate["origin"] != previous["origin"]:
        errors.append(f"hypothesis history changed origin for {hypothesis_id}")
    if (
        candidate["relations"]["replaces_hypothesis_id"]
        != previous["relations"]["replaces_hypothesis_id"]
    ):
        errors.append(
            f"hypothesis history changed replacement relation for {hypothesis_id}"
        )
    if candidate["state"] != previous["state"] and (
        candidate["state"] not in ALLOWED_TRANSITIONS[previous["state"]]
    ):
        errors.append(
            f"hypothesis history has invalid lifecycle transition for {hypothesis_id}"
        )
    if (
        len(candidate["evidence_ids"]) < len(previous["evidence_ids"])
        or candidate["evidence_ids"][: len(previous["evidence_ids"])]
        != previous["evidence_ids"]
    ):
        errors.append(
            f"hypothesis history rewrote evidence order for {hypothesis_id}"
        )
    if (
        len(candidate["owner_approvals"]) < len(previous["owner_approvals"])
        or candidate["owner_approvals"][: len(previous["owner_approvals"])]
        != previous["owner_approvals"]
    ):
        errors.append(
            f"hypothesis history rewrote approvals for {hypothesis_id}"
        )
    if (
        len(candidate["pending_owner_resolutions"])
        < len(previous["pending_owner_resolutions"])
        or candidate["pending_owner_resolutions"][
            : len(previous["pending_owner_resolutions"])
        ]
        != previous["pending_owner_resolutions"]
    ):
        errors.append(
            f"hypothesis history rewrote pending resolutions for {hypothesis_id}"
        )
    if previous["state"] in {"ready_to_run", "running", "ready_for_review"}:
        if frozen_test_contract(candidate) != frozen_test_contract(previous):
            errors.append(
                f"hypothesis history changed frozen test contract for {hypothesis_id}"
            )
    if previous["state"] in {"running", "ready_for_review"}:
        if candidate["execution_ref"] != previous["execution_ref"]:
            errors.append(
                f"hypothesis history changed execution ref for {hypothesis_id}"
            )
    if candidate["state"] in {"cancelled", "superseded"}:
        if candidate["execution_ref"] != previous["execution_ref"]:
            errors.append(
                f"hypothesis history terminal transition changed execution ref for {hypothesis_id}"
            )
    return errors


def state_summary(state: dict) -> dict:
    return {
        "base": state["base"],
        "active_decision_scope_id": state["active_decision_scope_id"],
        "decision_scope_count": len(state["decision_scope_log"]),
        "active_owner_tenure_id": state["active_owner_tenure_id"],
        "owner_tenure_count": len(state["owner_tenure_log"]),
        "hypothesis_count": len(state["hypotheses"]),
        "nexus_entry_count": len(state["nexus_entries"]),
        "evidence_count": len(state["evidence_log"]),
        "claim_event_count": len(state["claim_log"]),
        "outcome_event_count": len(state["outcome_log"]),
        "active_blocked_claim_count": len(
            active_blocked_claim_ids(state["claim_log"])
        ),
    }


def revision_delta_payload(
    manifest: dict,
    *,
    record_versions: dict[tuple[str, int], dict],
    decision_scope_by_id: dict[str, dict],
    owner_tenure_by_id: dict[str, dict],
    nexus_by_id: dict[str, dict],
    evidence_by_id: dict[str, dict],
    claim_event_by_id: dict[str, dict],
    outcome_event_by_id: dict[str, dict],
) -> tuple[dict | None, list[str]]:
    errors: list[str] = []
    changed_records: list[dict] = []
    for item in (
        manifest["hypothesis_creates"]
        + manifest["hypothesis_updates"]
    ):
        key = (item["hypothesis_id"], item["candidate_revision"])
        record = record_versions.get(key)
        if record is None:
            errors.append(
                "revision delta references a missing hypothesis record"
            )
        else:
            changed_records.append(record)

    def resolve_items(
        identifiers: list[str],
        source: dict[str, dict],
        label: str,
    ) -> list[dict]:
        resolved: list[dict] = []
        for identifier in identifiers:
            item = source.get(identifier)
            if item is None:
                errors.append(
                    f"revision delta references a missing {label}"
                )
            else:
                resolved.append(item)
        return resolved

    appended_nexus = resolve_items(
        manifest["appended_nexus_entry_ids"],
        nexus_by_id,
        "Nexus entry",
    )
    appended_evidence = resolve_items(
        manifest["appended_evidence_ids"],
        evidence_by_id,
        "evidence entry",
    )
    appended_claim_events = resolve_items(
        manifest["appended_claim_event_ids"],
        claim_event_by_id,
        "claim event",
    )
    appended_outcome_events = resolve_items(
        manifest["appended_outcome_event_ids"],
        outcome_event_by_id,
        "outcome event",
    )
    appended_decision_scopes = resolve_items(
        manifest["appended_decision_scope_ids"],
        decision_scope_by_id,
        "decision scope",
    )
    appended_owner_tenures = resolve_items(
        manifest["appended_owner_tenure_ids"],
        owner_tenure_by_id,
        "owner tenure",
    )
    if errors:
        return None, errors
    return (
        {
            "contract": "product-decision-paf/revision-delta/v1",
            "hypothesis_records": sorted(
                changed_records,
                key=lambda record: (
                    record["hypothesis_id"],
                    record["revision"],
                ),
            ),
            "decision_scopes": appended_decision_scopes,
            "owner_tenures": appended_owner_tenures,
            "nexus_entries": appended_nexus,
            "evidence_entries": appended_evidence,
            "claim_events": appended_claim_events,
            "outcome_events": appended_outcome_events,
        },
        [],
    )


def revision_delta_hash(payload: dict) -> str:
    return sha256_bytes(canonical_bytes(payload))


def revision_commitment_payload(
    *,
    workspace_id: str,
    workspace_revision: int,
    previous_revision_sha256: str | None,
    previous_state_sha256: str | None,
    change_set_sha256: str,
    receipt_id: str,
    accepted_at: str,
    change_manifest: dict,
    summary: dict,
    delta_sha256: str,
) -> dict:
    return {
        "contract": "product-decision-paf/revision-commitment/v1",
        "workspace_id": workspace_id,
        "workspace_revision": workspace_revision,
        "previous_revision_sha256": previous_revision_sha256,
        "previous_state_sha256": previous_state_sha256,
        "change_set_sha256": change_set_sha256,
        "receipt_id": receipt_id,
        "accepted_at": accepted_at,
        "change_manifest": change_manifest,
        "state_summary": summary,
        "revision_delta_sha256": delta_sha256,
    }


def revision_commitment_hash(**kwargs) -> str:
    return sha256_bytes(
        canonical_bytes(revision_commitment_payload(**kwargs))
    )


def proposal_attempt_payload(
    *,
    sequence: int,
    previous_proposal_sha256: str | None,
    change_set_id: str,
    change_set_sha256: str,
    receipt_id: str,
    receipt_sha256: str,
) -> dict:
    return {
        "contract": "product-decision-paf/proposal-attempt-commitment/v1",
        "sequence": sequence,
        "previous_proposal_sha256": previous_proposal_sha256,
        "change_set_id": change_set_id,
        "change_set_sha256": change_set_sha256,
        "receipt_id": receipt_id,
        "receipt_sha256": receipt_sha256,
    }


def proposal_attempt_hash(**kwargs) -> str:
    return sha256_bytes(canonical_bytes(proposal_attempt_payload(**kwargs)))


def approval_refs_for_records(
    records: list[dict],
    workspace_id: str,
    active_owner_tenure_id: str,
) -> list[str]:
    state = {
        "workspace_id": workspace_id,
        "active_owner_tenure_id": active_owner_tenure_id,
        "hypotheses": records,
    }
    return approval_refs(state)


def validate_bundle_semantics(bundle: dict, registry: SchemaRegistry) -> list[str]:
    errors = registry.validate(bundle, BUNDLE_SCHEMA)
    if errors:
        return errors

    current = bundle["current_state"]
    revisions = bundle["revision_history"]
    hypothesis_history = bundle["hypothesis_history"]
    receipts = bundle["receipts"]
    handled = bundle["handled_proposals"]
    workspace_id = bundle["workspace_id"]

    if len(revisions) > MAX_REVISION_COUNT:
        errors.append("bundle exceeds the reference adapter revision limit")

    if current is None:
        if revisions or hypothesis_history:
            errors.append("empty bundle contains accepted state history")
    else:
        if current["workspace_id"] != workspace_id:
            errors.append("current state belongs to another workspace")
        errors.extend(validate_state_semantics(current))
        if not revisions:
            errors.append("current state has no revision ledger")
        elif current["revision"] != revisions[-1]["workspace_revision"]:
            errors.append("current state revision does not match ledger")
        elif revisions[-1]["state_sha256"] != sha256_bytes(
            canonical_bytes(current)
        ):
            errors.append("current state hash does not match revision ledger")
        elif revisions[-1]["state_summary"] != state_summary(current):
            errors.append("current state summary does not match revision ledger")
        if revisions and current["revision_chain_head_sha256"] != (
            revisions[-1]["revision_sha256"]
        ):
            errors.append(
                "current state revision-chain head does not match ledger"
            )

    receipt_ids = [receipt["receipt_id"] for receipt in receipts]
    change_ids = [item["change_set_id"] for item in handled]
    handled_receipt_ids = [item["receipt_id"] for item in handled]
    if len(receipt_ids) != len(set(receipt_ids)):
        errors.append("bundle contains duplicate receipt IDs")
    if len(change_ids) != len(set(change_ids)):
        errors.append("bundle contains duplicate handled change-set IDs")
    if len(handled_receipt_ids) != len(set(handled_receipt_ids)):
        errors.append("bundle reuses a receipt across handled proposals")
    if len(receipts) != len(handled):
        errors.append("bundle receipt and handled-proposal counts differ")
    if receipt_ids != handled_receipt_ids:
        errors.append("bundle receipt and handled-proposal order differs")

    receipt_by_id = {
        receipt["receipt_id"]: receipt for receipt in receipts
    }
    handled_by_receipt = {
        item["receipt_id"]: item for item in handled
    }
    for item in handled:
        receipt = receipt_by_id.get(item["receipt_id"])
        if receipt is None:
            errors.append("handled proposal points to a missing receipt")
            continue
        if receipt["change_set_id"] != item["change_set_id"]:
            errors.append("handled proposal change_set_id does not match receipt")
        if receipt["change_set_sha256"] != item["change_set_sha256"]:
            errors.append("handled proposal hash does not match receipt")
        expected_receipt_sha256 = sha256_bytes(canonical_bytes(receipt))
        if item["receipt_sha256"] != expected_receipt_sha256:
            errors.append(
                "handled proposal receipt commitment does not match receipt"
            )
    previous_proposal_sha256: str | None = None
    for index, item in enumerate(handled, start=1):
        if item["sequence"] != index:
            errors.append("proposal-attempt sequence is not contiguous")
        if item["previous_proposal_sha256"] != previous_proposal_sha256:
            errors.append("proposal-attempt commitment chain is broken")
        expected_proposal_sha256 = proposal_attempt_hash(
            sequence=item["sequence"],
            previous_proposal_sha256=item["previous_proposal_sha256"],
            change_set_id=item["change_set_id"],
            change_set_sha256=item["change_set_sha256"],
            receipt_id=item["receipt_id"],
            receipt_sha256=item["receipt_sha256"],
        )
        if item["proposal_sha256"] != expected_proposal_sha256:
            errors.append(
                "proposal-attempt commitment hash does not match its payload"
            )
        previous_proposal_sha256 = item["proposal_sha256"]
    if bundle["proposal_history_head_sha256"] != previous_proposal_sha256:
        errors.append("proposal-attempt history head does not match its chain")
    for receipt in receipts:
        if receipt["workspace_id"] != workspace_id:
            errors.append("receipt belongs to another workspace")
        if (
            receipt["adapter"] != "standalone_file"
            or receipt["adapter_ref"] != "script:hypothesis-state-v1"
        ):
            errors.append("bundle contains a receipt from another adapter")
        if receipt["receipt_id"] != receipt_id_for(receipt["change_set_id"]):
            errors.append("receipt ID is not bound to its change-set ID")
        if receipt["receipt_id"] not in handled_by_receipt:
            errors.append("receipt has no handled-proposal entry")
        if not receipt["validation"]["atomic_replace_protocol_used"]:
            errors.append("persisted receipt lacks atomic bundle-write evidence")

    revision_numbers = [
        item["workspace_revision"] for item in revisions
    ]
    if revision_numbers != list(range(len(revisions))):
        errors.append("revision ledger must be contiguous from zero")
    for index, revision in enumerate(revisions):
        expected_previous_state = (
            None if index == 0 else revisions[index - 1]["state_sha256"]
        )
        expected_previous_revision = (
            None if index == 0 else revisions[index - 1]["revision_sha256"]
        )
        if revision["previous_state_sha256"] != expected_previous_state:
            errors.append("revision ledger state-hash chain is broken")
        if revision["previous_revision_sha256"] != expected_previous_revision:
            errors.append("revision commitment chain is broken")

    revision_by_number = {
        item["workspace_revision"]: item for item in revisions
    }
    accepted_by_revision: dict[int, list[dict]] = {}
    for receipt in receipts:
        if receipt["status"] != "accepted":
            continue
        if not all(receipt["validation"].values()):
            errors.append("accepted receipt contains a failed validation gate")
        revision = receipt["new_workspace_revision"]
        revision_record = revision_by_number.get(revision)
        if revision_record is None:
            errors.append("accepted receipt points to a missing revision record")
            continue
        accepted_by_revision.setdefault(revision, []).append(receipt)
        if receipt["state_sha256"] != revision_record["state_sha256"]:
            errors.append("accepted receipt state hash does not match ledger")
        if receipt["change_set_sha256"] != revision_record["change_set_sha256"]:
            errors.append(
                "accepted receipt change-set hash does not match ledger"
            )
        if receipt["persisted_at"] != revision_record["accepted_at"]:
            errors.append("accepted receipt time does not match ledger")
        if receipt["receipt_id"] != revision_record["receipt_id"]:
            errors.append("accepted receipt ID does not match ledger")
        if receipt["storage_ref"] != f"bundle:state:{revision}":
            errors.append("accepted receipt storage ref does not match ledger")
        expected_previous = None if revision == 0 else revision - 1
        if receipt["expected_workspace_revision"] != expected_previous:
            errors.append("accepted receipt expected revision is inconsistent")
        if receipt["observed_workspace_revision"] != expected_previous:
            errors.append("accepted receipt observed revision is inconsistent")

    for revision in revision_by_number:
        if len(accepted_by_revision.get(revision, [])) != 1:
            errors.append(
                f"revision {revision} lacks one unique accepted receipt"
            )

    record_versions: dict[tuple[str, int], dict] = {}
    records_by_hypothesis: dict[str, list[dict]] = {}
    for record in hypothesis_history:
        key = (record["hypothesis_id"], record["revision"])
        if key in record_versions:
            errors.append("bundle contains duplicate hypothesis revision")
            continue
        record_versions[key] = record
        records_by_hypothesis.setdefault(record["hypothesis_id"], []).append(record)

    for hypothesis_id, versions in records_by_hypothesis.items():
        versions.sort(key=lambda item: item["revision"])
        if [item["revision"] for item in versions] != list(range(len(versions))):
            errors.append(
                f"hypothesis history for {hypothesis_id} is not contiguous"
            )
        if (
            versions
            and versions[0]["state"] in {"cancelled", "superseded"}
            and versions[0]["execution_ref"] is not None
        ):
            errors.append(
                f"hypothesis history for {hypothesis_id} invents execution evidence"
            )
        for previous, candidate in zip(versions, versions[1:]):
            errors.extend(
                validate_hypothesis_transition(previous, candidate)
            )

    manifest_record_pairs: list[tuple[str, int]] = []
    cumulative_nexus: list[str] = []
    cumulative_evidence: list[str] = []
    cumulative_claim_events: list[str] = []
    cumulative_outcome_events: list[str] = []
    cumulative_decision_scopes: list[str] = []
    cumulative_owner_tenures: list[str] = []
    replay_claim_events: list[dict] = []
    decision_scope_by_id = (
        {
            scope["scope_id"]: scope
            for scope in current["decision_scope_log"]
        }
        if current is not None
        else {}
    )
    owner_tenure_by_id = (
        {
            tenure["tenure_id"]: tenure
            for tenure in current["owner_tenure_log"]
        }
        if current is not None
        else {}
    )
    nexus_by_id = (
        {
            entry["entry_id"]: entry
            for entry in current["nexus_entries"]
        }
        if current is not None
        else {}
    )
    evidence_by_id = (
        {
            entry["evidence_id"]: entry
            for entry in current["evidence_log"]
        }
        if current is not None
        else {}
    )
    claim_event_by_id = (
        {
            event["event_id"]: event
            for event in current["claim_log"]
        }
        if current is not None
        else {}
    )
    outcome_event_by_id = (
        {
            event["event_id"]: event
            for event in current["outcome_log"]
        }
        if current is not None
        else {}
    )
    replay_records: dict[str, dict] = {}
    replay_focus: str | None = None
    replay_base: str | None = None
    replay_active_scope_id: str | None = None
    replay_active_tenure_id: str | None = None
    nexus_first_revision: dict[str, int] = {}
    accepted_receipts = {
        receipt["new_workspace_revision"]: receipt
        for receipt in receipts
        if receipt["status"] == "accepted"
    }
    accepted_change_ids = {
        receipt["change_set_id"]
        for receipt in receipts
        if receipt["status"] == "accepted"
    }
    seen_approval_ids: set[str] = set()
    seen_pending_requirements: set[bytes] = set()
    seen_pending_resolution_ids: set[str] = set()
    for revision_index, revision in enumerate(revisions):
        manifest = revision["change_manifest"]
        created_records: list[dict] = []
        changed_records_this_revision: list[dict] = []
        for create in manifest["hypothesis_creates"]:
            pair = (create["hypothesis_id"], create["candidate_revision"])
            manifest_record_pairs.append(pair)
            record = record_versions.get(pair)
            if record is None:
                errors.append("revision manifest creates a missing hypothesis")
            elif pair[0] in replay_records:
                errors.append("revision manifest recreates a hypothesis")
            else:
                replay_records[pair[0]] = record
                created_records.append(record)
                changed_records_this_revision.append(record)
        for update in manifest["hypothesis_updates"]:
            pair = (update["hypothesis_id"], update["candidate_revision"])
            manifest_record_pairs.append(pair)
            record = record_versions.get(pair)
            previous = replay_records.get(update["hypothesis_id"])
            if record is None or previous is None:
                errors.append("revision manifest updates a missing hypothesis")
                continue
            if (
                update["expected_revision"] != previous["revision"]
                or update["candidate_revision"] != previous["revision"] + 1
                or update["from_state"] != previous["state"]
                or update["to_state"] != record["state"]
            ):
                errors.append("revision manifest hypothesis update is inconsistent")
            replay_records[update["hypothesis_id"]] = record
            changed_records_this_revision.append(record)

        for scope_id in manifest["appended_decision_scope_ids"]:
            scope = decision_scope_by_id.get(scope_id)
            expected_predecessor = (
                cumulative_decision_scopes[-1]
                if cumulative_decision_scopes
                else None
            )
            if scope is not None and (
                scope["opened_workspace_revision"]
                != revision["workspace_revision"]
                or scope["predecessor_scope_id"] != expected_predecessor
            ):
                errors.append(
                    "decision-scope history is inconsistent with its revision"
                )
            cumulative_decision_scopes.append(scope_id)
        if manifest["appended_decision_scope_ids"]:
            replay_active_scope_id = manifest[
                "appended_decision_scope_ids"
            ][-1]
        for tenure_id in manifest["appended_owner_tenure_ids"]:
            tenure = owner_tenure_by_id.get(tenure_id)
            expected_predecessor = (
                cumulative_owner_tenures[-1]
                if cumulative_owner_tenures
                else None
            )
            if tenure is not None and (
                tenure["effective_workspace_revision"]
                != revision["workspace_revision"]
                or tenure["predecessor_tenure_id"]
                != expected_predecessor
            ):
                errors.append(
                    "owner-tenure history is inconsistent with its revision"
                )
            cumulative_owner_tenures.append(tenure_id)
        if manifest["appended_owner_tenure_ids"]:
            replay_active_tenure_id = manifest[
                "appended_owner_tenure_ids"
            ][-1]
        for update in manifest["hypothesis_updates"]:
            if update["to_state"] != "closed":
                continue
            closing_record = replay_records.get(update["hypothesis_id"])
            if closing_record is None:
                continue
            for required_scope in ("decision_rule", "terminal_verdict"):
                if not has_current_approval(
                    closing_record,
                    required_scope,
                    workspace_id,
                    replay_active_tenure_id,
                ):
                    errors.append(
                        "historical closing decision lacks active owner authority"
                    )
        receipt = accepted_receipts.get(revision["workspace_revision"])
        accepted_change_id = (
            receipt["change_set_id"] if receipt is not None else None
        )
        for record in created_records:
            if record["decision_scope_id"] != replay_active_scope_id:
                errors.append(
                    "created hypothesis does not belong to the active decision scope"
                )
        for record in replay_records.values():
            if (
                record["state"] not in TERMINAL_STATES
                and record["decision_scope_id"] != replay_active_scope_id
            ):
                errors.append(
                    "historical active hypothesis belongs to an inactive decision scope"
                )
        for record in changed_records_this_revision:
            for approval in record["owner_approvals"]:
                approval_id = approval["approval_id"]
                if approval_id in seen_approval_ids:
                    continue
                seen_approval_ids.add(approval_id)
                tenure = owner_tenure_by_id.get(
                    approval["owner_tenure_id"]
                )
                if approval["owner_tenure_id"] != replay_active_tenure_id:
                    errors.append(
                        "owner approval was added under an inactive tenure"
                    )
                if (
                    tenure is None
                    or tenure["owner_ref"] != approval["owner_ref"]
                ):
                    errors.append(
                        "owner approval does not match its historical tenure"
                    )
            for requirement in record["pending_owner_approvals"]:
                requirement_key = canonical_bytes(requirement)
                if requirement_key in seen_pending_requirements:
                    continue
                seen_pending_requirements.add(requirement_key)
                if (
                    requirement["owner_tenure_id"]
                    != replay_active_tenure_id
                ):
                    errors.append(
                        "pending owner request was added under an inactive tenure"
                    )
                if requirement["source_change_set_id"] != accepted_change_id:
                    errors.append(
                        "pending owner request source does not match its creation revision"
                    )
            for resolution in record["pending_owner_resolutions"]:
                resolution_id = resolution["resolution_id"]
                if resolution_id in seen_pending_resolution_ids:
                    continue
                seen_pending_resolution_ids.add(resolution_id)
                if (
                    resolution["authority_tenure_id"]
                    != replay_active_tenure_id
                ):
                    errors.append(
                        "pending owner resolution was added under an inactive tenure"
                    )
                if (
                    resolution["resolution"]
                    == "invalidated_by_tenure_transition"
                    and resolution["authority_tenure_id"]
                    not in manifest["appended_owner_tenure_ids"]
                ):
                    errors.append(
                        "historical pending invalidation lacks its owner transition"
                    )
        for entry_id in manifest["appended_nexus_entry_ids"]:
            if entry_id in nexus_first_revision:
                errors.append(
                    "revision manifest appends a duplicate Nexus entry"
                )
            else:
                nexus_first_revision[entry_id] = revision[
                    "workspace_revision"
                ]
            entry = nexus_by_id.get(entry_id)
            if (
                entry is not None
                and entry["kind"] == "decision"
                and isinstance(entry["decision_authority"], dict)
                and (
                    entry["decision_authority"]["owner_tenure_id"]
                    != replay_active_tenure_id
                    or entry["decision_authority"]["decision_scope_id"]
                    != replay_active_scope_id
                )
            ):
                errors.append(
                    "historical Nexus decision was added outside active authority"
                )
            cumulative_nexus.append(entry_id)
        cumulative_evidence.extend(manifest["appended_evidence_ids"])
        appended_claim_event_ids = manifest["appended_claim_event_ids"]
        cumulative_claim_events.extend(appended_claim_event_ids)
        for event_id in appended_claim_event_ids:
            event = claim_event_by_id.get(event_id)
            if event is None:
                errors.append(
                    "revision manifest appends a missing claim event"
                )
            else:
                replay_claim_events.append(event)
        appended_outcome_event_ids = manifest[
            "appended_outcome_event_ids"
        ]
        cumulative_outcome_events.extend(appended_outcome_event_ids)
        for event_id in appended_outcome_event_ids:
            event = outcome_event_by_id.get(event_id)
            if event is None:
                errors.append(
                    "revision manifest appends a missing outcome event"
                )
                continue
            outcome_hypothesis = replay_records.get(
                event["hypothesis_id"]
            )
            if (
                outcome_hypothesis is None
                or outcome_hypothesis["state"] != "closed"
                or outcome_hypothesis["decision_scope_id"]
                != event["decision_scope_id"]
            ):
                errors.append(
                    "historical outcome event lacks its closed hypothesis context"
                )
        for record in created_records:
            origin = record["origin"]
            if origin["nexus_revision"] != revision["workspace_revision"]:
                errors.append(
                    "hypothesis origin revision does not match its creation revision"
                )
            for entry_id in origin["originating_entry_ids"]:
                first_revision = nexus_first_revision.get(entry_id)
                if (
                    first_revision is None
                    or first_revision > origin["nexus_revision"]
                ):
                    errors.append(
                        "hypothesis origin cites a future Nexus entry"
                    )
        base_change = manifest["base_change"]
        if base_change is not None:
            if base_change["from"] != replay_base:
                errors.append("revision manifest evidence-base chain is inconsistent")
            replay_base = base_change["to"]
        elif replay_base is None:
            errors.append("initial revision has no evidence-base change")
        focus_change = manifest["focus_change"]
        if focus_change is not None:
            if focus_change["from"] != replay_focus:
                errors.append("revision manifest focus chain is inconsistent")
            replay_focus = focus_change["to"]
        expected_summary = {
            "base": replay_base,
            "active_decision_scope_id": replay_active_scope_id,
            "decision_scope_count": len(cumulative_decision_scopes),
            "active_owner_tenure_id": replay_active_tenure_id,
            "owner_tenure_count": len(cumulative_owner_tenures),
            "hypothesis_count": len(replay_records),
            "nexus_entry_count": len(cumulative_nexus),
            "evidence_count": len(cumulative_evidence),
            "claim_event_count": len(cumulative_claim_events),
            "outcome_event_count": len(cumulative_outcome_events),
            "active_blocked_claim_count": len(
                active_blocked_claim_ids(replay_claim_events)
            ),
        }
        if revision["state_summary"] != expected_summary:
            errors.append("revision state summary does not match manifest history")
        delta_payload, delta_errors = revision_delta_payload(
            manifest,
            record_versions=record_versions,
            decision_scope_by_id=decision_scope_by_id,
            owner_tenure_by_id=owner_tenure_by_id,
            nexus_by_id=nexus_by_id,
            evidence_by_id=evidence_by_id,
            claim_event_by_id=claim_event_by_id,
            outcome_event_by_id=outcome_event_by_id,
        )
        errors.extend(delta_errors)
        if delta_payload is not None:
            expected_delta_sha256 = revision_delta_hash(delta_payload)
            if revision["revision_delta_sha256"] != expected_delta_sha256:
                errors.append(
                    "revision delta hash does not match immutable history"
                )
            expected_revision_sha256 = revision_commitment_hash(
                workspace_id=workspace_id,
                workspace_revision=revision["workspace_revision"],
                previous_revision_sha256=(
                    None
                    if revision_index == 0
                    else revisions[revision_index - 1]["revision_sha256"]
                ),
                previous_state_sha256=(
                    None
                    if revision_index == 0
                    else revisions[revision_index - 1]["state_sha256"]
                ),
                change_set_sha256=revision["change_set_sha256"],
                receipt_id=revision["receipt_id"],
                accepted_at=revision["accepted_at"],
                change_manifest=manifest,
                summary=revision["state_summary"],
                delta_sha256=revision["revision_delta_sha256"],
            )
            if revision["revision_sha256"] != expected_revision_sha256:
                errors.append(
                    "revision commitment hash does not match its payload"
                )
        if receipt is not None and receipt["approval_refs"] != (
            approval_refs_for_records(
                list(replay_records.values()),
                workspace_id,
                replay_active_tenure_id,
            )
        ):
            errors.append("accepted receipt approval refs do not match history")

    if len(manifest_record_pairs) != len(set(manifest_record_pairs)):
        errors.append("hypothesis revision appears in more than one manifest")
    if set(manifest_record_pairs) != set(record_versions):
        errors.append("hypothesis history and revision manifests differ")

    if current is not None:
        current_records = {
            record["hypothesis_id"]: record
            for record in current["hypotheses"]
        }
        if current_records != replay_records:
            errors.append("current hypotheses do not match replayed history")
        if [
            record["hypothesis_id"] for record in current["hypotheses"]
        ] != list(replay_records):
            errors.append("current hypothesis order does not match history")
        if [item["entry_id"] for item in current["nexus_entries"]] != (
            cumulative_nexus
        ):
            errors.append("current Nexus log does not match revision manifests")
        if [item["evidence_id"] for item in current["evidence_log"]] != (
            cumulative_evidence
        ):
            errors.append("current evidence log does not match revision manifests")
        if [
            scope["scope_id"] for scope in current["decision_scope_log"]
        ] != cumulative_decision_scopes:
            errors.append(
                "current decision-scope log does not match revision manifests"
            )
        if [
            tenure["tenure_id"] for tenure in current["owner_tenure_log"]
        ] != cumulative_owner_tenures:
            errors.append(
                "current owner-tenure log does not match revision manifests"
            )
        if [item["event_id"] for item in current["claim_log"]] != (
            cumulative_claim_events
        ):
            errors.append(
                "current claim log does not match revision manifests"
            )
        if [item["event_id"] for item in current["outcome_log"]] != (
            cumulative_outcome_events
        ):
            errors.append(
                "current outcome log does not match revision manifests"
            )
        if current["base"] != replay_base:
            errors.append("current evidence base does not match revision manifests")
        if current["active_decision_scope_id"] != replay_active_scope_id:
            errors.append(
                "current active decision scope does not match history"
            )
        if current["active_owner_tenure_id"] != replay_active_tenure_id:
            errors.append(
                "current active owner tenure does not match history"
            )
        if current["focus_hypothesis_id"] != replay_focus:
            errors.append("current focus does not match revision manifests")
        if revisions and current["last_persistence_receipt_ref"] != (
            f"receipt:{revisions[-1]['receipt_id']}"
        ):
            errors.append("current state does not point to latest accepted receipt")

        current_hypothesis_ids = set(current_records)
        nexus_ids = {item["entry_id"] for item in current["nexus_entries"]}
        evidence_ids = {item["evidence_id"] for item in current["evidence_log"]}
        for record in hypothesis_history:
            errors.extend(
                require_unique_ids(
                    record["owner_approvals"],
                    "approval_id",
                    f"archived approvals for {record['hypothesis_id']}",
                )
            )
            errors.extend(
                require_unique_ids(
                    record["pending_owner_resolutions"],
                    "resolution_id",
                    (
                        "archived pending resolutions for "
                        f"{record['hypothesis_id']}"
                    ),
                )
            )
            if not set(record["origin"]["originating_entry_ids"]).issubset(
                nexus_ids
            ):
                errors.append("archived hypothesis has unknown Nexus refs")
            if not set(record["evidence_ids"]).issubset(evidence_ids):
                errors.append("archived hypothesis has unknown evidence refs")
            if not set(record["result"]["outcome_evidence_ids"]).issubset(
                evidence_ids
            ):
                errors.append("archived hypothesis has unknown outcome evidence")
            if not set(record["result"]["new_nexus_entry_ids"]).issubset(
                nexus_ids
            ):
                errors.append("archived hypothesis has unknown new Nexus refs")
            for dependency in record["upstream_dependencies"]:
                dependency_hypothesis = dependency["hypothesis_id"]
                if (
                    dependency_hypothesis is not None
                    and dependency_hypothesis not in current_hypothesis_ids
                ):
                    errors.append(
                        "archived hypothesis has an unknown upstream hypothesis"
                    )
                if not set(dependency["evidence_ids"]).issubset(evidence_ids):
                    errors.append(
                        "archived hypothesis has unknown upstream evidence"
                    )
            relation_ids = set(record["relations"]["based_on_hypothesis_ids"])
            replacement = record["relations"]["replaces_hypothesis_id"]
            if replacement is not None:
                relation_ids.add(replacement)
            if not relation_ids.issubset(current_hypothesis_ids):
                errors.append("archived hypothesis has unknown relations")
            archived_tenure_id = (
                record["pending_owner_approvals"][-1]["owner_tenure_id"]
                if record["pending_owner_approvals"]
                else (
                    record["owner_approvals"][-1]["owner_tenure_id"]
                    if record["owner_approvals"]
                    else current["owner_tenure_log"][0]["tenure_id"]
                )
            )
            errors.extend(
                validate_owner_gates(
                    record,
                    owner_tenure_by_id,
                    archived_tenure_id,
                    workspace_id,
                )
            )
            errors.extend(
                validate_pending_approvals(
                    record,
                    owner_tenure_by_id,
                    archived_tenure_id,
                    workspace_id,
                )
            )
            errors.extend(validate_result_gates(record, evidence_by_id))
            for requirement in record["pending_owner_approvals"]:
                if requirement["source_change_set_id"] not in accepted_change_ids:
                    errors.append(
                        "pending owner approval source change set was not accepted"
                    )
            for approval in record["owner_approvals"]:
                subject_record = record_versions.get(
                    (
                        record["hypothesis_id"],
                        approval["subject_revision"],
                    )
                )
                if subject_record is None:
                    errors.append(
                        f"approval {approval['approval_id']} has no subject revision"
                    )
                    continue
                expected_hash = approval_subject_sha256(
                    subject_record,
                    approval["scope"],
                    workspace_id,
                    approval["owner_tenure_id"],
                    approval["subject_revision"],
                )
                if approval["subject_sha256"] != expected_hash:
                    errors.append(
                        f"approval {approval['approval_id']} subject history mismatch"
                    )
            for resolution in record["pending_owner_resolutions"]:
                subject_record = record_versions.get(
                    (
                        record["hypothesis_id"],
                        resolution["subject_revision"],
                    )
                )
                if subject_record is None:
                    errors.append(
                        f"pending resolution {resolution['resolution_id']} has no subject revision"
                    )
                    continue
                expected_hash = approval_subject_sha256(
                    subject_record,
                    resolution["approval_scope"],
                    workspace_id,
                    resolution["request_owner_tenure_id"],
                    resolution["subject_revision"],
                )
                if resolution["subject_sha256"] != expected_hash:
                    errors.append(
                        f"pending resolution {resolution['resolution_id']} subject history mismatch"
                    )

    errors.extend(validate_sensitive_data(bundle))
    return errors


def receipt_id_for(change_set_id: str) -> str:
    digest = hashlib.sha256(change_set_id.encode("utf-8")).hexdigest()[:24]
    return f"receipt-{digest}"


def storage_ref_for(revision: int) -> str:
    return f"bundle:state:{revision}"


def approval_refs(state: dict) -> list[str]:
    refs: set[str] = set()
    for record in state["hypotheses"]:
        for scope in (
            "decision_rule",
            "proposed_assumption",
            "state_transition",
            "terminal_verdict",
        ):
            approval = current_approval(
                record,
                scope,
                state["workspace_id"],
                (
                    None
                    if record["state"] in TERMINAL_STATES
                    else state["active_owner_tenure_id"]
                ),
            )
            if approval is not None:
                refs.add(approval["safe_receipt_ref"])
    return sorted(refs)


def build_receipt(
    change_set: dict,
    *,
    change_set_hash: str,
    status: str,
    attempted_at: str,
    observed_revision: int | None,
    new_revision: int | None = None,
    state_hash: str | None = None,
    approvals: list[str] | None = None,
    validation: dict[str, bool],
    error_code: str | None = None,
    error_message: str | None = None,
) -> dict:
    receipt_id = receipt_id_for(change_set["change_set_id"])
    accepted = status == "accepted"
    return {
        "schema_version": "product-decision-paf/persistence-receipt/v1",
        "data_policy": "safe_refs_and_summaries_only",
        "durability_scope": (
            "atomic_replace_with_readback_power_loss_host_dependent"
        ),
        "receipt_id": receipt_id,
        "change_set_id": change_set["change_set_id"],
        "change_set_sha256": change_set_hash,
        "workspace_id": change_set["workspace_id"],
        "status": status,
        "adapter": "standalone_file",
        "adapter_ref": "script:hypothesis-state-v1",
        "attempted_at": attempted_at,
        "persisted_at": attempted_at if accepted else None,
        "expected_workspace_revision": change_set["expected_workspace_revision"],
        "observed_workspace_revision": observed_revision,
        "new_workspace_revision": new_revision if accepted else None,
        "state_sha256": state_hash if accepted else None,
        "storage_ref": storage_ref_for(new_revision) if accepted else None,
        "approval_refs": approvals or [],
        "validation": validation,
        "safe_error": (
            None
            if accepted
            else {"code": error_code or "adapter_error", "message": error_message or "failed"}
        ),
    }


def validate_receipt_or_raise(registry: SchemaRegistry, receipt: dict) -> None:
    errors = registry.validate(receipt, RECEIPT_SCHEMA)
    if errors:
        raise AdapterError("adapter produced an invalid persistence receipt")


def empty_bundle(workspace_id: str) -> dict:
    return {
        "schema_version": "product-decision-paf/hypothesis-state-bundle/v1",
        "data_policy": "safe_refs_and_summaries_only",
        "workspace_id": workspace_id,
        "current_state": None,
        "revision_history": [],
        "hypothesis_history": [],
        "receipts": [],
        "handled_proposals": [],
        "proposal_history_head_sha256": None,
    }


def load_bundle(root: Path, registry: SchemaRegistry) -> dict | None:
    path = checked_child_path(root, BUNDLE_FILENAME)
    if not path.exists():
        return None
    try:
        if path.stat().st_size > MAX_BUNDLE_BYTES:
            raise AdapterError(
                "state bundle exceeds the reference adapter size limit"
            )
    except OSError as exc:
        raise AdapterError("hypothesis state bundle could not be inspected") from exc
    loaded = load_json(path, "hypothesis state bundle")
    if not isinstance(loaded, dict):
        raise AdapterError("hypothesis state bundle root must be an object")
    errors = validate_bundle_semantics(loaded, registry)
    if errors:
        raise AdapterError(
            f"persisted hypothesis state bundle is invalid: {errors[0]}"
        )
    return loaded


def write_bundle(
    root: Path,
    bundle: dict,
    registry: SchemaRegistry,
    *,
    lock_token: str,
) -> None:
    serialized = pretty_bytes(bundle)
    if len(serialized) > MAX_BUNDLE_BYTES:
        raise AdapterError(
            "state bundle exceeds the reference adapter size limit; migrate the "
            "same portable contract to a transactional host"
        )
    if len(bundle.get("revision_history", [])) > MAX_REVISION_COUNT:
        raise AdapterError(
            "state bundle exceeds the reference adapter revision limit; migrate "
            "the same portable contract to a transactional host"
        )
    errors = validate_bundle_semantics(bundle, registry)
    if errors:
        raise AdapterError(f"adapter produced an invalid state bundle: {errors[0]}")
    path = checked_child_path(root, BUNDLE_FILENAME)
    expected = canonical_bytes(bundle)
    atomic_write(path, serialized, lock_token=lock_token)
    try:
        loaded = load_json(path, "written hypothesis state bundle")
    except AdapterError as exc:
        raise OutcomeUnknownError(
            "bundle replace completed but exact readback is unknown; run verify"
        ) from exc
    if canonical_bytes(loaded) != expected:
        raise OutcomeUnknownError(
            "bundle replace completed but exact readback does not match; run verify"
        )


def append_handled_receipt(
    bundle: dict,
    receipt: dict,
    change_set_hash: str,
) -> None:
    sequence = len(bundle["handled_proposals"]) + 1
    previous_proposal_sha256 = bundle[
        "proposal_history_head_sha256"
    ]
    receipt_sha256 = sha256_bytes(canonical_bytes(receipt))
    proposal_sha256 = proposal_attempt_hash(
        sequence=sequence,
        previous_proposal_sha256=previous_proposal_sha256,
        change_set_id=receipt["change_set_id"],
        change_set_sha256=change_set_hash,
        receipt_id=receipt["receipt_id"],
        receipt_sha256=receipt_sha256,
    )
    bundle["receipts"].append(receipt)
    bundle["handled_proposals"].append(
        {
            "sequence": sequence,
            "previous_proposal_sha256": previous_proposal_sha256,
            "change_set_id": receipt["change_set_id"],
            "change_set_sha256": change_set_hash,
            "receipt_id": receipt["receipt_id"],
            "receipt_sha256": receipt_sha256,
            "proposal_sha256": proposal_sha256,
        }
    )
    bundle["proposal_history_head_sha256"] = proposal_sha256


def print_json(value: object) -> None:
    print(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
    )


def receipt_exit_code(status: str) -> int:
    return {
        "accepted": 0,
        "conflict": 3,
        "rejected": 4,
        "failed": 5,
    }[status]


def command_load(args: argparse.Namespace) -> int:
    root = ensure_state_root(args.root, create=False)
    registry = SchemaRegistry(ASSET_ROOT)
    bundle = load_bundle(root, registry)
    if bundle is None or bundle["current_state"] is None:
        print("workspace state does not exist", file=sys.stderr)
        return 2
    print_json(bundle["current_state"])
    return 0


def command_validate_intent(args: argparse.Namespace) -> int:
    registry = SchemaRegistry(ASSET_ROOT)
    intent = load_json(
        args.intent.resolve(),
        "proposal intent",
        max_bytes=MAX_PROPOSAL_INTENT_BYTES,
    )
    if not isinstance(intent, dict):
        raise AdapterError("proposal intent root must be an object")
    errors = registry.validate(intent, PROPOSAL_INTENT_SCHEMA)
    if not errors:
        errors.extend(validate_proposal_intent_semantics(intent))
    errors.extend(validate_sensitive_data(intent))
    if errors:
        print("proposal intent is invalid", file=sys.stderr)
        for error in errors[:20]:
            print(f"- {error}", file=sys.stderr)
        return 4
    print_json(
        {
            "status": "valid_proposal_intent",
            "intent_id": intent["intent_id"],
            "commit_eligible": False,
            "persistence_status": "not_persisted",
        }
    )
    return 0


def command_verify(args: argparse.Namespace) -> int:
    root = ensure_state_root(args.root, create=False)
    registry = SchemaRegistry(ASSET_ROOT)
    bundle = load_bundle(root, registry)
    if bundle is None:
        print("FAIL hypothesis workspace verification", file=sys.stderr)
        print("- hypothesis state bundle does not exist", file=sys.stderr)
        return 2
    if bundle["current_state"] is None:
        print("FAIL hypothesis workspace verification", file=sys.stderr)
        print("- bundle has no accepted workspace state", file=sys.stderr)
        return 2

    latest = bundle["current_state"]
    summary = {
        "status": "verified",
        "workspace_id": bundle["workspace_id"],
        "revision": latest["revision"] if latest is not None else None,
        "state_revisions": len(bundle["revision_history"]),
        "hypotheses": len(latest["hypotheses"]),
        "evidence_entries": len(latest["evidence_log"]),
        "receipts": len(bundle["receipts"]),
        "scope": (
            "local schema, semantic, revision-ledger, hypothesis-history, "
            "receipt-binding, "
            "and canonical-state-hash checks"
        ),
    }
    print_json(summary)
    return 0


def command_commit(args: argparse.Namespace) -> int:
    root = ensure_state_root(args.root, create=True)
    registry = SchemaRegistry(ASSET_ROOT)
    change_set = load_json(
        args.change_set.resolve(),
        "change set",
        max_bytes=MAX_CHANGE_SET_BYTES,
    )
    if not isinstance(change_set, dict):
        raise AdapterError("change set root must be an object")

    schema_errors = registry.validate(change_set, CHANGE_SET_SCHEMA)
    if schema_errors:
        print("change set is invalid", file=sys.stderr)
        for error in schema_errors[:20]:
            print(f"- {error}", file=sys.stderr)
        return 4

    sensitive_data_errors = validate_sensitive_data(change_set)
    change_set_hash = sha256_bytes(canonical_bytes(change_set))
    with exclusive_lock(root) as lock_payload:
        bundle = load_bundle(root, registry)
        if bundle is None:
            bundle = empty_bundle(change_set["workspace_id"])
        elif bundle["workspace_id"] != change_set["workspace_id"]:
            raise AdapterError("state root is bound to another workspace")

        handled_by_id = {
            item["change_set_id"]: item
            for item in bundle["handled_proposals"]
        }
        prior_handling = handled_by_id.get(change_set["change_set_id"])
        if prior_handling is not None:
            if prior_handling["change_set_sha256"] != change_set_hash:
                raise AdapterError(
                    "change-set ID was already used for different content"
                )
            receipt = next(
                (
                    item
                    for item in bundle["receipts"]
                    if item["receipt_id"] == prior_handling["receipt_id"]
                ),
                None,
            )
            if receipt is None:
                raise AdapterError("handled proposal has no immutable receipt")
            print_json(receipt)
            return receipt_exit_code(receipt["status"])

        previous = bundle["current_state"]

        observed_revision = previous["revision"] if previous is not None else None
        expected_revision = change_set["expected_workspace_revision"]
        operation = change_set["workspace_operation"]
        conflict = (
            (operation == "create" and previous is not None)
            or (operation == "replace" and previous is None)
            or (
                operation == "replace"
                and previous is not None
                and observed_revision != expected_revision
            )
        )
        attempted_at = utc_now()
        if conflict:
            receipt = build_receipt(
                change_set,
                change_set_hash=change_set_hash,
                status="conflict",
                attempted_at=attempted_at,
                observed_revision=observed_revision,
                validation={
                    "schema_valid": True,
                    "semantic_valid": False,
                    "concurrency_valid": False,
                    "append_only_valid": False,
                    "transition_valid": False,
                    "owner_approval_bindings_valid": False,
                    "history_chain_valid": False,
                    "sensitive_data_scan_passed": not sensitive_data_errors,
                    "atomic_replace_protocol_used": True,
                },
                error_code="revision_conflict",
                error_message="current workspace revision does not match proposal",
            )
            validate_receipt_or_raise(registry, receipt)
            candidate_bundle = copy.deepcopy(bundle)
            append_handled_receipt(
                candidate_bundle, receipt, change_set_hash
            )
            write_bundle(
                root,
                candidate_bundle,
                registry,
                lock_token=lock_payload["token"],
            )
            print_json(receipt)
            return 3

        receipt_id = receipt_id_for(change_set["change_set_id"])
        normalized_change_set = copy.deepcopy(change_set)
        candidate = normalized_change_set["candidate_state"]
        candidate["as_of"] = attempted_at
        candidate["revision_chain_head_sha256"] = None
        candidate["last_persistence_receipt_ref"] = f"receipt:{receipt_id}"
        final_schema_errors = registry.validate(candidate, WORKSPACE_SCHEMA)
        semantic_errors = (
            final_schema_errors
            + validate_change_semantics(normalized_change_set, previous)
            + sensitive_data_errors
        )
        if semantic_errors:
            receipt = build_receipt(
                change_set,
                change_set_hash=change_set_hash,
                status="rejected",
                attempted_at=attempted_at,
                observed_revision=observed_revision,
                validation={
                    "schema_valid": True,
                    "semantic_valid": False,
                    "concurrency_valid": True,
                    "append_only_valid": not any(
                        "append-only" in error for error in semantic_errors
                    ),
                    "transition_valid": not any(
                        "transition" in error or "terminal" in error
                        for error in semantic_errors
                    ),
                    "owner_approval_bindings_valid": not any(
                        "approval" in error or "unapproved" in error
                        for error in semantic_errors
                    ),
                    "history_chain_valid": False,
                    "sensitive_data_scan_passed": not any(
                        "sensitive-data" in error
                        for error in semantic_errors
                    ),
                    "atomic_replace_protocol_used": True,
                },
                error_code="semantic_rejection",
                error_message=semantic_errors[0][:500],
            )
            validate_receipt_or_raise(registry, receipt)
            candidate_bundle = copy.deepcopy(bundle)
            append_handled_receipt(
                candidate_bundle, receipt, change_set_hash
            )
            write_bundle(
                root,
                candidate_bundle,
                registry,
                lock_token=lock_payload["token"],
            )
            print_json(receipt)
            return 4

        manifest = normalized_change_set["change_manifest"]
        candidate_record_versions = {
            (record["hypothesis_id"], record["revision"]): record
            for record in candidate["hypotheses"]
        }
        delta_payload, delta_errors = revision_delta_payload(
            manifest,
            record_versions=candidate_record_versions,
            decision_scope_by_id={
                scope["scope_id"]: scope
                for scope in candidate["decision_scope_log"]
            },
            owner_tenure_by_id={
                tenure["tenure_id"]: tenure
                for tenure in candidate["owner_tenure_log"]
            },
            nexus_by_id={
                entry["entry_id"]: entry
                for entry in candidate["nexus_entries"]
            },
            evidence_by_id={
                entry["evidence_id"]: entry
                for entry in candidate["evidence_log"]
            },
            claim_event_by_id={
                event["event_id"]: event
                for event in candidate["claim_log"]
            },
            outcome_event_by_id={
                event["event_id"]: event
                for event in candidate["outcome_log"]
            },
        )
        if delta_errors or delta_payload is None:
            raise AdapterError(
                "adapter could not construct the accepted revision delta"
            )
        delta_sha256 = revision_delta_hash(delta_payload)
        previous_revision = (
            bundle["revision_history"][-1]
            if bundle["revision_history"]
            else None
        )
        previous_revision_sha256 = (
            previous_revision["revision_sha256"]
            if previous_revision is not None
            else None
        )
        previous_state_sha256 = (
            previous_revision["state_sha256"]
            if previous_revision is not None
            else None
        )
        summary = state_summary(candidate)
        revision_sha256 = revision_commitment_hash(
            workspace_id=candidate["workspace_id"],
            workspace_revision=candidate["revision"],
            previous_revision_sha256=previous_revision_sha256,
            previous_state_sha256=previous_state_sha256,
            change_set_sha256=change_set_hash,
            receipt_id=receipt_id,
            accepted_at=attempted_at,
            change_manifest=manifest,
            summary=summary,
            delta_sha256=delta_sha256,
        )
        candidate["revision_chain_head_sha256"] = revision_sha256
        final_schema_errors = registry.validate(candidate, WORKSPACE_SCHEMA)
        final_semantic_errors = (
            final_schema_errors + validate_state_semantics(candidate)
        )
        if final_semantic_errors:
            raise AdapterError("adapter metadata produced an invalid candidate state")

        state_hash = sha256_bytes(canonical_bytes(candidate))
        receipt = build_receipt(
            change_set,
            change_set_hash=change_set_hash,
            status="accepted",
            attempted_at=attempted_at,
            observed_revision=observed_revision,
            new_revision=candidate["revision"],
            state_hash=state_hash,
            approvals=approval_refs(candidate),
            validation={
                "schema_valid": True,
                "semantic_valid": True,
                "concurrency_valid": True,
                "append_only_valid": True,
                "transition_valid": True,
                "owner_approval_bindings_valid": True,
                "history_chain_valid": True,
                "sensitive_data_scan_passed": True,
                "atomic_replace_protocol_used": True,
            },
        )
        validate_receipt_or_raise(registry, receipt)

        candidate_bundle = copy.deepcopy(bundle)
        candidate_bundle["current_state"] = candidate
        candidate_records = {
            record["hypothesis_id"]: record
            for record in candidate["hypotheses"]
        }
        changed_pairs = [
            (
                item["hypothesis_id"],
                item["candidate_revision"],
            )
            for item in (
                manifest["hypothesis_creates"]
                + manifest["hypothesis_updates"]
            )
        ]
        for hypothesis_id, revision in changed_pairs:
            record = candidate_records[hypothesis_id]
            if record["revision"] != revision:
                raise AdapterError(
                    "change manifest record revision changed after validation"
                )
            candidate_bundle["hypothesis_history"].append(
                copy.deepcopy(record)
            )
        candidate_bundle["revision_history"].append(
            {
                "workspace_revision": candidate["revision"],
                "previous_revision_sha256": previous_revision_sha256,
                "previous_state_sha256": previous_state_sha256,
                "change_set_sha256": change_set_hash,
                "revision_delta_sha256": delta_sha256,
                "revision_sha256": revision_sha256,
                "state_sha256": state_hash,
                "receipt_id": receipt["receipt_id"],
                "accepted_at": attempted_at,
                "change_manifest": copy.deepcopy(manifest),
                "state_summary": summary,
            }
        )
        append_handled_receipt(candidate_bundle, receipt, change_set_hash)
        write_bundle(
            root,
            candidate_bundle,
            registry,
            lock_token=lock_payload["token"],
        )
        print_json(receipt)
        return 0


def command_inspect_lock(args: argparse.Namespace) -> int:
    root = ensure_state_root(args.root, create=False)
    _, _, payload = read_lock(root)
    liveness = process_liveness(payload["pid"])
    print_json(
        {
            "status": "locked",
            "pid": payload["pid"],
            "lock_id": payload["token"],
            "created_at": payload["created_at"],
            "owner_process_status": liveness,
            "recoverable": liveness == "dead",
        }
    )
    return 0


def command_recover_lock(args: argparse.Namespace) -> int:
    root = ensure_state_root(args.root, create=False)
    with lock_operation_gate(root):
        lock_path, raw, payload = read_lock(root)
        if payload["pid"] != args.expected_pid:
            raise AdapterError("lock PID does not match --expected-pid")
        if payload["token"] != args.expected_token:
            raise AdapterError("lock token does not match --expected-token")
        if process_liveness(payload["pid"]) != "dead":
            raise AdapterError("lock owner is not proven dead; refusing recovery")
        try:
            current = lock_path.read_bytes()
        except FileNotFoundError as exc:
            raise AdapterError("lock changed during recovery") from exc
        if current != raw:
            raise AdapterError("lock changed during recovery")
        removed = []
        for filename in (
            payload["bundle_temp_filename"],
            payload["owner_filename"],
        ):
            candidate = checked_child_path(root, filename)
            if not candidate.exists():
                continue
            metadata = candidate.stat()
            if not stat.S_ISREG(metadata.st_mode):
                raise AdapterError(
                    "lock-owned recovery target is not a regular file"
                )
            candidate.unlink()
            removed.append(filename)
        lock_path.unlink()
        removed.append(LOCK_FILENAME)
    print_json(
        {
            "status": "recovered",
            "removed": removed,
            "dead_pid": payload["pid"],
        }
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Explicit local host adapter for versioned product-decision-paf "
            "hypothesis state. It has no default storage path and no network access."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    load_parser = subparsers.add_parser(
        "load", help="validate and print the current bounded workspace state"
    )
    load_parser.add_argument("--root", required=True, type=Path)
    load_parser.set_defaults(handler=command_load)

    intent_parser = subparsers.add_parser(
        "validate-intent",
        help="validate a portable non-committable proposal intent",
    )
    intent_parser.add_argument("--intent", required=True, type=Path)
    intent_parser.set_defaults(handler=command_validate_intent)

    commit_parser = subparsers.add_parser(
        "commit", help="validate and atomically commit one explicit change set"
    )
    commit_parser.add_argument("--root", required=True, type=Path)
    commit_parser.add_argument("--change-set", required=True, type=Path)
    commit_parser.set_defaults(handler=command_commit)

    verify_parser = subparsers.add_parser(
        "verify", help="verify state semantics and the latest accepted receipt"
    )
    verify_parser.add_argument("--root", required=True, type=Path)
    verify_parser.set_defaults(handler=command_verify)

    inspect_parser = subparsers.add_parser(
        "inspect-lock",
        help="inspect the bounded lock record without changing it",
    )
    inspect_parser.add_argument("--root", required=True, type=Path)
    inspect_parser.set_defaults(handler=command_inspect_lock)

    recover_parser = subparsers.add_parser(
        "recover-lock",
        help="remove a lock only when its exact PID is proven dead",
    )
    recover_parser.add_argument("--root", required=True, type=Path)
    recover_parser.add_argument("--expected-pid", required=True, type=int)
    recover_parser.add_argument("--expected-token", required=True)
    recover_parser.set_defaults(handler=command_recover_lock)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except OutcomeUnknownError as exc:
        print(f"OUTCOME UNKNOWN: {exc}", file=sys.stderr)
        return 6
    except AdapterError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 5
    except OSError:
        print("ERROR: local filesystem operation failed", file=sys.stderr)
        return 5
    except RecursionError:
        print("ERROR: input exceeds the bounded nesting depth", file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
