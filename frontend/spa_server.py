import argparse
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote


class SPARequestHandler(SimpleHTTPRequestHandler):
    """Static file handler with SPA fallback to index.html.

    If a path doesn't map to an existing file, serve index.html so
    client-side routes like /login and /signup work.
    """

    def do_GET(self):
        requested_path = unquote(self.path.split("?", 1)[0].split("#", 1)[0])

        # Let the base handler try normal file resolution first.
        # But if it would 404 for a "route" (no dot-extension), fall back to index.html.
        candidate = Path(self.directory) / requested_path.lstrip("/")

        if requested_path != "/" and not candidate.exists() and "." not in Path(requested_path).name:
            self.path = "/index.html"

        return super().do_GET()


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve a built SPA with history fallback")
    parser.add_argument("--directory", "-d", default="dist", help="Directory to serve")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", "-p", type=int, default=5173, help="Bind port")
    args = parser.parse_args()

    directory = os.path.abspath(args.directory)

    handler = lambda *h_args, **h_kwargs: SPARequestHandler(*h_args, directory=directory, **h_kwargs)
    server = ThreadingHTTPServer((args.host, args.port), handler)

    print(f"Serving SPA from {directory}")
    print(f"Listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
