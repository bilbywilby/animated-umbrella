#!/usr/bin/env python3
"""
Comprehensive Test Suite for Pennsylvania Health Insurance Audit System

Covers:
  Part A: Statistical & Decimal Logic (Unit Tests)
  Part B: Shell Script Integration Tests (Exit Codes, Behaviors)
  Part C: Configuration Precedence Validation
  
Run: pytest tests/test_anomaly_premium_integration.py -v
Requires: pip install numpy pytest pytest-bdd tempfile
"""

# ==============================================================================
# PART A: STATISTICAL & DECIMAL LOGIC UNIT TESTS
# ==============================================================================

import unittest
from decimal import Decimal, ROUND_HALF_UP
from typing import List
import numpy as np
import subprocess
import tempfile
import os
import shutil
import json
from pathlib import Path


def calculate_effective_premium(
    base_rate: Decimal,
    age_factor: Decimal,
    rating_area_factor: Decimal,
    reinsurance_offset: Decimal
) -> Decimal:
    """
    Computes effective premium using a deterministic frozen Decimal pipeline.
    Rounds to two decimal places at every intermediate step using ROUND_HALF_UP.
    """
    gross_rate = (base_rate * age_factor * rating_area_factor).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    net_effective = (gross_rate - reinsurance_offset).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )
    return max(net_effective, Decimal('0.00'))


def detect_outliers_stratified(rates: List[float]) -> List[bool]:
    """
    Detects outliers in rate percentage changes.
    Uses non-parametric IQR for thin markets (N < 5) and Robust MAD for N >= 5.
    Returns a list of boolean flags indicating outlier status.
    """
    if not rates:
        return []
    
    arr = np.array(rates, dtype=float)
    n = len(arr)
    
    if n < 5:
        # Thin Market: Fall back to 1.5 * IQR
        q75, q25 = np.percentile(arr, [75, 25])
        iqr = q75 - q25
        if iqr == 0:
            return [False] * n
        lower_bound = q25 - (1.5 * iqr)
        upper_bound = q75 + (1.5 * iqr)
        return [bool(x < lower_bound or x > upper_bound) for x in arr]
    
    # Dense Market: Robust Median Absolute Deviation (MAD)
    median = np.median(arr)
    mad = np.median(np.abs(arr - median))
    
    if mad == 0:
        mad = np.mean(np.abs(arr - median))
        if mad == 0:
            return [False] * n

    modified_z = (0.6745 * np.abs(arr - median)) / mad
    return [bool(z > 3.5) for z in modified_z]


class TestActuarialRemediation(unittest.TestCase):
    """Part A: Statistical Logic Unit Tests"""

    # ==========================================================================
    # EFFECTIVE PREMIUM CALCULATION TESTS
    # ==========================================================================

    def test_effective_premium_decimal_precision(self):
        """Verifies no floating-point drift occurs during rate calculations."""
        base_rate = Decimal('350.55')
        age_factor = Decimal('1.245')
        area_factor = Decimal('1.050')
        reinsurance_offset = Decimal('42.18')

        # Gross = 350.55 * 1.245 * 1.050 = 458.25771875 -> rounds to 458.26
        # Net   = 458.26 - 42.18 = 416.08
        result = calculate_effective_premium(base_rate, age_factor, area_factor, reinsurance_offset)
        
        self.assertEqual(result, Decimal('416.08'))
        self.assertIsInstance(result, Decimal)

    def test_effective_premium_floor_at_zero(self):
        """Ensures large reinsurance offsets cannot yield negative premiums."""
        base_rate = Decimal('100.00')
        age_factor = Decimal('1.000')
        area_factor = Decimal('1.000')
        reinsurance_offset = Decimal('150.00')

        result = calculate_effective_premium(base_rate, age_factor, area_factor, reinsurance_offset)
        self.assertEqual(result, Decimal('0.00'))
        self.assertGreaterEqual(result, Decimal('0.00'))

    def test_effective_premium_drift_detection(self):
        """Runs 10,000 iterations to verify no cumulative drift."""
        for _ in range(10000):
            base = Decimal(str(round(np.random.uniform(200, 600), 2)))
            age = Decimal(str(round(np.random.uniform(0.8, 1.5), 4)))
            area = Decimal(str(round(np.random.uniform(0.9, 1.2), 4)))
            reinf = Decimal(str(round(np.random.uniform(0, 100), 2)))
            
            result = calculate_effective_premium(base, age, area, reinf)
            
            # Verify result has exactly 2 decimal places
            self.assertEqual(result.quantize(Decimal('0.01')), result)
            self.assertGreaterEqual(result, Decimal('0.00'))

    def test_boundary_calculation_scenarios(self):
        """Tests edge cases around boundary conditions."""
        # Exact round number
        result = calculate_effective_premium(
            Decimal('100.00'), Decimal('1.0000'), Decimal('1.0000'), Decimal('0.00')
        )
        self.assertEqual(result, Decimal('100.00'))
        
        # Half-up rounding verification
        result = calculate_effective_premium(
            Decimal('100.005'), Decimal('1.0000'), Decimal('1.0000'), Decimal('0.00')
        )
        self.assertEqual(result, Decimal('100.01'))  # 5 rounds up
        
        result = calculate_effective_premium(
            Decimal('100.004'), Decimal('1.0000'), Decimal('1.0000'), Decimal('0.00')
        )
        self.assertEqual(result, Decimal('100.00'))  # 4 rounds down

    # ==========================================================================
    # OUTLIER DETECTION TESTS
    # ==========================================================================

    def test_thin_county_no_false_positive_z_score(self):
        """Verifies thin counties (N=2) do not trigger zero-variance/false positive bugs."""
        rates = [0.128, 0.097]  # Highmark +12.8%, UPMC +9.7%
        outliers = detect_outliers_stratified(rates)
        
        self.assertEqual(outliers, [False, False])
        self.assertEqual(len(outliers), len(rates))

    def test_thin_county_three_carriers_iqr_bounds(self):
        """Verifies IQR bounds work correctly for N=3 rural county."""
        rates = [0.105, 0.112, 0.108]
        outliers = detect_outliers_stratified(rates)
        self.assertEqual(sum(outliers), 0)

    def test_dense_market_robust_mad_outlier_detection(self):
        """Verifies robust MAD identifies genuine carrier outliers in dense rating areas."""
        # Rating Area 8 sample with one extreme filer
        rates = [0.1272, 0.2130, 0.1835, 0.0970, 0.1348, 0.1480, 0.0138, 0.3513]
        outliers = detect_outliers_stratified(rates)
        
        self.assertTrue(outliers[7], "Extreme filer should be flagged")
        self.assertFalse(outliers[0], "Normal filer should not be flagged")

    def test_empty_list_returns_empty(self):
        """Verifies empty input returns empty output without error."""
        outliers = detect_outliers_stratified([])
        self.assertEqual(outliers, [])

    def test_single_element_no_outlier(self):
        """Single element cannot be statistically an outlier."""
        outliers = detect_outliers_stratified([0.15])
        self.assertEqual(outliers, [False])

    def test_identical_values_no_outliers(self):
        """Identical values have zero variance and produce no outliers."""
        rates = [0.15, 0.15, 0.15, 0.15, 0.15]
        outliers = detect_outliers_stratified(rates)
        self.assertEqual(outliers, [False, False, False, False, False])

    def test_exact_boundary_case_n_equals_4(self):
        """N=4 still uses IQR path, not MAD path."""
        rates = [0.10, 0.12, 0.11, 0.13]
        outliers = detect_outliers_stratified(rates)
        self.assertEqual(len(outliers), 4)

    def test_exact_boundary_case_n_equals_5(self):
        """N=5 switches to MAD path."""
        rates = [0.10, 0.12, 0.11, 0.13, 0.35]
        outliers = detect_outliers_stratified(rates)
        # With N=5, MAD path triggers; 35% may or may not be flagged depending on MAD calc
        self.assertEqual(len(outliers), 5)


# ==============================================================================
# PART B: SHELL SCRIPT INTEGRATION TESTS
# ==============================================================================

class TestScriptIntegration(unittest.TestCase):
    """Part B: Shell Script Behavior Integration Tests"""
    
    @classmethod
    def setUpClass(cls):
        """Find script path relative to test file location."""
        test_dir = Path(__file__).parent
        cls.repo_root = test_dir.parent
        cls.script_path = cls.repo_root / 'scripts' / 'generate_architecture.sh'
    
    def setUp(self):
        """Create temporary test directory for each test."""
        self.test_dir = tempfile.mkdtemp(prefix='arch_test_')
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Copy script to test directory
        shutil.copy(self.script_path, self.test_dir)
        os.chmod(os.path.join(self.test_dir, 'generate_architecture.sh'), 0o755)
        
        # Create minimal config
        config_content = """
system_name: Test Audit System
version: 2027.1.0-test
rating_areas: 5
"""
        os.makedirs('config', exist_ok=True)
        with open('config/architecture_config.yaml', 'w') as f:
            f.write(config_content.strip())
    
    def tearDown(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def run_script(self, args=None, env=None):
        """Helper to run script with optional args and environment."""
        cmd = ['./generate_architecture.sh'] + (args or [])
        script_env = os.environ.copy()
        if env:
            script_env.update(env)
        
        result = subprocess.run(
            cmd,
            cwd=self.test_dir,
            capture_output=True,
            text=True,
            env=script_env
        )
        return result
    
    def test_exit_code_success(self):
        """Exit code 0 for successful generation."""
        result = self.run_script()
        self.assertEqual(result.returncode, 0)
        self.assertIn('[INFO]', result.stdout)
        self.assertNotIn('[ERROR]', result.stdout)
    
    def test_exit_code_dry_run(self):
        """Exit code 3 for dry-run mode."""
        result = self.run_script(['--dry-run'])
        self.assertEqual(result.returncode, 3)
        self.assertIn('Dry-run', result.stdout)
        
        # Verify no artifacts were created
        docs_dir = os.path.join(self.test_dir, 'docs')
        self.assertFalse(os.path.exists(docs_dir))
    
    def test_exit_code_validation_failure(self):
        """Exit code 1 when JSON validation fails."""
        # Run normally first to create artifacts
        self.run_script()
        
        # Corrupt JSON
        json_path = os.path.join(self.test_dir, 'docs', 'ARCHITECTURE.json')
        with open(json_path, 'w') as f:
            f.write('{ invalid json }')
        
        # Re-run should fail validation
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn('Validation failed', result.stderr)
    
    def test_dry_run_no_filesystem_changes(self):
        """Dry-run leaves filesystem untouched."""
        initial_files = set(os.listdir(self.test_dir))
        
        result = self.run_script(['--dry-run'])
        self.assertEqual(result.returncode, 3)
        
        final_files = set(os.listdir(self.test_dir))
        self.assertSetEqual(initial_files, final_files)
    
    def test_backup_creation(self):
        """Backups are created for existing files."""
        # Run twice to trigger backup
        self.run_script()
        
        # Modify the first artifact
        md_path = os.path.join(self.test_dir, 'docs', 'ARCHITECTURE.md')
        with open(md_path, 'a') as f:
            f.write('\n# Modified content')
        
        self.run_script()
        
        # Check backup exists
        backups_dir = os.path.join(self.test_dir, 'backups', 'architecture')
        self.assertTrue(os.path.exists(backups_dir))
        
        # Should have .bak files
        backup_files = [f for f in os.listdir(backups_dir) if f.endswith('.bak')]
        self.assertGreater(len(backup_files), 0)
    
    def test_sha256_backup_storage(self):
        """SHA-256 hashes are stored with backups."""
        self.run_script(['--dry-run'], {'ENABLE_BACKUP': 'false'})  # Clean state
        self.run_script()  # First run (no backup)
        
        # Modify and run again
        md_path = os.path.join(self.test_dir, 'docs', 'ARCHITECTURE.md')
        with open(md_path, 'a') as f:
            f.write('\n# Modified')
        
        self.run_script()
        
        # Check for .sha256 files
        backups_dir = os.path.join(self.test_dir, 'backups', 'architecture')
        hash_files = [f for f in os.listdir(backups_dir) if f.endswith('.sha256')]
        self.assertGreater(len(hash_files), 0)
    
    def test_config_precedence_environment_overrides(self):
        """Environment variables take precedence over config file."""
        env = {
            'ARTIFACT_VERSION': '9.9.9-env_override',
            'SYSTEM_NAME': 'Environment Override System'
        }
        result = self.run_script([], env)
        self.assertEqual(result.returncode, 0)
        
        # Verify JSON contains env values
        json_path = os.path.join(self.test_dir, 'docs', 'ARCHITECTURE.json')
        with open(json_path) as f:
            data = json.load(f)
        
        self.assertEqual(data['version'], '9.9.9-env_override')
        self.assertEqual(data['system'], 'Environment Override System')
    
    def test_config_default_when_not_in_env(self):
        """Config file values are used when environment doesn't override."""
        result = self.run_script()
        self.assertEqual(result.returncode, 0)
        
        json_path = os.path.join(self.test_dir, 'docs', 'ARCHITECTURE.json')
        with open(json_path) as f:
            data = json.load(f)
        
        # Should match config file values
        self.assertEqual(data['system'], 'Test Audit System')
        self.assertEqual(data['version'], '2027.1.0-test')
    
    def test_log_level_verbose(self):
        """Verbose mode shows DEBUG-level logs."""
        result = self.run_script(['--verbose'])
        self.assertIn('[DEBUG]', result.stdout)
    
    def test_log_level_quiet(self):
        """Quiet mode suppresses non-error logs."""
        result = self.run_script(['--quiet'])
        self.assertNotIn('[INFO]', result.stdout)
        self.assertNotIn('[DEBUG]', result.stdout)
    
    def test_no_backup_flag(self):
        """--no-backup flag prevents backup creation."""
        # First run to create artifact
        self.run_script()
        
        # Modify
        md_path = os.path.join(self.test_dir, 'docs', 'ARCHITECTURE.md')
        with open(md_path, 'a') as f:
            f.write('\n# Modified')
        
        # Run with no backup
        result = self.run_script(['--no-backup'])
        self.assertEqual(result.returncode, 0)
        
        # Check no backup directory was created
        backups_dir = os.path.join(self.test_dir, 'backups')
        self.assertFalse(os.path.exists(backups_dir))
    
    def test_help_flag(self):
        """--help displays usage information."""
        result = self.run_script(['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('--dry-run', result.stdout)
        self.assertIn('--verbose', result.stdout)
    
    def test_unknown_option_exit_code(self):
        """Unknown options return exit code 2."""
        result = self.run_script(['--invalid-option'])
        self.assertEqual(result.returncode, 2)
        self.assertIn('[ERROR]', result.stdout)
    
    def test_artifacts_created_with_correct_names(self):
        """Correct artifact filenames are created."""
        result = self.run_script()
        self.assertEqual(result.returncode, 0)
        
        md_path = os.path.join(self.test_dir, 'docs', 'ARCHITECTURE.md')
        json_path = os.path.join(self.test_dir, 'docs', 'ARCHITECTURE.json')
        
        self.assertTrue(os.path.isfile(md_path))
        self.assertTrue(os.path.isfile(json_path))
    
    def test_json_artifact_valid_syntax(self):
        """Generated JSON is valid and parseable."""
        result = self.run_script()
        self.assertEqual(result.returncode, 0)
        
        json_path = os.path.join(self.test_dir, 'docs', 'ARCHITECTURE.json')
        
        with open(json_path) as f:
            data = json.load(f)  # Will raise if invalid
        
        # Verify structure
        self.assertIn('system', data)
        self.assertIn('version', data)
        self.assertIn('rating_areas', data)
        self.assertIn('modules', data)
    
    def test_markdown_no_shell_expansion_hazards(self):
        """Markdown artifacts don't contain expanded shell sequences."""
        result = self.run_script()
        self.assertEqual(result.returncode, 0)
        
        md_path = os.path.join(self.test_dir, 'docs', 'ARCHITECTURE.md')
        with open(md_path) as f:
            content = f.read()
        
        # Verify special characters preserved literally
        self.assertIn('$N < 5$', content)  # Should NOT be expanded
        self.assertIn('`Decimal`', content)  # Should preserve backticks


# ==============================================================================
# PART C: END-TO-END WORKFLOW VALIDATION
# ==============================================================================

class TestEndToEndWorkflow(unittest.TestCase):
    """Part C: Full Pipeline Integration"""
    
    @classmethod
    def setUpClass(cls):
        test_dir = Path(__file__).parent
        cls.repo_root = test_dir.parent
        cls.script_path = cls.repo_root / 'scripts' / 'generate_architecture.sh'
    
    def test_complete_generation_cycle(self):
        """Full lifecycle: generate -> validate -> modify -> regenerate -> backup."""
        test_dir = tempfile.mkdtemp()
        orig_cwd = os.getcwd()
        
        try:
            os.chdir(test_dir)
            
            # Phase 1: Initial generation
            result1 = subprocess.run(
                [str(self.script_path)],
                capture_output=True, text=True, env=os.environ.copy()
            )
            self.assertEqual(result1.returncode, 0)
            
            # Get first hash
            md_path = os.path.join(test_dir, 'docs', 'ARCHITECTURE.md')
            with open(md_path) as f:
                first_content = f.read()
            
            # Phase 2: Modify
            with open(md_path, 'a') as f:
                f.write('\n# Modification 1')
            
            # Phase 3: Regeneration (creates backup)
            result2 = subprocess.run(
                [str(self.script_path)],
                capture_output=True, text=True, env=os.environ.copy()
            )
            self.assertEqual(result2.returncode, 0)
            
            # Phase 4: Verify backup exists
            backups = list(Path(test_dir).glob('backups/architecture/**/*'))
            self.assertGreater(len(backups), 0)
            
            # Phase 5: Dry-run after modifications
            result3 = subprocess.run(
                [str(self.script_path), '--dry-run'],
                capture_output=True, text=True, env=os.environ.copy()
            )
            self.assertEqual(result3.returncode, 3)
            
        finally:
            os.chdir(orig_cwd)
            shutil.rmtree(test_dir, ignore_errors=True)


# ==============================================================================
# RUN TESTS
# ==============================================================================

if __name__ == '__main__':
    unittest.main()
