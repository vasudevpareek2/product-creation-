import subprocess
import asyncio
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import threading

logger = logging.getLogger(__name__)

class ScriptExecutor:
    def __init__(self, scripts_dir: str, config_dir: str, upload_dir: str, log_dir: str):
        self.scripts_dir = scripts_dir
        self.config_dir = config_dir
        self.upload_dir = upload_dir
        self.log_dir = log_dir
        
    async def execute_stage1(
        self,
        config_file: str,
        token_file: str,
        products_csv: str,
        variants_new_csv: str,
        variants_existing_csv: str,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """Execute create_products_and_variants.py"""
        script_path = os.path.join(self.scripts_dir, "create_products_and_variants.py")
        
        cmd = [
            "python", script_path,
            "--config", config_file,
            "--token-file", token_file,
            "--products-csv", products_csv,
            "--variants-new-csv", variants_new_csv,
            "--variants-existing-csv", variants_existing_csv
        ]
        
        if not dry_run:
            cmd.append("--execute")
        
        return await self._execute_command(cmd, "stage1")
    
    async def execute_stage2(
        self,
        config_file: str,
        token_file: str,
        enrichment_plan: str,
        dry_run: bool = True,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """Execute enrich_batch.py"""
        script_path = os.path.join(self.scripts_dir, "enrich_batch.py")
        
        cmd = [
            "python", script_path,
            "--config", config_file,
            "--token-file", token_file,
            "--plan", enrichment_plan
        ]
        
        if use_ai:
            cmd.append("--use-ai")
        
        if not dry_run:
            cmd.append("--execute")
        
        return await self._execute_command(cmd, "stage2")
    
    async def execute_stage3(
        self,
        config_file: str,
        token_file: str,
        enrichment_plan: str,
        source_sheet: str,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """Execute finalize_batch.py"""
        script_path = os.path.join(self.scripts_dir, "finalize_batch.py")
        
        cmd = [
            "python", script_path,
            "--config", config_file,
            "--token-file", token_file,
            "--plan", enrichment_plan,
            "--sheet", source_sheet
        ]
        
        if not dry_run:
            cmd.append("--execute")
        
        return await self._execute_command(cmd, "stage3")
    
    async def _execute_command(self, cmd: list, stage_name: str) -> Dict[str, Any]:
        """Execute a command and return results"""
        start_time = datetime.now()
        log_file = os.path.abspath(os.path.join(self.log_dir, f"{stage_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))
        
        try:
            # Run the command using subprocess in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            
            def run_subprocess():
                return subprocess.run(
                    cmd,
                    cwd=self.scripts_dir,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
            
            result = await loop.run_in_executor(None, run_subprocess)
            
            # Save logs
            with open(log_file, 'w', encoding='utf-8', errors='replace') as f:
                f.write(f"Command: {' '.join(cmd)}\n")
                f.write(f"Return code: {result.returncode}\n")
                f.write("\n=== STDOUT ===\n")
                f.write(result.stdout)
                f.write("\n=== STDERR ===\n")
                f.write(result.stderr)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Parse results from log files if they exist
            results = self._parse_results(stage_name, self.scripts_dir)
            
            success = result.returncode == 0
            logger.info(f"Command completed with return code: {result.returncode}, success: {success}")
            
            return {
                "success": success,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "log_file": log_file,
                "duration": duration,
                "results": results,
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing {stage_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "log_file": log_file,
                "started_at": start_time.isoformat(),
                "completed_at": datetime.now().isoformat()
            }
    
    def _parse_results(self, stage_name: str, scripts_dir: str) -> Dict[str, Any]:
        """Parse results from CSV log files created by scripts"""
        results = {}
        
        if stage_name == "stage1":
            results_file = os.path.join(scripts_dir, "results_log.csv")
            if os.path.exists(results_file):
                results["stage1_results"] = self._read_csv_results(results_file)
        
        elif stage_name == "stage2":
            results_file = os.path.join(scripts_dir, "enrichment_results_log.csv")
            if os.path.exists(results_file):
                results["stage2_results"] = self._read_csv_results(results_file)
        
        elif stage_name == "stage3":
            results_file = os.path.join(scripts_dir, "finalize_results_log.csv")
            if os.path.exists(results_file):
                results["stage3_results"] = self._read_csv_results(results_file)
        
        return results
    
    def _read_csv_results(self, csv_file: str) -> list:
        """Read results from CSV file"""
        import csv
        results = []
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    results.append(row)
        except Exception as e:
            logger.error(f"Error reading CSV results: {str(e)}")
        return results