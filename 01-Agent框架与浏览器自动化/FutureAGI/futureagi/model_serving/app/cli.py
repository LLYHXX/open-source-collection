"""
Command Line Interface for Model Serving

Provides CLI commands for running and managing the model serving application.
"""

import os
import sys

import click
import uvicorn
from app import __version__


@click.group()
@click.version_option(version=__version__, prog_name="model-serving")
def cli():
    """Model Serving CLI - High-performance embedding model serving service."""
    pass


@cli.command()
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind to (use 0.0.0.0 for all interfaces)",
    show_default=True,
)
@click.option(
    "--port", default=8080, type=int, help="Port to bind to", show_default=True
)
@click.option(
    "--workers",
    default=1,
    type=int,
    help="Number of worker processes",
    show_default=True,
)
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["debug", "info", "warning", "error", "critical"]),
    help="Log level",
    show_default=True,
)
@click.option(
    "--access-log/--no-access-log", default=True, help="Enable/disable access log"
)
def serve(host, port, workers, reload, log_level, access_log):
    """Start the model serving API server."""
    click.echo(f"🚀 Starting Model Serving API v{__version__}")
    click.echo(f"📡 Server: http://{host}:{port}")
    click.echo(f"👥 Workers: {workers}")
    click.echo(f"📊 Log Level: {log_level}")

    if reload and workers > 1:
        click.echo(
            "⚠️  Warning: --reload is incompatible with multiple workers. Setting workers=1"
        )
        workers = 1

    try:
        if workers > 1:
            # Use Gunicorn for multiple workers
            import gunicorn.app.wsgiapp as wsgi

            sys.argv = [
                "gunicorn",
                "app.main:app",
                f"--bind={host}:{port}",
                f"--workers={workers}",
                "--worker-class=uvicorn.workers.UvicornWorker",
                f"--log-level={log_level}",
                "--access-logfile=-" if access_log else "--access-logfile=/dev/null",
            ]
            wsgi.run()
        else:
            # Use Uvicorn for single worker or development
            uvicorn.run(
                "app.main:app",
                host=host,
                port=port,
                reload=reload,
                log_level=log_level,
                access_log=access_log,
            )
    except KeyboardInterrupt:
        click.echo("\n👋 Shutting down gracefully...")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--format",
    type=click.Choice(["json", "yaml", "table"]),
    default="table",
    help="Output format",
    show_default=True,
)
def models(format):
    """List available models and their status."""
    from app.servable_models.constants import get_all_model_configs

    configs = get_all_model_configs()

    if format == "json":
        import json

        click.echo(json.dumps(configs, indent=2))
    elif format == "yaml":
        import yaml

        click.echo(yaml.dump(configs, default_flow_style=False))
    else:
        # Table format
        click.echo("📋 Available Models:")
        click.echo("-" * 50)
        for model_name, config in configs.items():
            status = "✅ Available" if config.get("enabled", True) else "❌ Disabled"
            click.echo(f"{model_name:<25} {status}")


@cli.command()
@click.option(
    "--host", default="localhost", help="Server host to check", show_default=True
)
@click.option(
    "--port", default=8080, type=int, help="Server port to check", show_default=True
)
@click.option(
    "--timeout",
    default=10,
    type=int,
    help="Request timeout in seconds",
    show_default=True,
)
def health(host, port, timeout):
    """Check server health status."""
    import requests

    url = f"http://{host}:{port}/health"

    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            click.echo(f"✅ Server is healthy: {url}")
            data = response.json()
            if isinstance(data, dict):
                for key, value in data.items():
                    click.echo(f"   {key}: {value}")
        else:
            click.echo(f"❌ Server unhealthy: {response.status_code}", err=True)
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        click.echo(f"❌ Cannot connect to server: {url}", err=True)
        sys.exit(1)
    except requests.exceptions.Timeout:
        click.echo(f"⏰ Request timeout: {url}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def info():
    """Show system and package information."""
    import platform

    import torch

    click.echo(f"🚀 Model Serving v{__version__}")
    click.echo("-" * 40)
    click.echo(f"Python: {platform.python_version()}")
    click.echo(f"Platform: {platform.platform()}")
    click.echo(f"Architecture: {platform.architecture()[0]}")

    # PyTorch info
    if torch.cuda.is_available():
        click.echo(f"PyTorch: {torch.__version__} (CUDA {torch.version.cuda})")
        click.echo(f"CUDA Devices: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            name = torch.cuda.get_device_name(i)
            click.echo(f"  Device {i}: {name}")
    else:
        click.echo(f"PyTorch: {torch.__version__} (CPU only)")

    # Environment variables
    env_vars = [
        "MODEL_SERVING_URL",
        "CORS_ORIGINS",
        "ENABLE_DOCS",
        "CUDA_VISIBLE_DEVICES",
    ]

    click.echo("\n🔧 Environment:")
    for var in env_vars:
        value = os.getenv(var, "Not set")
        click.echo(f"  {var}: {value}")


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
