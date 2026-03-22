"""
OpenClaw Agent Adapter for ClawArena.

This adapter enables testing of OpenClaw agents (lobsters 🦞) within the ClawArena
benchmarking framework. It provides integration with OpenClaw's agent execution
system, allowing any OpenClaw agent to be evaluated on real-world tasks.

Key features:
- Integration with OpenClaw's agent execution system
- Support for various OpenClaw agent types (Claude, GPT, Gemini, etc.)
- Real-time task execution with proper sandboxing
- Comprehensive metrics collection (tokens, duration, API calls)
- Error handling and graceful degradation
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional

from clawarena.core.agent import AgentAdapter, AgentInfo, AgentResponse, TokenUsage
from clawarena.core.task import Task


class OpenClawAdapter(AgentAdapter):
    """
    Adapter for executing tasks through OpenClaw agents.
    
    This adapter allows any OpenClaw agent (lobster 🦞) to be tested within
    the ClawArena benchmarking framework. It provides a bridge between
    ClawArena's task system and OpenClaw's agent execution capabilities.
    
    Args:
        agent_id: The ID of the OpenClaw agent to use (e.g., "claude", "gpt-4", "gemini")
        openclaw_path: Path to the OpenClaw executable (default: "openclaw")
        workspace_dir: Workspace directory for the agent (optional)
        model_override: Override the default model for the agent (optional)
        timeout_seconds: Maximum execution time per task in seconds (default: 300)
    """
    
    def __init__(
        self,
        agent_id: str = "claude",
        openclaw_path: str = "openclaw",
        workspace_dir: Optional[str] = None,
        model_override: Optional[str] = None,
        timeout_seconds: int = 300,
        **kwargs: Any,
    ) -> None:
        self.agent_id = agent_id
        self.openclaw_path = openclaw_path
        self.workspace_dir = Path(workspace_dir) if workspace_dir else None
        self.model_override = model_override
        self.timeout_seconds = timeout_seconds
        self._execution_count = 0
        
        # Validate OpenClaw installation
        self._validate_openclaw_installation()
    
    def info(self) -> AgentInfo:
        """Return information about this OpenClaw adapter."""
        return AgentInfo(
            name=f"OpenClaw-{self.agent_id}",
            version="1.0.0",
            model=self.model_override or self.agent_id,
            description=f"OpenClaw agent adapter for {self.agent_id} agent testing",
            metadata={
                "agent_id": self.agent_id,
                "openclaw_path": self.openclaw_path,
                "model_override": self.model_override,
                "timeout_seconds": self.timeout_seconds,
            },
        )
    
    async def run_task(self, task: Task) -> AgentResponse:
        """
        Execute a task using the configured OpenClaw agent.
        
        This method:
        1. Creates a temporary workspace for the task
        2. Prepares task context and instructions
        3. Executes the agent via OpenClaw CLI
        4. Captures and parses the response
        5. Returns structured metrics
        
        Args:
            task: The task to execute
            
        Returns:
            AgentResponse containing the execution results
        """
        self._execution_count += 1
        start_time = time.monotonic()
        
        try:
            # Create a temporary workspace for this task
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Prepare task files in the workspace
                task_files = self._prepare_task_workspace(temp_path, task)
                
                # Build the OpenClaw command
                command = self._build_openclaw_command(task, task_files)
                
                # Execute the command
                result = await self._execute_openclaw_command(command, temp_path)
                
                # Parse the response
                response = self._parse_openclaw_response(result, start_time)
                
                return response
                
        except Exception as e:
            # Handle execution errors gracefully
            duration = time.monotonic() - start_time
            return AgentResponse(
                output=f"Error executing task: {str(e)}",
                token_usage=TokenUsage(),
                duration_seconds=duration,
                api_calls=1,
                error=str(e),
                trace=[{"step": "error", "error": str(e)}],
            )
    
    def _validate_openclaw_installation(self) -> None:
        """Validate that OpenClaw is properly installed and accessible."""
        try:
            result = subprocess.run(
                [self.openclaw_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"OpenClaw command failed: {result.stderr}"
                )
        except FileNotFoundError:
            raise RuntimeError(
                f"OpenClaw not found at '{self.openclaw_path}'. "
                f"Please ensure OpenClaw is installed and in your PATH."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("OpenClaw version check timed out")
    
    def _prepare_task_workspace(self, workspace: Path, task: Task) -> Dict[str, Path]:
        """
        Prepare the workspace with task-related files.
        
        Args:
            workspace: Path to the temporary workspace directory
            task: The task to prepare
            
        Returns:
            Dictionary mapping file types to their paths
        """
        task_files = {}
        
        # Create task instruction file
        instruction_file = workspace / "task_instruction.txt"
        instruction_file.write_text(task.instruction)
        task_files["instruction"] = instruction_file
        
        # Create task context file (if context exists)
        if task.context:
            context_file = workspace / "task_context.json"
            context_file.write_text(json.dumps(task.context, indent=2))
            task_files["context"] = context_file
        
        # Create expected output file (for reference)
        if task.expected_output:
            expected_file = workspace / "expected_output.txt"
            expected_file.write_text(str(task.expected_output))
            task_files["expected"] = expected_file
        
        # Create any additional files from task context
        for key, value in task.context.items():
            if isinstance(value, str) and key.endswith("_file"):
                file_path = workspace / f"{key}.txt"
                file_path.write_text(value)
                task_files[key] = file_path
        
        return task_files
    
    def _build_openclaw_command(self, task: Task, task_files: Dict[str, Path]) -> list[str]:
        """
        Build the OpenClaw command for executing the task.
        
        Args:
            task: The task to execute
            task_files: Dictionary of prepared task files
            
        Returns:
            List of command arguments
        """
        command = [self.openclaw_path, "agent"]
        
        # Add agent specification if provided
        if self.agent_id:
            command.extend(["--agent", self.agent_id])
        
        # Add local flag to run embedded agent
        command.append("--local")
        
        # Add task instruction as message
        instruction = task.instruction
        if "context" in task_files:
            # Include context in the message
            try:
                context_content = task_files["context"].read_text(encoding="utf-8")
                context_data = json.loads(context_content)
                instruction += f"\n\nContext: {json.dumps(context_data, indent=2)}"
            except:
                instruction += f"\n\nContext file: {task_files['context']}"
        
        command.extend(["--message", instruction])
        
        # Add timeout
        command.extend(["--timeout", str(min(self.timeout_seconds, task.timeout_seconds))])
        
        # Add JSON output for easier parsing
        command.append("--json")
        
        return command
    
    async def _execute_openclaw_command(
        self, command: list[str], workspace: Path
    ) -> Dict[str, Any]:
        """
        Execute the OpenClaw command and capture results.
        
        Args:
            command: The command to execute
            workspace: Workspace directory for execution
            
        Returns:
            Dictionary containing execution results
        """
        # Create a log file for capturing output
        log_file = workspace / "execution.log"
        
        # Execute the command
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(workspace),
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )
            
            # Decode outputs
            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")
            
            # Write to log file
            log_file.write_text(
                f"Command: {' '.join(command)}\n\n"
                f"STDOUT:\n{stdout_text}\n\n"
                f"STDERR:\n{stderr_text}\n\n"
                f"Return code: {process.returncode}"
            )
            
            return {
                "stdout": stdout_text,
                "stderr": stderr_text,
                "returncode": process.returncode,
                "log_file": str(log_file),
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
        Parse OpenClaw execution results into an AgentResponse.
        
        Args:
            result: Dictionary containing execution results
            start_time: Start time of the execution
            
        Returns:
            Structured AgentResponse
        """
        duration = time.monotonic() - start_time
        
        # Extract output from stdout (now JSON format)
        stdout = result["stdout"].strip()
        output = ""
        token_usage = TokenUsage()
        
        try:
            # Try to parse JSON output
            if stdout:
                json_data = json.loads(stdout)
                
                # Extract response text from OpenClaw JSON format
                if isinstance(json_data, dict):
                    # OpenClaw returns response in payloads[0].text
                    if "payloads" in json_data and isinstance(json_data["payloads"], list):
                        if len(json_data["payloads"]) > 0:
                            payload = json_data["payloads"][0]
                            if isinstance(payload, dict) and "text" in payload:
                                output = payload["text"]
                    
                    # If not found in payloads, look for other fields
                    if not output:
                        for field in ["response", "text", "output", "message"]:
                            if field in json_data:
                                output = str(json_data[field])
                                break
                    
                    # If still not found, use the whole JSON as string
                    if not output:
                        output = json.dumps(json_data, indent=2)
                    
                    # Try to extract token usage from OpenClaw meta structure
                    if "meta" in json_data and isinstance(json_data["meta"], dict):
                        meta = json_data["meta"]
                        if "agentMeta" in meta and isinstance(meta["agentMeta"], dict):
                            agent_meta = meta["agentMeta"]
                            if "usage" in agent_meta and isinstance(agent_meta["usage"], dict):
                                usage = agent_meta["usage"]
                                # OpenClaw uses "input" and "output" keys
                                token_usage = TokenUsage(
                                    input_tokens=usage.get("input", 0),
                                    output_tokens=usage.get("output", 0),
                                    total_tokens=usage.get("total", 0),
                                )
                            elif "lastCallUsage" in agent_meta and isinstance(agent_meta["lastCallUsage"], dict):
                                usage = agent_meta["lastCallUsage"]
                                token_usage = TokenUsage(
                                    input_tokens=usage.get("input", 0),
                                    output_tokens=usage.get("output", 0),
                                    total_tokens=usage.get("total", 0),
                                )
        except json.JSONDecodeError:
            # If not JSON, use raw stdout
            output = stdout
        
        # Estimate token usage if not from JSON
        if token_usage.total_tokens == 0 and output:
            estimated_tokens = len(output.split()) * 1.3  # Approximate
            token_usage = TokenUsage(
                input_tokens=int(estimated_tokens),
                output_tokens=int(estimated_tokens),
                total_tokens=int(estimated_tokens * 2),
            )
        
        # Check for errors
        error = None
        if result["returncode"] != 0:
            error = f"OpenClaw exited with code {result['returncode']}: {result['stderr'][:500]}"
        
        # Build trace information
        trace = [
            {
                "step": "execute",
                "agent_id": self.agent_id,
                "returncode": result["returncode"],
                "duration": duration,
            }
        ]
        
        return AgentResponse(
            output=output,
            token_usage=token_usage,
            duration_seconds=duration,
            api_calls=1,
            error=error,
            trace=trace,
            raw_metadata={
                "openclaw_result": result,
                "execution_count": self._execution_count,
            },
        )
    
    async def setup(self) -> None:
        """Perform any necessary setup before task execution."""
        # Ensure workspace directory exists
        if self.workspace_dir:
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Test OpenClaw connectivity
        self._validate_openclaw_installation()
    
    async def teardown(self) -> None:
        """Perform cleanup after task execution."""
        # Currently no cleanup needed
        pass


# Factory function for easy instantiation
def create_openclaw_adapter(
    agent_id: str = "claude",
    **kwargs: Any,
) -> OpenClawAdapter:
    """
    Factory function to create an OpenClawAdapter instance.
    
    Args:
        agent_id: The ID of the OpenClaw agent to use
        **kwargs: Additional arguments passed to OpenClawAdapter
        
    Returns:
        Configured OpenClawAdapter instance
    """
    return OpenClawAdapter(agent_id=agent_id, **kwargs)