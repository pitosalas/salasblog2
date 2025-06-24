"""
Unified CLI for Salasblog2 - Static site generator with Raindrop.io integration.
"""
import argparse
import sys
from .generator import SiteGenerator
from .raindrop import RaindropDownloader


def cmd_generate(args):
    """Generate the static site"""
    generator = SiteGenerator(theme=args.theme)
    generator.generate_site()


def cmd_reset(args):
    """Delete all generated files"""
    generator = SiteGenerator()
    generator.reset_output()


def cmd_deploy(args):
    """Deploy site to Fly.io"""
    generator = SiteGenerator()
    generator.deploy_to_fly()


def cmd_themes(args):
    """List available themes"""
    generator = SiteGenerator()
    generator.list_themes()


def cmd_sync_raindrops(args):
    """Download new bookmarks from Raindrop.io"""
    downloader = RaindropDownloader()
    downloader.download_raindrops(reset=args.reset, count=args.count)


def cmd_server(args):
    """Start the FastAPI server"""
    import uvicorn
    from .server import app
    
    print(f"🚀 Starting server on http://localhost:{args.port}")
    uvicorn.run(app, host="0.0.0.0", port=args.port, reload=args.reload)

def cmd_help(args):
    """Show help message"""
    print("salasblog2 - Static site generator with Raindrop.io integration")
    print()
    print("Commands:")
    print("  generate           - Process markdown files and generate static HTML site")
    print("  server             - Start FastAPI server to serve site with API endpoints")
    print("  reset              - Delete all generated files")
    print("  deploy             - Deploy site to Fly.io")
    print("  themes             - List available themes")
    print("  sync-raindrops     - Download new bookmarks from Raindrop.io (for link blog)")
    print("  help               - Show this help message")
    print()
    print("Options:")
    print("  --theme THEME      - Use specific theme (for generate command)")
    print("  --port PORT        - Port for server (default: 8000)")
    print("  --reload           - Enable auto-reload for development (server command)")
    print("  --reset            - Reset link blog cache (for sync-raindrops command)")
    print("  --count N          - Limit link blog download (for sync-raindrops command)")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Static site generator with Raindrop.io integration",
        add_help=False  # We'll handle help ourselves
    )
    
    # We'll handle theme in the generate subcommand instead
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate static site')
    generate_parser.add_argument('--theme', default='winer', 
                                help='Theme to use for site generation')
    generate_parser.set_defaults(func=cmd_generate)
    
    # Server command
    server_parser = subparsers.add_parser('server', help='Start FastAPI server')
    server_parser.add_argument('--port', type=int, default=8000,
                              help='Port to run server on (default: 8000)')
    server_parser.add_argument('--reload', action='store_true',
                              help='Enable auto-reload for development')
    server_parser.set_defaults(func=cmd_server)
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Delete generated files')
    reset_parser.set_defaults(func=cmd_reset)
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy to Fly.io')
    deploy_parser.set_defaults(func=cmd_deploy)
    
    # Themes command
    themes_parser = subparsers.add_parser('themes', help='List available themes')
    themes_parser.set_defaults(func=cmd_themes)
    
    # Sync raindrops command
    sync_parser = subparsers.add_parser('sync-raindrops', help='Download bookmarks from Raindrop.io for link blog')
    sync_parser.add_argument('--reset', action='store_true',
                           help='Delete all existing link blog posts and rebuild from scratch')
    sync_parser.add_argument('--count', type=int, metavar='N',
                           help='Limit the number of link blog posts to download')
    sync_parser.set_defaults(func=cmd_sync_raindrops)
    
    # Help command
    help_parser = subparsers.add_parser('help', help='Show help message')
    help_parser.set_defaults(func=cmd_help)
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no command specified, show help
    if not args.command:
        cmd_help(args)
        return
    
    # Execute the command
    args.func(args)


if __name__ == '__main__':
    main()