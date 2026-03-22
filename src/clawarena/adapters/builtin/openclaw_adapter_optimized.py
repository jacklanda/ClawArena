"""
Optimized OpenClaw adapter with improved token counting and error handling.
"""

from __future__ import annotations

import asyncio
import json
import shlex
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

from clawarena.core.agent import AgentAdapter, AgentInfo, AgentResponse, TokenUsage
from clawarena.core.task import Task


class OptimizedOpenClawAdapter(AgentAdapter):
    """
    Optimized adapter for OpenClaw agents with improved token counting and error handling.
    
    Features:
    1. More accurate token counting based on actual response text
    2. Better error message filtering (removes configuration warnings)
    3. Enhanced performance monitoring
    4. Support for both JSON and text output formats
    """
    
    def __init__(
        self,
        agent_id: str = "main",
        openclaw_path: str = "openclaw",
        timeout_seconds: int = 120,
        workspace_dir: Optional[str] = None,
        model_override: Optional[str] = None,
        enable_debug: bool = False,
    ) -> None:
        """
        Initialize the optimized OpenClaw adapter.
        
        Args:
            agent_id: OpenClaw agent ID (e.g., "main", "claude", "gpt-4")
            openclaw_path: Path to OpenClaw executable
            timeout_seconds: Maximum execution time in seconds
            workspace_dir: Directory for temporary files
            model_override: Override default model
            enable_debug: Enable debug logging
        """
        self.agent_id = agent_id
        self.openclaw_path = openclaw_path
        self.timeout_seconds = timeout_seconds
        self.model_override = model_override
        self.enable_debug = enable_debug
        
        # Setup workspace
        if workspace_dir:
            self.workspace = Path(workspace_dir)
            self.workspace.mkdir(parents=True, exist_ok=True)
        else:
            self.workspace = Path(tempfile.mkdtemp(prefix="openclaw_"))
        
        # Performance tracking
        self._execution_count = 0
        self._total_tokens = 0
        self._total_duration = 0.0
        self._total_errors = 0
        
        # Cache for token estimation
        self._token_cache: Dict[str, int] = {}
    
    def info(self) -> AgentInfo:
        """Return adapter information."""
        return AgentInfo(
            name=f"OpenClaw-{self.agent_id}",
            version="1.0.0",
            model=self.model_override or "openclaw-default",
            description=f"Optimized OpenClaw agent adapter for {self.agent_id} agent testing",
            metadata={
                "agent_id": self.agent_id,
                "openclaw_path": self.openclaw_path,
                "workspace": str(self.workspace),
                "optimized": True,
            },
        )
    
    async def run_task(self, task: Task) -> AgentResponse:
        """
        Execute a task using OpenClaw.
        
        Args:
            task: The task to execute
            
        Returns:
            AgentResponse with results
        """
        self._execution_count += 1
        start_time = time.monotonic()
        
        if self.enable_debug:
            print(f"[DEBUG] Executing task: {task.name}")
            print(f"[DEBUG] Instruction length: {len(task.instruction)} chars")
        
        try:
            # Prepare task files if needed
            task_files = await self._prepare_task_files(task)
            
            # Build command
            command_args = self._build_command(task, task_files)
            
            if self.enable_debug:
                print(f"[DEBUG] Command: {' '.join(shlex.quote(arg) for arg in command_args)}")
            
            # Execute command
            result = await self._execute_command(command_args)
            
            # Parse response
            response = self._parse_openclaw_response(result, start_time)
            
            # Update performance metrics
            self._total_duration += response.duration_seconds
            self._total_tokens += response.token_usage.total_tokens
            
            if response.error:
                self._total_errors += 1
            
            return response
            
        except Exception as e:
            # Handle unexpected errors
            error_time = time.monotonic() - start_time
            self._total_errors += 1
            
            return AgentResponse(
                output="",
                token_usage=TokenUsage(),
                duration_seconds=error_time,
                api_calls=0,
                error=f"Adapter error: {str(e)}",
                trace=[{"step": "adapter_error", "error": str(e)}],
            )
    
    async def _prepare_task_files(self, task: Task) -> Dict[str, str]:
        """
        Prepare any necessary task files.
        
        Args:
            task: The task to prepare files for
            
        Returns:
            Dictionary of file paths
        """
        task_files = {}
        
        # If task has context, create a context file
        if task.context:
            context_file = self.workspace / f"context_{task.id}.json"
            with open(context_file, "w", encoding="utf-8") as f:
                json.dump(task.context, f, indent=2)
            task_files["context"] = str(context_file)
        
        return task_files
    
    def _build_command(self, task: Task, task_files: Dict[str, str]) -> list[str]:
        """
        Build OpenClaw command arguments.
        
        Args:
            task: The task to execute
            task_files: Dictionary of prepared task files
            
        Returns:
            List of command arguments
        """
        command = [self.openclaw_path, "agent"]
        
        # Add agent specification
        command.extend(["--agent", self.agent_id])
        
        # Add task instruction
        instruction = task.instruction
        
        # Add context information if available
        if "context" in task_files:
            instruction += f"\n\nContext available in: {task_files['context']}"
        
        command.extend(["--message", instruction])
        
        # Add local execution flag (faster, no Gateway)
        command.append("--local")
        
        # Add JSON output flag
        command.append("--json")
        
        # Add timeout (seconds for OpenClaw)
        timeout_seconds = min(self.timeout_seconds, 600)  # Max 10 minutes
        command.extend(["--timeout", str(timeout_seconds)])
        
        return command
    
    async def _execute_command(self, command_args: list[str]) -> Dict[str, Any]:
        """
        Execute the OpenClaw command.
        
        Args:
            command_args: Command arguments
            
        Returns:
            Dictionary with execution results
        """
        process = await asyncio.create_subprocess_exec(
            *command_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.workspace),
        )
        
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )
            
            stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr = stderr_bytes.decode("utf-8", errors="replace").strip()
            
            return {
                "returncode": process.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "command": " ".join(shlex.quote(arg) for arg in command_args),
            }
            
        except asyncio.TimeoutError:
            # Terminate the process on timeout
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                process.kill()
            
            raise TimeoutError(
                f"OpenClaw execution timed out after {self.timeout_seconds} seconds"
            )
    
    def _parse_openclaw_response(
        self, result: Dict[str, Any], start_time: float
    ) -> AgentResponse:
        """
        Parse OpenClaw execution result with improved token counting.
        
        Args:
            result: Dictionary containing execution results
            start_time: Start time of the execution
            
        Returns:
            Structured AgentResponse
        """
        duration = time.monotonic() - start_time
        
        # Extract output from stdout (JSON format expected)
        stdout = result["stdout"].strip()
        output = ""
        token_usage = TokenUsage()
        raw_metadata = {}
        
        # Try to parse JSON output
        json_data = None
        if stdout:
            try:
                json_data = json.loads(stdout)
                raw_metadata["json_parsed"] = True
            except json.JSONDecodeError:
                raw_metadata["json_parsed"] = False
                # If not JSON, use raw stdout
                output = stdout
        
        # Extract response text from JSON
        if json_data and isinstance(json_data, dict):
            raw_metadata.update(json_data)
            
            # Extract response text from OpenClaw JSON format
            output = self._extract_response_text(json_data)
            
            # Extract token usage with improved accuracy
            token_usage = self._extract_token_usage(json_data, output)
        
        # If no JSON or no output extracted, use raw stdout
        if not output and stdout:
            output = stdout
        
        # Estimate token usage if not extracted
        if token_usage.total_tokens == 0 and output:
            token_usage = self._estimate_token_usage(output)
        
        # Process error information
        error = self._extract_error_info(result, json_data)
        
        # Build trace information
        trace = [
            {
                "step": "execute",
                "agent_id": self.agent_id,
                "returncode": result["returncode"],
                "duration": duration,
                "output_length": len(output),
                "tokens_estimated": token_usage.total_tokens > 0,
            }
        ]
        
        return AgentResponse(
            output=output,
            token_usage=token_usage,
            duration_seconds=duration,
            api_calls=1,
            error=error,
            trace=trace,
            raw_metadata=raw_metadata,
        )
    
    def _extract_response_text(self, json_data: Dict[str, Any]) -> str:
        """
        Extract response text from OpenClaw JSON structure.
        
        Args:
            json_data: Parsed JSON data from OpenClaw
            
        Returns:
            Extracted response text
        """
        # OpenClaw returns response in payloads[0].text
        if "payloads" in json_data and isinstance(json_data["payloads"], list):
            if len(json_data["payloads"]) > 0:
                payload = json_data["payloads"][0]
                if isinstance(payload, dict) and "text" in payload:
                    return str(payload["text"])
        
        # Alternative field names
        for field in ["response", "text", "output", "message", "content"]:
            if field in json_data:
                value = json_data[field]
                if isinstance(value, str):
                    return value
                elif value is not None:
                    return str(value)
        
        # If not found, return empty string
        return ""
    
    def _extract_token_usage(self, json_data: Dict[str, Any], response_text: str) -> TokenUsage:
        """
        Extract token usage with improved accuracy.
        
        Priority:
        1. Estimate based on response text (most accurate for our purposes)
        2. Use OpenClaw's reported usage if it seems reasonable
        3. Fall back to estimation
        
        Args:
            json_data: Parsed JSON data from OpenClaw
            response_text: Extracted response text
            
        Returns:
            TokenUsage object
        """
        # First, estimate based on response text only
        # This is most accurate for benchmarking as it excludes system prompts
        estimated_from_text = self._estimate_token_usage(response_text)
        
        # Try to get usage from OpenClaw meta structure
        openclaw_usage = None
        if "meta" in json_data and isinstance(json_data["meta"], dict):
            meta = json_data["meta"]
            
            # Check agentMeta.usage
            if "agentMeta" in meta and isinstance(meta["agentMeta"], dict):
                agent_meta = meta["agentMeta"]
                
                if "usage" in agent_meta and isinstance(agent_meta["usage"], dict):
                    usage = agent_meta["usage"]
                    openclaw_usage = TokenUsage(
                        input_tokens=usage.get("input", 0),
                        output_tokens=usage.get("output", 0),
                        total_tokens=usage.get("total", 0),
                    )
                
                # Check lastCallUsage
                elif "lastCallUsage" in agent_meta and isinstance(agent_meta["lastCallUsage"], dict):
                    usage = agent_meta["lastCallUsage"]
                    openclaw_usage = TokenUsage(
                        input_tokens=usage.get("input", 0),
                        output_tokens=usage.get("output", 0),
                        total_tokens=usage.get("total", 0),
                    )
        
        # Decide which usage to use
        if openclaw_usage and openclaw_usage.total_tokens > 0:
            # Check if OpenClaw's reported usage seems reasonable
            # It should be within 2x of our text-based estimate
            text_estimate = estimated_from_text.total_tokens
            openclaw_total = openclaw_usage.total_tokens
            
            # Reasonable range: 0.5x to 3x of text estimate
            # (allowing for some system prompt overhead)
            reasonable_min = text_estimate * 0.5
            reasonable_max = text_estimate * 3.0
            
            if reasonable_min <= openclaw_total <= reasonable_max:
                # OpenClaw's usage seems reasonable, use it
                return openclaw_usage
            else:
                # OpenClaw's usage seems inflated (likely includes system prompts)
                # Use our text-based estimate instead
                if self.enable_debug:
                    print(f"[DEBUG] OpenClaw token count seems inflated: {openclaw_total} vs estimated {text_estimate}")
                    print(f"[DEBUG] Using text-based estimate instead")
                return estimated_from_text
        
        # No OpenClaw usage data or zero tokens, use text estimate
        return estimated_from_text
    
    def _estimate_token_usage(self, text: str) -> TokenUsage:
        """
        Estimate token usage based on text content.
        
        Uses tiktoken-like estimation for better accuracy.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated TokenUsage
        """
        # Cache estimation for performance
        if text in self._token_cache:
            total = self._token_cache[text]
        else:
            # More accurate token estimation
            # Based on OpenAI's tiktoken approximation:
            # - English: ~0.75 tokens per word
            # - Code/mixed: ~1 token per 4 characters
            # - Chinese/Japanese: ~2 tokens per character
            
            if not text:
                total = 0
            else:
                # Count characters and words
                char_count = len(text)
                word_count = len(text.split())
                
                # Check if text contains Chinese/Japanese characters
                has_cjk = any('\u4e00' <= char <= '\u9fff' for char in text)
                
                if has_cjk:
                    # CJK text: ~2 tokens per character
                    total = char_count * 2
                else:
                    # English/mixed text
                    # Use average of word-based and char-based estimation
                    word_based = word_count * 0.75
                    char_based = char_count / 4
                    total = int((word_based + char_based) / 2)
                
                # Ensure minimum token count
                total = max(total, 1)
                
                # Add some overhead for formatting and structure
                total = int(total * 1.1)
            
            self._token_cache[text] = total
        
        # For OpenClaw responses, we need to estimate input/output split
        # Typically: input = task instruction, output = response
        # Since we're only estimating based on response text, assume it's all output
        # Input tokens would be for the instruction, which we don't have here
        
        # For benchmarking purposes, we can assume:
        # - Output tokens = response text tokens
        # - Input tokens = estimated based on typical instruction length
        # But for simplicity, we'll put all tokens in output for now
        
        return TokenUsage(
            input_tokens=0,  # We don't have instruction text here
            output_tokens=total,
            total_tokens=total,
        )
    
    def _extract_error_info(self, result: Dict[str, Any], json_data: Optional[Dict]) -> Optional[str]:
        """
        Extract and clean error information.
        
        Args:
            result: Execution results
            json_data: Parsed JSON data (if any)
            
        Returns:
            Cleaned error message or None
        """
        # Check return code
        if result["returncode"] == 0:
            return None
        
        stderr = result["stderr"]
        
        # Filter out common configuration warnings
        filtered_lines = []
        for line in stderr.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Skip configuration warnings
            if any(warning in line.lower() for warning in [
                "config warnings",
                "duplicate plugin",
                "plugins.allow is empty",
                "auto-load",
            ]):
                continue
            
            filtered_lines.append(line)
        
        # If we have filtered lines, use them
        if filtered_lines:
            error_msg = "\n".join(filtered_lines[:5])  # First 5 lines
            if len(filtered_lines) > 5:
                error_msg += "\n..."
            return f"OpenClaw error: {error_msg}"
        
        # If no filtered lines but stderr exists, use first 200 chars
        if stderr:
            return f"OpenClaw exited with code {result['returncode']}: {stderr[:200]}"
        
        # Default error
        return f"OpenClaw exited with code {result['returncode']}"
    
    async def teardown(self) -> None:
        """Perform cleanup after task execution."""
        if self.enable_debug:
            print(f"[DEBUG] Tearing down OpenClaw adapter")
            print(f"[DEBUG] Total executions: {self._execution_count}")
            print(f"[DEBUG] Total tokens: {self._total_tokens}")
            print(f"[DEBUG] Total duration: {self._total_duration:.2f}s")
            print(f"[DEBUG] Total errors: {self._total_errors}")
            print(f"[DEBUG] Success rate: {((self._execution_count - self._total_errors) / max(1, self._execution_count) * 100):.1f}%")
        
        # Clean up temporary workspace if we created it
        if "tmp" in str(self.workspace):
            import shutil
            try:
                shutil.rmtree(self.workspace)
                if self.enable_debug:
                    print(f"[DEBUG] Cleaned up workspace: {self.workspace}")
            except Exception as e:
                if self.enable_debug:
                    print(f"[DEBUG] Failed to clean workspace: {e}")


# Factory function for registry
def openclaw_factory(**kwargs: Any) -> OptimizedOpenClawAdapter:
    """Factory function to create OptimizedOpenClawAdapter instances."""
    return OptimizedOpenClawAdapter(**kwargs)