"""
FastAPI server for Salasblog2 - serves static files + API endpoints
Includes Blogger API (XML-RPC) support for blog editors
"""
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response
from .generator import SiteGenerator
from .raindrop import RaindropDownloader
from .blogger_api import BloggerAPI

app = FastAPI(title="Salasblog2", description="Static site generator with API endpoints")

# Get paths
root_dir = Path(__file__).parent.parent.parent
output_dir = root_dir / "output"

# Mount static files
if output_dir.exists():
    app.mount("/static", StaticFiles(directory=output_dir / "static"), name="static")

@app.get("/")
async def serve_home():
    """Serve the home page"""
    home_file = output_dir / "index.html"
    if home_file.exists():
        return HTMLResponse(content=home_file.read_text(encoding='utf-8'))
    raise HTTPException(status_code=404, detail="Site not generated yet")

@app.get("/admin")
async def serve_admin():
    """Serve the admin page"""
    admin_file = root_dir / "templates" / "admin.html"
    if admin_file.exists():
        return HTMLResponse(content=admin_file.read_text(encoding='utf-8'))
    raise HTTPException(status_code=404, detail="Admin page not found")

@app.get("/api/sync-raindrops")
async def sync_raindrops():
    """Trigger raindrop sync and regenerate site"""
    try:
        # Download new raindrops
        downloader = RaindropDownloader()
        downloader.download_raindrops()
        
        # Regenerate site
        generator = SiteGenerator()
        generator.generate_site()
        
        return JSONResponse(content={
            "status": "success",
            "message": "Raindrops synced and site regenerated"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@app.get("/api/regenerate")
async def regenerate_site():
    """Regenerate the static site"""
    try:
        generator = SiteGenerator()
        generator.generate_site()
        
        return JSONResponse(content={
            "status": "success", 
            "message": "Site regenerated successfully"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")

@app.post("/xmlrpc")
async def xmlrpc_endpoint(request: Request):
    """XML-RPC endpoint for Blogger API"""
    try:
        body = await request.body()
        
        # Parse XML-RPC request
        root = ET.fromstring(body.decode('utf-8'))
        method_name = root.find('.//methodName').text
        params = []
        
        # Extract parameters
        param_nodes = root.findall('.//param/value')
        for param in param_nodes:
            # Handle different value types
            if param.find('string') is not None:
                params.append(param.find('string').text or "")
            elif param.find('boolean') is not None:
                params.append(param.find('boolean').text == '1')
            elif param.find('int') is not None:
                params.append(int(param.find('int').text))
            elif param.find('i4') is not None:
                params.append(int(param.find('i4').text))
            else:
                params.append(param.text or "")
        
        # Handle Blogger API methods
        api = BloggerAPI()
        
        if method_name == "blogger.newPost":
            result = api.blogger_newPost(*params)
        elif method_name == "blogger.editPost":
            result = api.blogger_editPost(*params)
        elif method_name == "blogger.deletePost":
            result = api.blogger_deletePost(*params)
        elif method_name == "blogger.getRecentPosts":
            result = api.blogger_getRecentPosts(*params)
        elif method_name == "blogger.getUsersBlogs":
            result = api.blogger_getUsersBlogs(*params)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method_name}")
        
        # Create XML-RPC response
        response_xml = create_xmlrpc_response(result)
        
        return Response(
            content=response_xml,
            media_type="text/xml",
            headers={"Content-Type": "text/xml"}
        )
        
    except Exception as e:
        # Return XML-RPC fault
        fault_xml = create_xmlrpc_fault(str(e))
        return Response(
            content=fault_xml,
            media_type="text/xml",
            status_code=500
        )


def create_xmlrpc_response(result):
    """Create XML-RPC response"""
    if isinstance(result, str):
        value = f"<string>{result}</string>"
    elif isinstance(result, bool):
        value = f"<boolean>{'1' if result else '0'}</boolean>"
    elif isinstance(result, int):
        value = f"<int>{result}</int>"
    elif isinstance(result, list):
        array_items = ""
        for item in result:
            if isinstance(item, dict):
                struct_members = ""
                for key, val in item.items():
                    struct_members += f"<member><name>{key}</name><value><string>{val}</string></value></member>"
                array_items += f"<value><struct>{struct_members}</struct></value>"
            else:
                array_items += f"<value><string>{item}</string></value>"
        value = f"<array><data>{array_items}</data></array>"
    else:
        value = f"<string>{str(result)}</string>"
    
    return f"""<?xml version="1.0"?>
<methodResponse>
    <params>
        <param>
            <value>{value}</value>
        </param>
    </params>
</methodResponse>"""


def create_xmlrpc_fault(message):
    """Create XML-RPC fault response"""
    return f"""<?xml version="1.0"?>
<methodResponse>
    <fault>
        <value>
            <struct>
                <member>
                    <name>faultCode</name>
                    <value><int>1</int></value>
                </member>
                <member>
                    <name>faultString</name>
                    <value><string>{message}</string></value>
                </member>
            </struct>
        </value>
    </fault>
</methodResponse>"""

# Serve all other routes as static files or 404
@app.get("/{path:path}")
async def serve_static_or_404(path: str):
    """Serve static files or 404"""
    # Try to serve as static file
    file_path = output_dir / path
    
    # If it's a directory, try index.html
    if file_path.is_dir():
        file_path = file_path / "index.html"
    
    # If no extension, try adding .html
    if not file_path.suffix and not file_path.exists():
        file_path = output_dir / f"{path}.html"
    
    if file_path.exists() and file_path.is_file():
        content_type = "text/html" if file_path.suffix == ".html" else None
        return HTMLResponse(
            content=file_path.read_text(encoding='utf-8'),
            media_type=content_type
        )
    
    raise HTTPException(status_code=404, detail="Page not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)