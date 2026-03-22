"""
OpenClaw Agent Adapter for ClawArena - Version 2

A more robust implementation with better error handling, configuration options,
and integration with ClawArena's CLI system.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from clawarena.core.agent import AgentAdapter, AgentInfo, AgentResponse, TokenUsage
from clawarena.core.task import Task


@dataclass
class OpenClawConfig:
    """Configuration for OpenClaw adapter."""
    
    # Required
    agent_id: str = "claude"
    
    # Optional with defaults
    openclaw_path: str = "openclaw"
    workspace_dir: Optional[str] = None
    model_override: Optional[str] = None
    timeout_seconds: int = 300
    max_output_length: int = 10000
    
    # Advanced options
    enable_debug: bool = False
    capture_logs: bool = True
    preserve_workspace: bool = False
    additional_args: List[str] = field(default_factory=list)
    
    # Environment
    env_vars: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_kwargs(cls, **kwargs) -> OpenClawConfig:
        """Create config from keyword arguments."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        config_kwargs = {k: v for k, v in kwargs.items() if k in valid_fields}
        return cls(**config_kwargs)


class OpenClawAdapter(AgentAdapter):
    """
    Robust adapter for executing tasks through OpenClaw agents.
    
    Features:
    - Comprehensive error handling and recovery
    - Detailed logging and traceability
    - Configurable execution parameters
    - Support for various OpenClaw agent types
    - Integration with ClawArena's scoring system
    """
    
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the OpenClaw adapter.
        
        Args:
            **kwargs: Configuration options (see OpenClawConfig for details)
        """
        self.config = OpenClawConfig.from_kwargs(**kwargs)
        self._execution_count = 0
        self._total_tokens = 0
        self._total_duration = 0.0
        
        # Create workspace if specified
        if self.config.workspace_dir:
            workspace_path = Path(self.config.workspace_dir)
            workspace_path.mkdir(parents=True, exist_ok=True)
            self._workspace = workspace_path
        else:
            self._workspace = None
        
        # Validate OpenClaw installation
        self._validate_installation()
    
    def info(self) -> AgentInfo:
        """Return information about this adapter."""
        return AgentInfo(
            name=f"OpenClaw-{self.config.agent_id}",
            version="2.0.0",
            model=self.config.model_override or self.config.agent_id,
            description=(
                f"OpenClaw agent adapter for {self.config.agent_id}. "
                f"Timeout: {self.config.timeout_seconds}s, "
                f"Debug: {self.config.enable_debug}"
            ),
            metadata={
                "agent_id": self.config.agent_id,
                "model": self.config.model_override or self.config.agent_id,
                "timeout_seconds": self.config.timeout_seconds,
                "openclaw_path": self.config.openclaw_path,
                "workspace_dir": str(self.config.workspace_dir) if self.config.workspace_dir else None,
                "execution_count": self._execution_count,
                "total_tokens": self._total_tokens,
                "total_duration": self._total_duration,
            },
        )
    
    async def run_task(self, task: Task) -> AgentResponse:
        """
        Execute a task using OpenClaw agent.
        
        This is the main entry point for task execution. It handles:
        - Workspace preparation
        - Command execution
        - Output parsing
        - Error handling
        - Metrics collection
        """
        self._execution_count += 1
        start_time = time.monotonic()
        
        try:
            # Prepare execution context
            context = self._prepare_execution_context(task)
            
            # Execute the task
            result = await self._execute_task(context)
            
            # Parse and validate the response
            response = self._parse_response(result, start_time)
            
            # Update statistics
            self._total_tokens += response.token_usage.total_tokens
            self._total_duration += response.duration_seconds
            
            return response
            
        except Exception as e:
            # Handle any unexpected errors
            duration = time.monotonic() - start_time
            error_response = self._create_error_response(e, duration, task)
            
            if self.config.enable_debug:
                print(f"[DEBUG] Task execution failed: {e}")
                import traceback
                traceback.print_exc()
            
            return error_response
    
    def _validate_installation(self) -> None:
        """Validate that OpenClaw is properly installed."""
        try:
            result = subprocess.run(
                [self.config.openclaw_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                env={**os.environ, **self.config.env_vars},
            )
            
            if result.returncode != 0:
                raise RuntimeError(
                    f"OpenClaw command failed with exit code {result.returncode}:\n"
                    f"STDERR: {result.stderr[:500]}"
                )
            
            if self.config.enable_debug:
                print(f"[DEBUG] OpenClaw version check passed: {result.stdout.strip()}")
                
        except FileNotFoundError:
            raise RuntimeError(
                f"OpenClaw not found at '{self.config.openclaw_path}'. "
                f"Please ensure OpenClaw is installed and in your PATH."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("OpenClaw version check timed out after 10 seconds")
    
    def _prepare_execution_context(self, task: Task) -> Dict[str, Any]:
        """Prepare all necessary files and context for task execution."""
        
        # Create temporary workspace for this execution
        if self.config.preserve_workspace and self._workspace:
            workspace = self._workspace / f"task_{task.id}_{int(time.time())}"
            workspace.mkdir(parents=True, exist_ok=True)
        else:
            workspace = Path(tempfile.mkdtemp(prefix=f"clawarena_{task.id}_"))
        
        # Prepare task files
        context = {
            "workspace": workspace,
            "task": task,
            "files": {},
            "start_time": time.monotonic(),
        }
        
        # Create instruction file
        instruction_file = workspace / "instruction.txt"
        instruction_content = self._format_instruction(task)
        instruction_file.write_text(instruction_content, encoding="utf-8")
        context["files"]["instruction"] = instruction_file
        
        # Create context file if context exists
        if task.context:
            context_file = workspace / "context.json"
            context_file.write_text(
                json.dumps(task.context, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            context["files"]["context"] = context_file
        
        # Create metadata file
        metadata = {
            "task_id": task.id,
            "task_name": task.name,
            "category": task.category.value,
            "difficulty": task.difficulty.value,
            "timeout": task.timeout_seconds,
            "created_at": time.time(),
        }
        
        metadata_file = workspace / "metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        context["files"]["metadata"] = metadata_file
        
        # Create expected output file for reference
        if task.expected_output:
            expected_file = workspace / "expected_output.txt"
            expected_file.write_text(str(task.expected_output), encoding="utf-8")
            context["files"]["expected"] = expected_file
        
        if self.config.enable_debug:
            print(f"[DEBUG] Prepared workspace at: {workspace}")
            print(f"[DEBUG] Created files: {list(context['files'].keys())}")
        
        return context
    
    def _format_instruction(self, task: Task) -> str:
        """Format task instruction for OpenClaw execution."""
        instruction = task.instruction.strip()
        
        # Add context information if available
        if task.context:
            context_summary = "\n\nAdditional Context:\n"
            for key, value in task.context.items():
                if isinstance(value, (str, int, float, bool)):
                    context_summary += f"- {key}: {value}\n"
                elif isinstance(value, list):
                    context_summary += f"- {key}: {', '.join(str(v) for v in value[:5])}"
                    if len(value) > 5:
                        context_summary += f" ... and {len(value) - 5} more"
                    context_summary += "\n"
            
            instruction += context_summary
        
        # Add task requirements
        instruction += "\n\nPlease provide your response in the following format:\n"
        instruction += "1. Complete the task as requested\n"
        instruction += "2. Be concise but thorough\n"
        instruction += "3. If you need clarification, state what's unclear\n"
        
        return instruction
    
    async def _execute_task(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the task using OpenClaw CLI."""
        workspace = context["workspace"]
        task = context["task"]
        
        # Build command
        command = self._build_command(context)
        
        if self.config.enable_debug:
            print(f"[DEBUG] Executing command: {' '.join(command)}")
            print(f"[DEBUG] Workspace: {workspace}")
        
        # Execute with timeout
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(workspace),
                env={**os.environ, **self.config.env_vars},
            )
            
            # Wait for completion with timeout
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.timeout_seconds,
                )
                
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                
            except asyncio.TimeoutExpired:
                # Terminate the process
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5)
                except asyncio.TimeoutExpired:
                    process.kill()
                
                raise TimeoutError(
                    f"Task execution timed out after {self.config.timeout_seconds} seconds"
                )
            
            # Capture logs if enabled
            if self.config.capture_logs:
                log_file = workspace / "execution.log"
                log_content = (
                    f"Command: {' '.join(command)}\n\n"
                    f"STDOUT:\n{stdout}\n\n"
                    f"STDERR:\n{stderr}\n\n"
                    f"Return code: {process.returncode}\n"
                    f"Duration: {time.monotonic() - context['start_time']:.2f}s"
                )
                log_file.write_text(log_content, encoding="utf-8")
            
            return {
                "stdout": stdout,
                "stderr": stderr,
                "returncode": process.returncode,
                "workspace": str(workspace),
                "log_file": str(workspace / "execution.log") if self.config.capture_logs else None,
            }
            
        except Exception as e:
            # Capture any execution errors
            error_log = workspace / "error.log"
            error_log.write_text(f"Execution error: {str(e)}\n", encoding="utf-8")
            raise
    
    def _build_command(self, context: Dict[str, Any]) -> List[str]:
        """Build OpenClaw command for task execution."""
        task = context["task"]
        workspace = context["workspace"]
        
        command = [self.config.openclaw_path]
        
        # Basic agent execution command
        command.extend(["agent", "run", self.config.agent_id])
        
        # Add instruction from file
        instruction_file = context["files"]["instruction"]
        command.extend(["--task", f"@{instruction_file}"])
        
        # Add model override if specified
        if self.config.model_override:
            command.extend(["--model", self.config.model_override])
        
        # Add timeout
        command.extend(["--timeout", str(min(self.config.timeout_seconds, task.timeout_seconds))])
        
        # Add additional arguments
        command.extend(self.config.additional_args)
        
        # Add workspace context if available
        if "context" in context["files"]:
            command.extend(["--context-file", str(context["files"]["context"])])
        
        return command
    
    def _parse_response(self, result: Dict[str, Any], start_time: float) -> AgentResponse:
        """Parse OpenClaw execution results into AgentResponse."""
        duration = time.monotonic() - start_time
        
        # Extract and clean output
        output = result["stdout"].strip()
        
        # Truncate if too long
        if len(output) > self.config.max_output_length:
            output = output[:self.config.max_output_length] + "\n...[output truncated]"
        
        # Estimate token usage (approximate)
        # In production, this should parse actual token counts from OpenClaw
        input_tokens = self._estimate_tokens(result.get("stdout", ""))
        output_tokens = self._estimate_tokens(output)
        
        # Check for errors
        error = None
        if result["returncode"] != 0:
            error_msg = result["stderr"].strip() or "Unknown error"
            error = f"OpenClaw exited with code {result['returncode']}: {error_msg[:200]}"
        
        # Build trace information
        trace = [
            {
                "step": "execute",
                "agent_id": self.config.agent_id,
                "returncode": result["returncode"],
                "duration": duration,
                "workspace": result.get("workspace"),
            }
        ]
        
        # Add debug info if enabled
        if self.config.enable_debug:
            trace.append({
                "step": "debug",
                "stdout_preview": result["stdout"][:200] + "..." if len(result["stdout"]) > 200 else result["stdout"],
                "stderr_preview": result["stderr"][:200] + "..." if len(result["stderr"]) > 200 else result["stderr"],
            })
        
        return AgentResponse(
            output=output,
            token_usage=TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            ),
            duration_seconds=duration,
            api_calls=1,
            error=error,
            trace=trace,
            raw_metadata={
                "openclaw_result": {
                    "returncode": result["returncode"],
                    "workspace": result.get("workspace"),
                    "log_file": result.get("log_file"),
                },
                "config": {
                    "agent_id": self.config.agent_id,
                    "model": self.config.model_override,
                    "timeout": self.config.timeout_seconds,
                },
            },
        )
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text (approximate)."""
        # Rough approximation: 1 token ≈ 4 characters for English
        # This should be replaced with actual token counting if available
        if not text:
            return 0
        
        # Count words and adjust for punctuation
        words = len(text.split())
        chars = len(text)
        
        # Use average of word-based and char-based estimates
        token_estimate = int((words * 1.3 + chars / 3.5) / 2)
        return max(10, token_estimate)  # Minimum 10 tokens
    
    def _create_error_response(self, error: Exception, duration: float, task: Task) -> AgentResponse:
        """Create an error response for failed executions."""
        return AgentResponse(
            output=f"Error executing task '{task.name}': {str(error)}",
            token_usage=TokenUsage(),
            duration_seconds=duration,
            api_calls=1,
            error=str(error),
            trace=[{"step": "error", "error_type": type(error).__name__, "message": str(error)}],
            raw_metadata={
                "error_details": {
                    "type": type(error).__name__,
                    "message": str(error),
                    "task_id": task.id,
                    "task_name": task.name,
                }
            },
        )
    
    async def setup(self) -> None:
        """Perform setup before task execution."""
        if self.config.enable_debug:
            print(f"[DEBUG] Setting up OpenClaw adapter for {self.config.agent_id}")
        
        # Validate installation
        self._validate_installation()
        
        # Prepare workspace if specified
        if self._workspace:
            self._workspace.mkdir(parents=True, exist_ok=True)
            if self.config.enable_debug:
                print(f"[DEBUG] Using workspace: {self._workspace}")
    
    async def teardown(self) -> None:
        """Perform cleanup after task execution."""
        if self.config.enable_debug:
            print(f"[DEBUG] Tearing down OpenClaw adapter")
            print(f"[DEBUG] Total executions: {self._execution_count}")
            print(f"[DEBUG] Total tokens: {self._total_tokens}")
            print(f"[DEBUG] Total duration: {self._total_duration:.2f}s")